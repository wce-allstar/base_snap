// ==========================================
// AgenticEval Frontend JS Logic
// ==========================================

// --- APP STATE ---
let activeTab = "dashboard";
let students = [];
let rubricsList = [];
let currentStudentIndex = 0;
let currentQuestionId = "q1"; 
let uploadProgressInterval = null;
let apiBaseUrl = (typeof window !== 'undefined' && window.location && window.location.origin && window.location.origin !== "null" && !window.location.origin.startsWith("file:"))
  ? window.location.origin
  : "http://localhost:8000";
let selectedDifficulty = "medium"; // 'easy' | 'medium' | 'hard'

const difficultyHints = {
  easy: '<i class="fa-solid fa-circle-info text-success"></i> <strong>Lenient grading:</strong> rewards conceptual grasp, grants generous partial marks, forgives minor syntax bugs or missing edge cases.',
  medium: '<i class="fa-solid fa-circle-info text-warning"></i> <strong>Standard grading:</strong> balanced academic evaluation against rubric criteria with standard proportional deductions.',
  hard: '<i class="fa-solid fa-circle-info text-danger"></i> <strong>Strict grading:</strong> strict penalty for missing edge cases (duplicates, memory limits) or informal proofs; requires high precision.'
};

const modelAnswerRubric = {
  q1: {
    question: "Define a Binary Search Tree (BST) and write its search complexity. Explain why search complexity can degenerate to O(N) and how height-balanced trees (AVL/Red-Black) solve this.",
    modelAnswer: `1. Definition: A binary tree where each node holds a key, and for any node, all keys in its left subtree are less than the node's key, and all keys in its right subtree are greater than the node's key. Both subtrees must also be BSTs.
2. Search Complexity: Best/Average case is O(log N) where N is number of nodes. Worst case is O(N).
3. Degeneration: Occurs when elements are inserted in a sorted or nearly-sorted order, causing the tree to grow linearly (skewed tree) and lose branching structure.
4. Balancing Solution: Height-balanced trees like AVL enforce balance by maintaining |Height(Left) - Height(Right)| <= 1. AVL/RB trees perform rotations (Single/Double) during insertions/deletions to keep the tree height bounded to O(log N), maintaining log-time searches.`,
    rubricPoints: [
      { id: "node-prop", text: "BST property: Left < Node < Right defined recursively.", maxMarks: 3, weight: "30%" },
      { id: "complexity", text: "Search complexities defined: average/best O(log N), worst O(N).", maxMarks: 2, weight: "20%" },
      { id: "degeneration", text: "Reason for degeneration explained (skewed tree, sorted inputs).", maxMarks: 2, weight: "20%" },
      { id: "balancing", text: "Balanced trees: AVL/RB balancing using height constraints and rotations.", maxMarks: 3, weight: "30%" }
    ]
  },
  q2: {
    question: "Write the pseudo-code for inserting a node in a BST. Explain the algorithm's time and space complexity.",
    modelAnswer: `Pseudo-code (Recursive):
Node insert(Node root, int val) {
    if (root == null) return new Node(val);
    if (val < root.key) root.left = insert(root.left, val);
    else if (val > root.key) root.right = insert(root.right, val);
    return root;
}
Complexities:
1. Time Complexity: O(h), where h is the height of the tree. In balanced trees h = O(log N), in skewed trees h = O(N).
2. Space Complexity: O(h) auxiliary space for call stacks. iterative version is O(1) space.`,
    rubricPoints: [
      { id: "code-struct", text: "Pseudo-code logic structure: base case (null check) and recursive/iterative routing.", maxMarks: 4, weight: "40%" },
      { id: "duplicate-check", text: "Duplicate handling or validation branching.", maxMarks: 1, weight: "10%" },
      { id: "time-comp", text: "Time complexity O(h) or O(log N) explained.", maxMarks: 2, weight: "20%" },
      { id: "space-comp", text: "Space complexity O(h) recursive stack explained.", maxMarks: 3, weight: "30%" }
    ]
  }
};

// --- DOM ELEMENTS ---
const elements = {
  navLinks: document.querySelectorAll('.nav-link'),
  tabViews: document.querySelectorAll('.tab-view'),
  pageTitle: document.getElementById('page-title'),
  queueTableBody: document.getElementById('queue-table-body'),
  queueSearch: document.getElementById('queue-search'),
  queueStatusFilter: document.getElementById('queue-status-filter'),
  statEvaluated: document.getElementById('stat-evaluated'),
  statPending: document.getElementById('stat-pending'),
  pendingBadge: document.getElementById('pending-badge'),
  batchSelector: document.getElementById('batch-selector'),

  // Login
  loginScreen: document.getElementById('login-screen'),
  appWrapper: document.getElementById('app-wrapper'),
  loginForm: document.getElementById('login-form'),
  loginEmail: document.getElementById('login-email'),
  loginPassword: document.getElementById('login-password'),
  togglePasswordBtn: document.getElementById('toggle-password-btn'),
  loginErrorMsg: document.getElementById('login-error-msg'),
  btnLoginText: document.getElementById('btn-login-text'),
  logoutSidebarBtn: document.getElementById('logout-sidebar-btn'),

  // Ingestion
  dropZone: document.getElementById('drop-zone'),
  fileInput: document.getElementById('file-input'),
  loadSampleBtn: document.getElementById('load-sample-btn'),
  qpFileInput: document.getElementById('qp-file-input'),
  qpList: document.getElementById('qp-list'),
  evaluationQpSelect: document.getElementById('evaluation-qp-select'),
  uploadProgressPanel: document.getElementById('upload-progress-panel'),
  uploadItemsContainer: document.getElementById('upload-items-container'),
  cancelUploadBtn: document.getElementById('cancel-upload-btn'),
  diffBtns: document.querySelectorAll('.diff-btn'),
  diffHint: document.getElementById('difficulty-hint'),

  // Workspace (v2 evaluation workspace)
  ws2StudentName: document.getElementById('ws2StudentName'),
  ws2StudentRoll: document.getElementById('ws2StudentRoll')
};

// --- INITIALIZATION ---
document.addEventListener("DOMContentLoaded", () => {
  initNavigation();
  initLoginControls();
  initUploadLogic();
  initWorkspaceLogic();
  
  // Initial DB sync load
  syncDatabaseState().then(() => {
    renderQueueTable();
    updateHeaderStats();
  });
});

// --- BACKEND SYNC HELPERS ---
async function syncDatabaseState() {
  try {
    const queueRes = await fetch(`${apiBaseUrl}/api/queue`);
    students = await queueRes.json();

    const rubricRes = await fetch(`${apiBaseUrl}/api/rubrics`);
    rubricsList = await rubricRes.json();

    await loadQuestionPapers();
  } catch (error) {
    console.error("LMS Sync failed. Falling back to local offline mock engines.", error);
  }
}

async function loadQuestionPapers() {
  try {
    const res = await fetch(`${apiBaseUrl}/api/question-papers`);
    const data = await res.json();
    questionPapers = (data && data.questionPapers) || [];
    renderQuestionPaperList();
  } catch (error) {
    console.error("Question paper sync failed.", error);
  }
}

function renderQuestionPaperList() {
  if (!elements.qpList) return;

  const currentSelection = elements.evaluationQpSelect ?
    elements.evaluationQpSelect.value : "";

  if (elements.evaluationQpSelect) {
    const options = questionPapers.map(p =>
      `<option value="${p.id}">${esc(p.name)}</option>`
    ).join("");
    elements.evaluationQpSelect.innerHTML = `<option value="">Select a question paper...</option>${options}`;
    elements.evaluationQpSelect.value = currentSelection;
    if (questionPapers.length && !currentSelection) {
      elements.evaluationQpSelect.selectedIndex = 1;
    }
  }

  if (questionPapers.length === 0) {
    elements.qpList.innerHTML = `<p class="text-muted small">No question paper uploaded yet.</p>`;
    return;
  }

  elements.qpList.innerHTML = questionPapers.map(p => `
    <div class="qp-item">
      <span class="qp-item-icon"><i class="fa-solid fa-file-circle-check"></i></span>
      <div class="qp-item-info">
        <strong>${esc(p.name)}</strong>
        <span class="small text-muted">${p.fileName} · ${p.uploadedAt || "uploaded"}</span>
      </div>
      <span class="badge success">Ready</span>
    </div>
  `).join("");
}

async function handleQuestionPaperUpload(filesList) {
  for (let i = 0; i < filesList.length; i++) {
    const file = filesList[i];
    try {
      const formData = new FormData();
      formData.append('file', file);
      await fetch(`${apiBaseUrl}/api/question-papers/upload`, {
        method: 'POST',
        body: formData
      });
    } catch (err) {
      console.error(err);
    }
  }
  await loadQuestionPapers();
}

// --- SECURE LOGIN CONTROLS ---
function initLoginControls() {
  elements.togglePasswordBtn.addEventListener('click', () => {
    const isPassword = elements.loginPassword.getAttribute('type') === 'password';
    elements.loginPassword.setAttribute('type', isPassword ? 'text' : 'password');
    elements.togglePasswordBtn.innerHTML = isPassword ? `<i class="fa-regular fa-eye-slash"></i>` : `<i class="fa-regular fa-eye"></i>`;
  });

  elements.logoutSidebarBtn.addEventListener('click', () => {
    elements.loginScreen.style.display = "flex";
    elements.appWrapper.style.display = "none";
    elements.loginEmail.value = "";
    elements.loginPassword.value = "";
    elements.loginErrorMsg.style.display = "none";
  });
}

function showLoginError(message) {
  elements.loginErrorMsg.querySelector('span').textContent = message;
  elements.loginErrorMsg.style.display = "flex";
}

async function handleLoginSubmit(event) {
  event.preventDefault();
  
  const email = elements.loginEmail.value.trim();
  const password = elements.loginPassword.value;
  
  if (!email.includes("@")) {
    showLoginError("Please enter a valid university email address.");
    return;
  }
  if (password.length < 6) {
    showLoginError("Password must be at least 6 characters.");
    return;
  }
  
  elements.loginErrorMsg.style.display = "none";
  elements.btnLoginText.disabled = true;
  elements.btnLoginText.innerHTML = `<i class="fa-solid fa-circle-notch pulsing"></i> <span>Authenticating credentials...</span>`;

  try {
    const response = await fetch(`${apiBaseUrl}/api/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    const result = await response.json();
    
    if (result.status === 'success') {
      // Complete transition
      elements.loginScreen.style.display = "none";
      elements.appWrapper.style.display = "flex";
      elements.btnLoginText.disabled = false;
      elements.btnLoginText.innerHTML = `<span>Log In to Workspace</span> <i class="fa-solid fa-arrow-right"></i>`;
      
      await syncDatabaseState();
      switchTab('dashboard');
    } else {
      throw new Error(result.message);
    }
  } catch (err) {
    elements.btnLoginText.disabled = false;
    elements.btnLoginText.innerHTML = `<span>Log In to Workspace</span> <i class="fa-solid fa-arrow-right"></i>`;
    showLoginError("Could not reach the server. Make sure the backend is running (python server.py) and open http://localhost:8000.");
  }
}

function simulateSSOLogin(provider) {
  const email = provider === 'Google Workspace' ? "rao.d@sit-edu.in" : "drao@shibboleth.sit-edu.in";
  elements.loginEmail.value = email;
  elements.loginPassword.value = "dummySSOpass123";
  
  const event = new Event('submit');
  handleLoginSubmit(event);
}

window.handleLoginSubmit = handleLoginSubmit;
window.simulateSSOLogin = simulateSSOLogin;

// --- NAVIGATION SYSTEM ---
function initNavigation() {
  elements.navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const tab = link.getAttribute('data-tab');
      switchTab(tab);
    });
  });
}

function switchTab(tab) {
  activeTab = tab;
  
  elements.navLinks.forEach(link => {
    link.classList.toggle('active', link.getAttribute('data-tab') === tab);
  });

  elements.tabViews.forEach(view => {
    view.classList.toggle('active', view.getAttribute('id') === `${tab}-view`);
  });

  const titles = {
    dashboard: "Dashboard",
    upload: "Upload Answer Scripts",
    workspace: "Evaluation Workspace"
  };

  elements.pageTitle.innerText = titles[tab] || "Dashboard";

  if (tab === 'workspace') {
    loadStudentIntoWorkspace(currentStudentIndex);
  }
}

// --- DASHBOARD QUEUE ---
function renderQueueTable() {
  const searchTerm = elements.queueSearch.value.toLowerCase();
  const statusFilter = elements.queueStatusFilter ? elements.queueStatusFilter.value : "all";
  elements.queueTableBody.innerHTML = "";

  const filtered = students.filter(s => {
    const matchesSearch = s.id.toLowerCase().includes(searchTerm) || s.name.toLowerCase().includes(searchTerm);
    const checked = s.status === 'Approved' || s.status === 'Flagged';
    const matchesStatus = statusFilter === 'all' ||
      (statusFilter === 'checked' && checked) ||
      (statusFilter === 'unchecked' && !checked);
    return matchesSearch && matchesStatus;
  });

  if (filtered.length === 0) {
    elements.queueTableBody.innerHTML = `<tr><td colspan="8" class="text-muted" style="text-align: center; padding: 2rem;">No students found in active queue</td></tr>`;
    return;
  }

  filtered.forEach((student, index) => {
    const originalIndex = students.findIndex(s => s.id === student.id);
    const row = document.createElement('tr');
    
    let badgeClass = "warning";
    if (student.status === 'Approved') badgeClass = "success";
    if (student.status === 'Flagged') badgeClass = "danger";

    let confidenceClass = "success";
    if (student.confidence < 80) confidenceClass = "warning";

    let biasIcon = `<i class="fa-solid fa-circle-check text-success"></i> Consistent`;
    if (student.selfCheck.includes("Flagged")) {
      biasIcon = `<i class="fa-solid fa-triangle-exclamation text-danger"></i> Audit Alert`;
    }

    const diff = student.difficulty || 'medium';
    let diffIcon = '🟡';
    let diffText = 'Medium';
    if (diff === 'easy') { diffIcon = '🟢'; diffText = 'Easy'; }
    else if (diff === 'hard') { diffIcon = '🔴'; diffText = 'Hard'; }
    const diffBadge = `<span class="badge-difficulty ${diff}">${diffIcon} ${diffText}</span>`;

    const totalMax = student.maxScore || Object.values(student.questions || {}).reduce((acc, q) => acc + (q.maxScore || 10), 0) || 20;
    const currentScore = student.aiScore !== undefined ? student.aiScore : Object.values(student.questions || {}).reduce((acc, q) => acc + (q.score || 0), 0);

    row.innerHTML = `
      <td><strong>${student.id}</strong></td>
      <td>${student.name}</td>
      <td class="text-muted"><i class="fa-regular fa-file-pdf"></i> ${student.format}</td>
      <td>${diffBadge}</td>
      <td><strong>${currentScore}</strong> / ${totalMax}</td>
      <td><span class="badge ${confidenceClass}">${student.confidence}%</span></td>
      <td class="text-muted" style="max-width: 180px;">${student.questionPaper ? esc(student.questionPaper) : '<span class="text-muted">—</span>'}</td>
      <td>
        <span class="status-badge ${badgeClass}">${student.status}</span>
        <div style="font-size: 0.65rem; margin-top: 2px;">${biasIcon}</div>
      </td>
      <td>
        <button class="btn btn-outline btn-xs" onclick="openStudentWorkspace(${originalIndex})">
          <i class="fa-solid fa-square-poll-horizontal"></i> Grade
        </button>
      </td>
    `;
    elements.queueTableBody.appendChild(row);
  });
}

elements.queueSearch.addEventListener('input', renderQueueTable);
elements.queueStatusFilter.addEventListener('change', renderQueueTable);

function updateHeaderStats() {
  const evaluatedCount = students.filter(s => s.status === 'Approved').length;
  const pendingCount = students.filter(s => s.status !== 'Approved').length;
  const totalCount = students.length;

  elements.statEvaluated.innerText = `${evaluatedCount}/${totalCount}`;
  elements.statPending.innerText = pendingCount;
  elements.pendingBadge.innerText = pendingCount;
  
  const percentage = totalCount > 0 ? Math.round((evaluatedCount / totalCount) * 100) : 0;
  const fill = document.querySelector('.metric-card .progress-bar-fill');
  const percentText = document.querySelector('.metric-card .progress-percentage');
  
  if (fill) fill.style.width = `${percentage}%`;
  if (percentText) percentText.innerText = `${percentage}%`;
}


// --- UPLOAD PIPELINE IMPLEMENTATION ---
function initUploadLogic() {
  // Difficulty selector buttons
  elements.diffBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const diff = btn.getAttribute('data-difficulty');
      setUploadDifficulty(diff);
    });
  });

  // Drag and drop support for answer sheets
  if (elements.dropZone) {
    ['dragenter', 'dragover'].forEach(eventName => {
      elements.dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        elements.dropZone.classList.add('drag-active');
      }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      elements.dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        elements.dropZone.classList.remove('drag-active');
      }, false);
    });

    elements.dropZone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files && files.length > 0) {
        handleFilesUpload(files);
      }
    });
  }

  // Drag and drop support for question papers
  const qpDropZone = document.getElementById('qp-drop-zone');
  if (qpDropZone) {
    ['dragenter', 'dragover'].forEach(eventName => {
      qpDropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        qpDropZone.classList.add('drag-active');
      }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      qpDropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        qpDropZone.classList.remove('drag-active');
      }, false);
    });

    qpDropZone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files && files.length > 0) {
        handleQuestionPaperUpload(files);
      }
    });
  }

  // Cancel upload button handler
  if (elements.cancelUploadBtn) {
    elements.cancelUploadBtn.addEventListener('click', () => {
      if (uploadProgressInterval) clearInterval(uploadProgressInterval);
      elements.uploadProgressPanel.style.display = "none";
    });
  }

  elements.fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFilesUpload(e.target.files);
    }
  });

  elements.qpFileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleQuestionPaperUpload(e.target.files);
      e.target.value = "";
    }
  });

  elements.loadSampleBtn.addEventListener('click', () => {
    simulateOfflineUpload();
  });
}

function setUploadDifficulty(diff) {
  selectedDifficulty = diff;
  elements.diffBtns.forEach(btn => {
    const bDiff = btn.getAttribute('data-difficulty');
    const isActive = bDiff === diff;
    btn.classList.toggle('active', isActive);
    btn.classList.toggle(bDiff, isActive);
  });
  if (elements.diffHint && difficultyHints[diff]) {
    elements.diffHint.innerHTML = difficultyHints[diff];
  }
}

async function handleFilesUpload(filesList) {
  elements.uploadProgressPanel.style.display = "block";
  elements.uploadItemsContainer.innerHTML = "";

  for (let i = 0; i < filesList.length; i++) {
    const file = filesList[i];
    const item = document.createElement('div');
    item.className = "upload-item";
    item.id = `upload-item-${i}`;
    item.innerHTML = `
      <div class="agent-avatar extractor-bg" id="upload-icon-${i}"><i class="fa-solid fa-file-arrow-up"></i></div>
      <div class="upload-item-details">
        <div class="upload-item-name">${file.name}</div>
        <div class="upload-item-size" id="upload-status-${i}">Uploading document...</div>
      </div>
      <div class="upload-item-progress">
        <div class="progress-bar-bg">
          <div class="progress-bar-fill" id="upload-bar-${i}" style="width: 20%;"></div>
        </div>
      </div>
      <div id="upload-badge-${i}" class="badge info">Uploading</div>
    `;
    elements.uploadItemsContainer.appendChild(item);

    try {
      // 1. Upload script file to REST backend
      const formData = new FormData();
      formData.append('file', file);
      formData.append('questionPaperId', elements.evaluationQpSelect.value || "");
      formData.append('difficulty', selectedDifficulty);
      
      const uploadRes = await fetch(`${apiBaseUrl}/api/upload`, {
        method: 'POST',
        body: formData
      });
      const uploadResult = await uploadRes.json();
      
      if (uploadResult.status === 'success') {
        const studentId = uploadResult.studentId;
        const bar = document.getElementById(`upload-bar-${i}`);
        const badge = document.getElementById(`upload-badge-${i}`);
        const statusText = document.getElementById(`upload-status-${i}`);
        const avatar = document.getElementById(`upload-icon-${i}`);
        
        // 2. Trigger multi-agent pipeline evaluate
        statusText.innerText = `Evaluating with [${selectedDifficulty.toUpperCase()}] rigor...`;
        bar.style.width = "50%";
        badge.innerText = "Agent Evaluator";
        
        const evalRes = await fetch(`${apiBaseUrl}/api/evaluate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            studentId,
            questionPaperId: elements.evaluationQpSelect.value || "",
            difficulty: selectedDifficulty
          })
        });
        const evalResult = await evalRes.json();
        
        if (evalResult.status === 'success') {
          bar.style.width = "100%";
          badge.innerText = "Done";
          badge.className = "badge success";
          statusText.innerHTML = `<span class="text-success"><i class="fa-solid fa-circle-check"></i> Analysis complete. Roll: ${studentId}</span>`;
          avatar.className = "agent-avatar checker-bg";
          avatar.innerHTML = `<i class="fa-solid fa-scale-balanced"></i>`;
        }
      }
    } catch (err) {
      console.error(err);
      const statusText = document.getElementById(`upload-status-${i}`);
      statusText.innerHTML = `<span class="text-danger">Evaluation pipeline connection failure</span>`;
    }
  }

  // Reload database queue
  await syncDatabaseState();
  renderQueueTable();
  updateHeaderStats();
}

// Fallback loader offline
function simulateOfflineUpload() {
  elements.uploadProgressPanel.style.display = "block";
  elements.uploadItemsContainer.innerHTML = "";
  
  const fileSamples = [
    { name: "Roll_85_Karan_Mathur_Booklet.pdf", size: "4.8 MB" },
    { name: "Roll_118_Tanvi_Desai_Booklet.pdf", size: "3.2 MB" }
  ];

  fileSamples.forEach((file, index) => {
    const item = document.createElement('div');
    item.className = "upload-item";
    item.id = `upload-item-${index}`;
    item.innerHTML = `
      <div class="agent-avatar extractor-bg" id="upload-icon-${index}"><i class="fa-solid fa-file"></i></div>
      <div class="upload-item-details">
        <div class="upload-item-name">${file.name}</div>
        <div class="upload-item-size" id="upload-status-${index}">Uploading... ${file.size}</div>
      </div>
      <div class="upload-item-progress">
        <div class="progress-bar-bg">
          <div class="progress-bar-fill" id="upload-bar-${index}" style="width: 0%;"></div>
        </div>
      </div>
      <div id="upload-badge-${index}" class="badge info">0%</div>
    `;
    elements.uploadItemsContainer.appendChild(item);
  });

  let step = 0;
  if (uploadProgressInterval) clearInterval(uploadProgressInterval);
  
  uploadProgressInterval = setInterval(async () => {
    step += 10;
    
    for (let i = 0; i < fileSamples.length; i++) {
      const bar = document.getElementById(`upload-bar-${i}`);
      const badge = document.getElementById(`upload-badge-${i}`);
      const statusText = document.getElementById(`upload-status-${i}`);
      
      const progress = Math.min(100, step - (i * 20));
      if (progress > 0) {
        bar.style.width = `${progress}%`;
        badge.innerText = `${progress}%`;
        
        if (progress === 30) statusText.innerText = "OCR Extractor transcription...";
        if (progress === 60) statusText.innerText = "Semantic Rubric Mapper matching...";
        if (progress === 90) statusText.innerText = "Grader feedback justification...";
        
        if (progress === 100) {
          badge.className = "badge success";
          statusText.innerHTML = `<span class="text-success"><i class="fa-solid fa-circle-check"></i> Evaluation finished!</span>`;
        }
      }
    }

    if (step >= 140) {
      clearInterval(uploadProgressInterval);
      
      // Inject fallback offline entries into server db
      try {
        await fetch(`${apiBaseUrl}/api/evaluate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            studentId: "CS2026-085",
            questionPaperId: elements.evaluationQpSelect.value || "",
            difficulty: selectedDifficulty
          })
        });
      } catch (e) {}

      await syncDatabaseState();
      renderQueueTable();
      updateHeaderStats();
      setTimeout(() => {
        alert("Completed offline evaluation pipeline! Queue synchronized.");
        switchTab('dashboard');
      }, 1000);
    }
  }, 300);
}


// --- EVALUATION WORKSPACE LOGIC (v2) ---

let ws2Student = null;
let ws2Zoom = 1;

const ws2State = {
  questionStatus: {}, // qid -> 'done' | 'flagged' | null
  notes: {},          // qid -> note text
  edited: {},         // qid -> boolean
  awarded: {},        // qid -> [awarded per criterion]
  current: null       // active qid
};

const ws2 = {
  studentName: document.getElementById('ws2StudentName'),
  studentRoll: document.getElementById('ws2StudentRoll'),
  diffSelect: document.getElementById('ws2DiffSelect'),
  recheckBtn: document.getElementById('ws2RecheckBtn'),
  sheetSeat: document.getElementById('ws2SheetSeat'),
  sheetPaper: document.getElementById('ws2SheetPaper'),
  sheetPage: document.getElementById('ws2SheetPage'),
  sheetBody: document.getElementById('ws2SheetBody'),
  pageLabel: document.getElementById('ws2PageLabel'),
  zoomVal: document.getElementById('ws2ZoomVal'),
  sheet: document.getElementById('ws2Sheet'),
  sheetScroll: document.getElementById('ws2SheetScroll'),
  qNo: document.getElementById('ws2QNo'),
  qText: document.getElementById('ws2QText'),
  qMax: document.getElementById('ws2QMax'),
  qCritN: document.getElementById('ws2QCritN'),
  qScoreMax: document.getElementById('ws2QScoreMax'),
  ansToggle: document.getElementById('ws2AnsToggle'),
  studentAnswer: document.getElementById('ws2StudentAnswer'),
  rubricRows: document.getElementById('ws2RubricRows'),
  qScore: document.getElementById('ws2QScore'),
  scoreSrc: document.getElementById('ws2ScoreSrc'),
  notes: document.getElementById('ws2Notes'),
  qnav: document.getElementById('ws2QNav'),
  sheetScore: document.getElementById('ws2SheetScore'),
  sheetMax: document.getElementById('ws2SheetMax'),
  progFill: document.getElementById('ws2ProgFill'),
  reviewLabel: document.getElementById('ws2ReviewLabel'),
  status: document.getElementById('ws2Status'),
  evalScroll: document.getElementById('ws2EvalScroll'),
  btnConfirm: document.getElementById('ws2BtnConfirm'),
  btnAdjust: document.getElementById('ws2BtnAdjust'),
  btnFlag: document.getElementById('ws2BtnFlag'),
  studentIdx: document.getElementById('ws2StudentIdx'),
  prevStudentBtn: document.getElementById('ws2PrevStudent'),
  nextStudentBtn: document.getElementById('ws2NextStudent'),
  zoomIn: document.getElementById('ws2ZoomIn'),
  zoomOut: document.getElementById('ws2ZoomOut'),
  pgPrev: document.getElementById('ws2PgPrev'),
  pgNext: document.getElementById('ws2PgNext')
};

const CHECK_ICON = '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>';

function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }

function ws2QuestionIds() {
  return ws2Student ? Object.keys(ws2Student.questions) : [];
}

// Distribute a question's total score across rubric criteria based on coverage.
function deriveAwarded(qid, qData) {
  const schema = modelAnswerRubric[qid] || {
    question: `Question ${qid.replace('q', '')}`,
    rubricPoints: [
      { id: "p1", text: "Conceptual accuracy and definitions.", maxMarks: Math.ceil((qData?.maxScore || 10) * 0.4) },
      { id: "p2", text: "Structure, proof / implementation logic.", maxMarks: Math.floor((qData?.maxScore || 10) * 0.3) },
      { id: "p3", text: "Completeness and edge-case handling.", maxMarks: Math.floor((qData?.maxScore || 10) * 0.3) }
    ]
  };
  const points = schema.rubricPoints;
  const coverage = points.map(p => {
    if (qid === 'q1') {
      if (p.id === 'balancing' && qData.score < 8.5) return 'partial';
      if (p.id === 'complexity' && qData.score < 5.5) return 'missed';
    }
    if (qid === 'q2' && p.id === 'duplicate-check' && qData.score < 9.5) return 'missed';
    return 'full';
  });
  const raw = points.map((p, i) => coverage[i] === 'full' ? 1 : coverage[i] === 'partial' ? 0.5 : 0);
  const rawTotal = points.reduce((s, p, i) => s + raw[i] * p.maxMarks, 0);
  const scale = rawTotal > 0 ? qData.score / rawTotal : 0;
  const awarded = points.map((p, i) => Math.round(raw[i] * p.maxMarks * scale * 10) / 10);
  const drift = Math.round((qData.score - awarded.reduce((a, b) => a + b, 0)) * 10) / 10;
  if (drift !== 0 && awarded.length) {
    const maxIdx = awarded.indexOf(Math.max(...awarded));
    awarded[maxIdx] = Math.round((awarded[maxIdx] + drift) * 10) / 10;
  }
  return awarded;
}

function ws2AwardedTotal(qid) {
  const arr = ws2State.awarded[qid];
  if (!arr) return 0;
  return Math.round(arr.reduce((a, b) => a + b, 0) * 10) / 10;
}

function ws2RenderSheet() {
  const qid = ws2State.current;
  const qData = ws2Student.questions[qid];
  const status = ws2State.questionStatus[qid];
  const pillCls = status === 'done' ? 'confirmed' : (status === 'flagged' ? 'review' : 'suggest');
  const pillTxt = status === 'done' ? 'Confirmed' : (status === 'flagged' ? 'Review' : 'Suggested');
  const total = ws2AwardedTotal(qid);

  // Build the answer sheet viewer: show uploaded image/PDF if available, else show OCR text
  let sheetContent = '';
  const filePath = ws2Student.filePath || '';
  const fileName = filePath ? filePath.split('/').pop() : '';
  const isPdf = fileName.toLowerCase().endsWith('.pdf');
  const isImage = /\.(png|jpg|jpeg|webp|gif)$/i.test(fileName);

  if (fileName && (isPdf || isImage)) {
    const fileUrl = `${apiBaseUrl}/api/uploads/${encodeURIComponent(fileName)}`;
    if (isPdf) {
      sheetContent = `<iframe src="${fileUrl}" style="width:100%;height:520px;border:none;border-radius:6px;" title="Uploaded answer sheet PDF"></iframe>`;
    } else {
      sheetContent = `<img src="${fileUrl}" alt="Uploaded answer sheet" style="width:100%;border-radius:6px;display:block;" />`;
    }
  } else {
    // No uploaded file — display the OCR/handwriting text as before
    const displayText = qData.handwritingMock || qData.ocrText || 'No digitized answer yet.';
    sheetContent = '<div class="ws2-hand">' + esc(displayText) + '</div>';
  }

  ws2.sheetBody.innerHTML =
    '<div class="ws2-q-mark"><span class="q">' + qid.toUpperCase() + '</span>' +
    '<span class="ws2-qpts">' + total + ' <span class="ws2-of">/ ' + qData.maxScore + ' marks</span></span></div>' +
    sheetContent +
    '<div class="ws2-sheet-note"><span class="ws2-score-pill ' + pillCls + '">' + CHECK_ICON +
    ' ' + pillTxt + ' marks <b>' + total + ' / ' + qData.maxScore + '</b></span></div>';
}


function ws2RenderEval() {
  const qid = ws2State.current;
  const qData = ws2Student.questions[qid] || { score: 0, maxScore: 10, ocrText: "" };

  // Use real AI coverage from evaluation if available, else fall back to hardcoded or generic rubric
  let points;
  let questionText;

  if (qData.coverage && qData.coverage.length > 0) {
    // Real AI evaluation data is available — use actual coverage criteria
    questionText = `Question ${qid.replace('q', '')}`;
    const maxPerCrit = qData.maxScore / qData.coverage.length;
    points = qData.coverage.map((c, i) => ({
      id: `c${i}`,
      text: c.criterion,
      maxMarks: Math.round(maxPerCrit * 10) / 10,
      status: c.status
    }));
  } else {
    // No AI evaluation yet — try hardcoded schema or use generic fallback
    const schema = modelAnswerRubric[qid] || {
      question: `Question ${qid.replace('q', '')}`,
      rubricPoints: [
        { id: "p1", text: "Conceptual accuracy and definitions.", maxMarks: Math.ceil(qData.maxScore * 0.4) },
        { id: "p2", text: "Structure, proof / implementation logic.", maxMarks: Math.floor(qData.maxScore * 0.3) },
        { id: "p3", text: "Completeness and edge-case handling.", maxMarks: Math.floor(qData.maxScore * 0.3) }
      ]
    };
    questionText = schema.question;
    points = schema.rubricPoints;
  }

  const awarded = ws2State.awarded[qid] || deriveAwarded(qid, qData);
  ws2State.awarded[qid] = awarded;

  ws2.qNo.textContent = "Question " + qid.replace('q', '');
  ws2.qText.textContent = questionText;
  ws2.qMax.textContent = qData.maxScore;
  ws2.qCritN.textContent = points.length;
  ws2.qScoreMax.textContent = qData.maxScore;
  ws2.studentAnswer.textContent = qData.ocrText || "Digitized text is being processed…";

  let rows = "";
  points.forEach((p, i) => {
    const weak = awarded[i] < p.maxMarks ? '<span class="ws2-verify">Verify</span>' : '';
    rows +=
      '<div class="ws2-crit">' +
        '<div>' +
          '<div class="ws2-crit-name"><span class="ws2-crit-idx">' + (i + 1) + '</span>' + esc(p.text) + weak + '</div>' +
          '<div class="ws2-crit-note"><span class="why">Why</span>Suggested coverage from the AI grader.</div>' +
        '</div>' +
        '<div class="ws2-crit-ctrl">' +
          '<button class="ws2-stepper" data-mi="' + i + '" data-d="-1" aria-label="Decrease mark">−</button>' +
          '<div class="ws2-pts-input-wrap">' +
            '<input type="number" class="ws2-crit-input" data-mi="' + i + '" min="0" max="' + p.maxMarks + '" step="any" value="' + awarded[i] + '">' +
            '<span class="ws2-of">/ ' + p.maxMarks + '</span>' +
          '</div>' +
          '<button class="ws2-stepper" data-mi="' + i + '" data-d="1" aria-label="Increase mark">+</button>' +
        '</div>' +
      '</div>';
  });
  ws2.rubricRows.innerHTML = rows;

  // Stepper buttons (+ / -) incrementing/decrementing by 0.5 only without resetting scroll
  ws2.rubricRows.querySelectorAll(".ws2-stepper").forEach(b => {
    b.addEventListener("click", (e) => {
      e.preventDefault();
      const mi = +b.dataset.mi, d = +b.dataset.d;
      const max = points[mi].maxMarks;
      const step = 0.5;
      const newScore = Math.max(0, Math.min(max, +(awarded[mi] + d * step).toFixed(2)));
      awarded[mi] = newScore;
      ws2State.edited[qid] = true;

      // Update input field in-place
      const input = ws2.rubricRows.querySelector(`.ws2-crit-input[data-mi="${mi}"]`);
      if (input) input.value = newScore;

      const total = ws2AwardedTotal(qid);
      ws2.qScore.textContent = total;

      const src = ws2.scoreSrc;
      const st = ws2State.questionStatus[qid];
      src.classList.remove("edited");
      if (st === 'done') {
        src.textContent = "Confirmed · edited by you";
        src.classList.add("edited");
      } else if (st === 'flagged') {
        src.textContent = "Flagged for a second look";
      } else {
        src.textContent = "Edited by you · not yet confirmed";
      }

      ws2RenderSheet();
      ws2RenderTotals();
      ws2SetStatus("Adjusted by " + (d > 0 ? "+0.5" : "-0.5") + " marks (" + newScore + "/" + max + ").", false);
    });
  });

  // Direct numeric input listeners without resetting scroll
  ws2.rubricRows.querySelectorAll(".ws2-crit-input").forEach(input => {
    input.addEventListener("input", (e) => {
      const mi = +input.dataset.mi;
      const max = points[mi].maxMarks;
      let val = parseFloat(e.target.value);
      if (isNaN(val)) val = 0;
      val = Math.max(0, Math.min(max, val));
      awarded[mi] = val;
      ws2State.edited[qid] = true;

      const total = ws2AwardedTotal(qid);
      ws2.qScore.textContent = total;

      const src = ws2.scoreSrc;
      const st = ws2State.questionStatus[qid];
      src.classList.remove("edited");
      if (st === 'done') {
        src.textContent = "Confirmed · edited by you";
        src.classList.add("edited");
      } else if (st === 'flagged') {
        src.textContent = "Flagged for a second look";
      } else {
        src.textContent = "Edited by you · not yet confirmed";
      }

      ws2RenderSheet();
      ws2RenderTotals();
      ws2SetStatus("Custom mark entered (" + val + " / " + max + ").", false);
    });

    input.addEventListener("blur", () => {
      const mi = +input.dataset.mi;
      input.value = awarded[mi];
    });
  });

  const total = ws2AwardedTotal(qid);
  ws2.qScore.textContent = total;

  const src = ws2.scoreSrc;
  const st = ws2State.questionStatus[qid];
  src.classList.remove("edited");
  if (st === 'done') {
    src.textContent = ws2State.edited[qid] ? "Confirmed · edited by you" : "Confirmed by you";
  } else if (st === 'flagged') {
    src.textContent = "Flagged for a second look";
  } else {
    src.textContent = ws2State.edited[qid] ? "Edited by you · not yet confirmed" : "Suggested · not yet confirmed";
  }
  if (ws2State.edited[qid] && st === 'done') src.classList.add("edited");

  ws2.notes.value = ws2State.notes[qid] || "";
}

function ws2RenderNav() {
  let html = "";
  ws2QuestionIds().forEach(qid => {
    const st = ws2State.questionStatus[qid];
    const cls = ["ws2-qchip"];
    if (qid === ws2State.current) cls.push("active");
    if (st === 'done') cls.push("done");
    if (st === 'flagged') cls.push("flagged");
    html += '<button class="' + cls.join(' ') + '" data-qid="' + qid + '">Q' + qid.replace('q', '') + '<span class="st"></span></button>';
  });
  ws2.qnav.innerHTML = html;
  ws2.qnav.querySelectorAll(".ws2-qchip").forEach(c =>
    c.addEventListener("click", () => { ws2State.current = c.dataset.qid; ws2RenderAll(); }));
}

function ws2RenderTotals() {
  let score = 0, max = 0, reviewed = 0;
  const qids = ws2QuestionIds();
  qids.forEach(qid => {
    const st = ws2State.questionStatus[qid];
    if (st === 'done') {
      max += ws2Student.questions[qid].maxScore;
      score += ws2AwardedTotal(qid);
    }
    if (st) reviewed++;
  });
  ws2.sheetScore.textContent = Math.round(score * 10) / 10;
  ws2.sheetMax.textContent = max;
  ws2.reviewLabel.textContent = reviewed + " of " + qids.length;
  ws2.progFill.style.width = (qids.length ? reviewed / qids.length * 100 : 0) + "%";
}

function ws2SetStatus(msg, done) {
  ws2.status.textContent = msg;
  ws2.status.classList.toggle("done", !!done);
}

function ws2RenderAll() {
  ws2RenderSheet();
  ws2RenderEval();
  ws2RenderNav();
  ws2RenderTotals();
  ws2.sheetScroll.scrollTop = 0;
  ws2.evalScroll.scrollTop = 0;
  const es = ws2.evalScroll;
  es.classList.remove("ws2-eval-swap");
  void es.offsetWidth;
  es.classList.add("ws2-eval-swap");
  const st = ws2State.questionStatus[ws2State.current];
  if (st === 'done') ws2SetStatus("Confirmed. Use → to move to the next question.", true);
  else if (st === 'flagged') ws2SetStatus("Flagged for a second look. You can revisit it anytime.", false);
  else ws2SetStatus("Suggested marks are ready — confirm, adjust, or flag.", false);
}

function ws2SetZoom(d) {
  ws2Zoom = Math.min(1.6, Math.max(0.7, +(ws2Zoom + d).toFixed(2)));
  ws2.sheet.style.transform = "scale(" + ws2Zoom + ")";
  ws2.zoomVal.textContent = Math.round(ws2Zoom * 100) + "%";
}

function ws2GoPage(d) {
  const qids = ws2QuestionIds();
  if (!qids.length) return;
  const idx = Math.max(0, Math.min(qids.length - 1, qids.indexOf(ws2State.current) + d));
  ws2State.current = qids[idx];
  ws2.pageLabel.textContent = "p. " + (idx + 1) + " / " + qids.length;
  ws2RenderAll();
}

async function ws2SaveToBackend(flag) {
  const qScores = {};
  ws2QuestionIds().forEach(qid => { qScores[qid] = ws2Student.questions[qid].score; });
  try {
    await fetch(`${apiBaseUrl}/api/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        studentId: ws2Student.id,
        questions: qScores,
        comments: flag ? "Flagged for moderator audit." : (ws2State.notes[ws2State.current] || "")
      })
    });
    await syncDatabaseState();
    renderQueueTable();
    updateHeaderStats();
  } catch (e) { console.error("Workspace sync failed", e); }
}

function initWorkspaceLogic() {
  ws2.zoomIn.addEventListener('click', () => ws2SetZoom(0.15));
  ws2.zoomOut.addEventListener('click', () => ws2SetZoom(-0.15));
  ws2.pgPrev.addEventListener('click', () => ws2GoPage(-1));
  ws2.pgNext.addEventListener('click', () => ws2GoPage(1));

  ws2.ansToggle.addEventListener('click', () => {
    const a = ws2.studentAnswer;
    const open = a.hidden;
    a.hidden = !open;
    ws2.ansToggle.classList.toggle('open', open);
    ws2.ansToggle.innerHTML = (open ? "Hide" : "Show") +
      '<svg class="icon chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>';
  });

  ws2.notes.addEventListener('input', e => {
    ws2State.notes[ws2State.current] = e.target.value;
  });

  ws2.btnAdjust.addEventListener('click', () => {
    ws2.evalScroll.scrollTop = ws2.rubricRows.offsetTop - 8;
    ws2SetStatus("Use the − / + controls on each criterion to adjust marks.", false);
  });

  ws2.btnConfirm.addEventListener('click', async () => {
    const qid = ws2State.current;
    ws2State.questionStatus[qid] = 'done';
    ws2Student.questions[qid].score = ws2AwardedTotal(qid);
    
    await ws2SaveToBackend(false);

    const qids = ws2QuestionIds();
    const curIdx = qids.indexOf(qid);
    
    if (curIdx < qids.length - 1) {
      // Automatically advance to the next question
      const nextQid = qids[curIdx + 1];
      ws2State.current = nextQid;
      ws2.pageLabel.textContent = "p. " + (curIdx + 2) + " / " + qids.length;
      ws2RenderAll();
      ws2SetStatus(`Confirmed Q${qid.replace('q', '')} (${ws2AwardedTotal(qid)} marks). Advanced to Q${nextQid.replace('q', '')}.`, true);
    } else {
      // Last question confirmed!
      ws2RenderNav();
      ws2RenderTotals();
      ws2RenderSheet();
      ws2.scoreSrc.textContent = ws2State.edited[qid] ? "Confirmed · edited by you" : "Confirmed by you";
      if (ws2State.edited[qid]) ws2.scoreSrc.classList.add("edited");
      
      const allDone = qids.every(q => ws2State.questionStatus[q] === 'done');
      if (allDone) {
        if (currentStudentIndex < students.length - 1) {
          ws2SetStatus(`All questions confirmed for ${ws2Student.name}! Click 'Next Student' (or press N) to evaluate the next paper.`, true);
        } else {
          ws2SetStatus(`All questions confirmed for ${ws2Student.name}! All student papers in queue evaluated.`, true);
        }
      } else {
        ws2SetStatus(`Confirmed Q${qid.replace('q', '')}. Review remaining questions or move to next student.`, true);
      }
    }
  });

  ws2.btnFlag.addEventListener('click', async () => {
    const qid = ws2State.current;
    ws2State.questionStatus[qid] = 'flagged';
    ws2RenderNav();
    ws2RenderTotals();
    ws2RenderSheet();
    ws2.scoreSrc.textContent = "Flagged for a second look";
    ws2.scoreSrc.classList.remove("edited");
    ws2SetStatus("Flagged for a second look. You can revisit it anytime.", false);
    await ws2SaveToBackend(true);
  });

  if (ws2.prevStudentBtn) ws2.prevStudentBtn.addEventListener('click', ws2PrevStudent);
  if (ws2.nextStudentBtn) ws2.nextStudentBtn.addEventListener('click', ws2NextStudent);

  // Re-check difficulty switcher in workspace
  if (ws2.recheckBtn) {
    ws2.recheckBtn.addEventListener('click', async () => {
      if (!ws2Student) return;
      const targetDiff = ws2.diffSelect ? ws2.diffSelect.value : 'medium';
      await ws2RecheckDifficulty(targetDiff);
    });
  }

  document.addEventListener("keydown", e => {
    if (e.target.tagName === "TEXTAREA" || e.target.tagName === "INPUT") return;
    const qids = ws2QuestionIds();
    if (!qids.length) return;
    const idx = qids.indexOf(ws2State.current);
    if (e.key === "a" || e.key === "A") ws2.btnConfirm.click();
    else if (e.key === "f" || e.key === "F") ws2.btnFlag.click();
    else if (e.key === "n" || e.key === "N") ws2NextStudent();
    else if (e.key === "p" || e.key === "P") ws2PrevStudent();
    else if (e.key === "ArrowRight") { if (idx < qids.length - 1) { ws2State.current = qids[idx + 1]; ws2.pageLabel.textContent = "p. " + (idx + 2) + " / " + qids.length; ws2RenderAll(); } }
    else if (e.key === "ArrowLeft") { if (idx > 0) { ws2State.current = qids[idx - 1]; ws2.pageLabel.textContent = "p. " + idx + " / " + qids.length; ws2RenderAll(); } }
  });
}

async function ws2RecheckDifficulty(targetDiff) {
  if (!ws2Student) return;
  if (ws2.recheckBtn) {
    ws2.recheckBtn.disabled = true;
    ws2.recheckBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Checking...';
  }
  try {
    const res = await fetch(`${apiBaseUrl}/api/evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        studentId: ws2Student.id,
        questionPaperId: ws2Student.questionPaperId || "",
        difficulty: targetDiff
      })
    });
    const data = await res.json();
    if (data.status === 'success' && data.student) {
      const idx = students.findIndex(s => s.id === ws2Student.id);
      if (idx !== -1) {
        students[idx] = data.student;
      }
      ws2Student = data.student;
      ws2State.questionStatus = {};
      ws2State.edited = {};
      ws2State.awarded = {};
      ws2QuestionIds().forEach(qid => {
        ws2State.awarded[qid] = deriveAwarded(qid, ws2Student.questions[qid]);
      });
      ws2RenderAll();
      ws2SetStatus(`Re-evaluated under [${targetDiff.toUpperCase()}] grading strictness.`, true);
      renderQueueTable();
      updateHeaderStats();
    } else {
      alert("Evaluation error: " + (data.message || "Unknown error"));
    }
  } catch (err) {
    console.error(err);
    alert("Connection error while re-evaluating: " + err.message);
  } finally {
    if (ws2.recheckBtn) {
      ws2.recheckBtn.disabled = false;
      ws2.recheckBtn.innerHTML = '<i class="fa-solid fa-arrows-rotate"></i> Re-check';
    }
  }
}

function ws2NextStudent() {
  if (currentStudentIndex < students.length - 1) {
    loadStudentIntoWorkspace(currentStudentIndex + 1);
    ws2SetStatus(`Loaded next student: ${ws2Student.name} (${currentStudentIndex + 1} of ${students.length})`, true);
  } else {
    ws2SetStatus("You are already on the last student in the queue.", false);
  }
}

function ws2PrevStudent() {
  if (currentStudentIndex > 0) {
    loadStudentIntoWorkspace(currentStudentIndex - 1);
    ws2SetStatus(`Loaded previous student: ${ws2Student.name} (${currentStudentIndex + 1} of ${students.length})`, false);
  } else {
    ws2SetStatus("You are on the first student in the queue.", false);
  }
}

function loadStudentIntoWorkspace(index) {
  if (students.length === 0) return;
  currentStudentIndex = index;
  ws2Student = students[index];

  ws2State.questionStatus = {};
  ws2State.notes = {};
  ws2State.edited = {};
  ws2State.awarded = {};
  ws2QuestionIds().forEach(qid => {
    ws2State.awarded[qid] = deriveAwarded(qid, ws2Student.questions[qid]);
  });
  ws2State.current = ws2QuestionIds()[0] || null;

  ws2.studentName.textContent = ws2Student.name;
  ws2.studentRoll.textContent = ws2Student.id + " · " + ws2Student.format;
  
  if (ws2.studentIdx) {
    ws2.studentIdx.textContent = `${index + 1} of ${students.length}`;
  }
  if (ws2.prevStudentBtn) {
    ws2.prevStudentBtn.disabled = index <= 0;
  }
  if (ws2.nextStudentBtn) {
    ws2.nextStudentBtn.disabled = index >= students.length - 1;
  }

  const diff = ws2Student.difficulty || 'medium';
  if (ws2.diffSelect) {
    ws2.diffSelect.value = diff;
  }

  ws2.sheetSeat.textContent = "Roll No. " + ws2Student.id;
  const rubric = rubricsList.length ? rubricsList[0] : null;
  const paperLabel = ws2Student.questionPaper || (rubric ? rubric.subject : null);
  ws2.sheetPaper.textContent = paperLabel ? `Question Paper: ${paperLabel}` : "Descriptive Exam";
  ws2.pageLabel.textContent = "p. 1 / " + ws2QuestionIds().length;
  ws2Zoom = 1;
  ws2.sheet.style.transform = "scale(1)";
  ws2.zoomVal.textContent = "100%";

  ws2RenderAll();
}

function openStudentWorkspace(index) {
  if (index >= 0 && index < students.length) {
    currentStudentIndex = index;
    loadStudentIntoWorkspace(index);
  }
  switchTab('workspace');
}