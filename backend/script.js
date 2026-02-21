const fileInput = document.getElementById("fileInput");
const analyzeBtn = document.getElementById("analyzeBtn");
const statusText = document.getElementById("statusText");
const resultBox = document.getElementById("resultBox");
const hintChip = document.getElementById("hintChip");
const setTokenBtn = document.getElementById("setTokenBtn");

const TOKEN_KEY = "zoom_analyzer_token";

function getToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

function setToken(token) {
  if (!token) return;
  localStorage.setItem(TOKEN_KEY, token);
}

function ensureToken() {
  const token = getToken();
  if (token) return token;

  const input = prompt("社内パスコードを入力してください（管理者から共有される合言葉）");
  if (!input) throw new Error("社内パスコードが未設定です");
  setToken(input.trim());
  return getToken();
}

setTokenBtn.addEventListener("click", () => {
  const input = prompt("社内パスコードを入力してください");
  if (!input) return;
  setToken(input.trim());
  refreshHint();
});

async function refreshHint() {
  try {
    const r = await fetch("/api/health");
    const j = await r.json();
    if (j.ok) {
      hintChip.textContent = `model: ${j.whisper_model} / max: ${j.max_upload_mb}MB / conc: ${j.concurrency}`;
    } else {
      hintChip.textContent = "health: NG";
    }
  } catch {
    hintChip.textContent = "health: NG";
  }
}

analyzeBtn.addEventListener("click", async () => {
  const file = fileInput.files?.[0];
  if (!file) {
    alert("ファイルを選んでね");
    return;
  }

  analyzeBtn.disabled = true;
  const prevText = analyzeBtn.textContent;
  analyzeBtn.textContent = "解析中…";
  statusText.textContent = "アップロード中…";
  resultBox.textContent = "(解析中…)";

  try {
    const token = ensureToken();

    const form = new FormData();
    form.append("file", file);

    statusText.textContent = "解析リクエスト送信…";
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "X-App-Token": token },
      body: form
    });

    const data = await res.json();

    if (!data.ok) {
      throw new Error(data.error || "解析に失敗しました");
    }

    statusText.textContent = "完了";
    resultBox.textContent = data.text || "(空でした)";

  } catch (err) {
    statusText.textContent = "エラー";
    resultBox.textContent = String(err);
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = prevText;
  }
});

refreshHint();