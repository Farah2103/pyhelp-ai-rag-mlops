"""Start a real local uvicorn process and exercise TCP endpoints; no paid LLM call."""
import json
import subprocess
import sys
import time
import httpx
from src.common import ROOT, write_json

def smoke():
    log=(ROOT/'reports/live_server.log').open('w')
    process=subprocess.Popen([sys.executable,'-m','uvicorn','api.main:app','--host','127.0.0.1','--port','8010'],cwd=ROOT,stdout=log,stderr=log)
    try:
        with httpx.Client(base_url='http://127.0.0.1:8010',trust_env=False,timeout=5) as client:
            for _ in range(100):
                try:
                    response=client.get('/health');break
                except httpx.ConnectError:time.sleep(.1)
            else:raise RuntimeError('API failed to start')
            invalid=client.post('/ask',json={'question':''});ui=client.get('/')
            assert response.status_code==200 and invalid.status_code==422 and ui.status_code==200
            write_json(ROOT/'reports/live_http_smoke.json',{'transport':'actual TCP localhost:8010; uvicorn subprocess','health':response.json(),'health_status':response.status_code,'invalid_ask_status':invalid.status_code,'ui_status':ui.status_code,'note':'Real LLM /ask exercised separately via FastAPI TestClient in demo_monitoring.'})
            print('Live TCP smoke PASS: /health 200, invalid /ask 422, HTML 200')
    finally:
        process.terminate();process.wait(timeout=10);log.close()
if __name__=='__main__':smoke()
