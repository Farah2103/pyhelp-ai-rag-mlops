import json
import stat
import zipfile
from pathlib import Path
import pytest
from src.common import ROOT, config, read_json, write_json
from src.ingestion.pipeline import clean, sections, chunk_documents, ingest

def archive(tmp_path, name="docs/a.txt", content=b"Title\n=====\n\n   >>> print(1)\n"):
    p=tmp_path/"x.zip"
    with zipfile.ZipFile(p,"w") as z:z.writestr(name,content)
    cfg=tmp_path/"sel.json";write_json(cfg,{"version":"fixture","archive_sha256":"unused","archive_prefix":"docs/","documents":["a.txt"]})
    return p,cfg
@pytest.mark.parametrize("name",["../evil.txt","/absolute.txt","docs/../../evil.txt","C:/bad.txt","docs\\bad.txt"])
def test_zip_paths(tmp_path,name):
    p,c=archive(tmp_path,name)
    with pytest.raises(ValueError):ingest(p,tmp_path,c,False)
def test_hash(tmp_path):
    p,c=archive(tmp_path)
    with pytest.raises(ValueError,match="SHA256"):ingest(p,tmp_path,c)
def test_symlink(tmp_path):
    p,c=archive(tmp_path)
    with zipfile.ZipFile(p,"a") as z:
        i=zipfile.ZipInfo("docs/link");i.create_system=3;i.external_attr=(stat.S_IFLNK|0o777)<<16;z.writestr(i,"elsewhere")
    with pytest.raises(ValueError,match="symlink"):ingest(p,tmp_path,c,False)
def test_utf8(tmp_path):
    p,c=archive(tmp_path,content=b"\xff")
    with pytest.raises(UnicodeDecodeError):ingest(p,tmp_path,c,False)
def test_duplicate(tmp_path):
    p,c=archive(tmp_path)
    with zipfile.ZipFile(p,"a") as z:z.writestr("docs/a.txt",b"same")
    with pytest.raises(ValueError,match="Duplicate"):ingest(p,tmp_path,c,False)
def test_clean_indentation():assert clean("a\r\n   >>> if True:\r\n   ...     pass\r\n")=="a\n   >>> if True:\n   ...     pass\n"
def test_sections():assert sections("Title\n=====\n\nBody\n")[0]["title"]=="Title"
def test_actual_corpus_and_stable_chunks():
    inv=read_json(ROOT/"data/processed/inventory.json");assert inv["document_count"]==9
    a=chunk_documents(ROOT,config(ROOT/"configs/A.json"));b=chunk_documents(ROOT,config(ROOT/"configs/A.json"))
    assert a==b and len({c["chunk_id"] for c in a})==len(a)
    for c in a:
        assert len(c["text"])<=400 and c["version"]=="3.11.18"
        text=(ROOT/"data/processed/documents"/c["source_path"]).read_text(encoding="utf-8")
        assert text[c["start"]:c["end"]]==c["text"]
        assert all(c[k] for k in ["chunk_id","document_id","source_path","title","section"])
def test_invalid_config(tmp_path):
    p=tmp_path/"config.json";write_json(p,{"chunk_size":100,"chunk_overlap":100})
    with pytest.raises(ValueError):config(p)
def test_no_additional_sources():
    c=read_json(ROOT/"configs/corpus.json")
    assert len(c["documents"])==9
    assert sorted(str(p.relative_to(ROOT/"data/raw")).replace("\\","/") for p in (ROOT/"data/raw").rglob("*.txt"))==sorted(c["documents"])
