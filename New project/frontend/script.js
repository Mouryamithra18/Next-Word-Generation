const input = document.getElementById("sentence-input");
const suggestions = document.getElementById("suggestions");
const historyList = document.getElementById("history-list");
const statusText = document.getElementById("status-text");
const tokenCount = document.getElementById("token-count");
const modeLabel = document.getElementById("mode-label");
const healthLabel = document.getElementById("health-label");
const clearBtn = document.getElementById("clear-btn");
const copyBtn = document.getElementById("copy-btn");
const reloadBtn = document.getElementById("reload-btn");
const topNSelect = document.getElementById("top-n-select");

const state = {
  debounceTimer: null,
  selectedWords: [],
};

async function fetchHealth() {
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    modeLabel.textContent = data.mode === "lstm" ? "Trained LSTM" : "Fallback Predictor";
    healthLabel.textContent = data.status_message;
  } catch (error) {
    modeLabel.textContent = "Unavailable";
    healthLabel.textContent = "Could not reach the backend.";
    console.error("[health]", error);
  }
}

function updateWordCount() {
  const count = input.value.trim() ? input.value.trim().split(/\s+/).length : 0;
  tokenCount.textContent = `${count} ${count === 1 ? "word" : "words"}`;
}

function setStatus(message) {
  statusText.textContent = message;
}

function renderHistory() {
  if (state.selectedWords.length === 0) {
    historyList.innerHTML = '<li class="history-empty">No words selected yet.</li>';
    return;
  }

  historyList.innerHTML = state.selectedWords
    .slice(-8)
    .reverse()
    .map((word) => `<li>${escapeHtml(word)}</li>`)
    .join("");
}

function renderSuggestions(items) {
  if (!items || items.length === 0) {
    suggestions.classList.add("empty");
    suggestions.innerHTML = '<p class="empty-state">No suggestions available for that input yet.</p>';
    return;
  }

  suggestions.classList.remove("empty");
  suggestions.innerHTML = items
    .map((item) => {
      const confidence = Math.max(1, Math.round(Number(item.score || 0) * 100));
      return `
        <button class="suggestion-btn" type="button" data-word="${escapeHtml(item.word)}">
          <span>
            <span class="suggestion-word">${escapeHtml(item.word)}</span>
            <span class="suggestion-meta">
              <span>${item.source === "lstm" ? "Neural prediction" : "Fallback prediction"}</span>
            </span>
          </span>
          <span class="confidence-pill">${confidence}% match</span>
        </button>
      `;
    })
    .join("");

  suggestions.querySelectorAll(".suggestion-btn").forEach((button) => {
    button.addEventListener("click", () => applySuggestion(button.dataset.word));
  });
}

async function fetchPredictions() {
  const text = input.value.trim();
  updateWordCount();

  if (!text) {
    suggestions.classList.add("empty");
    suggestions.innerHTML = '<p class="empty-state">Suggestions will appear here.</p>';
    setStatus("Type a phrase to see predictions.");
    return;
  }

  setStatus("Finding the best next words...");

  try {
    const response = await fetch("/api/predict", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text, top_n: Number(topNSelect.value) }),
    });

    const data = await response.json();
    renderSuggestions(data.predictions || []);
    modeLabel.textContent = data.mode === "lstm" ? "Trained LSTM" : "Fallback Predictor";
    setStatus(data.message || "Suggestions updated.");
  } catch (error) {
    suggestions.classList.add("empty");
    suggestions.innerHTML = '<p class="empty-state">The prediction API is not responding.</p>';
    setStatus("Could not reach the prediction service.");
    console.error("[predict]", error);
  }
}

function applySuggestion(word) {
  const base = input.value.trim();
  input.value = base ? `${base} ${word}` : word;
  state.selectedWords.push(word);
  renderHistory();
  updateWordCount();
  fetchPredictions();
  input.focus();
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

input.addEventListener("input", () => {
  clearTimeout(state.debounceTimer);
  state.debounceTimer = setTimeout(fetchPredictions, 280);
  updateWordCount();
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    clearTimeout(state.debounceTimer);
    fetchPredictions();
  }
});

clearBtn.addEventListener("click", () => {
  input.value = "";
  state.selectedWords = [];
  renderHistory();
  updateWordCount();
  suggestions.classList.add("empty");
  suggestions.innerHTML = '<p class="empty-state">Suggestions will appear here.</p>';
  setStatus("Type a phrase to see predictions.");
  input.focus();
});

copyBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(input.value);
    setStatus("Sentence copied to clipboard.");
  } catch (error) {
    setStatus("Could not copy the sentence.");
  }
});

reloadBtn.addEventListener("click", async () => {
  try {
    setStatus("Reloading model status...");
    await fetch("/api/reload", { method: "POST" });
    await fetchHealth();
    await fetchPredictions();
  } catch (error) {
    setStatus("Could not reload the model.");
  }
});

document.querySelectorAll(".prompt-chip").forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.dataset.prompt;
    updateWordCount();
    fetchPredictions();
    input.focus();
  });
});

fetchHealth();
renderHistory();
updateWordCount();
