import json
from pathlib import Path
import faiss
import numpy as np
from src.common import digest, read_json, write_json, json_sha256_matches
from src.ingestion.pipeline import chunk_documents

def build(root, cfg, encoder, output):
    root, out = Path(root), Path(output); out.mkdir(parents=True, exist_ok=True)
    chunks = chunk_documents(root, cfg)
    if not chunks: raise ValueError("Empty chunks")
    vectors = encoder.encode([c["text"] for c in chunks]); faiss.normalize_L2(vectors)
    index = faiss.IndexFlatIP(vectors.shape[1]); index.add(vectors)
    faiss.write_index(index, str(out / "index.faiss")); write_json(out / "chunks.json", chunks)
    meta = {"config": cfg, "corpus_sha256": digest((root / "data/processed/inventory.json").read_bytes()),
        "chunk_count": len(chunks), "dimension": vectors.shape[1], "metric": "cosine / normalized inner product",
        "index_sha256": digest((out / "index.faiss").read_bytes()),
        "chunks_sha256": digest((out / "chunks.json").read_bytes())}
    write_json(out / "manifest.json", meta)
    return meta

class Retriever:
    def __init__(self, folder, encoder):
        folder = Path(folder); self.meta = read_json(folder / "manifest.json")
        for file, key in [("index.faiss", "index_sha256"), ("chunks.json", "chunks_sha256")]:
            path = folder / file
            valid = json_sha256_matches(path, self.meta[key]) if file.endswith(".json") else digest(path.read_bytes()) == self.meta[key]
            if not valid: raise ValueError("Corrupt artifact")
        self.index = faiss.read_index(str(folder / "index.faiss"))
        self.chunks = read_json(folder / "chunks.json"); self.encoder = encoder
        if self.index.ntotal != len(self.chunks): raise ValueError("Index metadata mismatch")
    def search(self, question, k=None):
        q = self.encoder.encode([question]); faiss.normalize_L2(q)
        scores, ids = self.index.search(q, min(k or self.meta["config"]["top_k"], len(self.chunks)))
        return [dict(self.chunks[int(i)], score=float(score)) for i, score in zip(ids[0], scores[0]) if i >= 0]
