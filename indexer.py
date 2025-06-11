import yaml
from llama_index import VectorStoreIndex, SimpleDirectoryReader
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
        self.index = VectorStoreIndex.from_documents(docs, embed_model=self.embedding_model)
        os.makedirs(self.index_path, exist_ok=True)
        self.index.save_to_disk(os.path.join(self.index_path, 'index.json'))

    def load_index(self):
        self.index = VectorStoreIndex.load_from_disk(os.path.join(self.index_path, 'index.json'), embed_model=self.embedding_model)

    def query(self, question):
        if self.index is None:
            self.load_index()
        return self.index.query(question) 