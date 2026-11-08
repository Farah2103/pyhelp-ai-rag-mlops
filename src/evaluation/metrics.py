import numpy as np

def overlaps(hit, evidence):
    return (hit["source_path"] == evidence["source_path"] and
        max(0,min(hit["end"],evidence["end"])-max(hit["start"],evidence["start"])) >= min(40,evidence["end"]-evidence["start"]))

def retrieval_metrics(hits, evidences):
    if not evidences: return {"recall":None,"precision":None,"all_evidence":None}
    # Evidence-group recall, independent of the chunk configuration. A hit must overlap >=40 chars.
    recovered = [any(overlaps(h,e) for h in hits) for e in evidences]
    return {"recall":sum(recovered)/len(recovered),
        "precision":sum(any(overlaps(h,e) for e in evidences) for h in hits)/len(hits) if hits else 0,
        "all_evidence":float(all(recovered))}

def summarize(rows):
    positive = [r for r in rows if r.get("recall") is not None]
    neg = [r for r in rows if r["expected_behavior"]=="abstention"]
    lat = [r["retrieval_ms"] for r in rows]
    result={"n":len(rows),"n_answerable":len(positive),"n_negative":len(neg),
        "recall_at_k":float(np.mean([r["recall"] for r in positive])) if positive else 0,
        "passage_precision_at_k":float(np.mean([r["precision"] for r in positive])) if positive else 0,
        "all_evidence_rate":float(np.mean([r["all_evidence"] for r in positive])) if positive else 0,
        "retrieval_mean_ms":float(np.mean(lat)),"retrieval_p95_ms":float(np.percentile(lat,95)),
        "guard_abstention_recall":sum(r["guard_abstains"] for r in neg)/len(neg) if neg else 0,
        "guard_false_abstention_rate":sum(r["guard_abstains"] for r in positive)/len(positive) if positive else 0,
        "error_rate":sum(bool(r.get("error")) for r in rows)/len(rows)}
    for lang in ["fr","en"]:
        subset=[r for r in positive if r["language"]==lang]
        result["recall_"+lang]=float(np.mean([r["recall"] for r in subset])) if subset else 0
    return result
