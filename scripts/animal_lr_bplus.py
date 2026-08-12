#!/usr/bin/env python3
import argparse, collections, gzip, json, statistics
from pathlib import Path

def paf(path):
    d=collections.defaultdict(list)
    for line in Path(path).open():
        f=line.rstrip().split('\t')
        if len(f)>=12: d[f[0]].append({'qlen':int(f[1]),'qs':int(f[2]),'qe':int(f[3]),'target':f[5],'ts':int(f[7]),'te':int(f[8]),'tlen':int(f[6]),'matches':int(f[9]),'aln':int(f[10]),'mapq':int(f[11])})
    return d
def union_len(iv):
    z=sorted(iv); total=0; end=-1
    for s,e in z:
        if e>end: total+=e-max(s,end); end=e
    return total
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--rotations',required=True); ap.add_argument('--anchor',required=True); ap.add_argument('--reads',required=True); ap.add_argument('--self-paf',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    rot,anc=paf(a.rotations),paf(a.anchor); lengths={}; opener=gzip.open if str(a.reads).endswith('.gz') else open
    with opener(a.reads,'rt') as f:
        while True:
            h=f.readline()
            if not h: break
            s=f.readline().strip(); f.readline(); f.readline(); lengths[h[1:].split()[0]]=len(s)
    fractions=[]; identities=[]; length_bins=collections.Counter(); rot_stats=[]
    for q,rs in rot.items():
        qlen=lengths.get(q,rs[0]['qlen']); frac=union_len([(r['qs'],r['qe']) for r in rs])/qlen if qlen else 0; fractions.append(frac)
        identities.extend([r['matches']/r['aln'] for r in rs if r['aln']]); length_bins.update([k for k,v in [('ge2k',qlen>=2000),('ge5k',qlen>=5000),('ge6k',qlen>=6000),('ge10k',qlen>=10000)] if v]); rot_stats.append({'read_id':q,'read_length':qlen,'alignment_records':len(rs),'aligned_query_union':union_len([(r['qs'],r['qe']) for r in rs]),'aligned_fraction':frac,'max_identity':max(r['matches']/r['aln'] for r in rs if r['aln'])})
    bins=collections.Counter(min(9,int(x*10)) for x in fractions); ibins=collections.Counter(min(19,int(x*20)) for x in identities)
    anchor_cov=collections.Counter()
    for rs in anc.values():
        for r in rs:
            for p in range(r['ts']//100, (r['te']-1)//100+1): anchor_cov[p]+=1
    self_records=0; periodic=[]
    if Path(a.self_paf).exists():
        for line in Path(a.self_paf).open():
            f=line.rstrip().split('\t')
            if len(f)>=12 and f[0]!=f[5]: self_records+=1
            if len(f)>=12 and f[0]==f[5]:
                span=abs(int(f[3])-int(f[2])); periodic.append({'read_id':f[0],'span':span,'matches':int(f[9]),'aln':int(f[10])})
    d={'schema_version':'animal-lr-bplus-0.1','scope':'existing_recruited_824_reads_only','aligned_fraction':{'per_read':rot_stats,'histogram_0.1_bins':dict(sorted((str(k/10),v) for k,v in bins.items()))},'read_length_strata':dict(length_bins),'identity':{'histogram_0.05_bins':dict(sorted((str(k/20),v) for k,v in ibins.items())),'n_alignments':len(identities),'mean':statistics.mean(identities) if identities else None,'median':statistics.median(identities) if identities else None},'anchor_coverage_100bp_bins':dict(sorted((str(k),v) for k,v in anchor_cov.items())),'self_alignment':{'nonself_records':self_records,'self_records':len(periodic),'periodic_self_spans':periodic,'periodic_14_5kb_candidates':sum(1 for x in periodic if 13000<=x['span']<=16000)},'interpretation':{'min_query_fraction':'pending_review','min_overlap':'pending_review','tandem_repeat':'pending_review','numt':'pending_review'}}
    out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(d,indent=2)+'\n'); print(json.dumps({k:d[k] for k in ('read_length_strata','identity','self_alignment')},indent=2))
if __name__=='__main__': main()
