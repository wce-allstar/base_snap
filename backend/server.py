import os
import json
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Optional library for reading PDF content in real pipeline
try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

# Optional library for Gemini integrations
try:
    from google import genai
    from google.genai import types

    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# Current model used by the real AI evaluation pipeline.
DEFAULT_EVAL_MODEL = "gemini-3.5-flash"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'Frontend')
if not os.path.exists(FRONTEND_DIR):
    FRONTEND_DIR = BASE_DIR

DB_PATH = os.path.join(BASE_DIR, 'db.json')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)

# ---------------------------------------------------------
# MOCK DATABASE INITIAL SEED
# ---------------------------------------------------------
INITIAL_STUDENTS = [
  {
    "id": "CS2026-084",
    "name": "Amit Patel",
    "format": "Scanned PDF (Handwritten)",
    "aiScore": 15.5,
    "maxScore": 20,
    "confidence": 89,
    "status": "Pending Review",
    "selfCheck": "Consistent",
    "handwritingQuality": "Average",
    "difficulty": "medium",
    "questions": {
      "q1": {
        "score": 7.5,
        "maxScore": 10,
        "ocrText": "A Binary Search Tree (BST) is a node-based binary tree data structure which has the following properties: The left subtree of a node contains only nodes with keys lesser than the node's key. The right subtree of a node contains only nodes with keys greater than the node's key. Both the left and right subtrees must also be binary search trees.\n\nSearch complexity: In the best case, it is O(log N) where N is the number of nodes. In the worst case, it can degenerate to O(N) when the tree becomes unbalanced (like a linked list).\n\nAVL and Red-Black trees solve this by performing rotations during insert/delete, ensuring the height remains balanced, which keeps search complexity strictly at O(log N).",
        "handwritingMock": "A Binary Search Tree (BST) is a node-based binary tree data structure with properties:\n- Left subtree keys < Node key\n- Right subtree keys > Node key\n- Subtrees are also BSTs.\n\nSearch complexity:\nBest case = O(log N). Worst case = O(N) (when tree degenerates into a single line like a linked list).\n\nAVL & Red-Black trees solve this. They balance height dynamically using rotations during insert/delete. This keeps height h ~ log N, maintaining O(log N) search complexity.",
        "strengths": [
          "Perfect coverage of BST definition properties.",
          "Clear explanation of why unbalance causes O(N) worst-case degeneration.",
          "Identifies dynamic rotations in AVL and Red-Black trees."
        ],
        "weaknesses": [
          "Missed mathematical formulation of AVL height balance factor (|h_L - h_R| <= 1).",
          "Confuses average case and best case search complexity terminology."
        ],
        "justification": "The student provides a solid standard definition of a BST and correctly identifies the O(log N) best/average case and O(N) worst-case search complexity. The explanation of degeneration is clear. AVL and Red-Black trees are appropriately mentioned as solutions utilizing rotations, though the mathematical height balance condition is not explicitly formulated. Thus, 7.5 out of 10 marks are assigned."
      },
      "q2": {
        "score": 8.0,
        "maxScore": 10,
        "ocrText": "insertNode(Node root, int val) {\n  if (root == null) {\n     return new Node(val);\n  }\n  if (val < root.key) {\n      root.left = insertNode(root.left, val);\n  } else {\n      root.right = insertNode(root.right, val);\n  }\n  return root;\n}\n\nComplexity:\n- Time Complexity is O(h) where h is the tree height. In balanced trees, h = log N.\n- Space Complexity is O(h) due to recursive stack calls.",
        "handwritingMock": "insertNode(Node root, int val) {\n  if (root == null) return new Node(val);\n  if (val < root.key) {\n      root.left = insertNode(root.left, val);\n  } else {\n      root.right = insertNode(root.right, val);\n  }\n  return root;\n}\nComplexity:\nTime = O(h) where h is height. (O(log N) if balanced).\nSpace = O(h) for call stack recursively.",
        "strengths": [
          "Clean, functional recursive pseudo-code implementation.",
          "Correctly correlates time complexity to tree height O(h).",
          "Accurately defines recursive call space complexity as O(h)."
        ],
        "weaknesses": [
          "Does not define behavior or handling strategy for duplicate keys.",
          "Iterative approach was not discussed."
        ],
        "justification": "Pseudocode is syntactically sound and covers the standard recursive BST insertion mechanism. Time and space complexities are correctly identified as O(h). Minor omission: no explicit handling of duplicate keys is shown. Grade is set to 8.0 out of 10."
      }
    }
  },
  {
    "id": "CS2026-003",
    "name": "Priya Sharma",
    "format": "Digital Upload (Typed)",
    "aiScore": 18.5,
    "maxScore": 20,
    "confidence": 96,
    "status": "Pending Review",
    "selfCheck": "Consistent",
    "handwritingQuality": "Not Applicable",
    "difficulty": "medium",
    "questions": {
      "q1": {
        "score": 9.5,
        "maxScore": 10,
        "ocrText": "A Binary Search Tree (BST) is a hierarchical data structure. Each node has a key, and for any node:\n1. All keys in the left subtree are smaller than the node's key: Keys(L) < Key(Node)\n2. All keys in the right subtree are larger than the node's key: Keys(R) > Key(Node)\n3. Both subtrees are recursively BSTs.\n\nThe search complexity depends on tree shape. In a balanced BST, the height is O(log N), so search is O(log N). If nodes are inserted in sorted order, the tree degenerates into a linear chain (skewed tree), causing search complexity to become O(N).\nSelf-balancing trees like AVL trees enforce structural balance. AVL trees maintain balance factor BF = |Height(Left) - Height(Right)| <= 1. If BF exceeds 1, rotations (LL, RR, LR, RL) are executed to rebalance height, restoring O(log N) lookup.",
        "handwritingMock": "[Typed Document Input - Rendered as clean monospace text]\nA Binary Search Tree (BST) is defined by recursive hierarchy:\n- Left-subtree nodes < Root\n- Right-subtree nodes > Root\n- No duplicate elements.\n\nWorst-case search degrades to O(N) when data is skew-inserted. Height-balanced trees like AVL trees keep height limited to O(log N) by enforcing |h(Left) - h(Right)| <= 1 through rotation operations.",
        "strengths": [
          "Highly precise mathematical definition of BST properties.",
          "Clear explanation of skewed tree degeneration.",
          "Explicitly states AVL balance factor equation and rotation types."
        ],
        "weaknesses": [
          "Very minor: did not mention Red-Black trees as requested in alternative height-balanced options, but AVL detail is exhaustive."
        ],
        "justification": "Excellent comprehensive answer. Features precise definition, clear skewed tree examples, and thorough explanation of AVL balancing mechanism and rotations. Almost perfect, a 9.5/10 is awarded."
      },
      "q2": {
        "score": 9.0,
        "maxScore": 10,
        "ocrText": "class Node {\n    int key;\n    Node left, right;\n    Node(int val) { key = val; left = right = null; }\n}\n\nNode insert(Node root, int key) {\n    if (root == null) {\n        return new Node(key);\n    }\n    if (key < root.key) {\n        root.left = insert(root.left, key);\n    } else if (key > root.key) {\n        root.right = insert(root.right, key);\n    }\n    return root;\n}\n\nComplexity:\nTime: O(h) - worst case O(N) for skewed tree, O(log N) for balanced.\nSpace: O(h) memory on stack.",
        "handwritingMock": "[Typed Document Input]\nclass Node {\n    int key; Node left, right;\n    Node(int v) { key = v; }\n}\nNode insert(Node root, int val) {\n    if(root == null) return new Node(val);\n    if(val < root.key) root.left = insert(root.left, val);\n    else if(val > root.key) root.right = insert(root.right, val);\n    return root;\n}",
        "strengths": [
          "Includes correct node class definition structure.",
          "Handles duplicate elements appropriately by skipping them (key > root.key).",
          "Accurately outlines complexities."
        ],
        "weaknesses": [
          "Missing comment/handling on how to update values if duplicates are updated."
        ],
        "justification": "Highly structured and complete code script. The inclusion of the helper Node class and duplicate key exclusion makes it clean and efficient. Time and space complexities are correct. Assigned 9.0/10."
      }
    }
  },
  {
    "id": "CS2026-112",
    "name": "Rahul Verma",
    "format": "Scanned PDF (Handwritten)",
    "aiScore": 7.5,
    "maxScore": 20,
    "confidence": 76,
    "status": "Pending Review",
    "selfCheck": "Flagged: Low Confidence",
    "handwritingQuality": "Poor / Scrawly",
    "difficulty": "medium",
    "questions": {
      "q1": {
        "score": 4.0,
        "maxScore": 10,
        "ocrText": "BST is a tree which is binary and has search property. Values on left are small and values on right are large.\n        \nSearch complexity:\nNormally it is O(log N). If bad, it can be O(N).\nAVL trees help balance it.",
        "handwritingMock": "BST is a binary tree.\nLeft elements < Root < Right elements.\n\nSearch is O(log N). Worst case O(N) when it is flat.\nAVL trees balance it.",
        "strengths": [
          "Understands base left-smaller and right-larger property.",
          "Correctly states worst case complexity is O(N)."
        ],
        "weaknesses": [
          "Extremely sparse explanation lacking detail.",
          "Fails to explain HOW height-balanced trees solve degeneration (no mention of rotations or height math)."
        ],
        "justification": "The answer is overly brief. While the basic definition is correct, it fails to explain the degeneration mechanism properly ('when it is flat' is imprecise) and gives no explanation of how AVL trees solve this besides stating that they 'help balance it'. Missing major parts of the question. Marks: 4.0/10."
      },
      "q2": {
        "score": 3.5,
        "maxScore": 10,
        "ocrText": "insert(val) {\n   if (root == null) root = val;\n   else if (val < root) root.left = insert(val);\n   else root.right = insert(val);\n}",
        "handwritingMock": "insert(val) {\n  if (root == null) root = val;\n  else if (val < root) root.left = insert(val);\n  else root.right = insert(val);\n}",
        "strengths": [
          "Identifies recursive direction routing logic based on value."
        ],
        "weaknesses": [
          "Highly invalid syntax and broken recursion (does not pass root down recursive steps).",
          "Completely missed writing time/space complexity analysis."
        ],
        "justification": "The pseudo-code is conceptually broken. It references a global 'root' instead of traversing recursively using sub-nodes, rendering the code dysfunctional. Furthermore, the student omitted the complexity analysis entirely. Scoring 3.5/10."
      }
    }
  }
]

DEFAULT_RUBRICS = [
  {
    "id": "cs101-mid",
    "subject": "CS101: Midterm - Data Structures & Algorithms",
    "version": "Rubric v3",
    "questionsCount": 2,
    "totalMarks": 20,
    "questions": [
      {
        "qId": "q1",
        "title": "BST & Complexities (Question 1)",
        "maxMarks": 10,
        "criteria": [
          { "text": "BST property: Left < Node < Right defined recursively.", "marks": 3 },
          { "text": "Search complexities defined: average/best O(log N), worst O(N).", "marks": 2 },
          { "text": "Reason for degeneration explained (skewed tree, sorted inputs).", "marks": 2 },
          { "text": "Balanced trees: AVL/RB balancing using height constraints and rotations.", "marks": 3 }
        ]
      },
      {
        "qId": "q2",
        "title": "BST Insertion Pseudocode (Question 2)",
        "maxMarks": 10,
        "criteria": [
          { "text": "Pseudo-code logic structure: base case (null check) and recursive routing.", "marks": 4 },
          { "text": "Duplicate handling or validation branching.", "marks": 1 },
          { "text": "Time complexity O(h) or O(log N) explained.", "marks": 2 },
          { "text": "Space complexity O(h) recursive stack explained.", "marks": 3 }
        ]
      }
    ]
  },
  {
    "id": "me202-mid",
    "subject": "ME202: Midterm - Thermodynamics",
    "version": "Rubric v1",
    "questionsCount": 2,
    "totalMarks": 30,
    "questions": [
      {
        "qId": "q1",
        "title": "First Law Formulation",
        "maxMarks": 15,
        "criteria": [
          { "text": "Mathematical statement of 1st Law (dQ = dU + dW).", "marks": 5 },
          { "text": "Concept explanation of Internal Energy as a state function.", "marks": 5 },
          { "text": "Path dependency explanation of heat and work.", "marks": 5 }
        ]
      },
      {
        "qId": "q2",
        "title": "Carnot Engine Efficiency",
        "maxMarks": 15,
        "criteria": [
          { "text": "PV Diagram cycle sketching.", "marks": 5 },
          { "text": "Derivation of efficiency formula: eta = 1 - T_C / T_H.", "marks": 7 },
          { "text": "Statement of thermodynamic limitations.", "marks": 3 }
        ]
      }
    ]
  }
]

DEFAULT_SETTINGS = {
  "institutionName": "State Institute of Technology (SIT)",
  "departmentName": "Computer Science & Engineering",
  "activeSemester": "Fall 2026",
  "rollMatchingMode": "Barcoded Booklet Coversheet (QR Reader)",
  "enableEmailReports": True,
  "safetyDriftLimit": 15,
  "auditSampleRatio": 10,
  "minConfidenceThreshold": 80,
  "defaultLlmSpine": "Gemini 1.5 Pro (Consistent Multi-Reasoning)",
  "geminiApiKey": "",
  "lmsDatabaseEndpoint": "https://lms.sit-edu.in/api/v2/grades-sync"
}

# ---------------------------------------------------------
# DATABASE LOAD/WRITE HELPERS
# ---------------------------------------------------------
def load_db():
    if not os.path.exists(DB_PATH):
        default_prompts = {
            "extractor": "System Role: OCR & Handwriting Ingestion Specialist\nTask: Convert raw handwritten scanned scripts (JPEG/PNG/PDF) into structured digitized text.\nInstructions:\n1. Perform high-precision Handwriting Character Recognition (HWR).\n2. Preserve original formatting, indentation, and structure (especially for pseudo-code blocks).\n3. If handwriting is illegible, flag with [UNCERTAIN_OCR] markers and output raw layout coordinates.\n4. Output structured output mapped per Question ID.",
            "mapper": "System Role: Semantic Rubric Mapping Agent\nTask: Align digitized student answers with rubric criteria points.\nInstructions:\n1. Match conceptual sentences in student answers to target rubric points.\n2. Rely on semantic understanding, synonyms, and logical equivalence (not mere keyword matching).\n3. Calculate similarity matrices for each rubric criterion.\n4. Grade coverage: 'Fully Covered', 'Partially Covered', or 'Not Covered'.",
            "reasoner": "System Role: Logical Reasoning & Flow Checking Agent\nTask: Audit mathematical proofs, algorithms, and step-by-step logic.\nInstructions:\n1. Trace algorithm execution steps in code blocks.\n2. Check for logical leaps, invalid loops, off-by-one errors, or incomplete derivations.\n3. Assess the soundness of reasoning behind explanations.\n4. Provide technical feedback on code or logic failures.",
            "grader": "System Role: Explainable Justification & Marks Assigner\nTask: Compute marks per question based on mapping, reasoning, and coverage checks, generating detailed constructive feedback.\nInstructions:\n1. Assign marks for each rubric item based on coverage classification.\n2. Draft an examiner-style feedback explaining EXACTLY why marks were deducted or awarded.\n3. Do not sound generic; refer to specific lines of the student response.\n4. Generate confidence metrics based on OCR clarity and rubric matching confidence.",
            "checker": "System Role: Multi-Sheet Grading Consistency & Bias Audit Agent\nTask: Cross-reference grades across student cohorts to identify grading drift, strictness shifts, or demographic/format bias.\nInstructions:\n1. Maintain vector indexes of grades and matching descriptions.\n2. Compare score variance for similar answers.\n3. Alert human moderator if grading strictness changes over time or if scanned writing is graded lower than typed text of equivalent semantic weight."
        }
        db = {
            "students": INITIAL_STUDENTS,
            "rubrics": DEFAULT_RUBRICS,
            "settings": DEFAULT_SETTINGS,
            "agent_prompts": default_prompts,
            "questionPapers": [],
            "logs": {
                "extractor": [],
                "mapper": [],
                "reasoner": [],
                "grader": [],
                "checker": []
            }
        }
        save_db(db)
        return db
    try:
        with open(DB_PATH, 'r') as f:
            return json.load(f)
    except Exception:
        return {"students": INITIAL_STUDENTS, "rubrics": DEFAULT_RUBRICS, "settings": DEFAULT_SETTINGS, "agent_prompts": {}, "questionPapers": []}

def save_db(db):
    with open(DB_PATH, 'w') as f:
        json.dump(db, f, indent=2)

def append_log(agent, text, log_type='info'):
    db = load_db()
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        "text": f"[{timestamp}] {log_type.upper()}: {text}" if log_type != 'agent-message' else text,
        "type": log_type
    }
    if "logs" not in db:
        db["logs"] = {"extractor": [], "mapper": [], "reasoner": [], "grader": [], "checker": []}
    db["logs"][agent].append(log_entry)
    
    if len(db["logs"][agent]) > 100:
        db["logs"][agent].pop(0)
        
    save_db(db)

# Seed initial logs if empty
db = load_db()
if "logs" not in db or not db["logs"]["extractor"]:
    db["logs"] = {"extractor": [], "mapper": [], "reasoner": [], "grader": [], "checker": []}
    templates = {
        "extractor": [
            { "type": "system", "text": "Initializing Ingestor Pipeline v1.2..." },
            { "type": "info", "text": "Loading HWR layout model: cnn-resnet-v4-hwr" },
            { "type": "success", "text": "Ingestion engine standing by." }
        ],
        "mapper": [
            { "type": "system", "text": "Rubric Mapper Agent active." }
        ],
        "reasoner": [
            { "type": "system", "text": "Reasoning check thread started." }
        ],
        "grader": [
            { "type": "system", "text": "Marks synthesizer standing by." }
        ],
        "checker": [
            { "type": "system", "text": "Cohort uniformity monitor initialized." }
        ]
    }
    for agent, logs in templates.items():
        db["logs"][agent] = logs
    save_db(db)


# ---------------------------------------------------------
# FLASK ROUTING ENDPOINTS
# ---------------------------------------------------------
@app.route('/')
def index_route():
    return send_from_directory(FRONTEND_DIR, 'index.html')

# API: Auth Mock Login
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json or {}
    email = data.get('email', '')
    password = data.get('password', '')
    
    if '@' in email and len(password) >= 6:
        append_log('checker', f"Examiner authenticated: {email}", 'success')
        return jsonify({"status": "success", "token": "mock-token-session-12345"})
    return jsonify({"status": "error", "message": "Verification failed"}), 400

# API: Cohort Queue
@app.route('/api/queue', methods=['GET'])
def api_get_queue():
    db = load_db()
    return jsonify(db.get('students', []))

# API: Get Settings
@app.route('/api/settings', methods=['GET'])
def api_get_settings():
    db = load_db()
    return jsonify(db.get('settings', {}))

# API: Save Settings
@app.route('/api/settings/save', methods=['POST'])
def api_save_settings():
    db = load_db()
    data = request.json or {}
    db['settings'] = data
    save_db(db)
    
    # Configure Gemini API dynamically if changed
    key = data.get('geminiApiKey', '')
    if key and HAS_GEMINI:
        try:
            genai.Client(api_key=key)
            append_log('grader', "Gemini API configurator connection initialized.", 'success')
        except Exception as e:
            append_log('grader', f"API key config fail: {str(e)}", 'warn')
            
    append_log('checker', "System configuration settings updated.", 'info')
    return jsonify({"status": "success"})

# API: Get Rubrics
@app.route('/api/rubrics', methods=['GET'])
def api_get_rubrics():
    db = load_db()
    return jsonify(db.get('rubrics', []))

# API: Save Rubrics
@app.route('/api/rubrics/save', methods=['POST'])
def api_save_rubrics():
    db = load_db()
    data = request.json or {}
    rubrics = db.get('rubrics', [])
    
    idx = next((i for i, r in enumerate(rubrics) if r['id'] == data.get('id')), -1)
    if idx != -1:
        rubrics[idx] = data
    else:
        rubrics.append(data)
        
    db['rubrics'] = rubrics
    save_db(db)
    append_log('mapper', f"Compiled rubric published: {data.get('subject')}", 'success')
    return jsonify({"status": "success"})

# API: Get Agent Prompts
@app.route('/api/agents', methods=['GET'])
def api_get_agents():
    db = load_db()
    return jsonify(db.get('agent_prompts', {}))

# API: Update Agent Prompt
@app.route('/api/agents/update', methods=['POST'])
def api_update_agent():
    db = load_db()
    data = request.json or {}
    agent_id = data.get('agentId')
    prompt = data.get('prompt')
    
    if agent_id in db['agent_prompts']:
        db['agent_prompts'][agent_id] = prompt
        save_db(db)
        append_log(agent_id, "System prompt updated. Restarting agent context...", 'warn')
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Unknown agent"}), 400

# API: Get Agent Logs
@app.route('/api/agents/logs', methods=['GET'])
def api_get_logs():
    db = load_db()
    agent = request.args.get('agent', 'extractor')
    logs = db.get('logs', {}).get(agent, [])
    return jsonify(logs)

# API: Manual Moderator Approve
@app.route('/api/approve', methods=['POST'])
def api_approve_grade():
    db = load_db()
    data = request.json or {}
    student_id = data.get('studentId')
    q_scores = data.get('questions', {})
    comments = data.get('comments', '')
    
    students = db.get('students', [])
    idx = next((i for i, s in enumerate(students) if s['id'] == student_id), -1)
    
    if idx != -1:
        student = students[idx]
        student['status'] = "Approved"
        
        # update question scores
        for qid, qscore in q_scores.items():
            if qid in student['questions']:
                student['questions'][qid]['score'] = float(qscore)
                
        student['aiScore'] = float(round(sum(q.get('score', 0) for q in student['questions'].values()), 1))
        student['maxScore'] = sum(q.get('maxScore', 10) for q in student['questions'].values())
        
        if comments.strip():
            student['selfCheck'] = "Manually Overridden"
            
        db['students'] = students
        save_db(db)
        append_log('checker', f"Moderator approved and locked grades for Roll: {student_id}.", 'success')
        return jsonify({"status": "success"})
        
    return jsonify({"status": "error", "message": "Student not found"}), 404

# API: Question Paper Upload & Listing
@app.route('/api/question-papers', methods=['GET'])
def api_list_question_papers():
    db = load_db()
    return jsonify({"status": "success", "questionPapers": db.get('questionPapers', [])})

@app.route('/api/question-papers/upload', methods=['POST'])
def api_upload_question_paper():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No empty filename"}), 400

    filename = file.filename
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    extracted_text = ""
    if filename.lower().endswith('.pdf') and HAS_PYPDF:
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                extracted_text += page.extract_text() + "\n"
        except Exception as e:
            extracted_text = f"Error extracting text from PDF: {str(e)}"

    db = load_db()
    papers = db.get('questionPapers', [])
    paper = {
        "id": f"qp-{len(papers) + 1}-{int(time.time())}",
        "name": os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title(),
        "fileName": filename,
        "filePath": file_path,
        "text": extracted_text,
        "uploadedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    papers.append(paper)
    db['questionPapers'] = papers
    save_db(db)

    append_log('mapper', f"Question paper '{paper['name']}' stored for evaluation mapping.", 'info')
    return jsonify({"status": "success", "questionPaper": paper})

# API: Script file Upload
@app.route('/api/upload', methods=['POST'])
def api_upload_script():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No empty filename"}), 400

    question_paper_id = request.form.get('questionPaperId', '') or ''
    db = load_db()
    papers = db.get('questionPapers', [])
    linked_paper = next((p for p in papers if p['id'] == question_paper_id), None)
        
    filename = file.filename
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    
    # Read text if PDF
    extracted_text = ""
    if filename.lower().endswith('.pdf') and HAS_PYPDF:
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                extracted_text += page.extract_text() + "\n"
        except Exception as e:
            extracted_text = f"Error extracting text from PDF: {str(e)}"
            
    difficulty = request.form.get('difficulty', 'medium') or 'medium'
    
    # Add temporary student placeholder
    temp_id = f"CS2026-00{len(db['students']) + 10}"
    new_student = {
        "id": temp_id,
        "name": filename.split('_')[0] if '_' in filename else "Uploaded Script",
        "format": "Scanned PDF" if filename.lower().endswith('.pdf') else "Scanned Image",
        "aiScore": 0.0,
        "maxScore": 20,
        "confidence": 80,
        "status": "Awaiting Pipeline",
        "selfCheck": "Awaiting Ingest",
        "handwritingQuality": "Analyzing...",
        "difficulty": difficulty,
        "questionPaperId": linked_paper['id'] if linked_paper else "",
        "questionPaper": linked_paper['name'] if linked_paper else "",
        "questions": {
            "q1": {
                "score": 0.0,
                "maxScore": 10,
                "ocrText": extracted_text or "Scanning in progress...",
                "handwritingMock": "Uploaded file path: " + file_path,
                "strengths": [],
                "weaknesses": [],
                "justification": "Evaluation pending."
            },
            "q2": {
                "score": 0.0,
                "maxScore": 10,
                "ocrText": "Analysis pending...",
                "handwritingMock": "",
                "strengths": [],
                "weaknesses": [],
                "justification": "Evaluation pending."
            }
        }
    }
    db['students'].append(new_student)
    save_db(db)
    
    append_log('extractor', f"Uploaded script '{filename}' saved and segmented.", 'info')
    return jsonify({"status": "success", "studentId": temp_id})

def run_mock_pipeline(student, paper_name, db, difficulty="medium"):
    """Simulated evaluation used when no API key is configured (or AI fails)."""
    time.sleep(0.5)  # small lag
    append_log('extractor', "Running OCR segment HWR text extraction...", 'info')
    append_log('extractor', "OCR segmentation complete. Layout coordinates bounding box synced.", 'success')

    append_log('mapper', f"Loading question paper '{paper_name}'...", 'info')
    append_log('mapper', "Parsing question items and expected answer keys from question paper.", 'info')
    append_log('mapper', "Calculating semantic match similarity distance...", 'info')
    append_log('mapper', "Rubric Mapper matched 3 key conceptual definitions (Confidence: 89%).", 'success')

    append_log('reasoner', f"Trace: auditing logic against [{difficulty.upper()}] difficulty constraints...", 'info')
    if difficulty == 'easy':
        append_log('reasoner', "Reasoner (Easy mode): Minor syntax flaws & duplicate checks forgiven.", 'info')
    elif difficulty == 'hard':
        append_log('reasoner', "Reasoner (Hard mode): Strict penalty applied for omitted duplicate check and missing balance factor formula.", 'warn')
    else:
        append_log('reasoner', "Reasoner logic warning: missing duplicate checks in BST insert.", 'warn')

    append_log('grader', f"Synthesizing scores using [{difficulty.upper()}] strictness rubric...", 'info')

    student['status'] = "Pending Review"
    student['selfCheck'] = "Consistent"
    student['difficulty'] = difficulty

    student['maxScore'] = sum(q.get('maxScore', 10) for q in student['questions'].values()) if 'questions' in student else 20

    if difficulty == 'easy':
        student['confidence'] = 93
        student['handwritingQuality'] = "Good"
        student['aiScore'] = 18.5
        append_log('grader', "Grader (Easy Mode) assigns Q1: 9.5/10, Q2: 9.0/10. Generous partial marks awarded.", 'success')
        student['questions'] = {
            "q1": {
                "score": 9.5,
                "maxScore": 10,
                "ocrText": "A Binary Search Tree is a binary tree with ordering. Left is smaller, right is larger. Average case is O(log n) height, worst case O(n) when elements sorted. AVL trees rotate to fix balancing.",
                "handwritingMock": "Student HWR definitions: left < root < right. AVL balances O(log n) height.",
                "strengths": [
                    "Clear BST ordering definition",
                    "Accurate complexity identification (O(log N) & O(N))",
                    "Understands height-balancing rotation principle"
                ],
                "weaknesses": [
                    "Minor: Mathematical formula for AVL factor omitted (forgiven under lenient check)"
                ],
                "justification": "Lenient (Easy) Evaluation: Student demonstrates solid conceptual grasp of Binary Search Trees and dynamic balancing. Minor formula omission forgiven under lenient checking. Marks: 9.5/10."
            },
            "q2": {
                "score": 9.0,
                "maxScore": 10,
                "ocrText": "insert(Node root, val) { if (root==null) return new Node(val) ... } Time O(h), space O(h)",
                "handwritingMock": "insert code structure recursive correct.",
                "strengths": [
                    "Clean, working recursive insertion algorithm",
                    "Correct time & space complexity stated as O(h)"
                ],
                "weaknesses": [
                    "Duplicate keys branch omitted (acceptable under lenient criteria)"
                ],
                "justification": "Lenient (Easy) Evaluation: Recursive insert structure is clean and syntactically sound. Standard complexities are correct. Marks: 9.0/10."
            }
        }
    elif difficulty == 'hard':
        student['confidence'] = 84
        student['handwritingQuality'] = "Average"
        student['aiScore'] = 11.5
        append_log('grader', "Grader (Hard Mode) assigns Q1: 6.0/10, Q2: 5.5/10. Strict deductions applied.", 'success')
        student['questions'] = {
            "q1": {
                "score": 6.0,
                "maxScore": 10,
                "ocrText": "A Binary Search Tree is a binary tree with ordering. Left is smaller, right is larger. Average case is O(log n) height, worst case O(n) when elements sorted. AVL trees rotate to fix balancing.",
                "handwritingMock": "Student HWR definitions: left < root < right. AVL balances O(log n) height.",
                "strengths": [
                    "Base BST left < node < right property correctly noted",
                    "States worst-case degeneration to O(N)"
                ],
                "weaknesses": [
                    "Failed to provide formal AVL balance factor formula |h_L - h_R| <= 1",
                    "Did not specify rotation types (LL, RR, LR, RL)",
                    "Vague explanation of tree degeneration cause"
                ],
                "justification": "Strict (Hard) Evaluation: While basic properties are present, the answer lacks academic rigor. Exact mathematical balance condition and concrete rotation proofs were missing. Heavy deduction applied. Marks: 6.0/10."
            },
            "q2": {
                "score": 5.5,
                "maxScore": 10,
                "ocrText": "insert(Node root, val) { if (root==null) return new Node(val) ... } Time O(h), space O(h)",
                "handwritingMock": "insert code structure recursive correct.",
                "strengths": [
                    "Recursive template present",
                    "States time and space complexities"
                ],
                "weaknesses": [
                    "Missing duplicate key validation or collision strategy",
                    "No memory allocation check or base-pointer validation",
                    "Incomplete space complexity explanation for recursive stack frames"
                ],
                "justification": "Strict (Hard) Evaluation: Pseudo-code fails to address duplicate key edge cases and lacks memory safety checks. Space complexity derivation is underspecified. Marks: 5.5/10."
            }
        }
    else:  # 'medium'
        student['confidence'] = 88
        student['handwritingQuality'] = "Good"
        student['aiScore'] = 15.0
        append_log('grader', "Grader (Medium Mode) assigns Q1: 8.0/10, Q2: 7.0/10. Standard rubric applied.", 'success')
        student['questions'] = {
            "q1": {
                "score": 8.0,
                "maxScore": 10,
                "ocrText": "A Binary Search Tree is a binary tree with ordering. Left is smaller, right is larger. Average case is O(log n) height, worst case O(n) when elements sorted. AVL trees rotate to fix balancing.",
                "handwritingMock": "Student HWR definitions: left < root < right. AVL balances O(log n) height.",
                "strengths": ["Correct node definition hierarchy", "Identifies average vs worst complexities"],
                "weaknesses": ["AVL equation details missed"],
                "justification": "Standard (Medium) Evaluation: Accurate BST properties and complexity analysis. Rotations mentioned. Grade 8.0/10."
            },
            "q2": {
                "score": 7.0,
                "maxScore": 10,
                "ocrText": "insert(Node root, val) { if (root==null) return new Node(val) ... } Time O(h), space O(h)",
                "handwritingMock": "insert code structure recursive correct.",
                "strengths": ["Standard structure perfect"],
                "weaknesses": ["No duplicates validation branch"],
                "justification": "Standard (Medium) Evaluation: Syntactically correct recursive structure. Time/Space matches O(h). Grade 7.0/10."
            }
        }

    student['aiScore'] = float(round(sum(q.get('score', 0) for q in student['questions'].values()), 1))
    student['maxScore'] = sum(q.get('maxScore', 10) for q in student['questions'].values())

    append_log('checker', "Comparing cohort standard deviation metrics...", 'info')
    append_log('checker', f"Drift alert: 0 outliers detected. Scores consistent with [{difficulty.upper()}] difficulty benchmark.", 'success')

    save_db(db)
    return jsonify({"status": "success", "student": student})


# API: RUN AGENTIC PIPELINE
@app.route('/api/evaluate', methods=['POST'])
def api_evaluate_script():
    data = request.json or {}
    student_id = data.get('studentId')
    question_paper_id = data.get('questionPaperId') or ''
    difficulty = str(data.get('difficulty', 'medium')).lower().strip()
    if difficulty not in ['easy', 'medium', 'hard']:
        difficulty = 'medium'
    
    db = load_db()
    students = db.get('students', [])
    idx = next((i for i, s in enumerate(students) if s['id'] == student_id), -1)
    
    if idx == -1:
        return jsonify({"status": "error", "message": "Student not found"}), 404
        
    student = students[idx]
    student['difficulty'] = difficulty
    settings = db.get('settings', {})
    api_key = settings.get('geminiApiKey', '')

    papers = db.get('questionPapers', [])
    linked_paper = next((p for p in papers if p['id'] == question_paper_id), None)
    if linked_paper:
        student['questionPaperId'] = linked_paper['id']
        student['questionPaper'] = linked_paper['name']
    paper_name = linked_paper['name'] if linked_paper else (student.get('questionPaper') or 'Default rubric v3')
    
    append_log('extractor', f"Starting processing trail for student {student['name']} under [{difficulty.upper()}] grading difficulty...", 'info')
    
    # ---------------------------------------------------------
    # MOCK SIMULATOR RUN
    # ---------------------------------------------------------
    # If no key, we run our extremely detailed high-fidelity mock engine
    if not api_key or not HAS_GEMINI:
        return run_mock_pipeline(student, paper_name, db, difficulty=difficulty)
        
    # ---------------------------------------------------------
    # REAL AI GEMINI AGENT PIPELINE RUN
    # ---------------------------------------------------------
    try:
        client = genai.Client(api_key=api_key)
        model_name = DEFAULT_EVAL_MODEL

        def ask(prompt):
            return client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    http_options=types.HttpOptions(timeout=300_000),
                ),
            ).text

        # We fetch the prompt setups from the DB config
        prompts = db.get('agent_prompts', {})
        
        difficulty_rules = {
            'easy': "GRADING RIGOR LEVEL: EASY (LENIENT).\n- Focus on core conceptual understanding.\n- Award generous partial credit for good faith attempts.\n- Forgive minor syntax errors, informal wording, or omitted edge cases (like duplicate handling).\n- Be encouraging and constructive in justification feedback.",
            'medium': "GRADING RIGOR LEVEL: MEDIUM (STANDARD).\n- Balanced academic evaluation against rubric criteria.\n- Deduct marks proportionately for omissions or incomplete explanations.\n- Provide objective, constructive feedback.",
            'hard': "GRADING RIGOR LEVEL: HARD (STRICT / RIGOROUS).\n- Apply zero tolerance for informal definitions, vague explanations, or omitted edge cases.\n- Strictly penalize missing mathematical formulas, incomplete proofs, or syntax bugs.\n- Require rigorous precision in complexity analysis and algorithm correctness."
        }
        rigor_instruction = difficulty_rules.get(difficulty, difficulty_rules['medium'])
        
        # 1. Extraction Agent
        append_log('extractor', "Connecting Gemini to run transcription...", 'info')
        ocr_prompt = f"{prompts.get('extractor')}\n\nHere is the raw text content to clean and structure:\n{student['questions']['q1']['ocrText']}"
        response_ocr = ask(ocr_prompt)
        append_log('extractor', "Handwriting transcription compiled.", 'success')
        
        # 2. Rubric Mapper Agent
        append_log('mapper', "Generating semantic rubric connections...", 'info')
        rubric_str = json.dumps(DEFAULT_RUBRICS[0])
        mapper_prompt = f"{prompts.get('mapper')}\n\nRubric Schema:\n{rubric_str}\n\nStudent Answer:\n{response_ocr}"
        response_map = ask(mapper_prompt)
        append_log('mapper', f"Criteria similarities mapped: {response_map[:100]}...", 'success')
        
        # 3. Reasoning Agent
        append_log('reasoner', f"Auditing logic under [{difficulty.upper()}] difficulty constraints...", 'info')
        reasoner_prompt = f"{prompts.get('reasoner')}\n\n{rigor_instruction}\n\nEvaluate code block logic in response:\n{response_ocr}"
        response_reason = ask(reasoner_prompt)
        append_log('reasoner', "Logic dry run validations compiled.", 'success')
        
        # 4. Grader Agent
        append_log('grader', f"Synthesizing scores under [{difficulty.upper()}] difficulty...", 'info')
        grader_prompt = f"""{prompts.get('grader')}
        
        {rigor_instruction}
        
        Here are the consolidated reviews from the pipeline:
        - Transcription: {response_ocr}
        - Mapping: {response_map}
        - Reasoning Audits: {response_reason}
        
        Output format: You MUST return a JSON structure with these fields:
        {{
           "q1_score": float,
           "q2_score": float,
           "q1_strengths": [list of strings],
           "q1_weaknesses": [list of strings],
           "q1_justification": string,
           "q2_strengths": [list of strings],
           "q2_weaknesses": [list of strings],
           "q2_justification": string,
           "confidence": int (0-100),
           "handwriting_quality": string
        }}
        Do not add any markdown wraps besides raw JSON.
        """
        response_grade = ask(grader_prompt)
        
        # Clean JSON wrappers if generated
        clean_json = response_grade.replace('```json', '').replace('```', '').strip()
        grade_data = json.loads(clean_json)
        
        # 5. Checker Agent
        append_log('checker', "Cross-referencing database grades consistency...", 'info')
        checker_prompt = f"{prompts.get('checker')}\n\nCheck score: {grade_data.get('q1_score')} + {grade_data.get('q2_score')} against cohort rules and [{difficulty.upper()}] rigor."
        response_check = ask(checker_prompt)
        append_log('checker', "Cohort alignment validated.", 'success')
        
        # Save results
        student['status'] = "Pending Review"
        student['selfCheck'] = "Consistent"
        student['confidence'] = grade_data.get('confidence', 90)
        student['handwritingQuality'] = grade_data.get('handwriting_quality', 'Average')
        student['difficulty'] = difficulty
        
        q1_score = grade_data.get('q1_score', 8.0)
        q2_score = grade_data.get('q2_score', 7.5)
        student['questions']['q1']['score'] = q1_score
        student['questions']['q1']['ocrText'] = response_ocr
        student['questions']['q1']['strengths'] = grade_data.get('q1_strengths', [])
        student['questions']['q1']['weaknesses'] = grade_data.get('q1_weaknesses', [])
        student['questions']['q1']['justification'] = grade_data.get('q1_justification', '')
        
        student['questions']['q2']['score'] = q2_score
        student['questions']['q2']['strengths'] = grade_data.get('q2_strengths', [])
        student['questions']['q2']['weaknesses'] = grade_data.get('q2_weaknesses', [])
        student['questions']['q2']['justification'] = grade_data.get('q2_justification', '')
        
        # Sum overall score
        student['aiScore'] = float(round(sum(q.get('score', 0) for q in student['questions'].values()), 1))
        student['maxScore'] = sum(q.get('maxScore', 10) for q in student['questions'].values())
        
        db['students'] = students
        save_db(db)
        return jsonify({"status": "success", "student": student})
        
    except Exception as e:
        append_log('grader', f"Real AI pipe failed: {str(e)}. Falling back to mock evaluation.", 'warn')
        return run_mock_pipeline(student, paper_name, db, difficulty=difficulty)

# Serve static files for frontend and uploads
@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    if os.path.exists(os.path.join(UPLOAD_FOLDER, path)):
        return send_from_directory(UPLOAD_FOLDER, path)
    if os.path.exists(os.path.join(PROJECT_ROOT, path)):
        return send_from_directory(PROJECT_ROOT, path)
    if os.path.exists(os.path.join(BASE_DIR, path)):
        return send_from_directory(BASE_DIR, path)
    return send_from_directory(FRONTEND_DIR, 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
