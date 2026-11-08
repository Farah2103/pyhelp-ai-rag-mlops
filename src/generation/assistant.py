import json
import re
import time
from src.common import ROOT

ABSTAIN = "Information fiable insuffisante dans le corpus Python 3.11.18 / Insufficient reliable evidence."

def guard(question, hits, threshold):
    q = question.lower()
    if re.search(r"(?:python\s*)?3\.(?:1[2-9]|[2-9][0-9])\b", q): return "version_mismatch"
    if len(q.split()) < 3: return "ambiguous"
    if re.search(r"ignore (all|previous)|ignore.*instructions|révèle.*secret|reveal.*secret", q): return "unsafe_instruction"
    if not hits or hits[0]["score"] < threshold: return "low_retrieval_score"
    for h in hits:
        if re.search(r"ignore (all|previous).*instructions|reveal.*(?:secret|key)|system prompt", h["text"], re.I):
            return "suspicious_context"
    return None

class Assistant:
    def __init__(self, retriever, llm, threshold=None):
        self.retriever, self.llm = retriever, llm
        self.cfg = retriever.meta["config"]
        self.threshold = self.cfg["min_score"] if threshold is None else threshold
    def ask(self, question):
        start = time.perf_counter(); hits = self.retriever.search(question)
        reason = guard(question, hits, self.threshold); refs = []; answer = ABSTAIN; status = "abstention"
        used = []; length = 0
        if not reason:
            for hit in hits:
                if length + len(hit["text"]) > self.cfg["max_context_chars"]: break
                used.append(hit); length += len(hit["text"])
            prompt = (ROOT / "configs/prompt.txt").read_text(encoding="utf-8")
            context = [{"chunk_id":f"S{idx+1}", "source":h["source_path"], "section":h["section"], "text":h["text"]} for idx,h in enumerate(used)]
            raw = self.llm.complete(prompt, question, context)
            self.last_model_output = raw
            try:
                raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
                obj = json.loads(raw)
                if not isinstance(obj, dict): raise ValueError("Model JSON must be an object")
                ids = obj.get("citations", [])
                allowed = {f"S{idx+1}":h for idx,h in enumerate(used)}
                valid = (obj.get("status") == "answer" and isinstance(obj.get("answer"), str)
                    and bool(obj["answer"].strip()) and isinstance(ids, list) and len(ids) > 0
                    and all(isinstance(i,str) and i in allowed for i in ids))
                if valid:
                    answer = obj["answer"]; status = "answer"
                    refs = [{k: allowed[i][k] for k in ["chunk_id", "document_id", "source_path", "section", "version", "start", "end", "text"]}
                        for i in dict.fromkeys(ids)]
                    reason = "validated_citations_not_semantic_proof"
                else: reason = "model_abstention_or_invalid_citations"
            except (ValueError, TypeError): reason = "invalid_model_json"
        return {"answer":answer,"references":refs,"status":status,"reason":reason,
            "latency_ms":(time.perf_counter()-start)*1000,"retrieved_chunks":len(hits)}
