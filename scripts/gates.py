"""Replay real precomputed query embeddings against the actual FAISS index in CI.
Does not evaluate changed encoders or real LLM responses; those require a full campaign.
"""
import numpy as np
import faiss
from src.common import ROOT, read_json, digest
from src.evaluation.metrics import retrieval_metrics
from scripts.verify import verify

def gates():
    verify()
    b=read_json(ROOT/"configs/baseline.json");m=read_json(ROOT/"artifacts/current/manifest.json")
    assert m["corpus_sha256"]==b["corpus_sha256"]
    assert digest((ROOT/"data/processed/inventory.json").read_bytes())==b["corpus_sha256"]
    assert digest((ROOT/"data/evaluation/questions.json").read_bytes())==b["questions_sha256"]
    for f,k in [("index.faiss","index_sha256"),("chunks.json","chunks_sha256")]:
        assert digest((ROOT/"artifacts/current"/f).read_bytes())==m[k]
    query_meta=read_json(ROOT/"artifacts/replay/manifest.json")
    assert query_meta["embedding_revision"]==m["config"]["embedding_revision"]
    p=ROOT/"artifacts/replay/queries.npy";assert digest(p.read_bytes())==query_meta["sha256"]
    qs=read_json(ROOT/"data/evaluation/questions.json");assert [q["id"] for q in qs]==query_meta["ids"]
    vectors=np.load(p,allow_pickle=False);ix=faiss.read_index(str(ROOT/"artifacts/current/index.faiss"))
    chunks=read_json(ROOT/"artifacts/current/chunks.json")
    _,ids=ix.search(vectors,m["config"]["top_k"])
    scores=[]
    for q,ii in zip(qs,ids):
        if q["split"]=="test" and q["expected_evidence"]:
            scores.append(retrieval_metrics([chunks[int(i)] for i in ii if i>=0],q["expected_evidence"])["recall"])
    score=float(np.mean(scores));assert score+1e-9>=b["minimum_recall"],(score,b["minimum_recall"])
    print(f"Frozen real-vector retrieval replay: PASS Recall={score:.6f}; floor={b['minimum_recall']:.6f}")
if __name__=="__main__":gates()
