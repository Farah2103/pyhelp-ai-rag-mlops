"""Audit inventory for the installed environment, not a portable installation lock."""
from pathlib import Path
from packaging.requirements import Requirement
from packaging.markers import default_environment
from packaging.version import Version
from importlib.metadata import distribution
from src.common import ROOT,write_json

def collect():
    pending=[Requirement(l) for l in (ROOT/'requirements.txt').read_text().splitlines() if l and not l.startswith('#')]
    done={};seen={}
    while pending:
        req=pending.pop();key=req.name.lower().replace('_','-');extras=set(req.extras)|{''}
        if extras.issubset(seen.get(key,set())):continue
        seen.setdefault(key,set()).update(extras);d=distribution(req.name)
        done[key]={'installed':d.version,'advisory_lookup':Version(d.version).base_version}
        for raw in d.requires or []:
            r=Requirement(raw)
            if r.marker is None or any(r.marker.evaluate({**default_environment(),'extra':ex}) for ex in extras):pending.append(r)
    (ROOT/'reports/runtime_dependency_closure.txt').write_text('\n'.join(f'{n}=={v["advisory_lookup"]}' for n,v in sorted(done.items()))+'\n')
    write_json(ROOT/'reports/runtime_dependency_closure_metadata.json',{'packages':done,'note':'Installed closure on Linux/Python 3.12. Local +cpu tag removed only for advisory lookup; see installed version metadata. Not an installation lock.'})
    print('Installed closure packages:',len(done))
if __name__=='__main__':collect()
