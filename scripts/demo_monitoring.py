"""In-process HTTP demonstration. Controlled failure is injected only in this script."""
import os
from pathlib import Path
from fastapi.testclient import TestClient
from src.common import ROOT, write_json
from src.generation.providers import ProviderError
import api.main as api
from monitoring.summarize import summarize

def demo():
    path=ROOT/"monitoring/demo_requests.jsonl"
    if path.exists():path.unlink()
    os.environ["PYHELP_LOG"]=str(path)
    original=api.get_assistant
    responses=[]
    with TestClient(api.app) as c:
        for body in [{"question":"How do I create a virtual environment using venv?"},
                     {"question":"What is the capital city of Morocco?"},{"question":""}]:
            r=c.post("/ask",json=body);responses.append({"http_status":r.status_code,"body":r.json()})
        class ControlledFailure:
            def ask(self,q):raise ProviderError("controlled fixture")
        try:
            api.get_assistant=lambda:ControlledFailure()
            r=c.post("/ask",json={"question":"Explain Python modules please"})
            responses.append({"http_status":r.status_code,"body":r.json(),"fixture":"controlled provider failure"})
        finally:api.get_assistant=original
        c.get("/health")
    write_json(ROOT/"reports/demo_http.json",responses)
    write_json(ROOT/"reports/monitoring.json",summarize(path))
    print(summarize(path))
if __name__=="__main__":demo()
