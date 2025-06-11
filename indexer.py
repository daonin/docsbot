import yaml
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.readers.web import BeautifulSoupWebReader, SimpleWebPageReader
from llama_index.readers.wikipedia import WikipediaReader
from sentence_transformers import SentenceTransformer
import os
import requests

class Indexer:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.index_path = self.config.get('llama_index_path', './index/')
        self.embedding_model = SentenceTransformer(self.config['embedding_model'])
        self.sources = self.config['sources']
        self.index = None
        
    # Получаем все страницы из википедии
    def get_all_wiki_titles(self, api_url):
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
            resp = requests.get(api_url, params=params).json()
            pages.extend([p['title'] for p in resp['query']['allpages']])
            if 'continue' in resp:
                apcontinue = resp['continue']['apcontinue']
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
                    titles = self.get_all_wiki_titles(api_url)
                    reader = WikipediaReader()
                    for title in titles:
                        try:
                            docs.extend(reader.load_data(pages=[title]))
                        except Exception as e:
                            print(f"Ошибка при загрузке {title}: {e}")
                else:
                    reader = WikipediaReader()
                    docs.extend(reader.load_data(pages=[src['url']]))
            elif src['type'] == 'swagger':
                reader = SimpleWebPageReader()
                docs.extend(reader.load_data([src['url']]))
            elif src['type'] == 'website':
                reader = BeautifulSoupWebReader()
                docs.extend(reader.load_data([src['url']]))
        self.index = VectorStoreIndex.from_documents(docs)
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