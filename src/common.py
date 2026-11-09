import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def digest(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode()).hexdigest()
def json_sha256_matches(path, expected):
    """Valide un SHA-256 en tolérant exclusivement la conversion LF/CRLF de Git."""
    content = Path(path).read_bytes().replace(b"\r\n", b"\n")
    return expected in (
        digest(content),
        digest(content.replace(b"\n", b"\r\n")),
    )

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
def write_json(path, obj):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    # Ecriture portable: toujours LF, y compris sous Windows.
    with p.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(obj, ensure_ascii=False, indent=2))
def config(path):
    c = read_json(path)
    if not (0 <= c["chunk_overlap"] < c["chunk_size"] <= 10000):
        raise ValueError("Invalid chunk sizes")
    if not (1 <= c["top_k"] <= 20 and -1 <= c["min_score"] <= 1):
        raise ValueError("Invalid retrieval parameters")
    return c
