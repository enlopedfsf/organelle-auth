#!/usr/bin/env python3
import argparse, collections, hashlib, json, math, gzip
from pathlib import Path

def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def entropy(seq):
 c=collections.Counter(seq); n=len(seq)
 return -sum((v/n)*math.log2(v/n) for v in c.values()) if n else 0
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--paf',required=True); ap.add_argument('--reads',required=True); ap.add_argument('--anchor-paf',required=True); ap.add_argument('--output',required=True); a=ap.parse_args()
 paf,reads,anchor,out=map(Path,(a.paf,a.reads,a.anchor_paf,a.output)); align=[]; by=collections.defaultdict(list)
 for l in paf.open():
  f=l.rstrip().split('\t')
  if len(f)>=12:
   qlen,aln=int(f[1]),int(f[10]); ident=int(f[9])/aln if aln else 0; rec={'read_id':f[0],'read_length':qlen,'target':f[5],'query_start':int(f[2]),'query_end':int(f[3]),'target_start':int(f[7]),'target_end':int(f[8]),'alignment_length':aln,'identity':ident,'mapq':int(f[11])}; align.append(rec); by[f[0]].append(rec)
 seqstats=[]; opener=gzip.open if reads.suffix=='.gz' else open
 with opener(reads,'rt') as f:
  while True:
   h=f.readline()
   if not h: break
   s=f.readline().strip(); f.readline(); f.readline(); seqstats.append({'read_id':h[1:].split()[0],'length':len(s),'entropy':entropy(s),'gc':(s.count('G')+s.count('C'))/len(s) if s else 0})
 mq=collections.Counter('mapq0' if x['mapq']==0 else 'mapq_positive' for x in align)
 anchor_ids=set(l.split('\t')[0] for l in anchor.open() if l.strip())
 unique=set(by); d={'schema_version':'animal-lr-recruitment-diagnostics-0.1','experimental_only':True,'decision':'NOT_APPLICABLE','A':{'subsample_status':'PASS_USER_VERIFIED','subsample_path':'runs/output/animal-long-read-pilot/subsample/SRR27841065.seed11.p10.fastq.gz','subsample_bytes':2181678470,'seed':11,'fraction':0.1,'integrity':'USER_VERIFIED_IN_PERSISTENT_BASH'},'B':{'paf':{'path':str(paf),'bytes':paf.stat().st_size,'sha256':sha(paf)},'alignment_records':len(align),'unique_recruited_reads':len(unique),'mapq':dict(mq),'mapq0_fraction':mq['mapq0']/len(align) if align else None,'mean_identity':sum(x['identity'] for x in align)/len(align) if align else None,'read_length':{'min':min((x['length'] for x in seqstats),default=0),'max':max((x['length'] for x in seqstats),default=0),'mean':sum(x['length'] for x in seqstats)/len(seqstats) if seqstats else 0},'entropy':{'min':min((x['entropy'] for x in seqstats),default=0),'max':max((x['entropy'] for x in seqstats),default=0),'mean':sum(x['entropy'] for x in seqstats)/len(seqstats) if seqstats else 0},'anchor_intersection':len(unique & anchor_ids),'anchor_unique_reads':len(anchor_ids),'note':'anchor PAF read IDs are compared; no threshold is applied'}}
 out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(d,indent=2)+'\n'); Path(str(out)+'.alignments.tsv').write_text('read_id\tread_length\ttarget\talignment_length\tidentity\tmapq\n'+'\n'.join(f"{x['read_id']}\t{x['read_length']}\t{x['target']}\t{x['alignment_length']}\t{x['identity']:.6f}\t{x['mapq']}" for x in align)+'\n'); print(json.dumps(d,indent=2))
if __name__=='__main__': main()
