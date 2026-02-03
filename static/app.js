const textInput = document.getElementById("textInput");
const charCount = document.getElementById("charCount");
const voiceSelect = document.getElementById("voiceSelect");
const styleSelect = document.getElementById("styleSelect");
const rateInput = document.getElementById("rateInput");
const pitchInput = document.getElementById("pitchInput");
const generateBtn = document.getElementById("generateBtn");
const statusText = document.getElementById("statusText");
const errorBox = document.getElementById("errorBox");
const resultBox = document.getElementById("resultBox");
const audioPlayer = document.getElementById("audioPlayer");
const downloadLink = document.getElementById("downloadLink");

let currentAudioUrl = null;
let isLoading = false;

function updateButtonState() {
  const hasText = textInput.value.trim().length > 0;
  generateBtn.disabled = !hasText || isLoading;
}

function updateCharCount() {
  charCount.textContent = `${textInput.value.length} 字`;
  updateButtonState();
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove("hidden");
}

function hideError() {
  errorBox.classList.add("hidden");
  errorBox.textContent = "";
}

function resetAudioUrl() {
  if (currentAudioUrl) {
    URL.revokeObjectURL(currentAudioUrl);
    currentAudioUrl = null;
  }
}

function setLoading(loading, message) {
  isLoading = loading;
  generateBtn.textContent = loading ? "生成中..." : "生成语音";
  generateBtn.classList.toggle("is-loading", loading);
  statusText.textContent = message;
  updateButtonState();
}

function parseFilenameFromDisposition(headerValue) {
  if (!headerValue) return "tts_output.mp3";

  const utf8Match = headerValue.match(/filename\*=(?:UTF-8'')?([^;]+)/i);
  if (utf8Match && utf8Match[1]) {
    return decodeURIComponent(utf8Match[1].replace(/['"]/g, "").trim());
  }

  const plainMatch = headerValue.match(/filename=([^;]+)/i);
  if (plainMatch && plainMatch[1]) {
    return plainMatch[1].replace(/['"]/g, "").trim();
  }

  return "tts_output.mp3";
}

async function loadVoices() {
  try {
    const res = await fetch("/api/voices");
    if (!res.ok) throw new Error("加载音色失败");
    const data = await res.json();
    const voices = Array.isArray(data.voices) ? data.voices : [];
    if (voices.length === 0) return;

    voiceSelect.innerHTML = "";
    for (const voice of voices) {
      const option = document.createElement("option");
      option.value = voice.short_name;
      const localeText = voice.locale ? ` / ${voice.locale}` : "";
      const genderText = voice.gender ? ` / ${voice.gender}` : "";
      option.textContent = `${voice.short_name}${localeText}${genderText}`;
      voiceSelect.appendChild(option);
    }

    const defaultOption = [...voiceSelect.options].find(
      (item) => item.value === "zh-CN-XiaoxiaoNeural"
    );
    if (defaultOption) {
      voiceSelect.value = "zh-CN-XiaoxiaoNeural";
    }
  } catch (err) {
    showError("音色列表加载失败，已使用内置音色列表。");
  }
}

async function synthesize() {
  hideError();
  resultBox.classList.add("hidden");
  setLoading(true, "正在合成语音，请稍等...");

  const payload = {
    text: textInput.value,
    voice_name: voiceSelect.value,
    style: styleSelect.value,
    rate: rateInput.value,
    pitch: pitchInput.value,
  };

  try {
    const res = await fetch("/api/synthesize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      let message = "请求失败，请稍后再试。";
      try {
        const err = await res.json();
        if (err.message) message = err.message;
      } catch (ignore) {
        // Keep fallback error text.
      }
      throw new Error(message);
    }

    const blob = await res.blob();
    resetAudioUrl();
    currentAudioUrl = URL.createObjectURL(blob);

    audioPlayer.src = currentAudioUrl;
    downloadLink.href = currentAudioUrl;
    downloadLink.download = parseFilenameFromDisposition(
      res.headers.get("Content-Disposition")
    );

    resultBox.classList.remove("hidden");
    statusText.textContent = "合成完成，可以试听或下载。";
  } catch (err) {
    showError(err.message || "合成失败，请检查网络后重试。");
    statusText.textContent = "合成失败。";
  } finally {
    setLoading(false, statusText.textContent);
  }
}

textInput.addEventListener("input", updateCharCount);
generateBtn.addEventListener("click", synthesize);
window.addEventListener("beforeunload", resetAudioUrl);

updateCharCount();
loadVoices();
