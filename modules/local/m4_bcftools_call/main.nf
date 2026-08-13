process M4_BCFTOOLS_CALL {
    tag "${meta.taxon}:${meta.arm}:${meta.split}"
    label 'process_medium'
    conda "${moduleDir}/environment.yml"
    container 'quay.io/biocontainers/bcftools@sha256:969314d56b9131683917cc5801734891a9af130daf7a0fb902b7707060b06027'

    input:
    tuple val(meta), path(candidate), path(bam), path(bai), path(depth)

    output:
    tuple val(meta), path(candidate), path(bam), path(bai), path(depth), path("${meta.taxon}.${meta.arm}.${meta.split}.filtered.vcf.gz"), path("${meta.taxon}.${meta.arm}.${meta.split}.filtered.vcf.gz.csi"), emit: calls
    tuple val("${task.process}"), val('bcftools'), val('1.21'), topic: versions, emit: versions

    script:
    """
    set -euo pipefail
    ${params.m4_bcftools_bin} mpileup -Ou -q 20 -Q 20 -d 20000000 -L 20000000 \
      -a FORMAT/DP,FORMAT/AD -f ${candidate} ${bam} \
      | ${params.m4_bcftools_bin} call --ploidy 1 -m -v -Ou \
      | ${params.m4_bcftools_bin} norm -f ${candidate} -m -both -Ou \
      | ${params.m4_bcftools_bin} view -i 'QUAL>=30 && FORMAT/DP[0]>=10 && FORMAT/AD[0:1]/FORMAT/DP[0]>=0.8' \
          -Oz -o ${meta.taxon}.${meta.arm}.${meta.split}.filtered.vcf.gz
    ${params.m4_bcftools_bin} index -f ${meta.taxon}.${meta.arm}.${meta.split}.filtered.vcf.gz
    """

    stub:
    """
    printf '##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tstub\n' | gzip -c > ${meta.taxon}.${meta.arm}.${meta.split}.filtered.vcf.gz
    : > ${meta.taxon}.${meta.arm}.${meta.split}.filtered.vcf.gz.csi
    """
}
