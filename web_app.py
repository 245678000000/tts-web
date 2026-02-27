from __future__ import annotations

from datetime import datetime

import requests as http_client
from flask import Flask, Response, jsonify, render_template, request

from tts_service import ValidationError, get_available_voices, synthesize_text, validate_synthesis_payload

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024

TRANSCRIBE_API_URL = "https://api.infiniteai.cc/v1/audio/transcriptions"
TRANSCRIBE_API_KEY = "sk-X_8Tbr4jwJm-JDPQFasYAdla_Ts6AA9K"
ANALYZE_API_URL = "https://api.infiniteai.cc/v1/chat/completions"
ANALYZE_MODEL = "gpt-5"
ANALYZE_SYSTEM_PROMPT = (
    "你是一个专业的中文助手。请对以下音频转录内容进行："
    "1. 简洁总结 2. 提取关键点 3. 给出实用行动建议。"
    "用清晰的 Markdown 格式回复。"
)


def error_response(error_code: str, message: str, status_code: int) -> Response:
    payload = {"error_code": error_code, "message": message}
    return jsonify(payload), status_code


@app.get("/")
def index() -> str:
    return render_template("index.html")


@app.get("/api/voices")
def voices() -> Response:
    try:
        return jsonify({"voices": get_available_voices()})
    except Exception as exc:  # pragma: no cover - external dependency failures
        return error_response("voice_list_failed", f"获取音色失败：{exc}", 500)


@app.post("/api/synthesize")
def synthesize() -> Response:
    try:
        payload = validate_synthesis_payload(request.get_json(silent=True))
    except ValidationError as exc:
        return error_response("invalid_request", str(exc), 400)

    try:
        audio_data = synthesize_text(
            text=payload["text"],
            voice_name=payload["voice_name"],
            style=payload["style"],
            rate=payload["rate"],
            pitch=payload["pitch"],
        )
    except ValidationError as exc:
        return error_response("invalid_request", str(exc), 400)
    except Exception as exc:
        return error_response("synthesis_failed", f"合成失败：{exc}", 500)

    filename = datetime.now().strftime("tts_%Y%m%d_%H%M%S.mp3")
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(audio_data, status=200, mimetype="audio/mpeg", headers=headers)


@app.post("/api/transcribe")
def transcribe():
    if "file" not in request.files:
        return error_response("no_file", "没有收到文件", 400)

    audio_file = request.files["file"]
    if not audio_file.filename:
        return error_response("no_file", "请选择一个有效的音频文件。", 400)

    try:
        files = {"file": (audio_file.filename, audio_file.stream, audio_file.mimetype)}
        data = {
            "model": "whisper-1",
            "response_format": "text",
            "language": "zh",
        }
        headers = {"Authorization": f"Bearer {TRANSCRIBE_API_KEY}"}

        resp = http_client.post(
            TRANSCRIBE_API_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=120,
        )

        if resp.status_code == 200:
            try:
                result = resp.json()
                text = result.get("text", resp.text).strip()
            except ValueError:
                text = resp.text.strip()
            return jsonify({"text": text})
        else:
            error_msg = resp.text[:200] or f"HTTP {resp.status_code}"
            return jsonify({"error": error_msg}), resp.status_code
    except http_client.exceptions.Timeout:
        return error_response("timeout", "转录超时，请尝试较短的音频文件。", 504)
    except Exception as exc:
        return jsonify({"error": f"后端错误: {str(exc)}"}), 500


@app.post("/api/analyze")
def analyze():
    payload = request.get_json(silent=True)
    if not payload or not payload.get("text", "").strip():
        return error_response("no_text", "请提供要分析的文本。", 400)

    try:
        resp = http_client.post(
            ANALYZE_API_URL,
            headers={
                "Authorization": f"Bearer {TRANSCRIBE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": ANALYZE_MODEL,
                "messages": [
                    {"role": "system", "content": ANALYZE_SYSTEM_PROMPT},
                    {"role": "user", "content": payload["text"]},
                ],
            },
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return jsonify({"analysis": content})
    except http_client.exceptions.Timeout:
        return error_response("timeout", "分析超时，请稍后重试。", 504)
    except (KeyError, IndexError):
        return error_response("analyze_failed", "分析返回格式异常。", 500)
    except http_client.exceptions.RequestException as exc:
        return error_response("analyze_failed", f"分析失败：{exc}", 500)
    except Exception as exc:
        return error_response("analyze_failed", f"分析失败：{exc}", 500)


@app.errorhandler(413)
def file_too_large(e):
    return error_response("file_too_large", "文件过大，最大支持 25MB。", 413)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
