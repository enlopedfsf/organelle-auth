#!/usr/bin/env python3
import argparse, csv, hashlib, json
from collections import defaultdict
from pathlib import Path

def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def audit(paf, out):
    rows=defaultdict(list)
    with open(paf) as fh:
        for line in fh:
            x=line.rstrip().split('\t')
            if len(x)<12 or x[5] not in ('contig_1','contig_2'): continue
            q,ql,qs,qe,t,tl,ts,te,mapq=x[0],int(x[1]),int(x[2]),int(x[3]),x[5],int(x[6]),int(x[7]),int(x[8]),int(x[11])
            tags=x[12:]
            rows[q].append({'target':t,'target_start':ts,'target_end':te,'target_len':tl,'mapq':mapq,
                            'secondary':any(z.startswith('tp:A:S') for z in tags),
                            'supplementary':any(z.startswith('SA:Z:') for z in tags)})
    ledger=[]
    for read, rs in rows.items():
        left=[r for r in rs if r['target']=='contig_1' and r['target_end']>=r['target_len']-500]
        right=[r for r in rs if r['target']=='contig_2' and r['target_start']<=500]
        if not left or not right: continue
        all_targets={(r['target'],r['target_start'],r['target_end']) for r in rs}
        unique=(len(left)==1 and len(right)==1 and len(all_targets)==2 and left[0]['mapq']>0 and right[0]['mapq']>0 and not left[0]['secondary'] and not right[0]['secondary'])
        if unique: cls='QUALIFYING_CANDIDATE'
        elif len(left)>1 or len(right)>1: cls='COPY_AMBIGUOUS'
        elif left[0]['mapq']==0 or right[0]['mapq']==0: cls='MAPQ_ZERO_AMBIGUOUS'
        else: cls='NON_UNIQUE_ANCHOR'
        ledger.append({'read_id':read,'left_alignments':len(left),'right_alignments':len(right),'total_target_placements':len(all_targets),
                       'left_mapq':max(r['mapq'] for r in left),'right_mapq':max(r['mapq'] for r in right),'classification':cls,
                       'independent_alignment_support':False})
    counts=defaultdict(int)
    for r in ledger: counts[r['classification']]+=1
    out=Path(out); out.parent.mkdir(parents=True,exist_ok=True)
    rec={'schema_version':'topology-conclusion-revision-0.1','platform':'ONT','experimental_only':True,
         'paf':str(paf),'paf_sha256':sha256(paf),'flank_bases':500,'candidate_count':len(ledger),
         'qualifying_count':counts['QUALIFYING_CANDIDATE'],'classification_counts':dict(counts),
         'formal_topology':'INCONCLUSIVE','decision':'NOT_APPLICABLE','ledger':ledger}
    out.write_text(json.dumps(rec,indent=2)+'\n')
    with (out.with_suffix('.tsv')).open('w') as fh:
        w=csv.DictWriter(fh,fieldnames=['read_id','left_alignments','right_alignments','total_target_placements','left_mapq','right_mapq','classification','independent_alignment_support'],delimiter='\t'); w.writeheader(); w.writerows(ledger)
    return rec

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--paf',required=True); ap.add_argument('--output',required=True); a=ap.parse_args(); print(json.dumps(audit(a.paf,a.output),indent=2))
