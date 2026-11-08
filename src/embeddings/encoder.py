import os
import json
import hashlib
from pathlib import Path
import numpy as np
class Encoder:
    def __init__(self, model, revision=None):
        from sentence_transformers import SentenceTransformer
        self.model_id = model; self.revision = revision
        override = os.getenv("PYHELP_EMBED_PATH")
        if override:
            manifest = Path(__file__).resolve().parents[2] / "reports/model_files.json"
            files = json.loads(manifest.read_text())
            required = [r for r in files if r["model"] == "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
                        and r["file"] in {"model.safetensors", "config.json", "tokenizer.json"}]
            if len(required) != 3: raise ValueError("Local embedding snapshot manifest missing")
            for row in required:
                with (Path(override) / row["file"]).open("rb") as f:
                    hasher=hashlib.sha256()
                    for block in iter(lambda:f.read(1024*1024),b""):hasher.update(block)
                if hasher.hexdigest()!=row["sha256"]:raise ValueError("Local embedding snapshot hash mismatch")
        self.model = SentenceTransformer(os.getenv("PYHELP_EMBED_PATH", model), revision=None if os.getenv("PYHELP_EMBED_PATH") else revision, device="cpu", trust_remote_code=False)
        # Preserve the model's documented max_seq_length (128 for multilingual MiniLM).
    def encode(self, texts):
        return np.asarray(self.model.encode(texts, batch_size=32, show_progress_bar=False,
            normalize_embeddings=True, convert_to_numpy=True), dtype="float32")
