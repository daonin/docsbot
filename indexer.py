import yaml
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.readers.web import BeautifulSoupWebReader, WebBaseReader
from llama_index.readers.mediawiki import MediaWikiReader
from sentence_transformers import SentenceTransformer
import os

class Indexer:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.index_path = self.config.get('llama_index_path', './index/')
        self.embedding_model = SentenceTransformer(self.config['embedding_model'])
        self.sources = self.config['sources']
        self.index = None

    def build_index(self):
        docs = []
        for src in self.sources:
            if src['type'] == 'local':
                reader = SimpleDirectoryReader(src['path'])
                docs.extend(reader.load_data())
            elif src['type'] == 'wiki':
                reader = MediaWikiReader()
                docs.extend(reader.load_data(page_titles=[src['url']]))
            elif src['type'] == 'swagger':
                reader = WebBaseReader()
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