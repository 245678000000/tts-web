from __future__ import annotations

import re
from typing import Dict, List

from azure_tts import get_voice, get_voice_list

DEFAULT_VOICE_NAME = "zh-CN-XiaoxiaoNeural"
DEFAULT_STYLE = "narration-relaxed"
DEFAULT_RATE = "0"
DEFAULT_PITCH = "0"
MAX_CHARS_PER_CHUNK = 1200
BUILTIN_VOICES = [
    {"short_name": "zh-CN-XiaoxiaoNeural", "locale": "zh-CN", "gender": "Female", "display_name": "Xiaoxiao"},
    {"short_name": "zh-CN-YunxiNeural", "locale": "zh-CN", "gender": "Male", "display_name": "Yunxi"},
    {"short_name": "zh-CN-YunjianNeural", "locale": "zh-CN", "gender": "Male", "display_name": "Yunjian"},
    {"short_name": "zh-CN-XiaoyiNeural", "locale": "zh-CN", "gender": "Female", "display_name": "Xiaoyi"},
    {"short_name": "zh-CN-YunyangNeural", "locale": "zh-CN", "gender": "Male", "display_name": "Yunyang"},
    {"short_name": "zh-CN-XiaohanNeural", "locale": "zh-CN", "gender": "Female", "display_name": "Xiaohan"},
    {"short_name": "zh-CN-XiaomoNeural", "locale": "zh-CN", "gender": "Female", "display_name": "Xiaomo"},
    {"short_name": "zh-CN-YunfengNeural", "locale": "zh-CN", "gender": "Male", "display_name": "Yunfeng"},
    {
        "short_name": "zh-CN-XiaoxiaoMultilingualNeural",
        "locale": "zh-CN",
        "gender": "Female",
        "display_name": "Xiaoxiao Multilingual",
    },
]


class ValidationError(ValueError):
    """Raised when user input is invalid."""


def _normalize_numeric_param(raw: object, name: str) -> str:
    if raw is None:
        return DEFAULT_RATE if name == "rate" else DEFAULT_PITCH

    value = str(raw).strip()
    if not value:
        return DEFAULT_RATE if name == "rate" else DEFAULT_PITCH

    if not re.fullmatch(r"[+-]?\d+", value):
        raise ValidationError(f"{name} 必须是整数，范围 -100 到 100。")

    number = int(value)
    if number < -100 or number > 100:
        raise ValidationError(f"{name} 超出范围，请填写 -100 到 100。")

    return str(number)


def validate_synthesis_payload(payload: object) -> Dict[str, str]:
    if not isinstance(payload, dict):
        raise ValidationError("请求体必须是 JSON 对象。")

    text = str(payload.get("text", "")).replace("\r\n", "\n")
    if not text.strip():
        raise ValidationError("请输入要合成的文字。")

    voice_name = str(payload.get("voice_name") or DEFAULT_VOICE_NAME).strip() or DEFAULT_VOICE_NAME
    style = str(payload.get("style") or DEFAULT_STYLE).strip() or DEFAULT_STYLE
    rate = _normalize_numeric_param(payload.get("rate"), "rate")
    pitch = _normalize_numeric_param(payload.get("pitch"), "pitch")

    return {
        "text": text,
        "voice_name": voice_name,
        "style": style,
        "rate": rate,
        "pitch": pitch,
    }


def split_text_into_chunks(text: str, max_chars: int = MAX_CHARS_PER_CHUNK) -> List[str]:
    normalized = text.replace("\r\n", "\n")
    if not normalized:
        return []

    sentences = [part for part in re.split(r"(?<=[。！？；\n])", normalized) if part]
    chunks: List[str] = []
    current = ""

    for sentence in sentences:
        if len(sentence) > max_chars:
            if current:
                chunks.append(current)
                current = ""

            for i in range(0, len(sentence), max_chars):
                chunks.append(sentence[i : i + max_chars])
            continue

        if len(current) + len(sentence) <= max_chars:
            current += sentence
        else:
            if current:
                chunks.append(current)
            current = sentence

    if current:
        chunks.append(current)

    return chunks


def synthesize_text(
    text: str,
    voice_name: str = DEFAULT_VOICE_NAME,
    style: str = DEFAULT_STYLE,
    rate: str = DEFAULT_RATE,
    pitch: str = DEFAULT_PITCH,
    max_chars: int = MAX_CHARS_PER_CHUNK,
) -> bytes:
    chunks = split_text_into_chunks(text, max_chars=max_chars)
    if not chunks:
        raise ValidationError("请输入要合成的文字。")

    audio_parts: List[bytes] = []
    for chunk in chunks:
        audio_parts.append(
            get_voice(
                text=chunk,
                voice_name=voice_name,
                style=style,
                rate=rate,
                pitch=pitch,
            )
        )

    return b"".join(audio_parts)


def _build_voice_item(voice: Dict[str, object]) -> Dict[str, str]:
    short_name = str(voice.get("ShortName") or voice.get("Name") or "").strip()
    locale = str(voice.get("Locale") or "").strip()
    gender = str(voice.get("GenderName") or voice.get("Gender") or "").strip()
    display_name = str(voice.get("DisplayName") or short_name).strip()
    return {
        "short_name": short_name,
        "locale": locale,
        "gender": gender,
        "display_name": display_name,
    }


def get_available_voices() -> List[Dict[str, str]]:
    raw_voices = get_voice_list() or []
    result: List[Dict[str, str]] = list(BUILTIN_VOICES)
    seen = {item["short_name"] for item in result}

    for voice in raw_voices:
        if not isinstance(voice, dict):
            continue
        parsed = _build_voice_item(voice)
        if parsed["short_name"] and parsed["short_name"] not in seen:
            result.append(parsed)
            seen.add(parsed["short_name"])

    result.sort(
        key=lambda item: (
            0 if item["locale"].startswith("zh-CN") else 1,
            item["locale"],
            item["short_name"],
        )
    )
    return result
