document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.querySelector('.chatbot-toggle');
    const windowEl = document.querySelector('.chatbot-window');
    const closeBtn = document.querySelector('.chatbot-close');
    const input = document.querySelector('.chatbot-input');
    const sendBtn = document.querySelector('.chatbot-send');
    const messages = document.querySelector('.chatbot-messages');

    if (!toggle || !windowEl) return;

    // Load marked.js for Markdown rendering (CDN)
    if (!window.marked) {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
        document.head.appendChild(script);
    }

    toggle.addEventListener('click', () => {
        windowEl.classList.toggle('active');
        if (windowEl.classList.contains('active')) {
            input.focus();
            // Show welcome message if empty
            if (messages.children.length === 0) {
                addMessage("👋 Hi! I'm **TravelMate AI**. Ask me about any Indian destination, travel tips, or itinerary suggestions!", 'bot');
            }
        }
    });

    closeBtn.addEventListener('click', () => {
        windowEl.classList.remove('active');
    });

    const addMessage = (text, type) => {
        const msg = document.createElement('div');
        msg.className = `message ${type}`;

        if (type === 'bot' && window.marked) {
            // Render Markdown for bot responses
            msg.innerHTML = marked.parse(text);
        } else if (type === 'bot') {
            // Fallback: basic formatting if marked.js not loaded
            msg.innerHTML = text
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/## (.*?)(\n|$)/g, '<h4>$1</h4>')
                .replace(/- (.*?)(\n|$)/g, '<li>$1</li>')
                .replace(/\n/g, '<br>');
        } else {
            msg.textContent = text;
        }

        messages.appendChild(msg);
        messages.scrollTop = messages.scrollHeight;
    };

    const addTypingIndicator = () => {
        const typing = document.createElement('div');
        typing.className = 'message bot typing-indicator';
        typing.id = 'typing-indicator';
        typing.innerHTML = '<span></span><span></span><span></span>';
        messages.appendChild(typing);
        messages.scrollTop = messages.scrollHeight;
    };

    const removeTypingIndicator = () => {
        const typing = document.getElementById('typing-indicator');
        if (typing) typing.remove();
    };

    const handleSend = async () => {
        const text = input.value.trim();
        if (!text) return;

        addMessage(text, 'user');
        input.value = '';
        input.disabled = true;
        sendBtn.disabled = true;

        addTypingIndicator();

        try {
            const response = await fetch('/ai_chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ msg: text })
            });
            const data = await response.json();
            removeTypingIndicator();

            if (data.reply) {
                addMessage(data.reply, 'bot');
            } else {
                addMessage('⚠️ No response received. Please try again.', 'bot');
            }
        } catch (error) {
            removeTypingIndicator();
            addMessage('Sorry, I am having trouble connecting right now. Please try again! 🔄', 'bot');
        } finally {
            input.disabled = false;
            sendBtn.disabled = false;
            input.focus();
        }
    };

    sendBtn.addEventListener('click', handleSend);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSend();
    });
});
