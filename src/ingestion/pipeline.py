"""Safe, exact selection; untouched bytes in raw; offsets in cleaned documents."""
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath
from src.common import digest, read_json, write_json

def clean(text):
    # Preserve all code indentation, examples and headings. Only normalize line endings.
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("\x0c", "")

def sections(text):
    lines = text.splitlines(keepends=True); offset = 0; headings = []
    for i, line in enumerate(lines):
        if i + 1 < len(lines) and line.strip() and not line.startswith(" "):
            underline = lines[i + 1].strip()
            if len(underline) >= 3 and len(set(underline)) == 1 and underline[0] in "*=-~^":
                headings.append((offset, line.strip()))
        offset += len(line)
    if not headings or headings[0][0] != 0:
        headings.insert(0, (0, "Preamble"))
    return [{"title": title, "start": start, "end": headings[i+1][0] if i+1 < len(headings) else len(text)}
            for i, (start, title) in enumerate(headings)]

def ingest(archive, root, selection, verify_hash=True):
    root = Path(root); cfg = read_json(selection); archive = Path(archive)
    sha = digest(archive.read_bytes())
    if verify_hash and sha != cfg["archive_sha256"]:
        raise ValueError("Archive SHA256 differs from the approved corpus")
    documents = []; seen = set()
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            p = PurePosixPath(info.filename)
            if p.is_absolute() or ".." in p.parts or "\\" in info.filename or ":" in info.filename:
                raise ValueError("Unsafe ZIP path")
            if stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError("ZIP symlink forbidden")
            if info.filename in seen: raise ValueError("Duplicate ZIP member")
            seen.add(info.filename)
            if info.file_size > 25_000_000: raise ValueError("Oversized ZIP member")
        if sum(x.file_size for x in z.infolist()) > 100_000_000:
            raise ValueError("Oversized ZIP archive")
        bad = z.testzip()
        if bad: raise ValueError("CRC error: " + bad)
        selected = cfg["documents"]
        if len(selected) != len(set(selected)): raise ValueError("Duplicate selection")
        for path in selected:
            if path.startswith("/") or ".." in PurePosixPath(path).parts:
                raise ValueError("Unsafe selection")
            data = z.read(cfg["archive_prefix"] + path)
            text = clean(data.decode("utf-8", errors="strict"))
            if not text.strip(): raise ValueError("Empty source")
            for base, content in [("raw", data), ("processed/documents", text.encode("utf-8"))]:
                out = root / "data" / base / path; out.parent.mkdir(parents=True, exist_ok=True); out.write_bytes(content)
            ss = sections(text)
            documents.append({"document_id": digest(path)[:16], "source_path": path,
                "title": text.splitlines()[0], "version": cfg["version"], "sha256": digest(data),
                "clean_sha256": digest(text), "bytes": len(data), "characters": len(text),
                "sections": ss, "origin": "user-supplied Python documentation archive", "anomalies": []})
        for path in ["license.txt", "copyright.txt"]:
            data = z.read(cfg["archive_prefix"] + path)
            out = root / "legal" / path; out.parent.mkdir(parents=True, exist_ok=True); out.write_bytes(data)
    inventory = {"version": cfg["version"], "archive_sha256": sha, "documents": documents,
        "document_count": len(documents), "section_count": sum(len(x["sections"]) for x in documents),
        "total_bytes": sum(x["bytes"] for x in documents), "archive_crc_ok": True}
    write_json(root / "data/processed/inventory.json", inventory)
    return inventory

def chunk_documents(root, cfg):
    root = Path(root); inventory = read_json(root / "data/processed/inventory.json"); chunks = []
    size, overlap = cfg["chunk_size"], cfg["chunk_overlap"]
    if not 0 <= overlap < size: raise ValueError("Invalid chunk sizes")
    for doc in inventory["documents"]:
        text = (root / "data/processed/documents" / doc["source_path"]).read_text(encoding="utf-8")
        for sec in doc["sections"]:
            start = sec["start"]
            while start < sec["end"]:
                end = min(start + size, sec["end"])
                # Prefer a complete line; never remove leading indentation.
                if end < sec["end"]:
                    boundary = text.rfind("\n", start + size // 2, end)
                    if boundary > start: end = boundary + 1
                fragment = text[start:end]
                if fragment.strip():
                    meta = {k: doc[k] for k in ["document_id", "source_path", "title", "version"]}
                    meta.update({"section": sec["title"], "start": start, "end": end, "text": fragment})
                    meta["chunk_id"] = digest(doc["sha256"] + str(start) + str(end) + fragment)[:24]
                    chunks.append(meta)
                if end == sec["end"]: break
                start = max(start + 1, end - overlap)
    return chunks
