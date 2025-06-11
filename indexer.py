import yaml
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Document
from llama_index.readers.web import BeautifulSoupWebReader, SimpleWebPageReader
import os
import requests
from urllib.parse import urlparse
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from concurrent.futures import ThreadPoolExecutor, as_completed

class Indexer:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.index_path = self.config.get('llama_index_path', './index/')
        self.embedding_model = HuggingFaceEmbedding(model_name=self.config['embedding_model'])
        self.sources = self.config['sources']
        self.index = None
    
    def load_from_custom_wiki(self, api_url, page_id):
        params = {
            "action": "parse",
            "format": "json",
            "pageid": page_id,
        }
        response = requests.get(api_url, params=params).json()
        page = response["parse"]["text"]["*"]
        if not page:
            print(f"Нет содержимого для {page_id}")
            return None
        return Document(text=page)
        
    # Получаем все страницы из википедии
    def get_all_wiki_titles(self, api_url):
        base_netloc = urlparse(api_url).netloc
        pages = []
        apcontinue = ''
        while True:
            params = {
                'action': 'query',
                'list': 'allpages',
                'aplimit': 'max',
                'format': 'json'
            }
            if apcontinue:
                params['apcontinue'] = apcontinue
            resp = requests.get(api_url, params=params)
            try:
                data = resp.json()
            except Exception:
                print("Ошибка ответа MediaWiki API:")
                print(resp.status_code, resp.headers.get('content-type'))
                print(resp.text[:500])
                raise
            # Проверяем, что не ушли на другой домен (на всякий случай)
            if urlparse(resp.url).netloc != base_netloc:
                print(f"Пропущен внешний домен: {resp.url}")
                break
            pages.extend([p['pageid'] for p in data['query']['allpages']])
            if 'continue' in data:
                apcontinue = data['continue']['apcontinue']
            else:
                break
        return pages

    def build_index(self):
        docs = []
        total_sources = len(self.sources)
        for src_idx, src in enumerate(self.sources, 1):
            print(f"[Источник {src_idx}/{total_sources}] type={src['type']} path/url={src.get('path') or src.get('url') or src.get('api_url')}")
            if src['type'] == 'local':
                reader = SimpleDirectoryReader(src['path'])
                local_docs = reader.load_data()
                print(f"  Загружено {len(local_docs)} документов из локального источника")
                docs.extend(local_docs)
            elif src['type'] == 'wiki':
                api_url = src.get('api_url')
                if api_url:
                    page_ids = self.get_all_wiki_titles(api_url)
                    docs = []
                    with ThreadPoolExecutor(max_workers=8) as executor:
                        futures = {executor.submit(self.load_from_custom_wiki, api_url, pid): pid for pid in page_ids}
                        for i, future in enumerate(as_completed(futures), 1):
                            doc = future.result()
                            if doc:
                                docs.append(doc)
                            print(f"  [{i}/{len(page_ids)}] wiki page loaded")
            elif src['type'] == 'swagger':
                reader = SimpleWebPageReader()
                print(f"  Индексирую Swagger по адресу: {src['url']}")
                swagger_docs = reader.load_data([src['url']])
                print(f"  Загружено {len(swagger_docs)} документов из Swagger")
                docs.extend(swagger_docs)
            elif src['type'] == 'website':
                reader = BeautifulSoupWebReader()
                print(f"  Индексирую сайт по адресу: {src['url']}")
                site_docs = reader.load_data([src['url']])
                print(f"  Загружено {len(site_docs)} документов с сайта")
                docs.extend(site_docs)
        print(f"Всего документов для индексации: {len(docs)}")
        self.index = VectorStoreIndex.from_documents(docs, embed_model=self.embedding_model)
        os.makedirs(self.index_path, exist_ok=True)
        self.index.storage_context.persist(persist_dir=self.index_path)

    def load_index(self):
        from llama_index.core import StorageContext, load_index_from_storage
        storage_context = StorageContext.from_defaults(persist_dir=self.index_path)
        self.index = load_index_from_storage(storage_context)

    def query(self, question):
        if self.index is None:
            self.load_index()
        query_engine = self.index.as_query_engine()
        return query_engine.query(question) 