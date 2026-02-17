const uploadForm = document.getElementById("uploadForm");
const fileInput = document.getElementById("fileInput");
const resultBox = document.getElementById("result");
const statusBox = document.getElementById("status");

uploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const file = fileInput.files[0];
    if (!file) {
        alert("ファイルを選択してください");
        return;
    }

    statusBox.innerText = "アップロード中...";
    resultBox.innerHTML = "";

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch(
            "https://zoom-analysis-app.onrender.com/analyze",
            {
                method: "POST",
                body: formData,
            }
        );

        if (!response.ok) {
            throw new Error("サーバーエラー");
        }

        const data = await response.json();

        statusBox.innerText = "分析完了";

        resultBox.innerHTML = `
      <h3>分析結果</h3>
      <p><strong>コーチ話者割合:</strong> ${data.coach_ratio}%</p>
      <p><strong>受講生話者割合:</strong> ${data.student_ratio}%</p>
      <p><strong>最長連続発話:</strong> ${data.longest_speech} 秒</p>
    `;
    } catch (error) {
        statusBox.innerText = "エラーが発生しました";
        resultBox.innerHTML = `<p style="color:red;">${error.message}</p>`;
    }
});