const uploadForm = document.getElementById("uploadForm");
const fileInput = document.getElementById("fileInput");
const resultBox = document.getElementById("resultBox");
const statusText = document.getElementById("statusText");

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

        if (!response.ok) {
            throw new Error("サーバーエラー");
        }

        const data = await response.json();

        statusText.innerText = "分析完了！";

        resultBox.innerHTML = `
            <h3>📝 文字起こし</h3>
            <p>${data.text}</p>
        `;

    } catch (error) {
        console.error(error);
        statusText.innerText = "";
        resultBox.innerHTML = `
            <div style="color:red;">
                ❌ サーバーに接続できません。Renderが起動しているか確認してください。
            </div>
        `;
    }
});
