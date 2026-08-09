# MitoFinder 1.4.2 — built from GitHub source (RemiAllio/MitoFinder master, header: Version 1.4.2)
#
# MitoFinder core is Python 2.7 (`#!/usr/bin/python2.7` in the mitofinder script). The only
# published py2 biocontainer is 1.4.1 (quay.io/biocontainers/mitofinder:1.4.1--py27h779adbc_0) —
# older than master and frozen; per project decision (2026-08-09) we build from GitHub instead,
# replicating the official Singularity container's py2-bundled environment on Ubuntu 18.04
# (the last Ubuntu with python2.7 in apt).
#
# install.sh compiles the repo-bundled assemblers/annotators from source: idba, MetaSPAdes
# (symlink), tRNAscan-SE 2.0.6 + infernal 1.1.3, MiTFi + infernal 1.0.2. megahit/blast/arwen
# are shipped prebuilt in the repo. Mitofinder.config defaults (= "default") make MitoFinder
# resolve these tools relative to its own directory.
#
# Python deps: only biopython (MitoFinder imports `Bio.Alphabet`, removed in Biopython >=1.80,
# so we pin the last py2-compatible 1.79) + pillow (annotated-contig images, optional).

FROM ubuntu:18.04

LABEL org.opencontainers.image.title="MitoFinder"
LABEL org.opencontainers.image.description="MitoFinder 1.4.2 (RemiAllio/MitoFinder master) — animal mitogenome assembly + annotation, Python 2.7 core, built from GitHub source"
LABEL org.opencontainers.image.version="1.4.2"
LABEL org.opencontainers.image.source="https://github.com/RemiAllio/MitoFinder"

# Ubuntu 18.04 is EOL but bionic is still served from archive.ubuntu.com (verified 2026-08-09,
# returns 200). Point the security repo at the main archive host so apt-get update resolves
# cleanly on an EOL release.
RUN sed -i 's|http://security.ubuntu.com/ubuntu/|http://archive.ubuntu.com/ubuntu/|g' /etc/apt/sources.list

# System deps: compilers (idba/infernal/trnascan builds), autoconf/automake (install.sh), Java
# (MiTFi tRNA finder), python2.7 + pip (MitoFinder core), wget/git, zlib (infernal).
# ncbi-blast+ (2.6.0 on bionic): MitoFinder's repo BUNDLES blast 2.2.29 (2013) whose makeblastdb
# needs libidn.so.11 — absent on bionic → the identification step silently produces no hits
# (observed: `makeblastdb: error while loading shared libraries: libidn.so.11`). We install the
# system blast and point Mitofinder.config blastfolder at /usr/bin.
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential gcc g++ make autoconf automake \
      default-jre \
      python2.7 python2.7-dev python-pip \
      wget git ca-certificates zlib1g-dev \
      ncbi-blast+ \
    && rm -rf /var/lib/apt/lists/*

# No pip install: MitoFinder's GitHub source BUNDLES its own py2-compatible `Bio/` (biopython)
# tree (MitoFinder-master/Bio/), imported when running from /opt/MitoFinder. Pillow (annotation
# images) is optional and skipped. The GitHub source is COPYed into the build context (this
# directory) rather than git-cloned inside the build: the build container cannot reach
# github.com directly and cannot use the host's loopback proxy (v2ray listens on 127.0.0.1 only).
# Build context = containers/mitofinder/, so place MitoFinder-master.tar.gz there before `docker build`.
WORKDIR /opt
COPY MitoFinder-master.tar.gz /tmp/MitoFinder-master.tar.gz
RUN tar -xzf /tmp/MitoFinder-master.tar.gz -C /opt && \
    mv /opt/MitoFinder-master /opt/MitoFinder && \
    rm /tmp/MitoFinder-master.tar.gz

# install.sh compiles the bundled idba / MetaSPAdes symlink / tRNAscan-SE+infernal / MiTFi+infernal.
# install.sh chmods 764 (no execute for group/other) — but Nextflow runs the container as a
# non-root uid (e.g. 1000), so root-owned executables need a+rx (observed: `mitofinder: Permission
# denied`, exit 126). Fix perms here.
WORKDIR /opt/MitoFinder
RUN ./install.sh && test -f /opt/MitoFinder/install.sh.ok

# install.sh chmods 764 (no execute for group/other) — but Nextflow runs the container as a
# non-root uid (e.g. 1000), so root-owned executables need a+rx (observed: `mitofinder: Permission
# denied`, exit 126). Separate RUN keeps the expensive install.sh layer cached.
RUN chmod -R a+rX /opt/MitoFinder && \
    chmod a+x /opt/MitoFinder/mitofinder /opt/MitoFinder/*.py 2>/dev/null; \
    find /opt/MitoFinder -type f \( -name 'megahit' -o -name 'spades.py' \
        -o -name 'idba*' -o -name 'infernal' -o -name 'cmsearch' \) \
        -exec chmod a+x {} + 2>/dev/null; \
    # point MitoFinder's blast at the working system blast (/usr/bin) instead of the broken
    # bundled 2.2.29 (libidn.so.11 missing). MitoFinder concatenates blastfolder + "makeblastdb",
    # so the value MUST end with a slash (else it probes `/usr/binmakeblastdb`). Keep the rest as `default`.
    sed -i 's|^blastfolder.*|blastfolder = /usr/bin/|' /opt/MitoFinder/Mitofinder.config; true

ENV PATH="/opt/MitoFinder:/opt/MitoFinder/blast/bin:$PATH"
ENV MITOFINDER_HOME="/opt/MitoFinder"

# MitoFinder reads Mitofinder.config from its CWD; `-j` writes output under ./<seqid> by default
# (MitoFinder works in the current directory). Keep CWD=/opt/MitoFinder so `default` tool paths
# resolve; the module's `-o/-1/-2/-r` inputs are staged by Nextflow.
#
# NO ENTRYPOINT: nf-core/Nextflow requires the container to let the process's `.command.sh` run via
# bash. Setting ENTRYPOINT=/opt/MitoFinder/mitofinder would intercept Nextflow's `docker run ... bash
# .command.sh` and re-run mitofinder with the wrong args (observed: stub mode re-invoking mitofinder
# and failing on `import Bio`). The module's script calls `mitofinder` on PATH explicitly.
WORKDIR /opt/MitoFinder
