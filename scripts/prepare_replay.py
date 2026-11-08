import os
import numpy as np
from src.common import ROOT,read_json,write_json,digest
from src.embeddings.encoder import Encoder
if __name__=="__main__":
    import torch
    torch.set_num_threads(2)
    c=read_json(ROOT/"artifacts/current/manifest.json")["config"]
    qs=read_json(ROOT/"data/evaluation/questions.json")
    encoder=Encoder(c["embedding_model"],c["embedding_revision"])
    vectors=encoder.encode([q["question"] for q in qs])
    p=ROOT/"artifacts/replay/queries.npy";p.parent.mkdir(parents=True,exist_ok=True);np.save(p,vectors,allow_pickle=False)
    write_json(p.parent/"manifest.json",{"ids":[q["id"] for q in qs],"embedding_revision":c["embedding_revision"],"sha256":digest(p.read_bytes())})
