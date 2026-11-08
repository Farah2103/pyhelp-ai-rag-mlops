"""Attach final verification evidence to the local MLflow runs (no external service)."""
import sys
import platform
import importlib.metadata as md
from pathlib import Path
import mlflow
from src.common import ROOT,read_json,write_json,digest

def finalize():
    names=['numpy','faiss-cpu','sentence-transformers','transformers','torch','mlflow-skinny','dvc','fastapi','starlette','uvicorn','httpx','pydantic','python-dotenv','psutil','pytest','pathspec','msgpack','multidict','pip']
    env={'python':sys.version,'platform':platform.platform(),'packages':{n:md.version(n) for n in names},'tested_os':'Linux/Python 3.12; Windows and Python 3.11 not executed here'}
    write_json(ROOT/'reports/environment_final.json',env)
    mlflow.set_tracking_uri((ROOT/'mlruns').as_uri());client=mlflow.tracking.MlflowClient()
    selected=read_json(ROOT/'reports/comparison.json');generation=read_json(ROOT/'reports/generation_summary.json')
    for rid in [r['run_id'] for r in selected]+[generation['run_id']]:
        client.log_param(rid,'verified_python',platform.python_version())
        for name in ['torch','transformers','sentence-transformers']:client.log_param(rid,'verified_'+name,md.version(name))
        client.log_artifact(rid,str(ROOT/'reports/environment_final.json'))
        client.log_artifact(rid,str(ROOT/'requirements.txt'))
        client.log_artifact(rid,str(ROOT/'reports/model_files.json'))
    rid=generation['run_id']
    client.log_param(rid,'llm_revision',generation['llm_revision'])
    client.log_param(rid,'embedding_revision',read_json(ROOT/'artifacts/current/manifest.json')['config']['embedding_revision'])
    for file in ['assisted_review_summary.json','revue_generation.csv','review_manifest.json','robustness.json','promotion_gate.txt','rapport_technique.pdf']:
        client.log_artifact(rid,str(ROOT/'reports'/file),artifact_path='final_review')
    mlflow.set_experiment('PyHelp-monitoring')
    monitoring=read_json(ROOT/'reports/monitoring.json')
    with mlflow.start_run(run_name='local-http-demonstration'):
        mlflow.log_param('controlled_failure','one explicit provider fixture; no production fault endpoint')
        mlflow.log_metrics({k:v for k,v in monitoring.items() if isinstance(v,(int,float))})
        for f in ['monitoring.json','demo_http.json','live_http_smoke.json']:mlflow.log_artifact(str(ROOT/'reports'/f))
        mlflow.log_artifact(str(ROOT/'monitoring/demo_requests.jsonl'))
    runs=[]
    for e in client.search_experiments():
        for r in client.search_runs([e.experiment_id]):
            runs.append({'experiment':e.name,'run_id':r.info.run_id,'status':r.info.status,'params':r.data.params,'metrics':r.data.metrics})
    write_json(ROOT/'reports/mlflow_runs.json',runs)
    print('Local MLflow runs preserved:',len(runs))
if __name__=='__main__':finalize()
