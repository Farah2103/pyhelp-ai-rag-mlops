"""Mitigation for the known DiskCache pickle advisory in the DVC toolchain.
Use only a private cache whose contents are created by this user; never import untrusted caches.
"""
import os
import stat
from src.common import ROOT

def secure():
    p=ROOT/'.dvc/private-cache';p.mkdir(parents=True,exist_ok=True,mode=0o700)
    if os.name=='posix':
        if p.stat().st_uid!=os.getuid():raise PermissionError('DVC cache must belong to this user')
        p.chmod(0o700)
        if stat.S_IMODE(p.stat().st_mode)!=0o700:raise PermissionError('Private DVC cache permission check failed')
        print('DVC private cache owner/permissions verified (0700)')
    else:
        print('DVC cache is inside the project. Verify Windows ACLs restrict it to your account before running DVC; this OS check was not executed in the delivery environment.')
if __name__=='__main__':secure()
