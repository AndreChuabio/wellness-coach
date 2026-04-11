const LOCAL_API_BASE = "http://localhost:8000";
const PRODUCTION_API_BASE = "https://wellness-coach.up.railway.app";
const API_BASE = window.location.hostname.includes("railway.app")
  ? PRODUCTION_API_BASE
  : LOCAL_API_BASE;

const CATEGORY_ICONS = {
  breathing: "🫁",
  meditation: "🧘",
  movement: "🏃",
  sleep: "😴",
  recovery: "💙",
  mindfulness: "🌿",
  default: "✨"
};

// ── Init ──────────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("dateDisplay").textContent = new Date().toLocaleDateString(
    "en-US", { weekday: "long", month: "long", day: "numeric" }
  );
  loadSidebar();
});

async function loadSidebar() {
  try {
    const [healthRes, calRes] = await Promise.all([
      fetch(`${API_BASE}/health-data`),
      fetch(`${API_BASE}/calendar`)
    ]);
    const health = await healthRes.json();
    const cal = await calRes.json();
    renderHealth(health);
    renderCalendar(cal.events);
  } catch (e) {
    console.error("Failed to load sidebar data:", e);
    showToast("Could not connect to backend — is it running?", "error");
  }
}

// ── Health Stats ──────────────────────────────────────────────────────────────

function renderHealth(health) {
  const score = (val, max = 100) => {
    const pct = (val / max) * 100;
    const color = pct >= 80 ? "good" : pct >= 60 ? "ok" : "low";
    return `<span class="score ${color}">${val}</span>`;
  };
  document.getElementById("sleepScore").innerHTML = score(health.sleep_score) + "<small>/100</small>";
  document.getElementById("hrv").innerHTML = `${health.hrv_ms}<small>ms</small>`;
  document.getElementById("recovery").innerHTML = score(health.recovery_score) + "<small>/100</small>";
}

// ── Calendar ──────────────────────────────────────────────────────────────────

function renderCalendar(events) {
  const list = document.getElementById("eventList");
  if (!events || events.length === 0) {
    list.innerHTML = "<li class='loading-text'>No events today 🎉</li>";
    return;
  }
  list.innerHTML = events.map(e => `
    <li class="event-item ${e.type === 'high_stakes' ? 'high-stakes' : ''}">
      <span class="event-time">${e.time}</span>
      <span class="event-title">${e.title}</span>
      ${e.type === "high_stakes" ? '<span class="badge">⚡ Key</span>' : ""}
    </li>
  `).join("");
}

// ── Session ───────────────────────────────────────────────────────────────────

async function startSession() {
  const preSession = document.getElementById("preSession");
  const loading = document.getElementById("loadingSession");
  const frame = document.getElementById("tavusFrame");
  const btn = document.getElementById("startBtn");

  btn.disabled = true;
  preSession.style.display = "none";
  loading.style.display = "flex";

  try {
    const res = await fetch(`${API_BASE}/start-session`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_name: "Andre" })
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    const data = await res.json();

    loading.style.display = "none";

    // Show Tavus iframe
    if (data.conversation_url && !data.conversation_url.includes("mock")) {
      frame.src = data.conversation_url;
      frame.style.display = "block";
      document.getElementById("micHint").style.display = "block";
    } else {
      // Mock mode — show greeting
      loading.style.display = "none";
      preSession.style.display = "flex";
      preSession.querySelector(".avatar-subtitle").textContent = data.greeting || "Ready to chat!";
      preSession.querySelector(".avatar-emoji").textContent = "👋";
      preSession.querySelector(".avatar-name").textContent = "Healthmaxx says:";
      btn.style.display = "none";
      showToast("Mock mode — set Tavus API keys to enable live video", "info");
    }

    // Show recommendations
    if (data.recommendations?.length) {
      renderRecommendations(data.recommendations);
      document.getElementById("recommendations").style.display = "block";
    }

  } catch (e) {
    loading.style.display = "none";
    preSession.style.display = "flex";
    btn.disabled = false;
    console.error(e);
    showToast(`Error: ${e.message}`, "error");
  }
}

// ── Recommendations ───────────────────────────────────────────────────────────

function renderRecommendations(recs) {
  const container = document.getElementById("recCards");
  container.innerHTML = recs.map((r, i) => `
    <div class="rec-card priority-${r.priority}">
      <div class="rec-header">
        <span class="rec-icon">${CATEGORY_ICONS[r.category] || CATEGORY_ICONS.default}</span>
        <span class="rec-title">${r.title}</span>
        <span class="rec-duration">${r.duration_min} min</span>
      </div>
      <p class="rec-detail">${r.detail}</p>
    </div>
  `).join("");
}

// ── Toast ─────────────────────────────────────────────────────────────────────

function showToast(msg, type = "info") {
  const toast = document.getElementById("toast");
  toast.textContent = msg;
  toast.className = `toast show ${type}`;
  setTimeout(() => toast.classList.remove("show"), 4000);
}
