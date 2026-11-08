import argparse
from src.common import ROOT, config
from src.embeddings.encoder import Encoder
from src.retrieval.index import build
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--config",default="configs/B.json");p.add_argument("--output",default="artifacts/current");a=p.parse_args()
    c=config(a.config);print(build(ROOT,c,Encoder(c["embedding_model"],c["embedding_revision"]),a.output))
