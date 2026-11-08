import hashlib
import json
import numpy as np
import pytest
class FakeEncoder:
    """Deterministic CI-only vectors; never used in reported real retrieval experiments."""
    def encode(self,texts):
        rows=[]
        for t in texts:
            h=hashlib.sha256(t.encode()).digest();a=np.frombuffer(h,dtype=np.uint8).astype("float32")
            a=a/max(np.linalg.norm(a),1e-9);rows.append(a)
        return np.array(rows,dtype="float32")
@pytest.fixture
def encoder():return FakeEncoder()
@pytest.fixture
def cfg():return {"name":"fixture","chunk_size":100,"chunk_overlap":20,"top_k":3,"min_score":0.3,"max_context_chars":6000,"embedding_model":"CI-only","embedding_revision":"fixture"}
@pytest.fixture
def hit():return {"chunk_id":"real-id","document_id":"doc-id","source_path":"tutorial/venv.txt","title":"Venv","version":"3.11.18","section":"Creating environments","text":"Run python -m venv tutorial-env.","start":0,"end":31,"score":0.9}
class FakeLLM:
    def complete(self,system,question,context):
        return json.dumps({"status":"answer","answer":"Run python -m venv tutorial-env.","citations":[context[0]["chunk_id"]]})
class FakeRetriever:
    def __init__(self,hits,cfg):self.hits=hits;self.meta={"config":cfg}
    def search(self,q,k=None):return self.hits
