from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
import os

import reportlab
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether

DISCLAIMER = "Probe scores indicate similarity to learned error representations and are not calibrated probabilities or proof of factual incorrectness. The probe was trained on HotpotQA-style controlled factual corruptions and may not generalize to unrelated domains."


def make_report(result):
    font = "InspectorReport"
    if font not in pdfmetrics.getRegisteredFontNames():
        font_path = os.environ.get("REPORT_FONT") or str(Path(reportlab.__file__).parent / "fonts" / "Vera.ttf")
        pdfmetrics.registerFont(TTFont(font, font_path))
    available = pdfmetrics.getFont(font).face.charWidths

    def text(value):
        raw = str(value).replace("→", " -> ")
        raw = "".join(c if ord(c) in available or c in "\n\t" else f"[U+{ord(c):04X}]" for c in raw)
        return escape(raw).replace("\n", "<br/>")

    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName = font
    body = ParagraphStyle("InspectorBody", parent=styles["BodyText"], fontSize=9, leading=14, spaceAfter=8, wordWrap="CJK")
    heading = ParagraphStyle("InspectorHeading", parent=body, textColor=colors.HexColor("#2855e8"), fontSize=12, leading=17, spaceBefore=13, keepWithNext=True)
    small = ParagraphStyle("InspectorSmall", parent=body, fontSize=8, leading=12, textColor=colors.HexColor("#607087"))
    story = [Paragraph("Reasoning Error Inspector", styles["Title"]), Paragraph("Experimental factual reasoning diagnostic", small)]
    def section(title, value):
        story.extend([Paragraph(text(title), heading), Paragraph(text(value), body)])
    section("Question", result["question"])
    section("Generated answer", result["answer"])
    if result.get("answer_note"):
        story.append(Paragraph(text(result["answer_note"]), small))
    story.append(Paragraph(text(f"Reference: {result.get('reference_source', 'Pasted evidence')}"), small))
    first = result["first_flagged_hop"]
    section("Probe localization", (f"First flagged hop: {first}. " if first else "No hop crossed the learned threshold. ") +
            f"Highest-scoring hop: {result['most_suspicious_hop']}. Threshold: {result['threshold']:.3f}.")
    for hop in result["hops"]:
        label = f"Hop {hop['index']} | error score {hop['error_score']:.3f} | " + ("FLAGGED" if hop['flagged'] else "Not flagged")
        story.append(KeepTogether([Paragraph(text(label), heading), Paragraph(text(hop["text"]), body)]))
    if result.get("controlled_error"):
        edit = result["controlled_error"]
        section("CONTROLLED TEST ERROR", f"Inserted at Hop {edit['hop_index']}. " +
                ("The highest-scoring hop matched the edit." if edit["correct_localization"] else "The highest-scoring hop did not match the edit."))
        section("Original / edited assertion", edit["original"] + "\n" + edit["corrupted"])
        story.append(Paragraph(text(edit.get("note", "")), small))
    evidence = result["evidence_analysis"]
    section("Separate evidence-based explanation", evidence["status"])
    for label, key in [("Claim", "claim"), ("Reference quote", "evidence"), ("Claimed value", "claimed_value"),
                       ("Supported value", "supported_value"), ("Assessment", "explanation")]:
        if evidence.get(key):
            story.append(Paragraph(text(f"{label}: {evidence[key]}"), body))
    section("Evidence used", result["reference_context"])
    if result.get("retrieval", {}).get("used"):
        story.append(Paragraph("Only retrieved excerpts were analyzed. Omitted document content was not checked.", small))
    section("Model and probe", f"{result['model']['name']} | block {result['model']['layer']} | {result['model']['device']}\nRevision: {result['model']['revision']}")
    story.append(Paragraph(text(DISCLAIMER), small))
    for warning in result.get("warnings", []):
        story.append(Paragraph(text(warning), small))
    stream = BytesIO()
    doc = SimpleDocTemplate(stream, title="Reasoning diagnostic", author="Reasoning Error Inspector",
                           leftMargin=44, rightMargin=44, topMargin=38, bottomMargin=42)
    def page_number(canvas, document):
        canvas.setFont(font, 8)
        canvas.setFillColor(colors.HexColor("#607087"))
        canvas.drawString(44, 23, "Reasoning Error Inspector | Experimental diagnostic")
        canvas.drawRightString(document.pagesize[0]-44, 23, str(document.page))
    doc.build(story, onFirstPage=page_number, onLaterPages=page_number)
    return stream.getvalue()
