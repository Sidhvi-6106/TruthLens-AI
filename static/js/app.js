// State Store
let token = localStorage.getItem("truthlens_token") || null;
let currentUser = null;
let articles = [];
let savedArticles = [];
let categories = [];
let moderationQueue = [];
let auditLogs = [];

// Fallbacks
const categoriesFallback = [
  "Technology", "Politics", "Sports", "Finance", "Business", "Entertainment", "Health", "Science", "International"
];

const rumors = [
  ["Synthetic speech clip claims new banking rules", "Trending in 6 regions", "Misleading", "one"],
  ["Edited storm footage reused from 2022", "High share velocity", "Fake", "two"],
  ["Celebrity deepfake endorses investment app", "Detected across video platforms", "Fake", "three"],
  ["Local school closure message lacks source", "Community reports rising", "Unverified", "four"]
];

// Utility functions
function showToast(message, type = "success") {
  const container = document.getElementById("toastContainer");
  if (!container) return;
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${type === "success" ? "✅" : type === "error" ? "❌" : "⚠️"}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = "slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) reverse";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function scoreLabel(score) {
  if (score >= 95) return "Verified";
  if (score >= 75) return "Reliable";
  if (score >= 50) return "Needs Verification";
  return "Potentially Misleading";
}

function scoreColor(score) {
  if (score >= 75) return "var(--success)";
  if (score >= 50) return "var(--warning)";
  return "var(--danger)";
}

// Global Fetch Wrapper
async function fetchApi(url, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const response = await fetch(url, { ...options, headers });
  if (response.status === 401) {
    // Session expired
    logout();
    showToast("Session expired. Please sign in again.", "warning");
    throw new Error("Unauthorized");
  }
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Request failed with code ${response.status}`);
  }
  return response.json();
}

// Router & Views toggling
const views = [
  "home", "trending", "categories", "verification", "deepfake", "whatsapp", "rumors", "assistant", "saved", "profile", "admin", "login", "register"
];

function navigate(hash) {
  let target = hash.replace("#", "") || "home";
  
  // Guard authenticated views
  const authRequired = ["saved", "profile", "admin"];
  if (authRequired.includes(target) && !token) {
    target = "login";
    location.hash = "#login";
  }

  // Admin role guard
  if (target === "admin" && (!currentUser || currentUser.role !== "Admin")) {
    target = "home";
    location.hash = "#home";
    showToast("Unauthorized page. Administrators only.", "error");
  }

  // Toggle visible views
  views.forEach(v => {
    const el = document.getElementById(`${v}View`);
    if (el) el.style.display = (v === target) ? "block" : "none";
  });

  // Update nav links
  document.querySelectorAll("#sidebarNav a").forEach(link => {
    link.classList.remove("active");
    if (link.getAttribute("href") === `#${target}`) {
      link.classList.add("active");
    }
  });

  // View specific triggers
  if (target === "trending") loadTrendingNews();
  if (target === "categories") loadCategories();
  if (target === "admin") loadAdminDashboard();
  if (target === "saved") loadSavedArticles();
  if (target === "profile") loadProfile();
  if (target === "assistant") drawRelationshipGraph();

  document.body.classList.remove("nav-open");
}

// User Actions
async function registerUser(e) {
  e.preventDefault();
  const name = document.getElementById("registerName").value;
  const email = document.getElementById("registerEmail").value;
  const password = document.getElementById("registerPassword").value;
  const role = document.getElementById("registerRole").value;

  try {
    const res = await fetchApi("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, email, password, role })
    });
    showToast(res.message || "Registration completed. Please login.", "success");
    location.hash = "#login";
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function loginUser(e) {
  e.preventDefault();
  const email = document.getElementById("loginEmail").value;
  const password = document.getElementById("loginPassword").value;
  const otpCode = document.getElementById("loginOtpCode").value;
  const mfaCode = document.getElementById("loginMfaCode").value;

  try {
    const res = await fetchApi("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password, otp: otpCode, mfa_code: mfaCode })
    });

    if (res.otp_required) {
      document.getElementById("loginOtpGroup").style.display = "grid";
      showToast("OTP sent to your email. Enter code to complete login.", "warning");
      return;
    }

    if (res.mfa_required) {
      document.getElementById("loginMfaGroup").style.display = "grid";
      showToast("MFA enabled. Enter authenticator app code to login.", "warning");
      return;
    }

    token = res.access_token;
    localStorage.setItem("truthlens_token", token);
    currentUser = res.user;

    // Reset login fields
    document.getElementById("loginPassword").value = "";
    document.getElementById("loginOtpCode").value = "";
    document.getElementById("loginMfaCode").value = "";
    document.getElementById("loginOtpGroup").style.display = "none";
    document.getElementById("loginMfaGroup").style.display = "none";

    showToast(`Welcome back, ${currentUser.name}!`, "success");
    updateAuthState();
    location.hash = "#home";
  } catch (err) {
    showToast(err.message, "error");
  }
}

function logout() {
  token = null;
  currentUser = null;
  localStorage.removeItem("truthlens_token");
  updateAuthState();
  location.hash = "#home";
  showToast("Logged out successfully.", "success");
}

function updateAuthState() {
  const shell = document.getElementById("appShell");
  const guestDiv = document.querySelector(".guest-only");
  const userDiv = document.querySelector(".user-only");
  const adminLink = document.getElementById("adminNavLink");

  if (token && currentUser) {
    shell.classList.remove("logged-out");
    guestDiv.style.display = "none";
    userDiv.style.display = "flex";
    
    document.getElementById("headerPoints").textContent = `${currentUser.trust_points || 0} pts`;
    if (currentUser.avatar_url) {
      document.getElementById("headerAvatar").src = currentUser.avatar_url;
    }

    if (currentUser.role === "Admin" || currentUser.role === "Moderator") {
      adminLink.style.display = "block";
    } else {
      adminLink.style.display = "none";
    }
  } else {
    shell.classList.add("logged-out");
    guestDiv.style.display = "flex";
    userDiv.style.display = "none";
    adminLink.style.display = "none";
  }
}

async function loadProfile() {
  if (!token) return;
  try {
    const res = await fetchApi("/api/auth/profile");
    currentUser = res.user;
    
    document.getElementById("profileName").textContent = currentUser.name;
    document.getElementById("profileEmail").textContent = currentUser.email;
    document.getElementById("profileRole").textContent = currentUser.role;
    document.getElementById("profilePoints").textContent = `Trust Points: ${currentUser.trust_points}`;
    document.getElementById("profileAvatarUrl").value = currentUser.avatar_url || "";
    document.getElementById("profileBio").value = currentUser.bio || "";
    document.getElementById("profileLanguage").value = currentUser.preferred_language || "English";
    document.getElementById("profileMfa").checked = currentUser.mfa_enabled;

    if (currentUser.avatar_url) {
      document.getElementById("profileAvatar").src = currentUser.avatar_url;
    }

    // Populate profile logs & badges
    renderReadingHistory(res.reading_history || []);
    renderProfileBadges(res.badges || []);
  } catch (err) {
    showToast("Error loading profile: " + err.message, "error");
  }
}

async function updateProfile(e) {
  e.preventDefault();
  const avatarUrl = document.getElementById("profileAvatarUrl").value;
  const bio = document.getElementById("profileBio").value;
  const language = document.getElementById("profileLanguage").value;

  try {
    const res = await fetchApi("/api/auth/profile", {
      method: "PUT",
      body: JSON.stringify({ avatar_url: avatarUrl, bio, preferred_language: language })
    });
    currentUser = res.user;
    updateAuthState();
    showToast("Profile settings updated successfully.", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function toggleMfa(e) {
  const enable = e.target.checked;
  const container = document.getElementById("mfaQrContainer");

  if (enable) {
    try {
      const res = await fetchApi("/api/auth/otp/setup", { method: "POST" });
      document.getElementById("mfaSecretKey").textContent = res.secret;
      container.style.display = "block";
      showToast("Enter authenticator code to enable MFA protection.", "warning");
    } catch (err) {
      e.target.checked = false;
      showToast("MFA setup failed: " + err.message, "error");
    }
  } else {
    try {
      await fetchApi("/api/auth/otp/setup", {
        method: "DELETE"
      });
      container.style.display = "none";
      showToast("MFA disabled successfully.", "success");
      loadProfile();
    } catch (err) {
      e.target.checked = true;
      showToast(err.message, "error");
    }
  }
}

async function verifyMfaSetup() {
  const code = document.getElementById("mfaVerifyCode").value;
  try {
    await fetchApi("/api/auth/otp/verify", {
      method: "POST",
      body: JSON.stringify({ mfa_code: code })
    });
    showToast("MFA activated and verified successfully.", "success");
    document.getElementById("mfaQrContainer").style.display = "none";
    loadProfile();
  } catch (err) {
    showToast("Verification failed: " + err.message, "error");
  }
}

// News Aggregation functions
async function loadTrendingNews(force = false) {
  const listEl = document.getElementById("articleList");
  listEl.innerHTML = `<div class="skeleton-container"><div class="skeleton-line" style="width:50%"></div><div class="skeleton-line" style="width:90%"></div><div class="skeleton-line" style="width:70%"></div></div>`;
  
  try {
    const url = force ? "/api/news/top-stories?refresh=1" : "/api/news/top-stories";
    const res = await fetchApi(url);
    articles = res.items;
    renderNewsFeed(articles);
    drawTrendChart();
    
    // Update AI Alerts
    const alertsEl = document.getElementById("aiRiskInsights");
    if (alertsEl) {
      const misleading = articles.filter(a => a.score < 60);
      if (misleading.length > 0) {
        alertsEl.innerHTML = misleading.map(a => `
          <div class="insight-item">
            <span class="risk high"></span>
            <div>
              <strong>Misinformation Warning</strong>
              <p>"${a.title}" flagged with a low trust score (${a.score}%). Verification details recommended.</p>
            </div>
          </div>
        `).join("");
      } else {
        alertsEl.innerHTML = `
          <div class="insight-item">
            <span class="risk low"></span>
            <div>
              <strong>System Clear</strong>
              <p>No high-risk viral rumor spikes detected in primary channels.</p>
            </div>
          </div>
        `;
      }
    }
  } catch (err) {
    showToast("Error aggregating news: " + err.message, "error");
  }
}

function renderNewsFeed(list) {
  const listEl = document.getElementById("articleList");
  if (list.length === 0) {
    listEl.innerHTML = `<p class="muted">No news stories match search criteria.</p>`;
    return;
  }
  listEl.innerHTML = list.map(item => `
    <article class="news-item">
      <div class="article-meta">
        <span>${item.source}</span>
        <span>${item.published_at || item.time || '10 min ago'}</span>
      </div>
      <h3>${item.title}</h3>
      <p>${item.summary}</p>
      <div class="news-footer">
        <span>Category: ${item.category || item.topic}</span>
        <span style="color:${scoreColor(item.score)}">${item.score}% - ${item.label || scoreLabel(item.score)}</span>
      </div>
      <div class="progress" aria-label="Trust Score: ${item.score}%">
        <span style="--width:${item.score}%"></span>
      </div>
      <div style="margin-top: 10px; display: flex; gap: 8px;">
        <button class="ghost-button small select-article-btn" data-id="${item.id}" type="button">Detail Summary</button>
        <button class="ghost-button small save-article-btn" data-id="${item.id}" type="button">💾 Bookmark</button>
      </div>
    </article>
  `).join("");

  // Bind news action buttons
  document.querySelectorAll(".select-article-btn").forEach(btn => {
    btn.addEventListener("click", () => selectArticleForAssistant(btn.dataset.id));
  });
  document.querySelectorAll(".save-article-btn").forEach(btn => {
    btn.addEventListener("click", () => bookmarkArticle(btn.dataset.id));
  });
}

async function selectArticleForAssistant(id) {
  const article = articles.find(a => String(a.id) === String(id));
  if (!article) return;
  location.hash = "#assistant";
  
  // Update translation text
  document.getElementById("summaryTitle").textContent = article.title;
  document.getElementById("summaryOutput").textContent = article.summary;
  document.getElementById("summaryOutput").dataset.textToTranslate = article.summary;
  document.getElementById("summaryOutput").dataset.activeLang = "English";
}

async function bookmarkArticle(id) {
  if (!token) {
    location.hash = "#login";
    showToast("Please login to save articles to your library.", "warning");
    return;
  }
  try {
    const res = await fetchApi("/api/news/save", {
      method: "POST",
      body: JSON.stringify({ article_id: String(id) })
    });
    showToast(res.message || "Article bookmarked.", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function loadSavedArticles() {
  if (!token) return;
  const listEl = document.getElementById("savedArticleList");
  listEl.innerHTML = `<div class="skeleton-container"><div class="skeleton-line"></div></div>`;
  try {
    const res = await fetchApi("/api/auth/saved");
    savedArticles = res.items || [];
    if (savedArticles.length === 0) {
      listEl.innerHTML = `<p class="muted">No bookmarked articles. Save stories from the news feed to store them here.</p>`;
      return;
    }
    listEl.innerHTML = savedArticles.map(item => `
      <article class="news-item">
        <div class="article-meta"><span>${item.source}</span><span>Bookmarked</span></div>
        <h3>${item.title}</h3>
        <p>${item.summary}</p>
        <div style="margin-top: 10px; display: flex; gap: 8px;">
          <button class="ghost-button small select-article-btn" data-id="${item.id}" type="button">Summarize</button>
          <button class="ghost-button small remove-article-btn" data-id="${item.id}" type="button">❌ Remove</button>
        </div>
      </article>
    `).join("");

    document.querySelectorAll(".remove-article-btn").forEach(btn => {
      btn.addEventListener("click", () => removeBookmark(btn.dataset.id));
    });
    document.querySelectorAll(".select-article-btn").forEach(btn => {
      btn.addEventListener("click", () => selectArticleForAssistant(btn.dataset.id));
    });
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function removeBookmark(id) {
  try {
    await fetchApi(`/api/auth/saved?article_id=${id}`, { method: "DELETE" });
    showToast("Bookmark removed.", "success");
    loadSavedArticles();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Categories functions
async function loadCategories() {
  const gridEl = document.getElementById("categoryGrid");
  try {
    const res = await fetchApi("/api/news/categories");
    categories = res.items || [];
    const sortVal = document.querySelector("#categorySort button.active").dataset.sort;
    
    if (sortVal === "score") {
      categories.sort((a, b) => b.average_score - a.average_score);
    } else {
      categories.sort((a, b) => b.live_stories - a.live_stories);
    }

    gridEl.innerHTML = categories.map(c => `
      <button type="button" class="category-btn" data-category="${c.name}">
        <strong>${c.name}</strong>
        <span>Avg Trust: ${c.average_score}% • ${c.live_stories} stories</span>
      </button>
    `).join("");

    document.querySelectorAll(".category-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const cat = btn.dataset.category;
        location.hash = "#trending";
        document.getElementById("globalSearch").value = cat;
        renderNewsFeed(articles.filter(a => a.category === cat || a.topic === cat));
      });
    });
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Verification Engine
async function executeVerification() {
  const text = document.getElementById("claimInput").value.trim();
  const fileInput = document.getElementById("docUpload");
  const reportPanel = document.getElementById("verificationReportDetails");
  
  if (!text && !fileInput.files[0]) {
    showToast("Please enter a text claim or upload a verification file.", "warning");
    return;
  }

  showToast("Scanning assertions and compiling sources...", "info");
  
  try {
    let res;
    if (fileInput.files[0]) {
      const fd = new FormData();
      fd.append("document", fileInput.files[0]);
      const opts = { method: "POST", body: fd };
      if (token) opts.headers = { "Authorization": `Bearer ${token}` };
      const rawRes = await fetch("/api/verification/document", opts);
      res = await rawRes.json();
    } else {
      res = await fetchApi("/api/verification/article", {
        method: "POST",
        body: JSON.stringify({ text })
      });
    }

    // Update gauge
    document.getElementById("claimGauge").style.setProperty("--score", res.truthlens_score);
    document.getElementById("claimScore").textContent = res.truthlens_score;
    document.getElementById("claimLabel").textContent = res.label;
    document.getElementById("claimSummary").textContent = `Verification report finalized. Extracted claims crosschecked against authoritative indices. Contradictions found: ${res.verification_report.contradictions_found ? "Yes" : "No"}.`;
    
    // Render vectors
    const factorsEl = document.getElementById("factorList");
    factorsEl.innerHTML = Object.entries(res.factors).map(([k, val]) => `
      <div class="factor">
        <header><span>${k.replace(/_/g, " ").toUpperCase()}</span><span>${val}%</span></header>
        <div class="progress"><span style="--width:${val}%"></span></div>
      </div>
    `).join("");

    // Load AI detector
    if (res.ai_detector) {
      document.getElementById("aiDetectorPanel").style.display = "block";
      document.getElementById("aiProbabilityLabel").textContent = `AI Generation Probability: ${res.ai_detector.ai_generated_probability}%`;
      document.getElementById("aiProbabilityProgress").style.setProperty("--width", `${res.ai_detector.ai_generated_probability}%`);
      document.getElementById("aiDetectionDetails").innerHTML = res.ai_detector.detailed_analysis.map(x => `<li>${x}</li>`).join("");
    } else {
      document.getElementById("aiDetectorPanel").style.display = "none";
    }

    // Reveal report log
    reportPanel.style.display = "block";
    document.getElementById("extractedClaimsList").innerHTML = res.claim_extraction.map(x => `<li>${x}</li>`).join("");
    document.getElementById("evidenceSourcesList").innerHTML = res.verification_report.evidence_sources.map(x => `<li>${x}</li>`).join("");
    
    // Linguistic
    document.getElementById("biasPolitical").textContent = res.bias_analysis.political_bias;
    document.getElementById("biasEmotional").textContent = `${res.bias_analysis.emotional_manipulation}%`;
    document.getElementById("biasPropaganda").textContent = `${res.bias_analysis.propaganda_risk}%`;

    // Award points mock
    if (token) loadProfile();

    showToast("Integrity scan complete.", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Deepfake Detector
async function executeDeepfakeScan() {
  const fileInput = document.getElementById("mediaUpload");
  if (!fileInput.files[0]) {
    showToast("Please choose a media file for deepfake testing.", "warning");
    return;
  }

  showToast("Uploading media and running model ensemble...", "info");
  
  try {
    const fd = new FormData();
    fd.append("media", fileInput.files[0]);
    const response = await fetch("/api/deepfake/analyze", {
      method: "POST",
      body: fd
    });
    const res = await response.json();

    document.getElementById("authScore").textContent = `${res.authenticity_score}%`;
    document.getElementById("manipScore").textContent = `${res.manipulation_score}%`;
    document.getElementById("framesChecked").textContent = `${res.confidence}%`;
    document.getElementById("deepfakeModel").textContent = res.models.join(", ");
    
    // Modality details
    document.getElementById("deepfakeModalityResults").style.display = "block";
    document.getElementById("deepfakeSignals").innerHTML = res.signals.map(s => `<span>${s}</span>`).join("");

    // Setup Heatmap visuals
    const overlay = document.getElementById("heatmapOverlay");
    overlay.innerHTML = "";
    document.getElementById("heatmapPlaceholder").style.display = "none";
    
    const isImage = fileInput.files[0].type.startsWith("image");
    const imgEl = document.getElementById("heatmapImage");
    
    if (isImage) {
      imgEl.src = URL.createObjectURL(fileInput.files[0]);
      imgEl.style.display = "block";
      
      // Draw simulated hotspot circles onto the overlay
      res.heatmap_regions.forEach(h => {
        const dot = document.createElement("div");
        dot.className = "hotspot";
        dot.style.left = `${10 + Math.random() * 80}%`;
        dot.style.top = `${10 + Math.random() * 80}%`;
        dot.style.background = scoreColor(h.risk);
        dot.style.boxShadow = `0 0 0 8px ${scoreColor(h.risk)}33`;
        dot.title = `${h.region} manipulation risk: ${h.risk}%`;
        overlay.appendChild(dot);
      });
    } else {
      imgEl.style.display = "none";
      overlay.innerHTML = `<div class="muted" style="color:var(--danger); font-weight:bold; padding:20px;">Spectral anomaly detected in audio/video frequencies. Lip sync offset identified.</div>`;
    }

    if (token) loadProfile();
    showToast("Model scan finished.", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// WhatsApp Forward Verification
async function executeSocialVerification() {
  const text = document.getElementById("socialInput").value.trim();
  if (!text) {
    showToast("Please paste social message text to scan.", "warning");
    return;
  }
  try {
    const res = await fetchApi("/api/verification/social-claim", {
      method: "POST",
      body: JSON.stringify({ text })
    });
    
    document.getElementById("socialStatus").textContent = `${res.status.toUpperCase()}: (Score: ${res.truthlens_score}%)`;
    document.getElementById("socialStatus").style.color = scoreColor(res.truthlens_score);
    document.getElementById("socialExplanation").textContent = res.explanation;

    // Load comparison panel text
    document.getElementById("disputedText").textContent = text;
    document.getElementById("verifiedRealityText").textContent = res.explanation + " Verified check points show contradictions in forwarded details.";

    showToast("Hotline verifier matched claim.", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Rumor lists & maps
function renderRumorsList() {
  const list = document.getElementById("rumorList");
  if (!list) return;
  list.innerHTML = rumors.map(([title, detail, status, classKey]) => `
    <div class="rumor-item">
      <strong>${title}</strong>
      <p>${detail}</p>
      <div class="rumor-footer">
        <span>Risk class: ${status}</span>
        <button class="ghost-button small trace-rumor-btn" data-hotspot="${classKey}" type="button">Trace on Map</button>
      </div>
    </div>
  `).join("");

  document.querySelectorAll(".trace-rumor-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const key = btn.dataset.hotspot;
      const hs = document.querySelector(`.hotspot.${key}`);
      if (hs) {
        hs.style.transform = "scale(1.8)";
        setTimeout(() => hs.style.transform = "scale(1)", 1500);
        showToast(`Highlighting epicenter on map visualization.`, "info");
      }
    });
  });
}

// Chatbot interactions
async function askChatbot() {
  const promptEl = document.getElementById("botPrompt");
  const prompt = promptEl.value.trim();
  if (!prompt) return;

  const chat = document.getElementById("chatWindow");
  chat.insertAdjacentHTML("beforeend", `<div class="user-message">${prompt}</div>`);
  chat.scrollTop = chat.scrollHeight;
  promptEl.value = "";

  try {
    const activeLang = document.querySelector("#summaryLangGrid .lang-pill.active")?.dataset.lang || "English";
    const res = await fetchApi("/api/assistant/truthbot", {
      method: "POST",
      body: JSON.stringify({ prompt, language: activeLang })
    });
    chat.insertAdjacentHTML("beforeend", `<div class="bot-message">${res.answer}</div>`);
    chat.scrollTop = chat.scrollHeight;
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function requestTranslation(language) {
  const targetEl = document.getElementById("summaryOutput");
  const text = targetEl.dataset.textToTranslate || targetEl.textContent;
  if (!text || text.startsWith("Select an article")) {
    showToast("Please select a story details page from Trending to translate.", "warning");
    return;
  }
  showToast(`Translating text to ${language}...`, "info");
  try {
    const res = await fetchApi("/api/assistant/truthbot", {
      method: "POST",
      body: JSON.stringify({
        prompt: `Translate the following text into ${language}: "${text}"`,
        language
      })
    });
    targetEl.textContent = res.answer;
    targetEl.dataset.activeLang = language;
    showToast("Translation complete.", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function requestSummaryLength(lenType) {
  const targetEl = document.getElementById("summaryOutput");
  const text = targetEl.dataset.textToTranslate;
  if (!text) {
    showToast("Select a trending story to change summary mode.", "warning");
    return;
  }
  showToast("Re-summarizing story content...", "info");
  try {
    const prompt = `Summarize this text in mode: ${lenType}. Content: "${text}"`;
    const res = await fetchApi("/api/assistant/truthbot", {
      method: "POST",
      body: JSON.stringify({ prompt })
    });
    targetEl.textContent = res.answer;
    showToast("Summary updated.", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Text to Speech voice
function speakSummary() {
  const text = document.getElementById("summaryOutput").textContent;
  if (text.startsWith("Select an article")) {
    showToast("No readable text loaded.", "warning");
    return;
  }
  
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel(); // stop current reading
    const utterance = new SpeechSynthesisUtterance(text);
    const selectedLang = document.querySelector("#summaryLangGrid .lang-pill.active")?.dataset.lang || "English";
    
    // Map voices if possible
    if (selectedLang === "Hindi") utterance.lang = "hi-IN";
    else if (selectedLang === "Tamil") utterance.lang = "ta-IN";
    else if (selectedLang === "Telugu") utterance.lang = "te-IN";
    else utterance.lang = "en-US";

    window.speechSynthesis.speak(utterance);
    showToast("Reading aloud summary...", "info");
  } else {
    showToast("Web Speech Text-to-Speech not supported in this browser.", "error");
  }
}

// Graph Drawing on HTML5 Canvas
function drawRelationshipGraph() {
  const canvas = document.getElementById("sourceGraphCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const nodes = [
    { name: "BBC News", x: 100, y: 150, type: "source", color: "var(--success)" },
    { name: "Reuters", x: 250, y: 80, type: "source", color: "var(--success)" },
    { name: "Social Post A", x: 400, y: 220, type: "claim", color: "var(--danger)" },
    { name: "Govt Advisory", x: 550, y: 100, type: "source", color: "var(--success)" },
    { name: "Election Rumor", x: 700, y: 180, type: "claim", color: "var(--warning)" }
  ];

  const links = [
    { from: 0, to: 2 },
    { from: 1, to: 2 },
    { from: 3, to: 4 },
    { from: 2, to: 4 }
  ];

  // Draw lines
  ctx.strokeStyle = "var(--line)";
  ctx.lineWidth = 2;
  links.forEach(l => {
    ctx.beginPath();
    ctx.moveTo(nodes[l.from].x, nodes[l.from].y);
    ctx.lineTo(nodes[l.to].x, nodes[l.to].y);
    ctx.stroke();
  });

  // Draw dots
  nodes.forEach(n => {
    ctx.fillStyle = n.color;
    ctx.beginPath();
    ctx.arc(n.x, n.y, 14, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = "var(--text)";
    ctx.font = "bold 12px Inter";
    ctx.fillText(n.name, n.x - 30, n.y - 20);
  });
}

function drawTrendChart() {
  const canvas = document.querySelector("#trendCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const points = [38, 54, 49, 77, 68, 92, 86, 112, 104, 132];
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  ctx.strokeStyle = "#14b8a6";
  ctx.lineWidth = 4;
  ctx.beginPath();
  points.forEach((point, index) => {
    const x = 24 + index * ((canvas.width - 48) / (points.length - 1));
    const y = canvas.height - point;
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
  ctx.fillStyle = "rgba(20, 184, 166, 0.16)";
  ctx.lineTo(canvas.width - 24, canvas.height - 24);
  ctx.lineTo(24, canvas.height - 24);
  ctx.closePath();
  ctx.fill();
}

// Renderers
function renderReadingHistory(list) {
  const listEl = document.getElementById("readingHistoryList");
  if (list.length === 0) {
    listEl.innerHTML = `<p class="muted">No reading history registered.</p>`;
    return;
  }
  listEl.innerHTML = list.map(item => `
    <div class="news-item" style="padding: 10px;">
      <div class="article-meta"><span>Read At: ${item.read_at}</span></div>
      <strong>Article ID: ${item.article_id}</strong>
    </div>
  `).join("");
}

function renderProfileBadges(list) {
  const listEl = document.getElementById("userBadgesList");
  if (list.length === 0) {
    listEl.innerHTML = `<span>🏆 Verify Claims to earn badges!</span>`;
    return;
  }
  listEl.innerHTML = list.map(b => `
    <span>${b.icon} ${b.name} - <small>${b.description}</small></span>
  `).join("");
}

// Admin Operations
async function loadAdminDashboard() {
  if (!token) return;
  try {
    const res = await fetchApi("/api/admin/metrics");
    document.getElementById("adminActiveUsers").textContent = res.active_users;
    document.getElementById("adminReportsCount").textContent = res.reports;
    document.getElementById("adminAiUsage").textContent = res.ai_usage;
    document.getElementById("adminHealth").textContent = res.system_health;

    // Load reports queue
    moderationQueue = res.reports_queue || [];
    renderModerationQueue(moderationQueue);

    // Load audit logs
    auditLogs = res.audit_logs || [];
    renderAuditLogs(auditLogs);
  } catch (err) {
    showToast(err.message, "error");
  }
}

function renderModerationQueue(list) {
  const queueEl = document.getElementById("adminModerationQueue");
  if (list.length === 0) {
    queueEl.innerHTML = `<p class="muted">No community reports pending review.</p>`;
    return;
  }
  queueEl.innerHTML = list.map(item => `
    <div class="news-item">
      <div class="article-meta"><span>User Report ID: ${item.id}</span><span>Type: ${item.report_type}</span></div>
      <p><strong>Claim:</strong> ${item.claim_text}</p>
      ${item.evidence_url ? `<p><strong>Evidence:</strong> <a href="${item.evidence_url}" target="_blank" style="color:var(--accent); text-decoration:underline;">${item.evidence_url}</a></p>` : ''}
      <div style="margin-top: 10px; display: flex; gap: 8px;">
        <button class="primary-button small resolve-report-btn" data-id="${item.id}" data-action="resolved" type="button">Approve & Verify</button>
        <button class="ghost-button small resolve-report-btn" data-id="${item.id}" data-action="rejected" type="button">Reject</button>
      </div>
    </div>
  `).join("");

  document.querySelectorAll(".resolve-report-btn").forEach(btn => {
    btn.addEventListener("click", () => resolveReport(btn.dataset.id, btn.dataset.action));
  });
}

function renderAuditLogs(list) {
  const logsEl = document.getElementById("adminAuditLogs");
  if (list.length === 0) {
    logsEl.innerHTML = `<p class="muted">No system logs recorded.</p>`;
    return;
  }
  logsEl.innerHTML = list.map(l => `
    <div style="padding: 8px; border-bottom: 1px solid var(--line); font-size:12px; font-family: monospace;">
      [${l.created_at}] Actor ID: ${l.actor_id || 'System'} - Action: <strong>${l.action}</strong> (Target: ${l.target_type} #${l.target_id})
    </div>
  `).join("");
}

async function resolveReport(id, action) {
  try {
    const res = await fetchApi("/api/admin/moderate", {
      method: "POST",
      body: JSON.stringify({ report_id: id, status: action, notes: `Moderated via Admin panel action: ${action}` })
    });
    showToast(res.message || `Report updated to ${action}`, "success");
    loadAdminDashboard();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// In-memory Download ZIP simulation
function triggerExtensionDownload() {
  // We'll point to the API path that zips the extension folder
  window.open("/api/admin/download-extension");
  showToast("Downloading browser extension zip bundle.", "success");
}

// Event bindings
function bindAppEvents() {
  // Navigation / hash change listener
  window.addEventListener("hashchange", () => navigate(location.hash));

  // Forms submit
  document.getElementById("registerForm").addEventListener("submit", registerUser);
  document.getElementById("loginForm").addEventListener("submit", loginUser);
  document.getElementById("profileForm").addEventListener("submit", updateProfile);

  // Profile toggles
  document.getElementById("profileMfa").addEventListener("change", toggleMfa);
  document.getElementById("mfaVerifyBtn").addEventListener("click", verifyMfaSetup);
  document.getElementById("logoutBtn").addEventListener("click", logout);

  // Core scan clicks
  document.getElementById("verifyClaim").addEventListener("click", executeVerification);
  document.getElementById("analyzeMedia").addEventListener("click", executeDeepfakeScan);
  document.getElementById("verifySocial").addEventListener("click", executeSocialVerification);

  // News controls
  document.getElementById("refreshNewsBtn").addEventListener("click", () => loadTrendingNews(true));
  document.getElementById("categorySort").addEventListener("click", (e) => {
    const btn = e.target.closest("button");
    if (!btn) return;
    document.querySelectorAll("#categorySort button").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    loadCategories();
  });

  // Chat/Speech
  document.getElementById("askBot").addEventListener("click", askChatbot);
  document.getElementById("botPrompt").addEventListener("keydown", (e) => {
    if (e.key === "Enter") askChatbot();
  });
  document.querySelectorAll(".quick-prompts button").forEach(btn => {
    btn.addEventListener("click", () => {
      document.getElementById("botPrompt").value = btn.textContent;
      askChatbot();
    });
  });

  document.getElementById("summaryLangGrid").addEventListener("click", (e) => {
    const pill = e.target.closest(".lang-pill");
    if (!pill) return;
    document.querySelectorAll("#summaryLangGrid .lang-pill").forEach(p => p.classList.remove("active"));
    pill.classList.add("active");
    requestTranslation(pill.dataset.lang);
  });

  document.getElementById("summaryTabRow").addEventListener("click", (e) => {
    const tab = e.target.closest("button");
    if (!tab) return;
    document.querySelectorAll("#summaryTabRow button").forEach(b => b.classList.remove("active"));
    tab.classList.add("active");
    requestSummaryLength(tab.dataset.length);
  });

  document.getElementById("ttsPlayBtn").addEventListener("click", speakSummary);

  // Search filter
  document.getElementById("globalSearch").addEventListener("input", (e) => {
    const term = e.target.value.toLowerCase().trim();
    if (!term) {
      renderNewsFeed(articles);
      return;
    }
    const filtered = articles.filter(a => 
      a.title.toLowerCase().includes(term) || 
      a.summary.toLowerCase().includes(term) ||
      (a.category && a.category.toLowerCase().includes(term))
    );
    renderNewsFeed(filtered);
  });

  // Map Hover triggers
  const map = document.getElementById("hotspotMap");
  const mapTooltip = document.getElementById("mapTooltip");
  map.querySelectorAll(".hotspot").forEach(h => {
    h.addEventListener("mouseenter", (e) => {
      mapTooltip.style.display = "block";
      mapTooltip.textContent = h.dataset.rumor;
      mapTooltip.style.left = `${h.offsetLeft + 20}px`;
      mapTooltip.style.top = `${h.offsetTop}px`;
    });
    h.addEventListener("mouseleave", () => {
      mapTooltip.style.display = "none";
    });
  });

  // UI Theme toggle
  document.getElementById("themeToggle").addEventListener("click", (e) => {
    document.body.classList.toggle("dark");
    e.target.textContent = document.body.classList.contains("dark") ? "Light Mode" : "Dark Mode";
  });

  // Mobile menu navbar
  document.querySelector(".mobile-menu").addEventListener("click", () => {
    document.body.classList.toggle("nav-open");
  });

  // Dropzone drag
  const dropZone = document.getElementById("deepfakeDropZone");
  const mediaInput = document.getElementById("mediaUpload");
  const selectedLabel = document.getElementById("selectedDeepfakeFile");

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.style.borderColor = "var(--brand)";
  });
  dropZone.addEventListener("dragleave", () => {
    dropZone.style.borderColor = "var(--line)";
  });
  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.style.borderColor = "var(--line)";
    if (e.dataTransfer.files.length) {
      mediaInput.files = e.dataTransfer.files;
      selectedLabel.textContent = `File selected: ${mediaInput.files[0].name}`;
    }
  });
  mediaInput.addEventListener("change", () => {
    if (mediaInput.files[0]) {
      selectedLabel.textContent = `File selected: ${mediaInput.files[0].name}`;
    }
  });

  // Document verifier upload tracker
  const docInput = document.getElementById("docUpload");
  const docLabel = document.getElementById("uploadedDocName");
  docInput.addEventListener("change", () => {
    if (docInput.files[0]) {
      docLabel.textContent = docInput.files[0].name;
    }
  });

  // Download browser extension link
  document.getElementById("downloadExtensionLink").addEventListener("click", (e) => {
    e.preventDefault();
    triggerExtensionDownload();
  });
}

// App Bootloader
async function boot() {
  // Check auth session
  if (token) {
    try {
      const res = await fetchApi("/api/auth/profile");
      currentUser = res.user;
    } catch (err) {
      token = null;
      localStorage.removeItem("truthlens_token");
    }
  }

  updateAuthState();
  bindAppEvents();
  renderRumorsList();

  // Load news feed
  loadTrendingNews().catch(console.error);

  // Initial routing
  navigate(location.hash);
}

// Initialize on load
window.addEventListener("DOMContentLoaded", () => {
  boot().catch(console.error);
});
