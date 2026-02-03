from __future__ import annotations

from datetime import datetime

from flask import Flask, Response, jsonify, render_template, request

from tts_service import ValidationError, get_available_voices, synthesize_text, validate_synthesis_payload

app = Flask(__name__)


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


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
