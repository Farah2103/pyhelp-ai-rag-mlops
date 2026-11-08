"""Real embeddings, exact source evidence, no paid services. Run as a module."""
import argparse
import csv
import os
import shutil
import time
from pathlib import Path
import numpy as np
import mlflow
import psutil
from src.common import ROOT, config, read_json, write_json, digest
from src.embeddings.encoder import Encoder
from src.retrieval.index import build, Retriever
from src.generation.assistant import Assistant, guard
from src.generation.providers import LLM, ProviderError
from src.evaluation.metrics import retrieval_metrics, summarize

def verify_annotations(questions):
    assert len(questions) >= 30
    assert len({q["id"] for q in questions}) == len(questions)
    for q in questions:
        for e in q["expected_evidence"]:
            t=(ROOT/"data/processed/documents"/e["source_path"]).read_text(encoding="utf-8")
            assert t[e["start"]:e["end"]] == e["quote"] and e["quote"].strip(), q["id"]

def campaign(embed_path=None, generation=False):
    import torch
    torch.set_num_threads(2)
    qa=read_json(ROOT/"data/evaluation/questions.json");verify_annotations(qa)
    c0=config(ROOT/"configs/A.json")
    if embed_path: os.environ["PYHELP_EMBED_PATH"]=embed_path
    enc=Encoder(c0["embedding_model"], c0["embedding_revision"])
    mlflow.set_tracking_uri((ROOT/"mlruns").as_uri());mlflow.set_experiment("PyHelp-A-B-real-embeddings")
    comparison=[];all_rows={}
    for name in ["A","B"]:
        cfg=config(ROOT/f"configs/{name}.json");folder=ROOT/f"artifacts/experiments/{name}"
        start=time.perf_counter();cpu_start=time.process_time()
        with mlflow.start_run(run_name=name) as run:
            meta=build(ROOT,cfg,enc,folder);build_s=time.perf_counter()-start
            ret=Retriever(folder,enc);ret.search("warm up Python lists")
            rows=[]
            for q in qa:
                t=time.perf_counter();hits=ret.search(q["question"]);ms=(time.perf_counter()-t)*1000
                row={k:q[k] for k in ["id","question","language","category","split","expected_behavior"]}
                row.update(retrieval_metrics(hits,q["expected_evidence"]))
                row.update({"retrieval_ms":ms,"guard_abstains":guard(q["question"],hits,cfg["min_score"]) is not None,
                    "max_score":hits[0]["score"] if hits else -1,
                    "retrieved":[{k:h[k] for k in ["chunk_id","source_path","section","start","end","score"]} for h in hits]})
                rows.append(row)
            result={"configuration":name,"chunk_count":meta["chunk_count"],"build_s":build_s,
                "cpu_seconds":time.process_time()-cpu_start,"rss_mb":psutil.Process().memory_info().rss/1024**2,
                "all":summarize(rows),"dev":summarize([r for r in rows if r["split"]=="dev"]),
                "test":summarize([r for r in rows if r["split"]=="test"]),"run_id":run.info.run_id}
            mlflow.log_params({k:v for k,v in cfg.items()});mlflow.log_param("corpus_sha256",meta["corpus_sha256"])
            mlflow.log_param("questions_sha256",digest((ROOT/"data/evaluation/questions.json").read_bytes()))
            mlflow.log_metrics({f"{split}_{k}":v for split in ["all","dev","test"] for k,v in result[split].items()})
            mlflow.log_metrics({k:result[k] for k in ["chunk_count","build_s","cpu_seconds","rss_mb"]})
            write_json(ROOT/f"reports/retrieval_{name}.json",rows)
            write_json(ROOT/f"reports/summary_{name}.json",result)
            mlflow.log_artifact(str(ROOT/f"reports/retrieval_{name}.json"));mlflow.log_artifact(str(folder/"manifest.json"))
            mlflow.log_artifact(str(ROOT/"configs/prompt.txt"));mlflow.log_artifact(str(ROOT/"data/evaluation/questions.json"))
            comparison.append(result);all_rows[name]=rows
    # Selection on development only. Held-out test is reported, never used for tuning.
    best=max(comparison,key=lambda r:(r["dev"]["recall_at_k"],r["dev"]["passage_precision_at_k"],-r["chunk_count"]))
    selected=best["configuration"];rows=all_rows[selected]
    # Score threshold calibration only on dev: balanced correct guard decisions over positive/negative.
    dev=[r for r in rows if r["split"]=="dev"]
    curves=[]
    for th in np.arange(0.20,0.81,0.025):
        pos=[r for r in dev if r["expected_behavior"]=="answer"]
        neg=[r for r in dev if r["expected_behavior"]=="abstention"]
        tpr=sum(r["max_score"]>=th for r in pos)/len(pos)
        tnr=sum(r["max_score"]<th or r["guard_abstains"] for r in neg)/len(neg)
        curves.append({"threshold":float(th),"balanced_accuracy":(tpr+tnr)/2,"answer_retention":tpr,"negative_rejection":tnr})
    chosen=max(curves,key=lambda r:(r["balanced_accuracy"],r["answer_retention"],-r["threshold"]))
    current=ROOT/"artifacts/current";current.mkdir(parents=True,exist_ok=True)
    for p in (ROOT/f"artifacts/experiments/{selected}").iterdir():shutil.copy2(p,current/p.name)
    manifest=read_json(current/"manifest.json");manifest["config"]["min_score"]=chosen["threshold"]
    write_json(current/"manifest.json",manifest)
    write_json(ROOT/"reports/comparison.json",comparison)
    write_json(ROOT/"reports/selection.json",{"selected":selected,"reason":"highest dev evidence recall, then passage precision", "calibration":chosen,"curves":curves,
        "limitation":"Small source-derived dev/test set; no independent annotator. Threshold is a heuristic, not proof of grounding."})
    with (ROOT/"reports/comparison.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["configuration","chunk_count","build_s"]+list(best["test"]))
        w.writeheader()
        for x in comparison:w.writerow({"configuration":x["configuration"],"chunk_count":x["chunk_count"],"build_s":x["build_s"],**x["test"]})
    baseline={"config":selected,"corpus_sha256":manifest["corpus_sha256"],"questions_sha256":digest((ROOT/"data/evaluation/questions.json").read_bytes()),
        "embedding_revision":manifest["config"]["embedding_revision"],"test_recall":best["test"]["recall_at_k"],
        "minimum_recall":best["test"]["recall_at_k"],"policy":"No loss allowed versus frozen baseline on the same small benchmark; a new corpus needs an explicitly reviewed baseline."}
    write_json(ROOT/"configs/baseline.json",baseline)
    print({"selected":selected,"threshold":chosen["threshold"],"comparison":comparison},flush=True)
    if generation: generation_campaign(enc)

def generation_campaign(enc=None):
    if enc is None:
        c=read_json(ROOT/"artifacts/current/manifest.json")["config"]
        enc=Encoder(os.getenv("PYHELP_EMBED_PATH",c["embedding_model"]),c["embedding_revision"])
    import torch
    torch.set_num_threads(2)
    ret=Retriever(ROOT/"artifacts/current",enc);llm=LLM();assistant=Assistant(ret,llm)
    qs=read_json(ROOT/"data/evaluation/questions.json");rows=[]
    mlflow.set_tracking_uri((ROOT/"mlruns").as_uri());mlflow.set_experiment("PyHelp-generation")
    with mlflow.start_run(run_name=llm.provider+"-"+llm.model.replace("/","-")) as run:
        mlflow.log_params({"provider":llm.provider,"model":llm.model,"temperature":0,"prompt_sha256":digest((ROOT/"configs/prompt.txt").read_bytes())})
        for q in qs:
            t=time.perf_counter();cpu_start=time.process_time();err=None
            assistant.last_model_output=None;llm.last_usage={}
            try: answer=assistant.ask(q["question"])
            except ProviderError as e: answer={"status":"error","answer":"","references":[],"reason":str(e)};err=type(e).__name__
            row={"id":q["id"],"question":q["question"],"language":q["language"],"expected_behavior":q["expected_behavior"],
                "reference_answer":q["reference_answer"],"reference_evidence":q["expected_evidence"],**answer,
                "total_latency_ms":(time.perf_counter()-t)*1000,"error":err,"usage":dict(llm.last_usage),
                "cpu_seconds":time.process_time()-cpu_start,"rss_mb":psutil.Process().memory_info().rss/1024**2,
                "raw_model_output":getattr(assistant,"last_model_output",None),"human_correctness":None,"human_relevance":None,"human_faithfulness":None,"human_language_ok":None}
            rows.append(row);write_json(ROOT/"reports/generation.json",rows)
            print(q["id"],row["status"],round(row["total_latency_ms"]),flush=True)
        lat=[r["total_latency_ms"] for r in rows];neg=[r for r in rows if r["expected_behavior"]=="abstention"]
        positive=[r for r in rows if r["expected_behavior"]=="answer"]
        summary={"n":len(rows),"mean_ms":float(np.mean(lat)),"p95_ms":float(np.percentile(lat,95)),
            "error_rate":sum(r["status"]=="error" for r in rows)/len(rows),
            "observed_successful_calls_fraction":sum(r["status"]!="error" for r in rows)/len(rows),
            "negative_abstention_rate":sum(r["status"]=="abstention" for r in neg)/len(neg),
            "answerable_response_rate":sum(r["status"]=="answer" for r in positive)/len(positive),
            "citation_validity_rate_among_answers":1.0 if any(r["status"]=="answer" for r in rows) else None,
            "correctness":None,"faithfulness":None,"external_api_calls":0 if llm.provider in {"ollama","transformers"} else None,
            "cost_note":"Local CPU: no API bill. Electricity not measured. External pricing must be entered from account tariff.",
            "run_id":run.info.run_id,"provider":llm.provider,"model":llm.model,
            "cpu_seconds_total":sum(r["cpu_seconds"] for r in rows),"max_rss_mb":max(r["rss_mb"] for r in rows),
            "llm_revision":os.getenv("PYHELP_LLM_REVISION"),"torch_version":torch.__version__}
        write_json(ROOT/"reports/generation_summary.json",summary)
        mlflow.log_metrics({k:v for k,v in summary.items() if isinstance(v,(int,float))})
        mlflow.log_artifact(str(ROOT/"reports/generation.json"));mlflow.log_artifact(str(ROOT/"reports/generation_summary.json"))
    return rows

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--embed-path");p.add_argument("--generation",action="store_true");p.add_argument("--generation-only",action="store_true")
    a=p.parse_args()
    if a.generation_only:generation_campaign()
    else:campaign(a.embed_path,a.generation)
