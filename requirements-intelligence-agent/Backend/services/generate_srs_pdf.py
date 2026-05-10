import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def create_pdf(srs_text, meeting_id):

    os.makedirs("generated_pdfs", exist_ok=True)

    pdf_path = f"generated_pdfs/{meeting_id}.pdf"

    doc = SimpleDocTemplate(pdf_path)

    styles = getSampleStyleSheet()

    story = []

    paragraphs = srs_text.split("\n")

    for para in paragraphs:

        para = para.strip()

        if para:
            story.append(
                Paragraph(para, styles["BodyText"])
            )

            story.append(Spacer(1, 12))

    doc.build(story)

    return pdf_path