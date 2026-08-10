# Network setup for Nextflow and CI

GitHub Actions is the canonical MitoFinder image publisher. Local Docker is not part of the GHCR publication path. The workstation only needs network access when Nextflow resolves plugins, remote configs, or pulls containers.

For foreign services, use the workstation v2ray proxy for the current shell:

```bash
export http_proxy=http://127.0.0.1:10808
export https_proxy=http://127.0.0.1:10808
export HTTP_PROXY="$http_proxy"
export HTTPS_PROXY="$https_proxy"
export no_proxy=127.0.0.1,localhost
export NXF_OPTS="-Dhttp.proxyHost=127.0.0.1 -Dhttp.proxyPort=10808 -Dhttps.proxyHost=127.0.0.1 -Dhttps.proxyPort=10808"
```

Then run the three-scenario validation from the repository root. Do not proxy domestic Mamba mirrors; unset the variables for Mamba commands. If the proxy is unavailable, stop and record the failed network operation rather than substituting a local/public fallback reference.

The CI workflow `.github/workflows/animal-image-and-identify.yml` builds, publishes, and records the GHCR immutable digest before the animal identify tests. The digest and test artifacts are the release evidence required by issue #6.
