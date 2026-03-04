# Presenton Docker (Restored)

This directory restores a Docker-based presentation generation flow.

## Scope
- `pptx`: runs `presentation/generate_pptx.py`
- `docx`: runs `presentation/generate_실증보고서.py`
- `all`: runs both in sequence

Mounted host path:
- `/home/uproot/ax/docs/초기창업패키지` -> `/workspace/startup`

## Usage
From this directory:

```bash
docker compose build
docker compose run --rm presenton all
```

Run only PPTX:

```bash
docker compose run --rm presenton pptx
```

Run only DOCX:

```bash
docker compose run --rm presenton docx
```

Interactive shell in container:

```bash
docker compose run --rm presenton shell
```

## Output
Generated files are written back to host path:
- `/home/uproot/ax/docs/초기창업패키지/presentation/업루트_성과발표회_최종.pptx`
- `/home/uproot/ax/docs/초기창업패키지/presentation/실증테스트_결과보고서_업루트.docx`
