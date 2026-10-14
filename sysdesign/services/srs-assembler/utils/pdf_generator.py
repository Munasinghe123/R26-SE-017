import io
import re
import os
import base64
import logging
import urllib.request
from pathlib import Path
from PIL import Image as PILImage
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

logger = logging.getLogger("srs-assembler.pdf_generator")


def sanitize_pdf_text(text: str) -> str:
    """
    Sanitizes Unicode characters that cause missing glyphs (.notdef / black squares)
    in ReportLab's standard Helvetica fonts.
    Replaces non-breaking hyphens (fixes 'on■premises', 'third■party'), en/em dashes,
    smart quotes, and missing characters with clean ASCII equivalents.
    """
    if not text:
        return ""

    # Hyphens, dashes, and minus signs
    dash_map = {
        "\u2010": "-",   # Hyphen
        "\u2011": "-",   # Non-breaking hyphen (fixes 'on■premises', 'third■party')
        "\u2012": "-",   # Figure dash
        "\u2013": "-",   # En dash
        "\u2014": " - ", # Em dash
        "\u2015": " - ", # Horizontal bar
        "\u2212": "-",   # Minus sign
        "\u00ad": "",    # Soft hyphen
        "\ufe58": " - ", # Small em dash
        "\ufe63": "-",   # Small hyphen-minus
        "\uff0d": "-",   # Fullwidth hyphen-minus
    }
    for k, v in dash_map.items():
        text = text.replace(k, v)

    # Replace literal black square artifacts or replacement chars between words with hyphens
    text = re.sub(r"(\w)[■\u25a0\u25a1\u25aa\u25ab\u25fe\u25fc\u2588\ufffd](\w)", r"\1-\2", text)
    # Strip any remaining stray black squares
    text = re.sub(r"[■\u25a0\u25a1\u25aa\u25ab\u25fe\u25fc\u2588\ufffd]", "", text)

    # Curly quotes to ASCII quotes
    quote_map = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201a": "'",
        "\u201b": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u201e": '"',
        "\u201f": '"',
        "\u00ab": '"',
        "\u00bb": '"',
        "\u2032": "'",
        "\u2033": '"',
    }
    for k, v in quote_map.items():
        text = text.replace(k, v)

    # Spaces & zero-width characters
    space_map = {
        "\u00a0": " ",
        "\u2000": " ", "\u2001": " ", "\u2002": " ", "\u2003": " ",
        "\u2004": " ", "\u2005": " ", "\u2006": " ", "\u2007": " ",
        "\u2008": " ", "\u2009": " ", "\u200a": " ",
        "\u202f": " ", "\u205f": " ", "\u3000": " ",
        "\u200b": "", "\u200c": "", "\u200d": "", "\ufeff": "",
    }
    for k, v in space_map.items():
        text = text.replace(k, v)

    # Symbols & math
    symbol_map = {
        "\u2026": "...",
        "\u00a7": "Sec. ",
        "\u2192": "->",
        "\u27f6": "->",
        "\u2190": "<-",
        "\u2194": "<->",
        "\u2264": "<=",
        "\u2265": ">=",
        "\u2260": "!=",
        "\u00d7": "x",
        "\u00f7": "/",
        "\u00b1": "+/-",
    }
    for k, v in symbol_map.items():
        text = text.replace(k, v)

    return text


def _format_inline_markdown(text: str) -> str:
    """Converts basic markdown **bold**, *italic*, `code` into ReportLab HTML tags."""
    text = sanitize_pdf_text(text)
    # Escape XML entities before wrapping in tags
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Bold **text**
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    # Italic *text*
    text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)
    # Inline code `code`
    text = re.sub(r"`(.*?)`", r'<font face="Courier" color="#0369a1">\1</font>', text)
    return text


def _fetch_and_create_image_flowable(
    img_url: str,
    alt_text: str,
    max_width: float = 490,
    max_height: float = 320,
    caption_style: ParagraphStyle = None,
) -> list:
    """
    Downloads or decodes an image from Cloudinary, base64 data URI, or local path,
    calculates proportional dimensions, and returns ReportLab Flowables.
    """
    flowables = []
    img_bytes = None

    try:
        if img_url.startswith("data:image/"):
            # Base64 data URL
            _, b64_data = img_url.split(",", 1)
            img_bytes = base64.b64decode(b64_data)
        elif img_url.startswith("http://") or img_url.startswith("https://"):
            req = urllib.request.Request(
                img_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SysDesign-SRS/1.0"}
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                img_bytes = response.read()
        else:
            local_path = Path(img_url)
            if local_path.exists():
                with open(local_path, "rb") as f:
                    img_bytes = f.read()

        if img_bytes:
            with PILImage.open(io.BytesIO(img_bytes)) as pil_img:
                orig_w, orig_h = pil_img.size
                if orig_w > 0 and orig_h > 0:
                    scale = min(max_width / orig_w, max_height / orig_h, 1.0)
                    target_w = orig_w * scale
                    target_h = orig_h * scale

                    flowables.append(Spacer(1, 4))
                    flowables.append(RLImage(io.BytesIO(img_bytes), width=target_w, height=target_h))
                    flowables.append(Spacer(1, 2))
    except Exception as exc:
        logger.warning(f"Could not embed image '{alt_text}' from {img_url}: {exc}")

    if not flowables:
        # Fallback if download fails or URL isn't a valid image
        fallback_text = f"<b>[Artifact Diagram: {alt_text}]</b> (URI: <font color='#0284c7'>{img_url}</font>)"
        if caption_style:
            flowables.append(Paragraph(fallback_text, caption_style))
        flowables.append(Spacer(1, 4))
    elif caption_style:
        flowables.append(Paragraph(f"<i>Figure: {alt_text}</i>", caption_style))
        flowables.append(Spacer(1, 6))

    return flowables


def generate_srs_pdf_bytes(srs_markdown: str, project_name: str, job_id: str) -> bytes:
    """
    Compiles an IEEE 29148 SRS markdown string into styled PDF bytes completely in-memory.
    Zero dependency on local drives or project folders.
    """
    # Sanitize markdown globally before parsing
    srs_markdown = sanitize_pdf_text(srs_markdown)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    base_styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "SRS_Title",
        parent=base_styles["Title"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        alignment=0,
        spaceAfter=10,
    )
    h1_style = ParagraphStyle(
        "SRS_H1",
        parent=base_styles["Heading1"],
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=14,
        spaceAfter=6,
    )
    h2_style = ParagraphStyle(
        "SRS_H2",
        parent=base_styles["Heading2"],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#334155"),
        spaceBefore=10,
        spaceAfter=4,
    )
    h3_style = ParagraphStyle(
        "SRS_H3",
        parent=base_styles["Heading3"],
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor("#475569"),
        spaceBefore=6,
        spaceAfter=2,
    )
    h4_style = ParagraphStyle(
        "SRS_H4",
        parent=base_styles["Heading3"],
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=8,
        spaceAfter=2,
        fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "SRS_Body",
        parent=base_styles["BodyText"],
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=4,
    )
    bullet_style = ParagraphStyle(
        "SRS_Bullet",
        parent=base_styles["BodyText"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334155"),
        leftIndent=15,
        spaceAfter=2,
    )
    table_cell_style = ParagraphStyle(
        "SRS_TableCell",
        parent=base_styles["BodyText"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1e293b"),
    )
    table_header_style = ParagraphStyle(
        "SRS_TableHeader",
        parent=base_styles["BodyText"],
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        fontName="Helvetica-Bold",
    )
    figure_caption_style = ParagraphStyle(
        "SRS_Caption",
        parent=base_styles["BodyText"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#64748b"),
        alignment=1,  # Center
        spaceAfter=6,
    )

    story = []
    lines = srs_markdown.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        # Horizontal Rule
        if line.startswith("---"):
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceBefore=6, spaceAfter=8))
            i += 1
            continue

        # Markdown Image Embedding: ![alt](url)
        img_match = re.match(r"^!\[(.*?)\]\((.*?)\)$", line)
        if img_match:
            alt_text = img_match.group(1).strip()
            img_url = img_match.group(2).strip()
            flowables = _fetch_and_create_image_flowable(
                img_url=img_url,
                alt_text=alt_text,
                max_width=490,
                max_height=320,
                caption_style=figure_caption_style,
            )
            for f in flowables:
                story.append(f)
            i += 1
            continue

        # Headers
        if line.startswith("# "):
            story.append(Paragraph(_format_inline_markdown(line[2:].strip()), title_style))
            story.append(Spacer(1, 4))
            i += 1
            continue
        elif line.startswith("## "):
            story.append(Paragraph(_format_inline_markdown(line[3:].strip()), h1_style))
            i += 1
            continue
        elif line.startswith("### "):
            story.append(Paragraph(_format_inline_markdown(line[4:].strip()), h2_style))
            i += 1
            continue
        elif line.startswith("#### "):
            story.append(Paragraph(_format_inline_markdown(line[5:].strip()), h3_style))
            i += 1
            continue
        elif line.startswith("##### "):
            story.append(Paragraph(_format_inline_markdown(line[6:].strip()), h4_style))
            i += 1
            continue

        # Markdown Table Parsing (| col1 | col2 |)
        if line.startswith("|") and line.endswith("|"):
            table_raw = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row_str = lines[i].strip()
                # Skip divider row |---|---|
                if not re.match(r"^\|(\s*[-:]+\s*\|)+$", row_str):
                    cols = [c.strip() for c in row_str.strip("|").split("|")]
                    table_raw.append(cols)
                i += 1

            if table_raw:
                # Format cells into Paragraphs with inline styling
                formatted_table = []
                for row_idx, row in enumerate(table_raw):
                    f_row = []
                    for col in row:
                        clean_col = _format_inline_markdown(col.strip())
                        if row_idx == 0:
                            f_row.append(Paragraph(clean_col, table_header_style))
                        else:
                            f_row.append(Paragraph(clean_col, table_cell_style))
                    formatted_table.append(f_row)

                t = Table(formatted_table, colWidths=None)
                t.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
                    ])
                )
                story.append(t)
                story.append(Spacer(1, 8))
            continue

        # Bullet Points
        if line.startswith("- ") or line.startswith("* "):
            formatted_text = _format_inline_markdown(line[2:].strip())
            story.append(Paragraph(f"&bull; {formatted_text}", bullet_style))
            i += 1
            continue

        # Normal Paragraph
        formatted_text = _format_inline_markdown(line)
        story.append(Paragraph(formatted_text, body_style))
        story.append(Spacer(1, 3))
        i += 1

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


