document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('queryForm');
    const outputDiv = document.getElementById('output');
    const responseText = document.getElementById('responseText');
    const submitBtn = document.getElementById('submitBtn');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        submitBtn.disabled = true;
        submitBtn.textContent = 'Processing...';
        outputDiv.style.display = 'none';

        const model = document.getElementById('model').value;
        const input = document.getElementById('input').value.trim();

        if (!input) {
            responseText.innerHTML = "<p>Please enter a valid query.</p>";
            outputDiv.style.display = 'block';
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit';
            return;
        }

        try {
            responseText.innerHTML = "<p><em>Please wait, generating response...</em></p>";
            outputDiv.style.display = 'block';

            const response = await fetch('/api/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ model, input })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // ✅ Format response using markdown
            const latestResponse = marked.parse(data.output || "No output received.");

            // ✅ Show full history (last 5 messages)
            if (data.history && Array.isArray(data.history)) {
                const historyHtml = data.history.map(
                    (turn, idx) => `
                        <div class="chat-turn">
                            <p><strong>You:</strong> ${turn.input}</p>
                            <p><strong>AI:</strong> ${marked.parse(turn.output)}</p>
                            <hr>
                        </div>`
                ).join('');
                responseText.innerHTML = historyHtml;
            } else {
                responseText.innerHTML = latestResponse;
            }

            outputDiv.scrollIntoView({ behavior: 'smooth' });

        } catch (error) {
            console.error('Error:', error);
            responseText.innerHTML = `<p style="color:red;">Error: ${error.message}</p>`;
            outputDiv.style.display = 'block';
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit';
        }
    });
});
