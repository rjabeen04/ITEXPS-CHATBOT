const chatBox    = document.getElementById('chat-box');
const queryInput = document.getElementById('q');
const sendBtn    = document.getElementById('send-btn');
const chatCenter = document.getElementById('chat-center');
const reopenBtn  = document.getElementById('reopen-btn');
const API_URL    = "https://0sobzbid25.execute-api.us-east-1.amazonaws.com/ask";

document.getElementById('close-btn').addEventListener('click', () => {
    chatCenter.style.display = 'none';
});

reopenBtn.addEventListener('click', () => {
    const isOpen = chatCenter.style.display !== 'none';
    chatCenter.style.display = isOpen ? 'none' : 'flex';
});

async function sendMessage() {
    const text = queryInput.value.trim();
    if (!text) return;
    addMessage(text, 'user');
    queryInput.value = '';
    sendBtn.disabled = true;
    try {
        const res = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: text })
        });
        const data = await res.json();
        addMessage(data.answer || "Sorry, I couldn't process that.", 'bot');
    } catch {
        addMessage("Connection error. Please try again later.", 'bot');
    } finally {
        sendBtn.disabled = false;
    }
}

function addMessage(text, sender) {
    const wrapper = document.createElement('div');
    wrapper.className = `msg-${sender}`;
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.innerHTML = text
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
    wrapper.appendChild(bubble);
    chatBox.appendChild(wrapper);
    chatBox.scrollTop = chatBox.scrollHeight;
}

sendBtn.addEventListener('click', sendMessage);
queryInput.addEventListener('keypress', e => { if (e.key === 'Enter') sendMessage(); });
