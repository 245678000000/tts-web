# AGENTS.md

## Cursor Cloud specific instructions

This is a Python Flask web application for Chinese text-to-speech (TTS) using Azure Cognitive Services.

### Services

| Service | Command | Port | Notes |
|---------|---------|------|-------|
| Flask web app | `python3 web_app.py` | 5000 | Main web UI and API server |

### Running tests

```
python3 -m unittest discover tests/ -v
```

Tests mock Azure API calls — no network access needed.

### Key caveats

- There is no linter configured in the project. No `pyproject.toml`, `setup.cfg`, or linting config files exist.
- The app uses Azure TTS endpoints (`dev.microsofttranslator.com`, `eastus.api.speech.microsoft.com`). Actual voice synthesis requires outbound HTTPS access. The web UI loads fine without it.
- Auth credentials for the Azure TTS service are hardcoded in `azure_tts.py` (HMAC-signed). No `.env` file or environment variables are needed.
- Dependencies install to user site-packages (`~/.local/`). The `flask` CLI may require `~/.local/bin` on PATH — but `python3 web_app.py` works regardless.
- No database, Docker, or external service dependencies for local development.
