const fileInput = document.getElementById("fileInput");
const uploadBtn = document.getElementById("uploadBtn");
const resultBox = document.getElementById("resultBox");

uploadBtn.addEventListener("click", async () => {
  const file = fileInput.files[0];
  if (!file) {
    alert("ファイルを選択してください");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/analyze", {   // ← ここ重要
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error("API Error");
    }

    const data = await response.json();

    resultBox.innerHTML = `
      <p>コーチ割合: ${data.coach_ratio}%</p>
      <p>受講生割合: ${data.student_ratio}%</p>
      <p>最長発話時間: ${data.longest_speech}秒</p>
    `;
  } catch (error) {
    resultBox.innerHTML = `<p style="color:red;">エラーが発生しました</p>`;
  }
});