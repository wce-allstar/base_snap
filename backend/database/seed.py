"""Seed data for db.json (preserved verbatim from the original server.py)."""

INITIAL_STUDENTS = [
  {
    "id": "CS2026-084",
    "name": "Amit Patel",
    "format": "Scanned PDF (Handwritten)",
    "aiScore": 32.5,
    "maxScore": 50,
    "confidence": 89,
    "status": "Pending Review",
    "selfCheck": "Consistent",
    "handwritingQuality": "Average",
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
    "aiScore": 44.0,
    "maxScore": 50,
    "confidence": 96,
    "status": "Pending Review",
    "selfCheck": "Consistent",
    "handwritingQuality": "Not Applicable",
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
    "aiScore": 18.5,
    "maxScore": 50,
    "confidence": 76,
    "status": "Pending Review",
    "selfCheck": "Flagged: Low Confidence",
    "handwritingQuality": "Poor / Scrawly",
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

DEFAULT_AGENT_PROMPTS = {
  "extractor": "System Role: OCR & Handwriting Ingestion Specialist\nTask: Convert raw handwritten scanned scripts (JPEG/PNG/PDF) into structured digitized text.\nInstructions:\n1. Perform high-precision Handwriting Character Recognition (HWR).\n2. Preserve original formatting, indentation, and structure (especially for pseudo-code blocks).\n3. If handwriting is illegible, flag with [UNCERTAIN_OCR] markers and output raw layout coordinates.\n4. Output structured output mapped per Question ID.",
  "mapper": "System Role: Semantic Rubric Mapping Agent\nTask: Align digitized student answers with rubric criteria points.\nInstructions:\n1. Match conceptual sentences in student answers to target rubric points.\n2. Rely on semantic understanding, synonyms, and logical equivalence (not mere keyword matching).\n3. Calculate similarity matrices for each rubric criterion.\n4. Grade coverage: 'Fully Covered', 'Partially Covered', or 'Not Covered'.",
  "reasoner": "System Role: Logical Reasoning & Flow Checking Agent\nTask: Audit mathematical proofs, algorithms, and step-by-step logic.\nInstructions:\n1. Trace algorithm execution steps in code blocks.\n2. Check for logical leaps, invalid loops, off-by-one errors, or incomplete derivations.\n3. Assess the soundness of reasoning behind explanations.\n4. Provide technical feedback on code or logic failures.",
  "structurer": "System Role: Text Cleaner & Question Splitter Agent\nTask: Clean noisy OCR text and split it into numbered question packets.\nInstructions:\n1. Remove headers, footers, page numbers, and scanning artifacts.\n2. Identify each question by its number (1., 2., 3. ...) and keep answers with their numbers.\n3. Preserve code blocks, indentation, and any text describing diagrams.\n4. Keep every question even if the answer is partial or blank.\n5. Do not invent questions that are not present in the text.",
  "grader": "System Role: Explainable Justification & Marks Assigner\nTask: Compute marks per question based on mapping, reasoning, and coverage checks, generating detailed constructive feedback.\nInstructions:\n1. Assign marks for each rubric item based on coverage classification.\n2. Draft an examiner-style feedback explaining EXACTLY why marks were deducted or awarded.\n3. Do not sound generic; refer to specific lines of the student response.\n4. Generate confidence metrics based on OCR clarity and rubric matching confidence.",
  "checker": "System Role: Multi-Sheet Grading Consistency & Bias Audit Agent\nTask: Cross-reference grades across student cohorts to identify grading drift, strictness shifts, or demographic/format bias.\nInstructions:\n1. Maintain vector indexes of grades and matching descriptions.\n2. Compare score variance for similar answers.\n3. Alert human moderator if grading strictness changes over time or if scanned writing is graded lower than typed text of equivalent semantic weight.",
  "feedback": "System Role: Examiner-Style Feedback Writer\nTask: Generate concise, constructive feedback for a question.\nInstructions:\n1. List 2-4 strengths based on rubric coverage and reasoning notes.\n2. List 2-3 missing items, precise and actionable.\n3. End feedback_text with a short marks summary line."
}

SEED_LOGS = {
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
  ],
  "structurer": [
    { "type": "system", "text": "Cleaner & Question Splitter active." }
  ],
  "feedback": [
    { "type": "system", "text": "Feedback writer standing by." }
  ]
}