import argparse
from indexer import Indexer
import uvicorn
import yaml

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--reindex', action='store_true', help='Rebuild index')
    parser.add_argument('--config', default='config.yaml')
    args = parser.parse_args()

    indexer = Indexer(args.config)
    if args.reindex:
        indexer.build_index()
        print("Index rebuilt.")
    else:
        print("To rebuild index, run with --reindex. To start API: uvicorn api:app --reload") 