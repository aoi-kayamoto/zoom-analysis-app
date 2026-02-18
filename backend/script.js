const uploadForm = document.getElementById("uploadForm");
const fileInput = document.getElementById("fileInput");
const resultBox = document.getElementById("resultBox");
const statusText = document.getElementById("statusText");

function formatTime(sec) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  if (m <= 0) return `0:${String(s).padStart(2, "0")}`;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function formatDuration(sec) {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m}分${String(s).padStart(2, "0")}秒`;
}

function stars(score, outOf) {
  const full = "★".repeat(score);
  const empty = "☆".repeat(Math.max(0, outOf - score));
  return `<span class="stars">${full}${empty}</span>`;
}

function pctBar(label, pct, className) {
  return `
    <div class="bar-row">
      <div class="bar-label">${label}</div>
      <div class="bar-track">
        <div class="bar-fill ${className}" style="width:${pct}%;"></div>
      </div>
      <div class="bar-pct">${pct.toFixed(1)}%</div>
    </div>
  `;
}

function tagBadges(tags) {
  if (!tags || !tags.length) return "";
  return tags.map(t => `<span class="tag">${t}</span>`).join("");
}

uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  if (!fileInput.files.length) {
    alert("ファイルを選択してください");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  statusText.innerText = "アップロード中...";
  resultBox.innerHTML = "";

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      body: formData
    });

    if (!response.ok) throw new Error("サーバーエラー");

    const data = await response.json();
    statusText.innerText = "分析完了！";

    const s = data.summary;

    // スコア表
    const scoreRows = [
      ["共感スコア", data.scores.empathy],
      ["承認スコア", data.scores.approval],
      ["問いスコア", data.scores.question],
      ["沈黙の活用", data.scores.silence],
      ["傾聴スコア", data.scores.listening],
    ].map(([label, v]) => `
      <div class="score-row">
        <div class="score-label">${label}</div>
        <div class="score-stars">${stars(v.score, v.out_of)} <span class="evidence">(${v.evidence})</span></div>
      </div>
    `).join("");

    // タイムライン
    const timelineHtml = data.timeline.map(row => `
      <div class="tl-row">
        <div class="tl-time">${formatTime(row.start)}</div>
        <div class="tl-speaker ${row.speaker}">${row.speaker === "coach" ? "コーチ" : "受講生"}</div>
        <div class="tl-text">
          <div>${row.text}</div>
          <div class="tl-tags">${tagBadges(row.tags)}</div>
        </div>
        <div class="tl-dur">${(row.end - row.start).toFixed(1)}s</div>
      </div>
    `).join("");

    resultBox.innerHTML = `
      <div class="section">
        <div class="title">分析サマリー</div>
        <div class="muted">${data.file_name}（${formatDuration(data.duration_sec)}）</div>
        <div class="cards">
          <div class="card">
            <div class="card-title">最長連続発話</div>
            <div class="card-big">${s.longest_monologue_sec.toFixed(1)}秒</div>
          </div>
          <div class="card">
            <div class="card-title">発話回数（コーチ）</div>
            <div class="card-big">${s.coach_turns}回</div>
            <div class="muted">受講生: ${s.student_turns}回</div>
          </div>
          <div class="card">
            <div class="card-title">沈黙（3秒以上）</div>
            <div class="card-big">${s.silence_count}回</div>
            <div class="muted">平均 ${s.silence_avg_sec.toFixed(1)}秒</div>
          </div>
        </div>
      </div>

      <div class="section">
        <div class="title">発話割合</div>
        ${pctBar("コーチ", s.coach_ratio, "coach")}
        ${pctBar("受講生", s.student_ratio, "student")}
      </div>

      <div class="section">
        <div class="title">スキルスコア <span class="muted">（右の数字は根拠カウント）</span></div>
        <div class="scores">${scoreRows}</div>
      </div>

      <div class="section">
        <div class="title">改善アクション</div>
        <ul>
          ${data.actions.map(a => `<li>${a}</li>`).join("")}
        </ul>
      </div>

      <div class="section">
        <div class="title">発話タイムライン</div>
        <div class="timeline">
          ${timelineHtml}
        </div>
      </div>
    `;
  } catch (error) {
    statusText.innerText = "エラーが発生しました";
    console.error(error);
  }
});

        const data = await response.json();

        statusText.innerText = "分析完了！";

        resultBox.innerHTML = `
            <h3>結果</h3>
            <p>コーチ発話割合: ${data.coach_ratio}</p>
            <p>受講生発話割合: ${data.student_ratio}</p>
            <p>最長連続発話: ${data.longest_speech}</p>
            <p>フィードバック: ${data.feedback}</p>
        `;
    } catch (error) {
        statusText.innerText = "エラーが発生しました";
        console.error(error);
    }
});
