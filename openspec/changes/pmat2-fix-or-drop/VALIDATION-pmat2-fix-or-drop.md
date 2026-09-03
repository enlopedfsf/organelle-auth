# PMAT2 fix-or-drop validation

## Terminal disposition

`DROP`. The one authorized CI repair attempt used GitHub Actions run `32575965200`, job `99722219310`, with real Docker build execution. The runner, checkout, GHCR login, and Buildx initialization succeeded. The image build failed at Dockerfile line 8 while resolving `pmat2=2.1.5`:

```text
libmamba Could not solve for environment specs
pmat2 2.1.5 does not exist (perhaps a typo or a missing channel)
```

Because the image was not built, executable preflight and the plant comparator were not run. This is an environment/package availability failure, not biological evidence. No retry or parameter arm was added. Issue #10 was closed with this evidence.

PMAT2 remains outside `IDENTIFY` and `DECISION`; the animal line and M4 are unaffected.
