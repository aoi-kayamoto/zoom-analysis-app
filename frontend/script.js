async function uploadFile() {
    const fileInput = document.getElementById("fileInput");
    const file = fileInput.files[0];
    if (!file) {
        alert("ファイルを選択してください");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    // reset UI
    document.getElementById("uploadSection").style.display = "none";
    document.getElementById("loading").classList.remove("hidden");
    document.getElementById("statusMessage").innerText = "Uploading...";
    document.getElementById("progressBar").style.width = "0%";
    document.getElementById("progressText").innerText = "0%";

    try {
        // 1. Upload file and start job
        const response = await fetch("/upload", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error("Upload failed");
        }

        const data = await response.json();
        const jobId = data.job_id;

        // 2. Start polling
        pollStatus(jobId);

    } catch (error) {
        console.error("Error:", error);
        document.getElementById("loading").classList.add("hidden");
        document.getElementById("uploadSection").style.display = "block";
        alert("エラーが発生しました: " + error.message);
    }
}

function pollStatus(jobId) {
    const intervalId = setInterval(async () => {
        try {
            const response = await fetch(`/status/${jobId}`);
            if (!response.ok) throw new Error("Status check failed");

            const statusData = await response.json();

            // Update Progress
            const progress = statusData.progress;
            document.getElementById("progressBar").style.width = `${progress}%`;
            document.getElementById("progressText").innerText = `${progress}% - ${statusData.message}`;

            if (statusData.status === "completed") {
                clearInterval(intervalId);
                fetchResult(jobId);
            } else if (statusData.status === "failed") {
                clearInterval(intervalId);
                throw new Error(statusData.message);
            }

        } catch (error) {
            clearInterval(intervalId);
            console.error("Polling Error:", error);
            document.getElementById("loading").classList.add("hidden");
            document.getElementById("uploadSection").style.display = "block";
            alert("処理中にエラーが発生しました: " + error.message);
        }
    }, 2000); // Check every 2 seconds
}

async function fetchResult(jobId) {
    try {
        const response = await fetch(`/result/${jobId}`);
        if (!response.ok) throw new Error("Result fetch failed");

        const data = await response.json();
        renderDashboard(data);

        // Hide loading
        document.getElementById("loading").classList.add("hidden");

    } catch (error) {
        console.error("Result Error:", error);
        alert("結果の取得に失敗しました");
    }
}

function renderDashboard(data) {
    document.getElementById("dashboard").style.display = "grid";

    // Data Extraction (Assuming SPEAKER_00 is Coach, SPEAKER_01 is Student for MVP)
    const coach = data.speaker_stats.SPEAKER_00;
    const student = data.speaker_stats.SPEAKER_01;

    // 1. Speaker Ratio Bar
    const ratioBar = document.getElementById("ratioBar");
    ratioBar.innerHTML = `
        <div class="ratio-segment speaker-00" style="width: ${coach.percentage}%">${coach.percentage}%</div>
        <div class="ratio-segment speaker-01" style="width: ${student.percentage}%">${student.percentage}%</div>
    `;
    document.getElementById("coachPct").innerText = coach.percentage;
    document.getElementById("studentPct").innerText = student.percentage;

    // 2. Longest Speech Alert
    const longestSpeechVal = document.getElementById("longestSpeechVal");
    longestSpeechVal.innerText = `${coach.longest_single_speech}秒`;
    if (coach.longest_single_speech > 30) {
        longestSpeechVal.classList.add("alert-red");
    } else {
        longestSpeechVal.classList.remove("alert-red");
    }

    // 3. Scoring (Stars)
    // Simple logic: 1 mention = 1 star, max 5 stars
    function getStars(count) {
        const stars = Math.min(count, 5);
        return "★".repeat(stars) + "☆".repeat(5 - stars) + ` (${count})`;
    }

    document.getElementById("empathyStars").innerText = getStars(coach.empathy_count);
    document.getElementById("approvalStars").innerText = getStars(coach.approval_count);
    document.getElementById("questionStars").innerText = getStars(coach.question_count);

    // 4. Transcript
    document.getElementById("transcript").innerText = data.transcript;
}
