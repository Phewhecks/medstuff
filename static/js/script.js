// Dark Mode Toggle
const darkModeToggle = document.getElementById('darkModeToggle');
const body = document.body;

function updateToggleIcon(isDark) {
  // Use moon icon ☾ for dark mode, sun icon ☀︎ for light mode
  darkModeToggle.innerHTML = isDark ? '<i class="fas fa-moon"></i>' : '<i class="fas fa-sun"></i>';
}

function setDarkMode(enabled) {
  if (enabled) {
    body.classList.add('dark');
    localStorage.setItem('darkMode', 'enabled');
    updateToggleIcon(true);
  } else {
    body.classList.remove('dark');
    localStorage.setItem('darkMode', 'disabled');
    updateToggleIcon(false);
  }
}

(function initDarkMode() {
  const saved = localStorage.getItem('darkMode');
  if (saved === 'enabled') {
    setDarkMode(true);
  } else if (saved === 'disabled') {
    setDarkMode(false);
  } else {
    // No saved preference, use system preference
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    setDarkMode(prefersDark);
  }
})();

darkModeToggle.addEventListener('click', () => {
  const isDark = body.classList.contains('dark');
  setDarkMode(!isDark);
});





// chatbot fix

const chatbotToggle = document.querySelector('.chatbot-toggle');
const chatWindow = document.querySelector('.chat-window');
const chatCloseBtn = document.querySelector('.chat-header span[role="button"]') || document.querySelector('.chat-header span');
const chatInput = chatWindow.querySelector('input[type="text"]');
const chatBody = chatWindow.querySelector('.chat-body');

let welcomeShown = false;

chatbotToggle.addEventListener('click', () => {
  chatWindow.classList.toggle('active');
  if (chatWindow.classList.contains('active')) {
    chatInput.focus();
    if (!welcomeShown) {
      appendBotMessage("Hello, Please list your symptoms so i can provide suggestions.");
      welcomeShown = true;
    }
  }
});

chatCloseBtn.addEventListener('click', () => {
  chatWindow.classList.remove('active');
});

// user input to flask backend
chatInput.addEventListener('keypress', async (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    const msg = chatInput.value.trim();
    if (msg) {
      appendMessage('You', msg);
      chatInput.value = '';
 
      try {
        const response = await fetch('http://127.0.0.1:5000/chatbot', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message: msg }),
        });

        if (!response.ok) {
          throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();

        const recommendations = data.recommendations || {};
        const reply = `
<b>Diagnosis: </b> ${data.diagnosis}<br>
<b>Diet: I would suggest, </b> ${recommendations.diet || 'N/A'}<br>
<b>Exercise: </b> ${recommendations.exercise || 'N/A'}<br>
<b>Tips: I also advise you to, </b> ${recommendations.tips || 'N/A'}<br>
${recommendations.note || ''}
        `.trim();

        typeBotMessage(reply);
      } catch (error) {
        appendBotMessage("We arent able to provide any suggestions at the moment. Sorry for the inconvenience.");
        console.error("Fetch error:", error);
      }
    }
  }
});

function appendMessage(sender, message) {
  const p = document.createElement('p');
  p.innerHTML = `<strong>${sender}:</strong> ${message}`;
  chatBody.appendChild(p);
  chatBody.scrollTop = chatBody.scrollHeight;
}

function appendBotMessage(message) {
  const p = document.createElement('p');
  p.innerHTML = `<strong>Bot:</strong> ${message}`;
  chatBody.appendChild(p);
  chatBody.scrollTop = chatBody.scrollHeight;
}

// chatgpt type typing effect
function typeBotMessage(htmlString) {
  const container = document.createElement('p');
  container.innerHTML = `<strong>Bot: </strong> <span class="bot-message"></span>`;
  const messageSpan = container.querySelector('.bot-message');
  chatBody.appendChild(container);
  chatBody.scrollTop = chatBody.scrollHeight;

  let i = 0;
  const typingSpeed = 10; 
  let isTag = false;
  let tag = '';

  function type() {
    const char = htmlString.charAt(i);
    //check if we in html tag to prevent random sequence of characters copied from chatgpt
    if (char === '<') {
      isTag = true;
      tag = '<';
    } else if (char === '>') {
      isTag = false;
      tag += '>';
      messageSpan.innerHTML += tag; 
      tag = '';
    } else if (isTag) {
      tag += char; 
    } else {
      messageSpan.innerHTML += char; 
    }

    if (i < htmlString.length - 1) {
      i++;
      setTimeout(type, typingSpeed);
    }
    chatBody.scrollTop = chatBody.scrollHeight; // Ensure scrolls to the bottom
  }

  type(); 
}

