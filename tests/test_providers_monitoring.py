import json
import pytest
from pathlib import Path
from src.generation.providers import LLM,ProviderError
from monitoring.events import record
from monitoring.summarize import summarize

def test_external_opt_in(monkeypatch):
    monkeypatch.setenv("PYHELP_ALLOW_EXTERNAL","0")
    with pytest.raises(ValueError,match="External API"):LLM("mistral")
    with pytest.raises(ValueError,match="External API"):LLM("gemini")
def test_unknown_provider():
    with pytest.raises(ValueError):LLM("unknown")
def test_ollama_payload(monkeypatch):
    class R:
        def raise_for_status(self):pass
        def json(self):return {"message":{"content":'{"status":"abstention"}'},"prompt_eval_count":12,"eval_count":3}
    class C:
        def __init__(self,*a,**k):pass
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def post(self,url,**kwargs):
            assert url.endswith('/api/chat') and kwargs['json']['stream'] is False
            assert kwargs['json']['options']['temperature']==0
            return R()
    monkeypatch.setattr('httpx.Client',C)
    l=LLM('ollama');assert 'abstention' in l.complete('system','question',[])
    assert l.last_usage['output_tokens']==3
@pytest.mark.parametrize('provider',['gemini','mistral'])
def test_api_choice(monkeypatch,provider):
    monkeypatch.setenv('PYHELP_ALLOW_EXTERNAL','1');monkeypatch.setenv(provider.upper()+'_API_KEY','fixture-not-a-key')
    monkeypatch.setenv(provider.upper()+'_MODEL','fixture-model')
    class R:
        def raise_for_status(self):pass
        def json(self):return {'choices':[{'message':{'content':'{}'}}],'usage':{'total_tokens':4}}
    class C:
        def __init__(self,*a,**k):pass
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def post(self,url,**kw):
            assert 'chat/completions' in url and kw['json']['model']=='fixture-model';return R()
    monkeypatch.setattr('httpx.Client',C)
    assert LLM(provider).complete('system','question',[])=='{}'
def test_error_sanitized(monkeypatch):
    class C:
        def __init__(self,*a,**k):raise RuntimeError('secret-do-not-leak')
    monkeypatch.setattr('httpx.Client',C)
    with pytest.raises(ProviderError) as e:LLM('ollama').complete('system','question',[])
    assert 'secret' not in str(e.value)
def test_private_monitoring(tmp_path,monkeypatch):
    p=tmp_path/'events.jsonl';monkeypatch.setenv('PYHELP_LOG',str(p))
    record({'request_id':'fixture','path':'/ask','status':'abstention','http_status':200,'latency_ms':10,'retrieved_chunks':3})
    record({'request_id':'fixture2','path':'/ask','status':'provider_error','http_status':503,'latency_ms':20,'retrieved_chunks':0})
    s=summarize(p);assert s['ask_requests']==2 and s['server_errors']==1 and s['p95_ms']==19.5
    assert all('question' not in r and 'answer' not in r for r in map(json.loads,p.read_text().splitlines()))
