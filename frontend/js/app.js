// ========== STATE ==========
let selectedSkills = [];
let quizQueue = [];
let qIdx = 0;
let answers = [];
let timerInterval = null;
let timeLeft = 30;
let qStartTime = 0;
let results = null;
let radarChart = null;
let timeChart = null;
let latestAssessmentId = null;

const API_BASE = '/api';

// ========== NAVIGATION ==========
function showPage(id) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.getElementById('page-' + id).classList.add('active');
  const tabs = ['home', 'quiz', 'dashboard', 'recommendations'];
  const tabEls = document.querySelectorAll('.nav-tab');
  const idx = tabs.indexOf(id);
  if (idx >= 0) tabEls[idx].classList.add('active');
  window.scrollTo(0, 0);
}

// ========== SKILL SELECTOR ==========
function renderSkillSelector() {
  const sel = document.getElementById('skill-selector');
  sel.innerHTML = SKILLS.map(s => `
    <div class="skill-card" id="sc-${s.id}" onclick="toggleSkill('${s.id}')">
      <div class="skill-icon-lg">${s.icon}</div>
      <div class="skill-name-lg">${s.name}</div>
      <div class="skill-desc-sm">${s.desc}</div>
    </div>
  `).join('');
}

function toggleSkill(id) {
  const idx = selectedSkills.indexOf(id);
  if (idx >= 0) selectedSkills.splice(idx, 1);
  else selectedSkills.push(id);
  document.querySelectorAll('.skill-card').forEach(c => c.classList.remove('selected-skill'));
  selectedSkills.forEach(s => document.getElementById('sc-' + s).classList.add('selected-skill'));
  const btn = document.getElementById('start-btn');
  btn.disabled = selectedSkills.length === 0;
  btn.style.opacity = selectedSkills.length > 0 ? '1' : '0.4';
}

function startFresh() {
  selectedSkills = [];
  quizQueue = [];
  qIdx = 0;
  answers = [];
  document.getElementById('quiz-select').classList.remove('hidden');
  document.getElementById('quiz-active').classList.add('hidden');
  document.getElementById('quiz-done').classList.add('hidden');
  renderSkillSelector();
}

// ========== QUIZ ENGINE ==========
function beginQuiz() {
  if (selectedSkills.length === 0) return;
  quizQueue = [];
  selectedSkills.forEach(s => {
    QUESTIONS[s].forEach((q, i) => quizQueue.push({ ...q, skill: s, localIdx: i }));
  });
  qIdx = 0;
  answers = [];
  document.getElementById('quiz-select').classList.add('hidden');
  document.getElementById('quiz-active').classList.remove('hidden');
  renderQuestion();
}

function renderQuestion() {
  if (qIdx >= quizQueue.length) { endQuiz(); return; }
  const q = quizQueue[qIdx];
  const skill = SKILLS.find(s => s.id === q.skill);

  document.getElementById('q-skill-badge').textContent = skill.name;
  document.getElementById('q-skill-badge').className = 'skill-badge ' + skill.badgeClass;
  document.getElementById('q-counter').textContent = `Q${qIdx + 1} of ${quizQueue.length}`;

  const pct = Math.round((qIdx / quizQueue.length) * 100);
  document.getElementById('q-progress').style.width = pct + '%';
  document.getElementById('q-text').textContent = q.q;

  const optsEl = document.getElementById('q-options');
  optsEl.innerHTML = q.opts.map((o, i) =>
    `<button class="option" onclick="selectAnswer(${i})">${o}</button>`
  ).join('');

  document.getElementById('q-feedback').classList.add('hidden');
  document.getElementById('q-next-btn').style.display = 'none';

  const dots = document.getElementById('q-dots');
  dots.innerHTML = quizQueue.map((_, i) =>
    `<div class="step-dot ${i === qIdx ? 'active' : ''}"></div>`
  ).join('');

  clearInterval(timerInterval);
  timeLeft = 30;
  qStartTime = Date.now();
  updateTimer();
  timerInterval = setInterval(() => {
    timeLeft--;
    updateTimer();
    if (timeLeft <= 0) { clearInterval(timerInterval); autoTimeout(); }
  }, 1000);
}

function updateTimer() {
  const el = document.getElementById('timer-display');
  el.textContent = timeLeft;
  el.className = 'timer-val' + (timeLeft <= 8 ? ' timer-urgent' : '');
}

function autoTimeout() {
  const elapsed = Math.round((Date.now() - qStartTime) / 1000);
  answers.push({ qIdx, skill: quizQueue[qIdx].skill, selected: -1, correct: false, time: elapsed, diff: quizQueue[qIdx].diff });
  showFeedback(-1);
}

function selectAnswer(i) {
  clearInterval(timerInterval);
  const elapsed = Math.round((Date.now() - qStartTime) / 1000);
  const q = quizQueue[qIdx];
  const correct = i === q.ans;
  answers.push({ qIdx, skill: q.skill, selected: i, correct, time: elapsed, diff: q.diff });

  const opts = document.querySelectorAll('.option');
  opts.forEach((o, idx) => {
    o.disabled = true;
    if (idx === q.ans) o.classList.add('correct');
    if (idx === i && !correct) o.classList.add('wrong');
  });

  showFeedback(i);
}

function showFeedback(selected) {
  const q = quizQueue[qIdx];
  const correct = selected === q.ans;
  const fb = document.getElementById('q-feedback');
  fb.className = 'feedback-box ' + (correct ? 'feedback-correct' : 'feedback-wrong');
  fb.innerHTML = (correct ? '✓ Correct! ' : (selected === -1 ? '⏱ Time up. ' : '✗ Incorrect. ')) + q.exp;
  fb.classList.remove('hidden');
  document.getElementById('q-next-btn').style.display = 'flex';
}

function nextQuestion() {
  qIdx++;
  if (qIdx >= quizQueue.length) endQuiz();
  else renderQuestion();
}

function endQuiz() {
  clearInterval(timerInterval);
  results = computeResults();
  document.getElementById('quiz-active').classList.add('hidden');
  document.getElementById('quiz-done').classList.remove('hidden');
  autoSaveAssessmentRecord();
}

function getModelStatusEl() {
  return document.getElementById('model-status');
}

function buildBackendPayload(r, targetScore = null) {
  const sc = r.skillScores || {};
  return {
    selected_skills_count: selectedSkills.length || Object.keys(sc).length || 1,
    total_questions: r.totalAns,
    total_correct: r.totalCorrect,
    accuracy_pct: r.totalAns ? Math.round((r.totalCorrect / r.totalAns) * 1000) / 10 : 0,
    avg_time_sec: r.avgTime,
    overall_score: r.overallScore,
    math_score: sc.math ? sc.math.score : 0,
    logic_score: sc.logic ? sc.logic.score : 0,
    aptitude_score: sc.aptitude ? sc.aptitude.score : 0,
    problem_score: sc.problem ? sc.problem.score : 0,
    target_score: targetScore
  };
}

async function autoSaveAssessmentRecord() {
  const statusEl = getModelStatusEl();
  if (!statusEl || !results) return;
  statusEl.textContent = 'Saving assessment record to backend...';
  try {
    const response = await fetch(`${API_BASE}/assessments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(buildBackendPayload(results, null))
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || 'Could not save assessment.');
    latestAssessmentId = body.id;
    statusEl.textContent = `Saved as record #${body.id}. Add a target score to label it.`;
  } catch (error) {
    statusEl.textContent = `Backend save failed: ${error.message}`;
  }
}

async function saveTargetLabel() {
  const statusEl = getModelStatusEl();
  if (!latestAssessmentId) {
    if (statusEl) statusEl.textContent = 'No saved assessment record found yet.';
    return;
  }

  const input = document.getElementById('target-score-input');
  const val = Number(input.value);
  if (Number.isNaN(val) || val < 0 || val > 100) {
    if (statusEl) statusEl.textContent = 'Enter a valid target score between 0 and 100.';
    return;
  }

  if (statusEl) statusEl.textContent = 'Saving target label...';
  try {
    const response = await fetch(`${API_BASE}/assessments/${latestAssessmentId}/label`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_score: val })
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || 'Could not save label.');
    if (statusEl) statusEl.textContent = `Label saved for record #${body.id}.`;
  } catch (error) {
    if (statusEl) statusEl.textContent = `Label save failed: ${error.message}`;
  }
}

async function predictFromLatestAssessment() {
  const statusEl = getModelStatusEl();
  if (!results) {
    if (statusEl) statusEl.textContent = 'No assessment results available for prediction.';
    return;
  }

  if (statusEl) statusEl.textContent = 'Generating prediction...';
  try {
    const response = await fetch(`${API_BASE}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(buildBackendPayload(results, null))
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || 'Prediction failed.');
    if (statusEl) statusEl.textContent = `Predicted target score: ${body.predicted_target_score}`;
  } catch (error) {
    if (statusEl) statusEl.textContent = `Prediction failed: ${error.message}`;
  }
}

async function predictExternalModelsFromLatestAssessment() {
  const statusEl = getModelStatusEl();
  if (!results) {
    if (statusEl) statusEl.textContent = 'No assessment results available for external prediction.';
    return;
  }

  if (statusEl) statusEl.textContent = 'Running external model predictions...';
  try {
    const response = await fetch(`${API_BASE}/external/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(buildBackendPayload(results, null))
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || 'External prediction failed.');

    const score = body.predicted_score;
    const risk = body.risk_assessment?.predicted_label || 'Unknown';
    const grade = body.grade_classification?.predicted_grade || 'Unknown';
    if (statusEl) statusEl.textContent = `External models -> Score: ${score}, Risk: ${risk}, Grade: ${grade}`;
  } catch (error) {
    if (statusEl) statusEl.textContent = `External prediction failed: ${error.message}`;
  }
}

async function importKaggleDataFromUI() {
  const statusEl = getModelStatusEl();
  const csvInput = document.getElementById('kaggle-csv-file');
  const mapInput = document.getElementById('kaggle-map-file');
  const csvFile = csvInput && csvInput.files ? csvInput.files[0] : null;
  const mappingFile = mapInput && mapInput.files ? mapInput.files[0] : null;

  if (!csvFile || !mappingFile) {
    if (statusEl) statusEl.textContent = 'Select both a CSV file and mapping JSON file.';
    return;
  }

  const formData = new FormData();
  formData.append('csv_file', csvFile);
  formData.append('mapping_file', mappingFile);

  if (statusEl) statusEl.textContent = 'Importing Kaggle rows...';

  try {
    const response = await fetch(`${API_BASE}/import-kaggle`, {
      method: 'POST',
      body: formData
    });

    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || 'Kaggle import failed.');

    const imported = body.imported_rows ?? 0;
    const skipped = body.skipped_rows ?? 0;
    if (statusEl) statusEl.textContent = `Imported ${imported} rows, skipped ${skipped}.`;
  } catch (error) {
    if (statusEl) statusEl.textContent = `Kaggle import failed: ${error.message}`;
  }
}

// ========== RESULT COMPUTATION ==========
function computeResults() {
  const bySkill = {};
  SKILLS.forEach(s => { bySkill[s.id] = { correct: 0, total: 0, times: [], errors: { easy: 0, med: 0, hard: 0 } }; });

  answers.forEach(a => {
    const sk = bySkill[a.skill];
    sk.total++;
    if (a.correct) sk.correct++;
    else sk.errors[a.diff]++;
    sk.times.push(a.time);
  });

  const skillScores = {};
  Object.keys(bySkill).forEach(id => {
    const sk = bySkill[id];
    if (sk.total === 0) return;
    const acc = sk.correct / sk.total;
    const avgTime = sk.times.reduce((a, b) => a + b, 0) / sk.times.length;
    const timeScore = Math.max(0, 1 - (avgTime / 25));
    skillScores[id] = {
      acc: Math.round(acc * 100),
      avgTime: Math.round(avgTime),
      score: Math.round((acc * 0.7 + timeScore * 0.3) * 100),
      errors: sk.errors,
      total: sk.total,
      correct: sk.correct
    };
  });

  const overall = Object.values(skillScores);
  const overallScore = overall.length ? Math.round(overall.reduce((a, b) => a + b.score, 0) / overall.length) : 0;
  const totalCorrect = answers.filter(a => a.correct).length;
  const totalAns = answers.length;
  const avgTime = totalAns ? Math.round(answers.reduce((a, b) => a + b.time, 0) / totalAns) : 0;

  return { skillScores, overallScore, totalCorrect, totalAns, avgTime, answers };
}

// ========== DASHBOARD ==========
function buildDashboard() {
  if (!results) { loadDemoData(); return; }
  const r = results;

  document.getElementById('m-score').textContent = r.overallScore;
  document.getElementById('m-acc').textContent = Math.round((r.totalCorrect / r.totalAns) * 100) + '%';
  document.getElementById('m-time').textContent = r.avgTime + 's';
  document.getElementById('m-qs').textContent = r.totalAns;

  buildSkillBreakdown(r.skillScores);
  buildRadar(r.skillScores);
  buildTimeChart(r.answers);
  buildErrorAnalysis(r.skillScores);
  buildAIInsights(r);
}

function buildSkillBreakdown(skillScores) {
  const el = document.getElementById('skill-breakdown');
  const colors = { math: '#378ADD', logic: '#7F77DD', aptitude: '#BA7517', problem: '#1D9E75' };
  el.innerHTML = Object.entries(skillScores).map(([id, sc]) => {
    const skill = SKILLS.find(s => s.id === id);
    return `<div class="breakdown-row">
      <div class="breakdown-label">${skill.icon} ${skill.name.split(' ')[0]}</div>
      <div class="breakdown-bar-wrap">
        <div class="breakdown-bar-fill" style="width:${sc.score}%; background:${colors[id]};"></div>
      </div>
      <div class="breakdown-pct">${sc.score}</div>
    </div>`;
  }).join('');
}

function buildRadar(skillScores) {
  if (radarChart) { radarChart.destroy(); radarChart = null; }
  const labels = Object.keys(skillScores).map(id => SKILLS.find(s => s.id === id).name.split(' ')[0]);
  const data = Object.values(skillScores).map(s => s.score);
  const ctx = document.getElementById('radarChart');
  if (!ctx) return;
  radarChart = new Chart(ctx, {
    type: 'radar',
    data: {
      labels,
      datasets: [{
        label: 'Score',
        data,
        backgroundColor: 'rgba(29,158,117,0.15)',
        borderColor: '#1D9E75',
        pointBackgroundColor: '#1D9E75',
        pointRadius: 5,
        pointHoverRadius: 7
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: { legend: { display: false } },
      scales: {
        r: {
          min: 0,
          max: 100,
          ticks: { stepSize: 25, font: { size: 10 } },
          pointLabels: { font: { size: 12, weight: '500' } }
        }
      }
    }
  });
}

function buildTimeChart(answers) {
  if (timeChart) { timeChart.destroy(); timeChart = null; }
  const colors = { math: '#378ADD', logic: '#7F77DD', aptitude: '#BA7517', problem: '#1D9E75' };
  const ctx = document.getElementById('timeChart');
  if (!ctx) return;
  const labels = answers.map((_, i) => 'Q' + (i + 1));
  const data = answers.map(a => a.time);
  const bgs = answers.map(a => colors[a.skill] + 'CC');
  timeChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Time (s)',
        data,
        backgroundColor: bgs,
        borderRadius: 5,
        borderSkipped: false
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: {
          beginAtZero: true,
          max: 32,
          ticks: { callback: v => v + 's', font: { size: 11 } }
        },
        x: {
          ticks: { font: { size: 10 }, autoSkip: false, maxRotation: 0 }
        }
      }
    }
  });
}

function buildErrorAnalysis(skillScores) {
  const el = document.getElementById('error-analysis');
  const rows = Object.entries(skillScores).map(([id, sc]) => {
    const skill = SKILLS.find(s => s.id === id);
    const total = sc.errors.easy + sc.errors.med + sc.errors.hard;
    if (total === 0) {
      return `<div class="breakdown-row"><span class="muted">${skill.icon} ${skill.name}: No errors — perfect score!</span></div>`;
    }
    return `<div class="breakdown-row">
      <div class="breakdown-label">${skill.icon} ${skill.name.split(' ')[0]}</div>
      <div style="flex:1; display:flex; gap:6px; flex-wrap:wrap; align-items:center;">
        ${sc.errors.easy > 0 ? `<span class="diff diff-easy">${sc.errors.easy} easy</span>` : ''}
        ${sc.errors.med > 0 ? `<span class="diff diff-med">${sc.errors.med} medium</span>` : ''}
        ${sc.errors.hard > 0 ? `<span class="diff diff-hard">${sc.errors.hard} hard</span>` : ''}
        <span class="muted">(${sc.correct}/${sc.total} correct)</span>
      </div>
    </div>`;
  }).join('');
  el.innerHTML = rows || '<p class="muted">No data yet.</p>';
}

function buildAIInsights(r) {
  const el = document.getElementById('ai-insights-section');
  el.innerHTML = `<div class="ai-response">${formatAIText(buildLocalInsightText(r))}</div>`;
}

// ========== RECOMMENDATIONS ==========
function buildRecommendations() {
  if (!results) return;
  document.getElementById('recs-empty').classList.add('hidden');
  document.getElementById('recs-content').classList.remove('hidden');
  const el = document.getElementById('recs-plan');
  el.innerHTML = `<div class="card"><div class="ai-response">${formatAIText(buildLocalPlanText(results))}</div></div>`;
}

// ========== LOCAL INSIGHT ENGINE ==========
function buildInsightPrompt(r) {
  const details = Object.entries(r.skillScores).map(([id, sc]) => {
    const skill = SKILLS.find(s => s.id === id);
    return `${skill.name}: score=${sc.score}/100, accuracy=${sc.acc}%, avg_time=${sc.avgTime}s, errors_easy=${sc.errors.easy}, errors_medium=${sc.errors.med}, errors_hard=${sc.errors.hard}`;
  }).join('\n');
  return `You are an expert academic performance analyst. A student completed a multi-skill assessment. Here are their results:\n\n${details}\n\nOverall score: ${r.overallScore}/100, Total accuracy: ${Math.round((r.totalCorrect / r.totalAns) * 100)}%, Average response time: ${r.avgTime}s\n\nProvide a concise analysis (3-4 short paragraphs) covering:\n1. Their strongest and weakest skill areas\n2. What their error patterns (easy/medium/hard errors) reveal about their knowledge gaps vs. test-taking strategy\n3. How their response times compare across skills and what this means\n4. One key insight or pattern you noticed\n\nBe specific, encouraging, and actionable. Do not use markdown headers, just flowing paragraphs.`;
}

function buildPlanPrompt(r) {
  const details = Object.entries(r.skillScores).map(([id, sc]) => {
    const skill = SKILLS.find(s => s.id === id);
    return `${skill.name}: score=${sc.score}/100, accuracy=${sc.acc}%, errors_easy=${sc.errors.easy}, errors_med=${sc.errors.med}, errors_hard=${sc.errors.hard}`;
  }).join('\n');
  return `You are an expert personalized learning coach. A student completed a skills assessment:\n\n${details}\n\nCreate a structured 4-week improvement plan. For each skill (worst-performing first), provide:\n- 2-3 specific exercises or practice techniques\n- A daily time recommendation\n- 1-2 specific topics to focus on based on their error types\n- 1 resource type (e.g., "practice problem sets", "video tutorials", "flashcards")\n\nAlso add a final section with 3 general study strategies based on their performance patterns.\n\nFormat clearly with skill names as labels (not markdown), short bullets, and practical specific advice. Keep it motivating. Maximum 400 words.`;
}

function buildLocalInsightText(r) {
  const ranked = Object.entries(r.skillScores)
    .map(([id, s]) => ({ id, ...s, skill: SKILLS.find(x => x.id === id)?.name || id }))
    .sort((a, b) => b.score - a.score);
  const strongest = ranked[0];
  const weakest = ranked[ranked.length - 1];
  const overall = Math.round((r.totalCorrect / r.totalAns) * 100);
  const slowest = [...ranked].sort((a, b) => b.avgTime - a.avgTime)[0];

  return [
    `Overall performance is ${r.overallScore}/100 with ${overall}% accuracy. Strongest area: ${strongest.skill} (${strongest.score}). Weakest area: ${weakest.skill} (${weakest.score}).`,
    `The biggest score gap is between ${strongest.skill} and ${weakest.skill}, which suggests targeted practice on ${weakest.skill} can quickly raise your total score.`,
    `Response-time pattern shows ${slowest.skill} is taking the longest on average (${slowest.avgTime}s), so improving speed there should increase both confidence and marks.`,
    `Focus this week: do 20-30 minutes daily on ${weakest.skill}, review medium/hard errors first, and end each session with a timed mini-quiz.`
  ].join('\n\n');
}

function buildLocalPlanText(r) {
  const ranked = Object.entries(r.skillScores)
    .map(([id, s]) => ({ id, ...s, skill: SKILLS.find(x => x.id === id)?.name || id }))
    .sort((a, b) => a.score - b.score);

  const blocks = ranked.slice(0, 3).map((s, idx) => {
    const mins = s.score < 60 ? 40 : 30;
    return `Week ${idx + 1}: ${s.skill}\n- Daily ${mins} minutes focused practice\n- Solve 8-12 mixed questions with timer\n- Rework all medium/hard mistakes from previous attempts\n- Quick review checklist before finishing session`;
  });

  blocks.push('General strategy\n- Track accuracy and time together, not score alone\n- Practice in short daily sessions instead of long irregular sessions\n- End each week with one timed mock and error review');
  return blocks.join('\n\n');
}

function formatAIText(text) {
  return text.split('\n').filter(l => l.trim()).map(line => {
    const trimmed = line.trim();
    if (trimmed.startsWith('- ') || trimmed.startsWith('• ')) {
      return `<li>${trimmed.slice(2)}</li>`;
    }
    if (trimmed.endsWith(':') && trimmed.length < 60) {
      return `<h4>${trimmed}</h4>`;
    }
    return `<p>${trimmed}</p>`;
  }).join('');
}

// ========== DEMO DATA ==========
function loadDemoData() {
  results = {
    skillScores: {
      math: { score: 72, acc: 80, avgTime: 18, errors: { easy: 0, med: 1, hard: 0 }, total: 5, correct: 4 },
      logic: { score: 55, acc: 60, avgTime: 22, errors: { easy: 1, med: 1, hard: 0 }, total: 5, correct: 3 },
      aptitude: { score: 84, acc: 80, avgTime: 14, errors: { easy: 0, med: 1, hard: 0 }, total: 5, correct: 4 },
      problem: { score: 48, acc: 40, avgTime: 26, errors: { easy: 1, med: 1, hard: 1 }, total: 5, correct: 2 }
    },
    overallScore: 65,
    totalCorrect: 13,
    totalAns: 20,
    avgTime: 20,
    answers: Array.from({ length: 20 }, (_, i) => ({
      skill: ['math', 'math', 'math', 'math', 'math', 'logic', 'logic', 'logic', 'logic', 'logic', 'aptitude', 'aptitude', 'aptitude', 'aptitude', 'aptitude', 'problem', 'problem', 'problem', 'problem', 'problem'][i],
      correct: i % 3 !== 2,
      time: 12 + Math.round(Math.random() * 18),
      diff: ['easy', 'med', 'hard'][i % 3]
    }))
  };
  buildDashboard();
}

// ========== INIT ==========
renderSkillSelector();
