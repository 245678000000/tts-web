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
- The transcription feature proxies through `/api/transcribe` to InfiniteAI Whisper API. The analysis feature proxies through `/api/analyze` to InfiniteAI GPT-5 chat completions. Both require outbound HTTPS access to `api.infiniteai.cc`.
- Auth credentials are hardcoded: Azure TTS in `azure_tts.py`, InfiniteAI key in `web_app.py`. No `.env` file or environment variables are needed.
- `MAX_CONTENT_LENGTH` is set to 25 MB for audio file uploads.
- Dependencies install to user site-packages (`~/.local/`). The `flask` CLI may require `~/.local/bin` on PATH — but `python3 web_app.py` works regardless.
- No database, Docker, or external service dependencies for local development.
