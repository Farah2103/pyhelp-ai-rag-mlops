
"""Safe, exact selection; untouched bytes in raw; offsets in cleaned documents."""

import stat
import zipfile
from pathlib import Path, PurePosixPath

from src.common import digest, read_json, write_json


def clean(text):
    """Normalize line endings while preserving code indentation."""
    return (
        text.replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\x0c", "")
    )


def sections(text):
    """Detect documentation sections with exact character offsets."""
    lines = text.splitlines(keepends=True)
    offset = 0
    headings = []

    for i, line in enumerate(lines):
        if i + 1 < len(lines) and line.strip() and not line.startswith(" "):
            underline = lines[i + 1].strip()

            if (
                len(underline) >= 3
                and len(set(underline)) == 1
                and underline[0] in "*=-~^"
            ):
                headings.append((offset, line.strip()))

        offset += len(line)

    if not headings or headings[0][0] != 0:
        headings.insert(0, (0, "Preamble"))

    return [
        {
            "title": title,
            "start": start,
            "end": (
                headings[i + 1][0]
                if i + 1 < len(headings)
                else len(text)
            ),
        }
        for i, (start, title) in enumerate(headings)
    ]


def validate_zip_path(name, allow_directory=False):
    """Reject unsafe ZIP member names and traversal paths."""

    if not isinstance(name, str) or not name:
        raise ValueError("Invalid or empty ZIP path")

    if "\x00" in name:
        raise ValueError(f"Null byte in ZIP path: {name!r}")

    if "\\" in name:
        raise ValueError(f"Backslash forbidden in ZIP path: {name!r}")

    if name.startswith("/"):
        raise ValueError(f"Absolute ZIP path forbidden: {name!r}")

    if ":" in name:
        raise ValueError(f"Drive or colon forbidden in ZIP path: {name!r}")

    if name.endswith("/") and not allow_directory:
        raise ValueError(f"Directory path forbidden: {name!r}")

    normalized = name.rstrip("/") if allow_directory else name

    if not normalized:
        raise ValueError("Invalid ZIP path")

    parts = normalized.split("/")

    if any(part in ("", ".", "..") for part in parts):
        raise ValueError(f"Unsafe ZIP path: {name!r}")

    if PurePosixPath(normalized).is_absolute():
        raise ValueError(f"Absolute ZIP path forbidden: {name!r}")

    return True


def ingest(archive, root, selection, verify_hash=True):
    """Safely ingest selected Python documentation from a ZIP archive."""

    root = Path(root)
    archive = Path(archive)
    cfg = read_json(selection)

    sha = digest(archive.read_bytes())

    # 1. Verify archive SHA256.
    if verify_hash and sha != cfg["archive_sha256"]:
        raise ValueError(
            "Archive SHA256 differs from the approved corpus"
        )

    documents = []
    seen = set()

    with zipfile.ZipFile(archive) as z:

        # 2. Validate all archive members.
        members = z.infolist()

        for info in members:
            name = info.filename

            validate_zip_path(
                name,
                allow_directory=info.is_dir()
            )

            if stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError(
                    f"ZIP symlink forbidden: {name}"
                )

            if name in seen:
                raise ValueError(
                    f"Duplicate ZIP member: {name}"
                )

            seen.add(name)

            if info.file_size > 25_000_000:
                raise ValueError(
                    f"Oversized ZIP member: {name}"
                )

        # 3. Verify total uncompressed size.
        total_size = sum(
            info.file_size for info in members
        )

        if total_size > 100_000_000:
            raise ValueError("Oversized ZIP archive")

        # 4. Verify archive integrity.
        bad = z.testzip()

        if bad:
            raise ValueError("CRC error: " + bad)

        # 5. Validate selection configuration.
        selected = cfg["documents"]

        if len(selected) != len(set(selected)):
            raise ValueError("Duplicate selection")

        prefix = cfg["archive_prefix"]

        if not isinstance(prefix, str):
            raise ValueError("Invalid archive prefix")

        if prefix:
            if not prefix.endswith("/"):
                raise ValueError(
                    "Archive prefix must end with '/'"
                )

            validate_zip_path(prefix[:-1])

        archive_names = set(z.namelist())

        # 6. Validate all selected paths before reading.
        for path in selected:

            validate_zip_path(path)

            full_path = prefix + path

            validate_zip_path(full_path)

            if full_path not in archive_names:
                raise ValueError(
                    f"Selected document missing from ZIP: {full_path}"
                )

            if z.getinfo(full_path).is_dir():
                raise ValueError(
                    f"Selected document is a directory: {full_path}"
                )

        # 7. Read and process selected documents.
        for path in selected:

            full_path = prefix + path

            data = z.read(full_path)

            # IMPORTANT:
            # Invalid UTF-8 must raise UnicodeDecodeError.
            # Do not convert this exception to ValueError.
            text = clean(
                data.decode("utf-8", errors="strict")
            )

            if not text.strip():
                raise ValueError(
                    f"Empty source document: {full_path}"
                )

            # Save untouched raw bytes and cleaned text.
            outputs = [
                ("raw", data),
                (
                    "processed/documents",
                    text.encode("utf-8")
                ),
            ]

            for base, content in outputs:
                out = root / "data" / base / path

                out.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

                out.write_bytes(content)

            ss = sections(text)

            documents.append(
                {
                    "document_id": digest(path)[:16],
                    "source_path": path,
                    "title": text.splitlines()[0],
                    "version": cfg["version"],
                    "sha256": digest(data),
                    "clean_sha256": digest(text),
                    "bytes": len(data),
                    "characters": len(text),
                    "sections": ss,
                    "origin": (
                        "user-supplied Python documentation archive"
                    ),
                    "anomalies": [],
                }
            )

        # 8. Process legal files AFTER document decoding.
        # This preserves UnicodeDecodeError in the UTF-8 test.
        legal_files = [
            "license.txt",
            "copyright.txt",
        ]

        for path in legal_files:

            full_path = prefix + path

            validate_zip_path(full_path)

            if full_path not in archive_names:
                raise ValueError(
                    f"Required legal file missing: {full_path}"
                )

            if z.getinfo(full_path).is_dir():
                raise ValueError(
                    f"Legal file is a directory: {full_path}"
                )

            data = z.read(full_path)

            out = root / "legal" / path

            out.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            out.write_bytes(data)

    # 9. Generate document inventory.
    inventory = {
        "version": cfg["version"],
        "archive_sha256": sha,
        "documents": documents,
        "document_count": len(documents),
        "section_count": sum(
            len(x["sections"]) for x in documents
        ),
        "total_bytes": sum(
            x["bytes"] for x in documents
        ),
        "archive_crc_ok": True,
    }

    write_json(
        root / "data/processed/inventory.json",
        inventory
    )

    return inventory


def chunk_documents(root, cfg):
    """Create deterministic, overlapping document chunks."""

    root = Path(root)

    inventory = read_json(
        root / "data/processed/inventory.json"
    )

    chunks = []

    size = cfg["chunk_size"]
    overlap = cfg["chunk_overlap"]

    if not 0 <= overlap < size:
        raise ValueError("Invalid chunk sizes")

    for doc in inventory["documents"]:

        path = (
            root
            / "data/processed/documents"
            / doc["source_path"]
        )

        text = path.read_text(encoding="utf-8")

        for sec in doc["sections"]:

            start = sec["start"]

            while start < sec["end"]:

                end = min(
                    start + size,
                    sec["end"]
                )

                # Prefer complete lines without removing indentation.
                if end < sec["end"]:

                    boundary = text.rfind(
                        "\n",
                        start + size // 2,
                        end
                    )

                    if boundary > start:
                        end = boundary + 1

                fragment = text[start:end]

                if fragment.strip():

                    meta = {
                        k: doc[k]
                        for k in [
                            "document_id",
                            "source_path",
                            "title",
                            "version",
                        ]
                    }

                    meta.update(
                        {
                            "section": sec["title"],
                            "start": start,
                            "end": end,
                            "text": fragment,
                        }
                    )

                    meta["chunk_id"] = digest(
                        doc["sha256"]
                        + str(start)
                        + str(end)
                        + fragment
                    )[:24]

                    chunks.append(meta)

                if end == sec["end"]:
                    break

                start = max(
                    start + 1,
                    end - overlap
                )

    return chunks
