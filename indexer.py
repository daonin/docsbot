import yaml
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Document
from llama_index.readers.web import BeautifulSoupWebReader, SimpleWebPageReader
from sentence_transformers import SentenceTransformer
import os
import requests
from urllib.parse import urlparse

class Indexer:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.index_path = self.config.get('llama_index_path', './index/')
        self.embedding_model = SentenceTransformer(self.config['embedding_model'])
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
        for src in self.sources:
            if src['type'] == 'local':
                reader = SimpleDirectoryReader(src['path'])
                docs.extend(reader.load_data())
            elif src['type'] == 'wiki':
                api_url = src.get('api_url')
                if api_url:
                    page_ids = self.get_all_wiki_titles(api_url)
                    for page_id in page_ids:
                        try:
                            doc = self.load_from_custom_wiki(api_url, page_id)
                            if doc:
                                docs.append(doc)
                        except Exception as e:
                            print(f"Ошибка при загрузке {page_id}: {e}")
            elif src['type'] == 'swagger':
                reader = SimpleWebPageReader()
                docs.extend(reader.load_data([src['url']]))
            elif src['type'] == 'website':
                reader = BeautifulSoupWebReader()
                docs.extend(reader.load_data([src['url']]))
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