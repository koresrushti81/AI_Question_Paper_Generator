import os
import tempfile
from fpdf import FPDF
from datetime import datetime


class QuestionPaperPDF(FPDF):
    def __init__(self, institution_name, subject, stream, difficulty, date, marks, instructions, paper_id):
        super().__init__()
        self.institution_name = institution_name
        self.subject = subject
        self.stream = stream
        self.difficulty = difficulty
        self.exam_date = date
        self.marks = marks
        self.instructions = instructions
        self.paper_id = paper_id

    def header(self):
        # Top decorative line
        self.set_draw_color(30, 58, 138)
        self.set_line_width(1.2)
        self.line(10, 10, 200, 10)
        self.ln(5)

        # Institution Name
        self.set_font('Helvetica', 'B', 18)
        self.set_text_color(30, 58, 138)
        self.cell(0, 10, self.institution_name, align='C', new_x="LMARGIN", new_y="NEXT")

        # Subtitle
        self.set_font('Helvetica', '', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, f"Department of {self.stream}  |  Semester Examination", align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

        # Subject
        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(30, 30, 30)
        self.cell(0, 8, f"Subject: {self.subject}", align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        # Meta row
        self.set_font('Helvetica', '', 10)
        self.set_text_color(60, 60, 60)
        self.cell(65, 7, f"Date: {self.exam_date}")
        self.cell(65, 7, f"Total Marks: {self.marks}", align='C')
        self.cell(0, 7, f"Difficulty: {self.difficulty}", align='R', new_x="LMARGIN", new_y="NEXT")

        # Paper ID
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, f"Paper ID: {self.paper_id}", align='R', new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        # Separator line
        self.set_draw_color(30, 58, 138)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

        # Instructions
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(30, 30, 30)
        self.cell(0, 5, "General Instructions:", new_x="LMARGIN", new_y="NEXT")
        self.set_font('Helvetica', 'I', 9)
        self.set_text_color(70, 70, 70)
        self.multi_cell(0, 5, self.instructions)
        self.ln(3)

        # Another separator
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(30, 58, 138)
        self.set_line_width(0.5)
        self.line(10, self.get_y() - 2, 200, self.get_y() - 2)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}  |  {self.institution_name}', align='C')


def create_pdf(paper_data, institution="Dr. D.Y. Patil College of Engineering and Technology"):
    default_instructions = (
        "1. All questions are compulsory unless stated otherwise.\n"
        "2. Figures to the right indicate full marks.\n"
        "3. Assume suitable data wherever necessary.\n"
        "4. Write your roll number clearly on the answer sheet."
    )

    date_str = (
        paper_data['date'].strftime("%d %B %Y")
        if isinstance(paper_data['date'], datetime)
        else str(paper_data['date'])
    )

    pdf = QuestionPaperPDF(
        institution_name=institution,
        subject=paper_data['subject'],
        stream=paper_data.get('stream', 'General'),
        difficulty=paper_data.get('difficulty', 'Medium'),
        date=date_str,
        marks=str(paper_data['marks']),
        instructions=paper_data.get('instructions', default_instructions),
        paper_id=paper_data.get('id', 'N/A')
    )

    pdf.alias_nb_pages()
    pdf.add_page()

    sections = paper_data['sections']
    section_colors = {
        'A': (30, 58, 138),   # Navy
        'B': (5, 100, 70),    # Dark Green
        'C': (120, 40, 10),   # Dark Brown/Red
    }

    for sec_key in ['A', 'B', 'C']:
        if sec_key not in sections:
            continue
        sec = sections[sec_key]
        if sec['count'] <= 0:
            continue

        r, g, b = section_colors.get(sec_key, (30, 58, 138))

        # Section header background
        pdf.set_fill_color(r, g, b)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 9, f"  SECTION {sec_key}  -  {sec['name'].upper()}", fill=True, new_x="LMARGIN", new_y="NEXT")

        # Marks note
        pdf.set_text_color(80, 80, 80)
        pdf.set_font('Helvetica', 'I', 9)
        pdf.cell(0, 6, f"  (Attempt all questions. Each question carries {sec['marks_per_q']} marks.)", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        # Questions
        pdf.set_font('Helvetica', '', 11)
        pdf.set_text_color(20, 20, 20)
        for i, q in enumerate(sec['questions'], 1):
            # Question number in bold
            pdf.set_font('Helvetica', 'B', 11)
            q_label = f"Q{i}."
            pdf.cell(10, 8, q_label)

            # Question text
            pdf.set_font('Helvetica', '', 11)
            # marks in right margin
            x_before = pdf.get_x()
            pdf.multi_cell(170, 8, q, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)

        pdf.ln(6)

    # Output
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        filename = tmp_file.name

    pdf.output(filename)

    with open(filename, "rb") as f:
        pdf_bytes = f.read()

    try:
        os.remove(filename)
    except OSError:
        pass

    return pdf_bytes