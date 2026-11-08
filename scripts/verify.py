"""Integrity gate using original SHA256s, clean documents, stable chunk spans."""
from pathlib import Path
from src.common import ROOT, config, read_json, digest
from src.ingestion.pipeline import clean, chunk_documents

def verify():
    c=read_json(ROOT/"configs/corpus.json");inv=read_json(ROOT/"data/processed/inventory.json")
    assert len(c["documents"])==9 and set(c["documents"])=={d["source_path"] for d in inv["documents"]}
    for doc in inv["documents"]:
        data=(ROOT/"data/raw"/doc["source_path"]).read_bytes()
        assert digest(data)==doc["sha256"]
        text=(ROOT/"data/processed/documents"/doc["source_path"]).read_text(encoding="utf-8")
        assert clean(data.decode("utf-8"))==text and digest(text)==doc["clean_sha256"]
    for name in ["A","B"]:
        cfg=config(ROOT/f"configs/{name}.json");chunks=chunk_documents(ROOT,cfg)
        assert chunks and len(chunks)==len({x["chunk_id"] for x in chunks})
    qs=read_json(ROOT/"data/evaluation/questions.json");assert len(qs)>=30
    for q in qs:
        for e in q["expected_evidence"]:
            text=(ROOT/"data/processed/documents"/e["source_path"]).read_text(encoding="utf-8")
            assert text[e["start"]:e["end"]]==e["quote"],q["id"]
    print("Corpus/configuration/annotation integrity: PASS")
if __name__=="__main__":verify()
