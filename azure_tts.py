import base64
import hashlib
import hmac
import html
import json
import logging
import time
import uuid
from datetime import datetime
from urllib.parse import quote
import requests
from tenacity import retry, wait_exponential, stop_after_attempt

logger = logging.getLogger(__name__)

# 常量定义
ENDPOINT_URL = "https://dev.microsofttranslator.com/apps/endpoint?api-version=1.0"
VOICES_LIST_URL = "https://eastus.api.speech.microsoft.com/cognitiveservices/voices/list"
USER_AGENT = "okhttp/4.5.0"
CLIENT_VERSION = "4.0.530a 5fe1dc6c"
USER_ID = "0f04d16a175c411e"
HOME_GEOGRAPHIC_REGION = "zh-Hans-CN"
CLIENT_TRACE_ID = "aab069b9-70a7-4844-a734-96cd78d94be9"
VOICE_DECODE_KEY = "oik6PdDdMnOXemTbwvMn9de/h9lFnfBaCWbGMMZqqoSaQaqUOqjVGm5NqsmjcBI1x+sS9ugjB55HEJWRiFXYFw=="
DEFAULT_VOICE_NAME = "zh-CN-XiaoxiaoMultilingualNeural"
DEFAULT_RATE = "0"
DEFAULT_PITCH = "0"
DEFAULT_OUTPUT_FORMAT = "audio-24khz-48kbitrate-mono-mp3"
DEFAULT_STYLE = "general"

endpoint = None
expired_at = None
voice_list_cache = None

def get_endpoint(proxies=None):
    signature = sign(ENDPOINT_URL)
    headers = {
        "Accept-Language": "zh-Hans",
        "X-ClientVersion": CLIENT_VERSION,
        "X-UserId": USER_ID,
        "X-HomeGeographicRegion": HOME_GEOGRAPHIC_REGION,
        "X-ClientTraceId": CLIENT_TRACE_ID,
        "X-MT-Signature": signature,
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json; charset=utf-8",
        "Content-Length": "0",
        "Accept-Encoding": "gzip",
    }

    response = requests.post(ENDPOINT_URL, headers=headers, proxies=proxies)
    response.raise_for_status()
    return response.json()


def sign(url_str):
    u = url_str.split("://")[1]
    encoded_url = quote(u, safe='')
    uuid_str = str(uuid.uuid4()).replace("-", "")
    formatted_date = datetime.utcnow().strftime(
        "%a, %d %b %Y %H:%M:%S").lower() + "gmt"
    bytes_to_sign = f"MSTranslatorAndroidApp{encoded_url}{formatted_date}{uuid_str}".lower().encode('utf-8')

    decode = base64.b64decode(VOICE_DECODE_KEY)
    hmac_sha256 = hmac.new(decode, bytes_to_sign, hashlib.sha256)
    secret_key = hmac_sha256.digest()
    sign_base64 = base64.b64encode(secret_key).decode()

    return f"MSTranslatorAndroidApp::{sign_base64}::{formatted_date}::{uuid_str}"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=5))
def get_voice(text, voice_name="", rate="", pitch="", output_format="", style="", proxies=None):
    global endpoint, expired_at, client_id

    current_time = int(time.time())
    if not expired_at or current_time > expired_at - 60:
        endpoint = get_endpoint(proxies)
        jwt = endpoint['t'].split('.')[1]
        decoded_jwt = json.loads(base64.b64decode(jwt + '==').decode('utf-8'))
        expired_at = decoded_jwt['exp']
        seconds_left = expired_at - current_time
        client_id = str(uuid.uuid4())
    else:
        seconds_left = expired_at - current_time

    voice_name = voice_name or DEFAULT_VOICE_NAME
    rate = rate or DEFAULT_RATE
    pitch = pitch or DEFAULT_PITCH
    output_format = output_format or DEFAULT_OUTPUT_FORMAT
    style = style or DEFAULT_STYLE

    endpoint = get_endpoint(proxies)

    url = f"https://{endpoint['r']}.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        "Authorization": endpoint["t"],
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": output_format,
    }

    ssml = get_ssml(text, voice_name, rate, pitch, style)

    response = requests.post(url, headers=headers, data=ssml.encode(), proxies=proxies)
    response.raise_for_status()
    return response.content


def get_ssml(text, voice_name, rate, pitch, style):
    return f"""
<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" version="1.0" xml:lang="zh-CN">
<voice name="{voice_name}">
    <mstts:express-as style="{style}" styledegree="1.0" role="default">
        <prosody rate="{rate}%" pitch="{pitch}%">
            {text}
        </prosody>
    </mstts:express-as>
</voice>
</speak>
    """

def get_voice_list():
    """获取可用的语音列表"""
    global voice_list_cache

    # 如果缓存中有值，直接返回缓存的结果
    if voice_list_cache is not None:
        return voice_list_cache

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.26",
        "X-Ms-Useragent": "SpeechStudio/2021.05.001",
        "Content-Type": "application/json",
        "Origin": "https://azure.microsoft.com",
        "Referer": "https://azure.microsoft.com"
    }

    try:
        response = requests.get(VOICES_LIST_URL, headers=headers)
        response.raise_for_status()
        result = response.json()

        # 将结果存储到缓存中
        voice_list_cache = result

        return result
    except requests.exceptions.RequestException as e:
        logger.error(f"获取语音列表失败: {e}")
        return None