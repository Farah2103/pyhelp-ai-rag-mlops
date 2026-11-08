import json
import pytest
from fastapi.testclient import TestClient
from api.main import app, get_assistant
from src.generation.providers import ProviderError
from src.generation.assistant import Assistant
from tests.conftest import FakeLLM, FakeRetriever
@pytest.fixture
def client(tmp_path,monkeypatch,hit,cfg):
    monkeypatch.setenv("PYHELP_LOG",str(tmp_path/"events.jsonl"))
    app.dependency_overrides.clear()
    import api.main as m
    monkeypatch.setattr(m,"get_assistant",lambda:Assistant(FakeRetriever([hit],cfg),FakeLLM()))
    with TestClient(app) as c:yield c

def test_health(client):assert client.get("/health").json()["status"]=="ok"
def test_ask(client):
    r=client.post("/ask",json={"question":"How to create a virtual environment?"})
    assert r.status_code==200 and r.json()["references"] and r.headers["X-Request-ID"]
@pytest.mark.parametrize("body",[{}, {"question":""},{"question":"   "},{"question":"a"*2001},{"question":123},{"question":"abc\u0000def"}])
def test_validation(client,body):assert client.post("/ask",json=body).status_code==422
def test_error(client,monkeypatch):
    class Bad:
        def ask(self,q):raise ProviderError("controlled")
    import api.main as m
    monkeypatch.setattr(m,"get_assistant",lambda:Bad())
    assert client.post("/ask",json={"question":"Explain Python exceptions please"}).status_code==503
def test_ui(client):assert 'PyHelp AI' in client.get('/').text
