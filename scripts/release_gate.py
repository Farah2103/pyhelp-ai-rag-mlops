"""Semantic promotion gate; kept separate from fast software CI.
Reviews are evidence, not inferred from citation membership. Fill review after inspecting outputs.
"""
import csv
from src.common import ROOT,read_json,digest

def check():
    rows=read_json(ROOT/"reports/generation.json")
    meta=read_json(ROOT/"reports/review_manifest.json")
    if digest((ROOT/"reports/generation.json").read_bytes())!=meta["generation_sha256"]:
        raise SystemExit("PROMOTION BLOCKED: review does not match generation outputs")
    reviews={r["id"]:r for r in csv.DictReader((ROOT/"reports/revue_generation.csv").open(encoding="utf-8"))}
    failures=[]
    critical={"q03","q07","q11","q15","q19","q22","q24","q25","q26","q28"}
    for r in rows:
        review=reviews.get(r["id"],{})
        if r["expected_behavior"]=="abstention" and r["status"]!="abstention":failures.append(r["id"]+": expected abstention")
        if r["id"] in critical:
            if review.get("exactitude_0_1_2")!="2" or review.get("fidelite_0_1_2")!="2":
                failures.append(r["id"]+": critical answer not verified correct and grounded")
        if r["status"]=="error":failures.append(r["id"]+": technical error")
    if failures:raise SystemExit("PROMOTION BLOCKED (runnable academic demonstrator): " + "; ".join(failures))
    print("Semantic promotion gate PASS on the reviewed benchmark only")
if __name__=="__main__":check()
