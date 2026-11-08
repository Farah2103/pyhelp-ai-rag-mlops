import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
import psutil
_lock = threading.Lock()
def record(event):
    p = Path(os.getenv("PYHELP_LOG", "monitoring/requests.jsonl")); p.parent.mkdir(parents=True, exist_ok=True)
    event.update({"timestamp":datetime.now(timezone.utc).isoformat(),"rss_mb":psutil.Process().memory_info().rss/1024**2})
    with _lock, p.open("a",encoding="utf-8") as f: f.write(json.dumps(event)+"\n")
