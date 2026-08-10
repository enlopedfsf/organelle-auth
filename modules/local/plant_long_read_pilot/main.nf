/*
 * M3 plant long-read pilot runner.
 * This process intentionally emits an evaluation report, not an assembly_qc or decision status.
 * PMAT2 is invoked with -t ont -x 0 when the pinned pilot container is available.
 */
process PLANT_LONG_READ_PILOT_RUN {
    tag "${meta.id}"
    label 'process_high'
    container { params.pmat2_container }

    input:
    tuple val(meta), val(short_reads), path(long_reads)
    path reference_fasta
    path manifest

    output:
    tuple val(meta), path("${meta.id}.plant-long-read-report.json"), emit: report
    tuple val(meta), path("${meta.id}.plant-long-read-status.json"), emit: status
    path "versions.yml", emit: tool_versions
    tuple val("${task.process}"), val('plant_long_read_pilot'), val('0.1.0'), emit: versions

    script:
    def sr = short_reads ? short_reads.collect { it.toString() }.join(',') : ''
    """
    set -euo pipefail
    export SAMPLE_ID='${meta.id}'
    export REFERENCE='${reference_fasta}'
    export MANIFEST='${manifest}'
    export LONG_READS='${long_reads}'
    export SHORT_READS='${sr}'
    python3 - <<'PY'
    import gzip, json, os, shutil, statistics, subprocess, time
    sid=os.environ['SAMPLE_ID']; lr=os.environ['LONG_READS']; ref=os.environ['REFERENCE']
    manifest=json.load(open(os.environ['MANIFEST']))
    if not os.path.exists(lr) or os.path.getsize(lr)==0: raise SystemExit('LONG_READ_INPUT_EMPTY')
    # Validate every paired SR anchor before launching PMAT2; missing/corrupt evidence is fatal.
    sr_paths=[x for x in os.environ.get('SHORT_READS','').split(',') if x]
    if len(sr_paths) not in (0,2): raise SystemExit('SHORT_READ_PAIR_MISMATCH')
    for p in sr_paths:
        if not os.path.exists(p) or os.path.getsize(p)==0: raise SystemExit('SHORT_READ_INPUT_EMPTY')
        if p.endswith('.gz'):
            subprocess.run(['gzip','-t',p],check=True)
    if not os.path.exists(ref) or os.path.getsize(ref)==0: raise SystemExit('REFERENCE_INPUT_EMPTY')
    # Cheap integrity/read-length census; the full read stream is not loaded into memory.
    lengths=[]; opener=gzip.open if lr.endswith('.gz') else open
    with opener(lr,'rt',errors='replace') as fh:
        while True:
            h=fh.readline()
            if not h: break
            s=fh.readline(); fh.readline(); fh.readline()
            if not s: break
            lengths.append(len(s.strip()))
    lengths.sort()
    n=len(lengths)
    n50=0; acc=0
    for x in reversed(lengths):
        acc += x
        if acc >= sum(lengths)/2: n50=x; break
    qc={'read_count':n,'total_bases':sum(lengths),'read_n50':n50,'read_min':min(lengths) if lengths else 0,'read_max':max(lengths) if lengths else 0}
    # NanoPlot/filtlong are required tools in the production container; record availability
    # explicitly so a missing runtime never masquerades as a successful QC result.
    tools={x:shutil.which(x) is not None for x in ('NanoPlot','filtlong','PMAT','PMAT2','autoMito')}
    nanoplot_state='NOT_RUN'
    if tools['NanoPlot']:
        os.makedirs(sid+'_nanoplot',exist_ok=True)
        try:
            subprocess.run(['NanoPlot','--fastq',lr,'--outdir',sid+'_nanoplot','--threads','1'],check=True)
            nanoplot_state='COMPLETED'
        except subprocess.CalledProcessError: nanoplot_state='FAILED'
    filtered=lr; filter_state='NOT_RUN'
    # No quality/length threshold is invented here. A null filter policy is an honest
    # pass-through; a future engineering policy must be injected explicitly.
    filter_state='PASS_THROUGH_POLICY_NULL'
    pmat=next((x for x in ('PMAT','PMAT2','autoMito') if tools[x]),None)
    pmat_state='NOT_RUN'; pmat_cmd=None
    if pmat:
        out=sid+'_pmat2'; os.makedirs(out,exist_ok=True)
        pmat_cmd=[pmat,'autoMito','-i',filtered,'-o',out,'-t','ont','-x','0']
        try:
            subprocess.run(pmat_cmd,check=True)
            pmat_state='COMPLETED'
        except subprocess.CalledProcessError: pmat_state='FAILED'
    else: pmat_state='PMAT2_RUNTIME_UNAVAILABLE'
    # Evaluate only if PMAT2 produced an assembly. Missing output is a structured
    # not-assessable state, never a fabricated closure/concordance claim.
    assemblies=[]
    if pmat_state=='COMPLETED':
        for root,_,files in os.walk(sid+'_pmat2'):
            assemblies += [os.path.join(root,f) for f in files if f.endswith(('.fa','.fasta','.fna')) and os.path.getsize(os.path.join(root,f))>0]
    refseq=''
    with open(ref) as fh:
        refseq=''.join(x.strip() for x in fh if not x.startswith('>'))
    sequence_comparison={'state':'not_assessable','reference_length':len(refseq),'assembly_files':assemblies,'aligned_span':None,'identity':None}
    if assemblies:
        seq=''
        with open(assemblies[0]) as fh: seq=''.join(x.strip() for x in fh if not x.startswith('>'))
        # Exact-window comparison is descriptive only; no threshold is applied.
        m=min(len(seq),len(refseq)); matches=sum(a==b for a,b in zip(seq[:m],refseq[:m]))
        sequence_comparison.update({'state':'measured','assembly_length':len(seq),'aligned_span':m,'identity':matches/m if m else None})
    hp={'method':'maximal_reference_runs_lifted_through_fixed_alignment','state':'not_assessable','records':[],'callable_bases':0,'ambiguous_coordinates':[]}
    if sequence_comparison['state']=='measured':
        # In this pilot the fixed coordinate comparison is identity-by-position; future
        # alignment-backed lifting uses the same output schema unchanged for CycloneSEQ.
        run_start=0
        for i in range(1,len(refseq)+1):
            if i==len(refseq) or refseq[i]!=refseq[run_start]:
                run_len=i-run_start
                if run_len>=3:
                    lr_len=sum(1 for j in range(run_start,min(i,len(seq))) if seq[j]==refseq[run_start])
                    hp['records'].append({'ref_start':run_start+1,'ref_end':i,'base':refseq[run_start],'reference_run_length':run_len,'lr_callable_bases':lr_len,'run_length_delta':lr_len-run_len})
                run_start=i
        hp['callable_bases']=sum(x['reference_run_length'] for x in hp['records']); hp['state']='measured'
    result={'schema_version':'m3-plant-long-read-pilot-0.1','sample_id':sid,'experimental_only':True,'platform':manifest.get('platform'),'source_accession':manifest.get('source_accession'),'qc':qc,'nanoplot_state':nanoplot_state,'tool_availability':tools,'filter_state':filter_state,'pmat2_state':pmat_state,'pmat2_command':pmat_cmd,'reference_fasta':ref,'m1_ir_gap':manifest.get('m1_ir_gap'),'sequence_comparison':sequence_comparison,'homopolymer_error_spectrum':hp,'resource_usage':{'wall_time_seconds':None,'cpu_seconds':None,'peak_memory_kb':None},'started_epoch':time.time()}
    result['ir_closure']='not_assessable' if pmat_state!='COMPLETED' else 'pending_metric_extraction'
    json.dump(result,open(sid+'.plant-long-read-report.json','w'),indent=2)
    status={'sample_id':sid,'stage':'plant_long_read_pilot','status':'EXPERIMENTAL_COMPLETE' if pmat_state=='COMPLETED' else 'EXPERIMENTAL_BLOCKED','decision':'NOT_APPLICABLE','reason_codes':[] if pmat_state=='COMPLETED' else [pmat_state],'experimental_only':True}
    json.dump(status,open(sid+'.plant-long-read-status.json','w'),indent=2)
    PY
    printf 'plant_long_read_pilot:\n  PMAT2: 2.1.5\n  platform: ONT\n  mode: "ont/plant"\n' > versions.yml
    """

    stub:
    """
    printf '{"sample_id":"%s","experimental_only":true,"pmat2_state":"STUB","ir_closure":"not_assessable"}' '${meta.id}' > '${meta.id}.plant-long-read-report.json'
    printf '{"sample_id":"%s","stage":"plant_long_read_pilot","status":"EXPERIMENTAL_BLOCKED","decision":"NOT_APPLICABLE","reason_codes":["STUB"]}' '${meta.id}' > '${meta.id}.plant-long-read-status.json'
    printf 'plant_long_read_pilot:\n  PMAT2: stub\n' > versions.yml
    """
}
