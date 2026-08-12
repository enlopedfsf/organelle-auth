#!/usr/bin/env python3
import argparse, hashlib, json, os, time
from pathlib import Path

def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--reads',required=True); ap.add_argument('--reference',required=True); ap.add_argument('--metadata',required=True); ap.add_argument('--anchor',required=True); ap.add_argument('--status',required=True); ap.add_argument('--output',required=True); a=ap.parse_args()
    paths={k:Path(v) for k,v in vars(a).items() if k not in ('output',)}
    errors=[]; records={}
    for k,p in paths.items():
        ok=p.is_file() and p.stat().st_size>0 and os.access(p,os.R_OK)
        records[k]={'path':str(p),'exists_readable_nonempty':ok,'bytes':p.stat().st_size if p.exists() else 0,'sha256':sha256(p) if ok else None}
        if not ok: errors.append(f'{k}:missing_empty_or_unreadable')
    status={}
    if not errors:
        try: status=json.loads(paths['status'].read_text())
        except Exception as e: errors.append(f'status:invalid_json:{e}')
        if status.get('sample_id')!='WTM_NORMAL': errors.append('status:sample_id_mismatch')
        if status.get('assembly_grade')!='DRAFT': errors.append('status:anchor_not_DRAFT')
        if status.get('decision') not in ('NOT_APPLICABLE',''): errors.append('status:decision_not_isolated')
    out={'schema_version':'animal-long-read-preflight-0.1','experimental_only':True,'platform':'ONT','taxon_group':'animal','target':'mitome','status':'PASS' if not errors else 'FAIL','reason_codes':errors,'inputs':records,'m2_status':status,'decision':'NOT_APPLICABLE','cycloneseq':'PENDING_REAL_DATA','created_epoch':time.time()}
    Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2)); return 0 if not errors else 2
if __name__=='__main__': raise SystemExit(main())
