const bot = document.getElementById("aiBotWidget");
const chatBox = document.getElementById("chatBox");
const closeChat = document.getElementById("closeChat");
const sendBtn = document.getElementById("sendChat");
const input = document.getElementById("chatInput");
const messages = document.getElementById("chatMessages");

// Show chat box
bot.addEventListener("click", () => {
  chatBox.style.display = "block";
  addBotMsg("Hi! How can I help you today?");
});

// Close chat
closeChat.addEventListener("click", () => {
  chatBox.style.display = "none";
});

// Send message
sendBtn.addEventListener("click", sendChat);
input.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendChat();
});

function sendChat() {
  const text = input.value.trim();
  if (!text) return;

  addUserMsg(text);
  input.value = "";

  fetch("/api/chat", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ message: text })
  })
  .then(res => res.json())
  .then(data => addBotMsg(data.reply))
  .catch(() => addBotMsg("Server error, try again later."));
}

function addUserMsg(text) {
  messages.innerHTML += `<div class="chat-message user">${text}</div>`;
  messages.scrollTop = messages.scrollHeight;
}

function addBotMsg(text) {
  messages.innerHTML += `<div class="chat-message bot">${text}</div>`;
  messages.scrollTop = messages.scrollHeight;
}
