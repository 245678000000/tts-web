/* ── Theme Management ── */

(function initTheme() {
  const toggle = document.getElementById("themeToggle");
  const label = document.getElementById("themeLabel");
  const root = document.documentElement;

  const LABELS = { auto: "自动", light: "浅色", dark: "深色" };

  function getPref() {
    return localStorage.getItem("theme") || "auto";
  }

  function apply(pref) {
    const resolved = pref === "auto"
      ? (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")
      : pref;
    root.setAttribute("data-theme", resolved);
    root.setAttribute("data-pref", pref);
    localStorage.setItem("theme", pref);
    if (label) label.textContent = LABELS[pref] || pref;
  }

  if (toggle) {
    toggle.addEventListener("click", function () {
      const cur = getPref();
      const next = cur === "auto" ? "light" : cur === "light" ? "dark" : "auto";
      apply(next);
    });
  }

  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () {
    if (getPref() === "auto") apply("auto");
  });

  apply(getPref());
})();

/* ── TTS Controls ── */

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
  charCount.textContent = `${textInput.value.length} / 5000 字`;
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

/* ── Slider value display ── */

const rateValueDisplay = document.getElementById("rateValue");
const pitchValueDisplay = document.getElementById("pitchValue");

if (rateValueDisplay) {
  rateInput.addEventListener("input", function () {
    rateValueDisplay.textContent = rateInput.value;
  });
}

if (pitchValueDisplay) {
  pitchInput.addEventListener("input", function () {
    pitchValueDisplay.textContent = pitchInput.value;
  });
}

/* ═══════════════════════════════════════════════════════════
   音频转录与智能分析
   ═══════════════════════════════════════════════════════════ */

const uploadZone = document.getElementById("uploadZone");
const audioFileInput = document.getElementById("audioFileInput");
const fileInfo = document.getElementById("fileInfo");
const fileName = document.getElementById("fileName");
const fileSize = document.getElementById("fileSize");
const removeFileBtn = document.getElementById("removeFileBtn");
const transcribeBtn = document.getElementById("transcribeBtn");
const transcribeStatus = document.getElementById("transcribeStatus");
const transcribeResultPanel = document.getElementById("transcribeResultPanel");
const transcribeOutput = document.getElementById("transcribeOutput");
const transcribeCharCount = document.getElementById("transcribeCharCount");
const analyzeBtn = document.getElementById("analyzeBtn");
const analyzeStatus = document.getElementById("analyzeStatus");
const analysisResultPanel = document.getElementById("analysisResultPanel");
const analysisOutput = document.getElementById("analysisOutput");
const exportPanel = document.getElementById("exportPanel");
const exportTranscriptBtn = document.getElementById("exportTranscriptBtn");
const exportAnalysisBtn = document.getElementById("exportAnalysisBtn");
const exportFullBtn = document.getElementById("exportFullBtn");
const transcribeErrorBox = document.getElementById("transcribeErrorBox");

let selectedFile = null;
let isTranscribing = false;
let isAnalyzing = false;
let analysisRawText = "";

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function showTranscribeError(msg) {
  transcribeErrorBox.textContent = msg;
  transcribeErrorBox.classList.remove("hidden");
}

function hideTranscribeError() {
  transcribeErrorBox.classList.add("hidden");
  transcribeErrorBox.textContent = "";
}

function setFileSelected(file) {
  if (!file) return;
  const maxSize = 25 * 1024 * 1024;
  if (file.size > maxSize) {
    showTranscribeError("文件过大，最大支持 25 MB。");
    return;
  }
  selectedFile = file;
  fileName.textContent = file.name;
  fileSize.textContent = formatFileSize(file.size);
  fileInfo.classList.remove("hidden");
  uploadZone.style.display = "none";
  transcribeBtn.disabled = false;
  transcribeStatus.textContent = "文件已就绪，可以开始转录。";
  hideTranscribeError();
  audioFileInput.value = "";
}

function clearFile() {
  selectedFile = null;
  fileInfo.classList.add("hidden");
  uploadZone.style.display = "";
  audioFileInput.value = "";
  transcribeBtn.disabled = true;
  transcribeStatus.textContent = "请上传音频文件。";
}

function setTranscribeLoading(loading, msg) {
  isTranscribing = loading;
  transcribeBtn.textContent = loading ? "转录中…" : "开始转录";
  transcribeBtn.classList.toggle("is-loading", loading);
  transcribeBtn.disabled = loading || !selectedFile;
  transcribeStatus.textContent = msg;
}

function setAnalyzeLoading(loading, msg) {
  isAnalyzing = loading;
  analyzeBtn.textContent = loading ? "分析中…" : "🚀 使用 GPT-5 智能分析";
  analyzeBtn.classList.toggle("is-loading", loading);
  analyzeBtn.disabled = loading;
  analyzeStatus.textContent = msg || "";
}

/* ── Upload Zone Events ── */

uploadZone.addEventListener("dragover", function (e) {
  e.preventDefault();
  uploadZone.classList.add("drag-over");
});

uploadZone.addEventListener("dragleave", function () {
  uploadZone.classList.remove("drag-over");
});

uploadZone.addEventListener("drop", function (e) {
  e.preventDefault();
  uploadZone.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file) setFileSelected(file);
});

audioFileInput.addEventListener("change", function () {
  const file = audioFileInput.files[0];
  if (file) setFileSelected(file);
});

removeFileBtn.addEventListener("click", clearFile);

/* ── Transcribe ── */

async function doTranscribe() {
  if (!selectedFile || isTranscribing) return;
  hideTranscribeError();
  setTranscribeLoading(true, "正在转录，请稍等…");
  transcribeResultPanel.classList.add("hidden");
  analysisResultPanel.classList.add("hidden");
  exportPanel.classList.add("hidden");

  const formData = new FormData();
  formData.append("file", selectedFile);

  try {
    const res = await fetch("/api/transcribe", {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      let msg = "转录失败，请稍后再试。";
      try {
        const err = await res.json();
        if (err.message) msg = err.message;
        else if (err.error) msg = err.error;
      } catch (_) {}
      throw new Error(msg);
    }

    const data = await res.json();
    const text = (data.text || "").trim();
    if (!text) throw new Error("转录结果为空，请检查音频是否包含语音。");

    transcribeOutput.value = text;
    updateTranscribeCharCount();
    transcribeResultPanel.classList.remove("hidden");
    exportPanel.classList.remove("hidden");
    updateExportVisibility();
    setTranscribeLoading(false, "转录完成！");
  } catch (err) {
    showTranscribeError(err.message || "转录失败，请检查网络后重试。");
    setTranscribeLoading(false, "转录失败。");
  }
}

transcribeBtn.addEventListener("click", doTranscribe);

/* ── Transcribe Output ── */

function updateTranscribeCharCount() {
  transcribeCharCount.textContent = transcribeOutput.value.length + " 字";
}

transcribeOutput.addEventListener("input", function () {
  updateTranscribeCharCount();
  updateExportVisibility();
});

/* ── Analyze ── */

async function doAnalyze() {
  const text = transcribeOutput.value.trim();
  if (!text || isAnalyzing) return;

  hideTranscribeError();
  setAnalyzeLoading(true, "正在分析…");
  analysisResultPanel.classList.add("hidden");
  analysisRawText = "";

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text }),
    });

    if (!res.ok) {
      let msg = "分析失败，请稍后再试。";
      try {
        const err = await res.json();
        if (err.message) msg = err.message;
      } catch (_) {}
      throw new Error(msg);
    }

    const data = await res.json();
    analysisRawText = data.analysis || "";
    analysisOutput.innerHTML = renderMarkdown(analysisRawText);
    analysisResultPanel.classList.remove("hidden");
    updateExportVisibility();
    setAnalyzeLoading(false, "分析完成！");
  } catch (err) {
    showTranscribeError(err.message || "分析失败，请检查网络后重试。");
    setAnalyzeLoading(false, "分析失败。");
  }
}

analyzeBtn.addEventListener("click", doAnalyze);

/* ── Lightweight Markdown → HTML ── */

function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function inlineFmt(s) {
  return escapeHtml(s)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`(.+?)`/g, "<code>$1</code>");
}

function renderMarkdown(text) {
  if (!text) return "";
  const lines = text.split("\n");
  let html = "";
  let inUl = false;
  let inOl = false;

  function closeList() {
    if (inUl) { html += "</ul>"; inUl = false; }
    if (inOl) { html += "</ol>"; inOl = false; }
  }

  for (const raw of lines) {
    const line = raw.trimEnd();
    const trimmed = line.trim();

    if (!trimmed) { closeList(); html += "<br>"; continue; }

    if (trimmed.startsWith("### ")) { closeList(); html += "<h5>" + inlineFmt(trimmed.slice(4)) + "</h5>"; continue; }
    if (trimmed.startsWith("## "))  { closeList(); html += "<h4>" + inlineFmt(trimmed.slice(3)) + "</h4>"; continue; }
    if (trimmed.startsWith("# "))   { closeList(); html += "<h3>" + inlineFmt(trimmed.slice(2)) + "</h3>"; continue; }

    if (/^[-*]\s/.test(trimmed)) {
      if (inOl) { html += "</ol>"; inOl = false; }
      if (!inUl) { html += "<ul>"; inUl = true; }
      html += "<li>" + inlineFmt(trimmed.slice(2)) + "</li>";
      continue;
    }

    const olMatch = trimmed.match(/^\d+\.\s(.+)/);
    if (olMatch) {
      if (inUl) { html += "</ul>"; inUl = false; }
      if (!inOl) { html += "<ol>"; inOl = true; }
      html += "<li>" + inlineFmt(olMatch[1]) + "</li>";
      continue;
    }

    closeList();
    html += "<p>" + inlineFmt(trimmed) + "</p>";
  }
  closeList();
  return html;
}

/* ── Export ── */

function downloadBlob(content, filename, mime) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function updateExportVisibility() {
  const hasTranscript = transcribeOutput.value.trim().length > 0;
  const hasAnalysis = analysisRawText.trim().length > 0;
  exportPanel.classList.toggle("hidden", !hasTranscript);
  exportAnalysisBtn.disabled = !hasAnalysis;
  exportFullBtn.disabled = !hasAnalysis;
  exportAnalysisBtn.style.opacity = hasAnalysis ? "" : "0.45";
  exportFullBtn.style.opacity = hasAnalysis ? "" : "0.45";
}

exportTranscriptBtn.addEventListener("click", function () {
  const text = transcribeOutput.value.trim();
  if (text) downloadBlob(text, "transcript.txt", "text/plain;charset=utf-8");
});

exportAnalysisBtn.addEventListener("click", function () {
  if (analysisRawText.trim()) {
    downloadBlob(analysisRawText, "analysis.md", "text/markdown;charset=utf-8");
  }
});

exportFullBtn.addEventListener("click", function () {
  const transcript = transcribeOutput.value.trim();
  const analysis = analysisRawText.trim();
  if (!transcript) return;
  let report = "═══ 转录文本 ═══\n\n" + transcript;
  if (analysis) report += "\n\n═══ 智能分析 ═══\n\n" + analysis;
  downloadBlob(report, "full_report.txt", "text/plain;charset=utf-8");
});

/* Re-create Lucide icons for new DOM elements */
if (window.lucide) {
  window.lucide.createIcons({ attrs: { "stroke-width": "1.75" } });
}
