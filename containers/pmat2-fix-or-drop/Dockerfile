FROM mambaorg/micromamba:1.5.8

LABEL org.opencontainers.image.title="PMAT2 bounded comparator"
LABEL org.opencontainers.image.description="Single-attempt PMAT2 experimental comparator runtime"
LABEL org.opencontainers.image.version="2.1.5"

USER root
RUN micromamba install -y -n base -c conda-forge -c bioconda pmat2=2.1.5 \
    && micromamba clean --all --yes
ENV PATH=/opt/conda/bin:${PATH}
RUN command -v PMAT || command -v PMAT2 || command -v autoMito
USER $MAMBA_USER
ENTRYPOINT []
