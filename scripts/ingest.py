import argparse
from src.common import ROOT
from src.ingestion.pipeline import ingest
if __name__ == "__main__":
    p=argparse.ArgumentParser();p.add_argument("archive");a=p.parse_args()
    r=ingest(a.archive,ROOT,ROOT/"configs/corpus.json");print({k:v for k,v in r.items() if k!="documents"})
