import argparse
from collections import Counter
import numpy as np
from src.common import write_json
from pathlib import Path
import json

def summarize(path):
    rows = [json.loads(x) for x in Path(path).read_text().splitlines() if x]
    ask = [r for r in rows if r["path"]=="/ask"]
    lat = [r["latency_ms"] for r in ask]
    return {"requests":len(rows),"ask_requests":len(ask),"http_errors":sum(r["http_status"]>=400 for r in ask),
        "server_errors":sum(r["http_status"]>=500 for r in ask),
        "observed_non_5xx_fraction":sum(r["http_status"]<500 for r in ask)/len(ask) if ask else None,
        "mean_ms":float(np.mean(lat)) if lat else None,"p95_ms":float(np.percentile(lat,95)) if lat else None,
        "statuses":dict(Counter(r["status"] for r in ask)),"max_rss_mb":max((r["rss_mb"] for r in rows), default=0),
        "mean_retrieved_chunks":float(np.mean([r["retrieved_chunks"] for r in ask])) if ask else None,
        "privacy":"No questions, answers, keys or user identity recorded. Abstentions linked by request ID only."}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("path"); a=p.parse_args(); s=summarize(a.path)
    write_json("reports/monitoring.json",s); print(json.dumps(s,indent=2))
