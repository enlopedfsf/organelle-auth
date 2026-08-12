#!/usr/bin/env python3
"""Run the frozen-input Flye grid and produce copy-aware junction counts."""
import argparse, csv, hashlib, json, os, re, subprocess, sys, time
from pathlib import Path

EXPECTED = "93f4fd3bc3969e5d4d3577870b32f4a63d99ddc57a325f84403d7f089531f3c8"
COMBOS = [(200,5000),(None,5000)]

def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def run(cmd, cwd=None, out=None):
    t=time.time(); r=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if out: Path(out).write_text(r.stdout)
    return r.returncode, time.time()-t

def flye_grid(args):
    inp=Path(args.input); out=Path(args.output); out.mkdir(parents=True,exist_ok=True)
    got=sha256(inp)
    if got != EXPECTED: raise SystemExit(f'INPUT_CHECKSUM_MISMATCH expected={EXPECTED} got={got}')
    manifest={'schema_version':'topology-resolution-experiments-0.1','platform':'ONT','experimental_only':True,'input':str(inp),'input_bytes':inp.stat().st_size,'input_sha256':got,'flye_version':subprocess.check_output(['flye','--version'],text=True).strip(),'combinations':[]}
    for cov,ov in COMBOS:
        name=f'asm-{cov if cov is not None else "unlimited"}_overlap-{ov}'
        d=out/name; d.mkdir(parents=True,exist_ok=True)
        cmd=['flye']
        if cov is not None: cmd += ['--asm-coverage',str(cov)]
        cmd += ['--nano-hq',str(inp),'--genome-size','200k','--iterations','1','--min-overlap',str(ov),'--threads',str(args.threads),'--out-dir',str(d)]
        rc,secs=run(cmd,out=d/'command.log')
        rec={'name':name,'asm_coverage':cov,'min_overlap':ov,'command':' '.join(cmd),'returncode':rc,'runtime_seconds':round(secs,3),'input_sha256':got}
        fa=d/'assembly.fasta'; gfa=d/'assembly_graph.gfa'
        src=d/'assembly.fasta'; srcg=d/'assembly_graph.gfa'
        if src.exists(): fa=src
        if srcg.exists(): gfa=srcg
        if fa.exists():
            seqs=[]; h=None; n=0
            for line in fa.read_text().splitlines():
                if line.startswith('>'):
                    n+=1; h=line[1:].split()[0]; seqs.append([h,0])
                elif seqs: seqs[-1][1]+=len(line.strip())
            rec.update({'fasta':str(fa),'fasta_sha256':sha256(fa),'contig_count':n,'contig_lengths':[x[1] for x in seqs],'circularity':'not_claimed'})
        rec['gfa']=str(gfa) if gfa.exists() else None
        manifest['combinations'].append(rec)
        (d/'result.json').write_text(json.dumps(rec,indent=2)+'\n')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

def recount(args):
    paf=Path(args.paf); out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    # Junction is contig_1 end -> contig_2 start; retain a transparent 500-bp flank.
    rows=[]; seen={}
    for line in paf.open():
        x=line.rstrip().split('\t')
        if len(x)<12: continue
        q,ql,qs,qe,strand,t,tl,ts,te,nmatch,alen,mapq=x[:12]
        if t not in ('contig_1','contig_2'): continue
        # PAF records to the two contigs are joined by read identity and flank coverage.
        edge='contig1_end' if t=='contig_1' and int(te)>=int(tl)-500 else None
        edge2='contig2_start' if t=='contig_2' and int(ts)<=500 else None
        if edge or edge2:
            rows.append({'read':q,'mapq':int(mapq),'target':t,'edge':edge or edge2,'secondary':('tp:A:S' in line),'supplementary':('SA:Z:' in line)})
    by={}
    for r in rows: by.setdefault(r['read'],[]).append(r)
    support=[]
    for read,rs in by.items():
        edges={r['edge'] for r in rs};
        if {'contig1_end','contig2_start'} <= edges: support.append((read,rs))
    prior=37
    raw=len(support); hq=sum(1 for _,rs in support if all(r['mapq']>=20 for r in rs));
    weighted=sum(1/max(1,len({r['target'] for r in rs})) for _,rs in support)
    rec={'schema_version':'topology-junction-recount-0.1','platform':'ONT','experimental_only':True,'paf':str(paf),'paf_sha256':sha256(paf),'flank_bases':500,'prior_high_quality_count':prior,'raw_read_identity_count':raw,'mapq_ge_20_read_identity_count':hq,'copy_aware_weighted_support':weighted,'supporting_read_ids':[r for r,_ in support],'decision':'NOT_APPLICABLE'}
    out.write_text(json.dumps(rec,indent=2)+'\n'); out.with_suffix('.tsv').write_text('metric\tvalue\n'+'\n'.join(f'{k}\t{v}' for k,v in rec.items() if not isinstance(v,(list,dict)))+'\n')

if __name__=='__main__':
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='mode',required=True)
    a=sub.add_parser('grid'); a.add_argument('--input',required=True); a.add_argument('--output',required=True); a.add_argument('--threads',type=int,default=4)
    b=sub.add_parser('recount'); b.add_argument('--paf',required=True); b.add_argument('--output',required=True)
    x=ap.parse_args(); flye_grid(x) if x.mode=='grid' else recount(x)
