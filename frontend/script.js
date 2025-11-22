const chatBox = document.getElementById('chat-box');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const pdfForm = document.getElementById('pdf-form');
const pdfInput = document.getElementById('pdf-input');
const pdfStatus = document.getElementById('pdf-status');
const pdfFilename = document.getElementById('pdf-filename');
const usePdfCheckbox = document.getElementById('use-pdf');
const agentContextStatus = document.getElementById('agent-context-status');

// Update filename display when file is selected
pdfInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        pdfFilename.textContent = e.target.files[0].name;
    } else {
        pdfFilename.textContent = 'No file chosen';
    }
});

function appendMessage(text, sender, sources = []) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}`;

    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'avatar';
    avatarDiv.innerHTML = sender === 'bot' ? '<i class="fa-solid fa-robot"></i>' : '<i class="fa-solid fa-user"></i>';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'content';

    // Convert newlines to <br> for basic formatting
    const formattedText = text.replace(/\n/g, '<br>');
    contentDiv.innerHTML = formattedText;

    // Add sources if available
    if (sources && sources.length > 0) {
        const uniqueSources = [...new Set(sources.map(c => {
            if (c.startsWith('PDF')) return { name: 'PDF Context', icon: 'fa-file-pdf' };
            if (c.startsWith('Wikipedia')) return { name: 'Wikipedia', icon: 'fa-brands fa-wikipedia-w' };
            if (c.startsWith('DuckDuckGo')) return { name: 'DuckDuckGo', icon: 'fa-globe' };
            if (c.startsWith('arXiv')) return { name: 'arXiv', icon: 'fa-graduation-cap' };
            if (c.startsWith('ChatGPT')) return { name: 'Groq AI', icon: 'fa-solid fa-bolt' };
            return { name: 'Other', icon: 'fa-info-circle' };
        }).map(JSON.stringify))].map(JSON.parse);

        const sourcesContainer = document.createElement('div');
        sourcesContainer.className = 'sources-container';

        const sourcesTitle = document.createElement('div');
        sourcesTitle.className = 'sources-title';
        sourcesTitle.innerHTML = '<i class="fa-solid fa-link"></i> Sources Used:';
        sourcesContainer.appendChild(sourcesTitle);

        const badgesDiv = document.createElement('div');
        badgesDiv.className = 'source-badges';

        uniqueSources.forEach(source => {
            const badge = document.createElement('div');
            badge.className = 'source-badge';
            badge.innerHTML = `<i class="${source.icon}"></i> ${source.name}`;
            badgesDiv.appendChild(badge);
        });

        sourcesContainer.appendChild(badgesDiv);
        contentDiv.appendChild(sourcesContainer);
    }

    msgDiv.appendChild(avatarDiv);
    msgDiv.appendChild(contentDiv);

    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

pdfForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const file = pdfInput.files[0];
    if (!file) {
        pdfStatus.textContent = 'Please select a PDF file.';
        return;
    }

    const btn = pdfForm.querySelector('button');
    const originalText = btn.textContent;
    btn.textContent = 'Uploading...';
    btn.disabled = true;

    pdfStatus.textContent = '';

    const formData = new FormData();
    formData.append('pdf', file);

    try {
        const res = await fetch('http://localhost:5000/upload_pdf', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();

        if (data.error) {
            pdfStatus.textContent = 'Error: ' + data.error;
            pdfStatus.style.color = '#ef4444';
        } else {
            pdfStatus.textContent = 'PDF uploaded successfully!';
            pdfStatus.style.color = '#10b981';
        }
    } catch (err) {
        pdfStatus.textContent = 'Error uploading PDF.';
        pdfStatus.style.color = '#ef4444';
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
});

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = userInput.value.trim();
    if (!message) return;

    appendMessage(message, 'user');
    userInput.value = '';

    // Show typing indicator
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot typing';
    typingDiv.innerHTML = `
        <div class="avatar"><i class="fa-solid fa-robot"></i></div>
        <div class="content">Thinking...</div>
    `;
    chatBox.appendChild(typingDiv);
    chatBox.scrollTop = chatBox.scrollHeight;

    if (agentContextStatus) agentContextStatus.textContent = '';

    try {
        const res = await fetch('http://localhost:5000/agent', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message,
                query: message
            })
        });
        const data = await res.json();

        // Remove typing indicator
        chatBox.removeChild(typingDiv);

        appendMessage(data.reply, 'bot', data.agent_context);

    } catch (err) {
        if (chatBox.contains(typingDiv)) chatBox.removeChild(typingDiv);
        appendMessage('Error: Could not get response. Make sure the backend is running.', 'bot');
    }
});
