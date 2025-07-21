document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("queryForm");
    const inputBox = document.getElementById("input");
    const responseText = document.getElementById("responseText");
    const chatHistoryList = document.getElementById("chatHistoryList");
    const submitBtn = document.getElementById("submitBtn");
    const micBtn = document.getElementById("startVoiceBtn");

    let recognizing = false;
    let recognition;

    // Set up voice recognition if supported
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.lang = "en-US";
        recognition.interimResults = false;

        micBtn.addEventListener("click", () => {
            if (!recognizing) {
                recognition.start();
                micBtn.textContent = "🎙️ Listening...";
                recognizing = true;
            } else {
                recognition.stop();
                micBtn.textContent = "🎤 Speak";
                recognizing = false;
            }
        });

        recognition.onresult = function (event) {
            const transcript = event.results[0][0].transcript;
            inputBox.value += (inputBox.value ? " " : "") + transcript;
        };

        recognition.onerror = function (event) {
            console.error("Speech recognition error", event.error);
            micBtn.textContent = "🎤 Speak";
        };

        recognition.onend = function () {
            micBtn.textContent = "🎤 Speak";
            recognizing = false;
        };
    } else {
        micBtn.disabled = true;
        micBtn.textContent = "Voice not supported";
    }

    // Submit form logic
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        submitBtn.disabled = true;
        responseText.innerHTML = "Processing...";
        document.getElementById("output").style.display = "block";

        try {
            const response = await fetch("/api/process", {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            if (data.error) {
                responseText.innerText = data.error;
            } else {
                responseText.innerHTML = marked.parse(data.output);

                // Update chat history
                chatHistoryList.innerHTML = "";
                data.chat_history.forEach(item => {
                    const el = document.createElement("div");
                    el.className = "history-item";
                    el.innerHTML = `<p><strong>You:</strong> ${item.input}</p><p><strong>AI:</strong> ${item.output}</p>`;
                    chatHistoryList.appendChild(el);
                });
            }
        } catch (err) {
            responseText.innerText = "Error occurred. Please try again.";
        }

        submitBtn.disabled = false;
    });
});
