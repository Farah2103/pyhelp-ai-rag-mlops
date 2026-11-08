from pathlib import Path
import yaml
from src.common import ROOT
if __name__=="__main__":
    for meta in (ROOT/"mlruns").rglob("meta.yaml"):
        d=yaml.safe_load(meta.read_text())
        if "artifact_uri" in d:d["artifact_uri"]=(meta.parent/"artifacts").as_uri()
        if "artifact_location" in d:d["artifact_location"]=meta.parent.as_uri()
        meta.write_text(yaml.safe_dump(d))
    print("MLflow artifact locations updated to this project directory")
