import json
import os
import httpx

class ProviderError(RuntimeError): pass
class LLM:
    def __init__(self, provider=None, model=None):
        from dotenv import load_dotenv
        from src.common import ROOT
        load_dotenv(ROOT / ".env", override=False)
        self.provider = provider or os.getenv("PYHELP_PROVIDER", "ollama")
        self.model = model or os.getenv("PYHELP_MODEL", "qwen2.5:1.5b")
        self.last_usage = {}
        if self.provider not in {"ollama", "mistral", "gemini", "transformers"}:
            raise ValueError("Unknown provider")
        if self.provider in {"mistral", "gemini"} and os.getenv("PYHELP_ALLOW_EXTERNAL") != "1":
            raise ValueError("External API requires PYHELP_ALLOW_EXTERNAL=1")
        self.local = None
        self.local_source = os.getenv("PYHELP_LLM_PATH", self.model)
    def complete(self, system, question, context):
        user = json.dumps({"question": question, "context": context}, ensure_ascii=False)
        messages = [{"role":"system", "content":system}, {"role":"user", "content":user}]
        try:
            if self.provider == "transformers":
                import torch
                from transformers import AutoTokenizer, AutoModelForCausalLM
                if self.local is None:
                    self.tokenizer = AutoTokenizer.from_pretrained(self.local_source, trust_remote_code=False, revision=None if os.getenv("PYHELP_LLM_PATH") else os.getenv("PYHELP_LLM_REVISION"))
                    self.local = AutoModelForCausalLM.from_pretrained(self.local_source, trust_remote_code=False, revision=None if os.getenv("PYHELP_LLM_PATH") else os.getenv("PYHELP_LLM_REVISION")).eval()
                prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                inputs = self.tokenizer(prompt, return_tensors="pt")
                with torch.inference_mode():
                    output = self.local.generate(**inputs, max_new_tokens=240, do_sample=False,
                        pad_token_id=self.tokenizer.eos_token_id)
                self.last_usage = {"input_tokens": inputs.input_ids.shape[1], "output_tokens": output.shape[1]-inputs.input_ids.shape[1]}
                return self.tokenizer.decode(output[0, inputs.input_ids.shape[1]:], skip_special_tokens=True)
            with httpx.Client(timeout=120, trust_env=self.provider != "ollama") as client:
                if self.provider == "ollama":
                    base = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
                    r = client.post(base + "/api/chat", json={"model":self.model,"messages":messages,
                        "stream":False,"format":"json","options":{"temperature":0,"seed":42,"num_predict":350}})
                    r.raise_for_status(); data = r.json()
                    self.last_usage = {"input_tokens":data.get("prompt_eval_count"), "output_tokens":data.get("eval_count")}
                    return data["message"]["content"]
                keyname = "MISTRAL_API_KEY" if self.provider == "mistral" else "GEMINI_API_KEY"
                key = os.getenv(keyname)
                model = os.getenv("MISTRAL_MODEL" if self.provider == "mistral" else "GEMINI_MODEL")
                if not key or not model: raise ProviderError("Missing API key or explicit API model")
                base = "https://api.mistral.ai/v1" if self.provider == "mistral" else "https://generativelanguage.googleapis.com/v1beta/openai"
                r = client.post(base + "/chat/completions", headers={"Authorization":"Bearer " + key},
                    json={"model":model,"messages":messages,"temperature":0,"max_tokens":350,
                        "response_format":{"type":"json_object"}})
                r.raise_for_status(); data = r.json(); self.last_usage = data.get("usage", {})
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            # Never reflect keys, request content or remote response bodies to clients/logs.
            raise ProviderError(type(e).__name__) from None
