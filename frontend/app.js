// API_BASE is relative: nginx (see nginx.conf) proxies /api/* to the backend container.
const PRODUCTION_BACKEND_URL = "REPLACE_WITH_YOUR_BACKEND_PUBLIC_URL";
   const isLocal = ["localhost", "127.0.0.1"].includes(window.location.hostname);
   const API_BASE = isLocal ? "http://localhost:8000" : PRODUCTION_BACKEND_URL;

const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const browseBtn = document.getElementById("browseBtn");
const fileNameEl = document.getElementById("fileName");
const runBtn = document.getElementById("runBtn");
const pipelineTrace = document.getElementById("pipelineTrace");
const resultsSection = document.getElementById("results");

let selectedFile = null;
let interviewState = { role: null, difficulty: "Intermediate", history: [] };

document.getElementById("difficultyGroup").addEventListener("click", (e) => {
  const btn = e.target.closest(".difficulty-pill");
  if (!btn) return;
  document.querySelectorAll(".difficulty-pill").forEach((p) => p.classList.remove("active"));
  btn.classList.add("active");
  interviewState.difficulty = btn.dataset.level;
});

document.getElementById("resetBtn").addEventListener("click", () => {
  selectedFile = null;
  fileNameEl.textContent = "";
  runBtn.disabled = true;
  pipelineTrace.hidden = true;
  resultsSection.hidden = true;
  document.getElementById("interviewSetup").hidden = false;
  document.getElementById("interviewLive").hidden = true;
  window.scrollTo({ top: 0, behavior: "smooth" });
});

browseBtn.addEventListener("click", () => fileInput.click());
dropZone.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.classList.add("dragover"); });
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("dragover");
  if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener("change", (e) => {
  if (e.target.files.length) handleFile(e.target.files[0]);
});

function handleFile(file) {
  selectedFile = file;
  fileNameEl.textContent = file.name;
  runBtn.disabled = false;
}

function setTraceState(step, state) {
  const el = document.querySelector(`.trace-step[data-step="${step}"] .state`);
  const parent = document.querySelector(`.trace-step[data-step="${step}"]`);
  if (!el) return;
  el.textContent = state;
  parent.classList.remove("active", "done");
  if (state === "running") parent.classList.add("active");
  if (state === "done") parent.classList.add("done");

  const dot = document.querySelector(`.dot[data-agent="${step}"]`);
  if (dot) {
    dot.classList.remove("active", "done");
    if (state === "running") dot.classList.add("active");
    if (state === "done") dot.classList.add("done");
  }
}

runBtn.addEventListener("click", async () => {
  if (!selectedFile) return;
  runBtn.disabled = true;
  pipelineTrace.hidden = false;
  resultsSection.hidden = true;

  setTraceState("resume", "running");

  const formData = new FormData();
  formData.append("file", selectedFile);

  try {
    const res = await fetch(`${API_BASE}/api/pipeline/full-report`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(err.detail || "Pipeline failed");
    }
    const data = await res.json();

    setTraceState("resume", "done");
    setTraceState("skillgap", "running");
    await sleep(300);
    setTraceState("skillgap", "done");
    setTraceState("interview", "running");
    await sleep(300);
    setTraceState("interview", "done");

    renderResults(data);
  } catch (e) {
    alert("Something went wrong: " + e.message);
    runBtn.disabled = false;
  }
});

function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

function renderResults(data) {
  const { resume_analysis, skill_gap, interview_ready } = data;

  document.getElementById("resumeScoreNum").textContent = resume_analysis.overall_score ?? 0;
  const circumference = 327;
  const score = resume_analysis.overall_score ?? 0;
  const offset = circumference - (circumference * score) / 100;
  const gaugeFill = document.getElementById("resumeGaugeFill");
  gaugeFill.style.strokeDashoffset = offset;
  gaugeFill.style.stroke = score >= 75 ? "var(--good)" : score >= 50 ? "var(--accent)" : "var(--bad)";

  document.getElementById("targetRole").textContent = resume_analysis.suggested_target_role || "—";

  fillList("strengthsList", resume_analysis.strengths);
  fillList("weaknessesList", resume_analysis.weaknesses);
  fillList("suggestionsList", resume_analysis.improvement_suggestions);

  const pillGroup = document.getElementById("skillPills");
  pillGroup.innerHTML = "";
  (resume_analysis.extracted_skills || []).forEach((s) => {
    const span = document.createElement("span");
    span.className = "pill";
    span.textContent = s;
    pillGroup.appendChild(span);
  });

  document.getElementById("readinessFill").style.width = `${skill_gap.readiness_score}%`;
  document.getElementById("readinessLabel").textContent = `${skill_gap.readiness_score}% ready`;
  fillList("matchedSkills", skill_gap.matched_skills);
  fillList("missingSkills", skill_gap.missing_skills);

  document.getElementById("interviewRoleLabel").textContent = interview_ready.target_role;
  interviewState.role = interview_ready.target_role;
  interviewState.history = [];
  document.getElementById("interviewSetup").hidden = false;
  document.getElementById("interviewLive").hidden = true;

  resultsSection.hidden = false;
  resultsSection.scrollIntoView({ behavior: "smooth" });
}

function fillList(id, items) {
  const el = document.getElementById(id);
  el.innerHTML = "";
  (items || []).forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    el.appendChild(li);
  });
}

function renderChat() {
  const chatWindow = document.getElementById("chatWindow");
  chatWindow.innerHTML = "";
  interviewState.history.forEach((turn) => {
    const div = document.createElement("div");
    div.className = `msg ${turn.role === "interviewer" ? "interviewer" : "candidate"}`;
    div.textContent = turn.content;
    chatWindow.appendChild(div);
  });
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

document.getElementById("startInterviewBtn").addEventListener("click", startInterview);
document.getElementById("restartBtn").addEventListener("click", () => {
  document.getElementById("interviewSetup").hidden = false;
  document.getElementById("interviewLive").hidden = true;
  document.getElementById("interviewScore").hidden = true;
  interviewState.history = [];
});

async function startInterview() {
  if (!interviewState.role) return;
  const startBtn = document.getElementById("startInterviewBtn");
  startBtn.disabled = true;
  startBtn.textContent = "Starting...";
  try {
    const res = await fetch(`${API_BASE}/api/interview/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role: interviewState.role, difficulty: interviewState.difficulty }),
    });
    const data = await res.json();
    interviewState.history = [{ role: "interviewer", content: data.first_question }];
    document.getElementById("interviewSetup").hidden = true;
    document.getElementById("interviewLive").hidden = false;
    renderChat();
  } catch (e) {
    alert("Could not start interview: " + e.message);
  } finally {
    startBtn.disabled = false;
    startBtn.textContent = "Start Mock Interview →";
  }
}

document.getElementById("sendBtn").addEventListener("click", sendAnswer);
document.getElementById("chatInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendAnswer();
});

async function sendAnswer() {
  const input = document.getElementById("chatInput");
  const answer = input.value.trim();
  if (!answer || !interviewState.role) return;

  interviewState.history.push({ role: "candidate", content: answer });
  renderChat();
  input.value = "";

  try {
    const res = await fetch(`${API_BASE}/api/interview/continue`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        role: interviewState.role,
        history: interviewState.history.slice(0, -1),
        candidate_answer: answer,
        difficulty: interviewState.difficulty,
      }),
    });
    const data = await res.json();
    interviewState.history.push({ role: "interviewer", content: data.interviewer_reply });
    renderChat();
  } catch (e) {
    alert("Interview agent error: " + e.message);
  }
}

document.getElementById("finishBtn").addEventListener("click", async () => {
  if (!interviewState.role) return;
  try {
    const res = await fetch(`${API_BASE}/api/interview/score`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role: interviewState.role, history: interviewState.history }),
    });
    const data = await res.json();
    const scoreEl = document.getElementById("interviewScore");
    scoreEl.hidden = false;
    scoreEl.innerHTML = `
      Communication: ${data.communication_score}/100 &nbsp;|&nbsp;
      Technical: ${data.technical_score}/100 &nbsp;|&nbsp;
      Confidence: ${data.confidence_score}/100<br/><br/>
      ${data.overall_feedback || ""}
    `;
  } catch (e) {
    alert("Scoring error: " + e.message);
  }
});
