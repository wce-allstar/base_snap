import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_pdf():
    pdf_path = "sample_student_paper.pdf"
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles for descriptive handwritten-feel paper
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        alignment=1, # Center
        spaceAfter=12
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569'),
        alignment=1, # Center
        spaceAfter=20
    )
    
    question_style = ParagraphStyle(
        'QuestionStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=15,
        spaceAfter=8,
        borderPadding=6,
        borderColor=colors.HexColor('#cbd5e1'),
        borderWidth=0.5,
        borderRadius=4,
        backColor=colors.HexColor('#f8fafc')
    )
    
    student_style = ParagraphStyle(
        'StudentStyle',
        parent=styles['Normal'],
        fontName='Courier-Oblique',
        fontSize=10,
        leading=16,
        textColor=colors.HexColor('#1b2a4a')
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Code'],
        fontName='Courier',
        fontSize=9,
        leading=12,
        leftIndent=20,
        spaceBefore=6,
        spaceAfter=6,
        textColor=colors.HexColor('#0f172a')
    )
    
    story = []
    
    # Institution Banner
    story.append(Paragraph("State Institute of Technology (SIT)", title_style))
    story.append(Paragraph("CS101: Midterm Exam - Data Structures & Algorithms", subtitle_style))
    
    # Metadata Table
    meta_data = [
        [Paragraph("<b>Student Name:</b> Siddharth Sen", student_style), Paragraph("<b>Roll Number:</b> CS2026-092", student_style)],
        [Paragraph("<b>Session:</b> Fall 2026 Semester", student_style), Paragraph("<b>Date:</b> August 3, 2026", student_style)]
    ]
    t = Table(meta_data, colWidths=[250, 250])
    t.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor('#94a3b8')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))
    
    # Question 1
    story.append(Paragraph("<b>Question 1 (10 Marks):</b> Define a Binary Search Tree (BST) and write its search complexity. Explain why search complexity can degenerate to O(N) and how height-balanced trees (AVL/Red-Black) solve this.", question_style))
    
    ans_q1_text = """<b>Answer 1:</b><br/>
    A Binary Search Tree (BST) is a node-based binary tree data structure with the following recursive properties:<br/>
    1. The left subtree of a node contains only nodes with keys less than the node's key.<br/>
    2. The right subtree of a node contains only nodes with keys greater than the node's key.<br/>
    3. Both the left and right subtrees must also be binary search trees.<br/><br/>
    
    <b>Search Complexity:</b><br/>
    - <i>Best and Average Case:</i> O(log N), where N is the number of nodes. In a balanced BST, the height of the tree is bounded by log N, meaning search path halves at each level.<br/>
    - <i>Worst Case:</i> O(N). This occurs when the tree becomes unbalanced. For example, if elements are inserted in a pre-sorted order (e.g., 1, 2, 3, 4, 5), the tree degenerates into a linear chain (known as a skewed tree), resembling a linked list. In this state, searches require linear scanning.<br/><br/>
    
    <b>Height-Balanced Solution (AVL):</b><br/>
    AVL trees solve this degeneration problem by enforcing structural balance constraints. Specifically, they maintain a balance factor BF = |height(Left Subtree) - height(Right Subtree)| <= 1 for every node. If an insertion or deletion violates this property (BF > 1), AVL trees trigger rebalancing rotations (Single LL/RR, or Double LR/RL rotations) to reduce height. This guarantees that the height h remains strictly bounded by O(log N), keeping lookup complexity consistently at O(log N)."""
    
    story.append(Paragraph(ans_q1_text, student_style))
    story.append(Spacer(1, 15))
    
    # Question 2
    story.append(Paragraph("<b>Question 2 (10 Marks):</b> Write the pseudo-code for inserting a node in a BST. Explain the algorithm's time and space complexity.", question_style))
    
    ans_q2_intro = """<b>Answer 2:</b><br/>
    Here is the recursive logic for inserting a key value in a Binary Search Tree:"""
    story.append(Paragraph(ans_q2_intro, student_style))
    
    code_text = """Node insert(Node root, int val) {
    // Base Case: return a new node if tree is empty
    if (root == null) {
        return new Node(val);
    }
    
    // Recursive traversal directions
    if (val < root.key) {
        root.left = insert(root.left, val);
    } else if (val > root.key) {
        root.right = insert(root.right, val);
    }
    
    // Duplicate values are ignored in this implementation
    return root;
}"""
    story.append(Paragraph(code_text.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_style))
    
    ans_q2_outro = """<b>Complexity Explanations:</b><br/>
    - <i>Time Complexity:</i> O(h), where h is the tree height. If the tree is height-balanced, h is O(log N). If the tree degenerates into a skewed structure, h is O(N) as it traverses all nodes.<br/>
    - <i>Space Complexity:</i> O(h) auxiliary stack space. Because the code is recursive, each call places a stack frame in memory. In worst-case skewed trees, this requires O(N) stack frames. (An iterative implementation would require O(1) space)."""
    
    story.append(Paragraph(ans_q2_outro, student_style))
    
    doc.build(story)
    print("Successfully generated sample_student_paper.pdf")

if __name__ == '__main__':
    generate_pdf()
