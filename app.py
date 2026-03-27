#!/usr/bin/env python3

"""
OBC Invoice Generator — Web Server
Run: python app.py
Then open: http://<NAS-IP>:5050
"""

import json, os, tempfile, uuid
from datetime import date
from flask import Flask, request, jsonify, send_file, render_template
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader, PdfWriter

# ── Register Chinese Fonts ────────────────────────────────────────────────────
try:
    # Try to register system fonts for Chinese support
    # For Windows
    if os.path.exists("C:\\Windows\\Fonts\\msyh.ttc"):  # Microsoft YaHei
        pdfmetrics.registerFont(TTFont("SimHei", "C:\\Windows\\Fonts\\SimHei.ttf"))
        pdfmetrics.registerFont(TTFont("MicrosoftYaHei", "C:\\Windows\\Fonts\\msyh.ttc"))
    # For Linux/Mac - common Chinese font locations
    elif os.path.exists("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"):
        pdfmetrics.registerFont(TTFont("ChineseFont", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"))
    elif os.path.exists("/System/Library/Fonts/STHeiti Light.ttc"):  # macOS
        pdfmetrics.registerFont(TTFont("ChineseFont", "/System/Library/Fonts/STHeiti Light.ttc"))
except Exception as e:
    print(f"Warning: Could not register Chinese fonts: {e}")

# Define a Chinese-compatible font name (fallback)
CHINESE_FONT = "MicrosoftYaHei" if os.path.exists("C:\\Windows\\Fonts\\msyh.ttc") else "ChineseFont"
if not os.path.exists("C:\\Windows\\Fonts\\msyh.ttc") and not os.path.exists("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc") and not os.path.exists("/System/Library/Fonts/STHeiti Light.ttc"):
    CHINESE_FONT = "Helvetica"  # Fallback to Helvetica if no Chinese font found

# ── Config ────────────────────────────────────────────────────────────────────
app         = Flask(__name__)
DATA_FILE   = os.path.join(os.path.dirname(__file__), "templates", "invoice_data.json")
UPLOAD_DIR  = os.path.join(os.path.dirname(__file__), "uploads")
OUTPUT_DIR  = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

A4_W, A4_H = A4

DEFAULT_DATA = {
    "from_profiles": [{
        "name": "Default Profile", "full_name": "OBC Full Name",
        "street": "House No. & Street", "post_code": "Post Code", "city": "City"
    }],
    "billto_profiles": [{
        "name": "Default Client", "company": "Company Name", "address": "Client Address"
    }],
    "payment_profiles": [{
        "name": "Default Bank", "payment": "Bank Transfer",
        "bank_name": "Bank Name & Address", "beneficiary": "Beneficiary Name",
        "swift": "SWIFT Code", "iban": "Account Number / IBAN"
    }]
}

# ── Profiles persistence ───────────────────────────────────────────────────────
def load_profiles():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_DATA.copy()

def save_profiles(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ── PDF Generation ─────────────────────────────────────────────────────────────
def generate_pdf(form_data, output_path):
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=15*mm, bottomMargin=15*mm
    )

    # Styles - use Chinese font for content, Helvetica for English headers
    title_s  = ParagraphStyle("T",  fontSize=26, textColor=colors.HexColor("#1a1a2e"),
                               fontName="Helvetica-Bold", alignment=TA_RIGHT, spaceAfter=6)
    head_s   = ParagraphStyle("H",  fontSize=9,  textColor=colors.HexColor("#888888"),
                               fontName="Helvetica", spaceAfter=1)
    val_s    = ParagraphStyle("V",  fontSize=10, textColor=colors.HexColor("#1a1a2e"),
                               fontName=CHINESE_FONT, spaceAfter=2, leading=14)
    bold_s   = ParagraphStyle("B",  fontSize=10, textColor=colors.HexColor("#1a1a2e"),
                               fontName=CHINESE_FONT, spaceAfter=2)
    small_s  = ParagraphStyle("S",  fontSize=8,  textColor=colors.HexColor("#555555"),
                               fontName=CHINESE_FONT)
    total_s  = ParagraphStyle("To", fontSize=12, textColor=colors.white,
                               fontName="Helvetica-Bold", alignment=TA_RIGHT)
    note_s   = ParagraphStyle("N",  fontSize=9,  textColor=colors.HexColor("#444444"),
                               fontName=CHINESE_FONT, leading=13)
    th_s     = ParagraphStyle("TH", fontSize=9,  fontName="Helvetica-Bold",
                               textColor=colors.white, alignment=TA_CENTER)
    td_c     = ParagraphStyle("Tc", fontSize=9,  fontName=CHINESE_FONT,
                               textColor=colors.HexColor("#1a1a2e"), alignment=TA_CENTER)
    td_l     = ParagraphStyle("Tl", fontSize=9,  fontName=CHINESE_FONT,
                               textColor=colors.HexColor("#1a1a2e"), alignment=TA_LEFT)
    td_r     = ParagraphStyle("Tr", fontSize=9,  fontName=CHINESE_FONT,
                               textColor=colors.HexColor("#1a1a2e"), alignment=TA_RIGHT)

    story = []
    f  = form_data.get("from", {})
    bt = form_data.get("billto", {})
    py = form_data.get("payment", {})
    inv_number = (form_data.get("inv_number","") or "").strip()

    # Header: FROM (left) | INVOICE + DATE + TRIP (right)
    from_col = [
        Spacer(1, 4),
        Paragraph("FROM", head_s),
        Paragraph(f.get("full_name",""), bold_s),
        Paragraph(f.get("street",""),    val_s),
        Paragraph(f.get("post_code",""), val_s),
        Paragraph(f.get("city",""),      val_s),
    ]
    right_col = [Paragraph("INVOICE", title_s)]
    if inv_number:
        inv_num_s = ParagraphStyle("InvNum", fontSize=11, textColor=colors.HexColor("#4f46e5"),
                                   fontName="Helvetica-Bold", alignment=TA_RIGHT,
                                   spaceBefore=4, spaceAfter=4)
        right_col.append(Spacer(1, 6))
        right_col.append(Paragraph(inv_number, inv_num_s))
    right_col += [
        Spacer(1, 10),
        Paragraph("DATE", head_s),
        Paragraph(form_data.get("date", str(date.today())), bold_s),
        Spacer(1, 4),
        Paragraph("OBC TRIP", head_s),
        Paragraph(form_data.get("obc_trip","") or "—", val_s),
    ]
    hdr = Table([[from_col, right_col]],
                colWidths=[A4_W*0.55 - 36*mm, A4_W*0.45])
    hdr.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),0),
    ]))
    story += [hdr, Spacer(1,6),
              HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1a1a2e")),
              Spacer(1,8)]

    # Bill To | Payment
    bill_col = [
        Paragraph("BILL TO", head_s),
        Paragraph(bt.get("company",""), bold_s),
        Paragraph(bt.get("address",""), val_s),
    ]
    pay_col = [
        Paragraph("PAYMENT", head_s),
        Paragraph(py.get("payment",""),    val_s), Spacer(1,4),
        Paragraph("BANK NAME & ADDRESS",   head_s),
        Paragraph(py.get("bank_name",""),  val_s), Spacer(1,4),
        Paragraph("BENEFICIARY NAME",      head_s),
        Paragraph(py.get("beneficiary",""),val_s), Spacer(1,4),
        Paragraph("SWIFT CODE",            head_s),
        Paragraph(py.get("swift",""),      val_s), Spacer(1,4),
        Paragraph("ACCOUNT NUMBER / IBAN", head_s),
        Paragraph(py.get("iban",""),       val_s),
    ]
    cw = (A4_W - 36*mm) / 2
    mid = Table([[bill_col, pay_col]], colWidths=[cw, cw])
    mid.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),6),
    ]))
    story += [mid, Spacer(1,10),
              HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")),
              Spacer(1,8)]

    # Items table
    hbg  = colors.HexColor("#1a1a2e")
    ralt = colors.HexColor("#f5f5f8")
    col_w = [10*mm, 72*mm, 28*mm, 20*mm, 28*mm]
    tdata = [[Paragraph("#",th_s), Paragraph("DESCRIPTION",th_s),
              Paragraph("COST",th_s), Paragraph("QTY",th_s),
              Paragraph("AMOUNT (USD)",th_s)]]
    total = 0.0
    for i, item in enumerate(form_data.get("items",[]), 1):
        try: cost = float(item.get("cost","0") or 0)
        except: cost = 0.0
        try: qty  = float(item.get("qty","0")  or 0)
        except: qty = 0.0
        amt = cost * qty
        total += amt
        tdata.append([
            Paragraph(str(i), td_c),
            Paragraph(item.get("description",""), td_l),
            Paragraph(f"{cost:.2f}" if item.get("cost") else "", td_r),
            Paragraph(f"{qty:.0f}"  if item.get("qty")  else "", td_c),
            Paragraph(f"{amt:.2f}"  if (item.get("cost") or item.get("qty")) else "", td_r),
        ])
    while len(tdata) < 8:
        tdata.append([Paragraph("",td_c)]*5)

    itbl = Table(tdata, colWidths=col_w, repeatRows=1)
    itbl.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), hbg),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, ralt]),
        ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#dddddd")),
        ("TOPPADDING",(0,0),(-1,-1),5), ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),6), ("RIGHTPADDING",(0,0),(-1,-1),6),
    ]))
    story.append(itbl)

    tot_tbl = Table([[Paragraph(f"TOTAL USD   {total:,.2f}", total_s)]],
                    colWidths=[sum(col_w)])
    tot_tbl.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), hbg),
        ("TOPPADDING",(0,0),(-1,-1),8), ("BOTTOMPADDING",(0,0),(-1,-1),8),
        ("LEFTPADDING",(0,0),(-1,-1),6), ("RIGHTPADDING",(0,0),(-1,-1),6),
    ]))
    story.append(tot_tbl)

    notes = (form_data.get("notes","") or "").strip()
    if notes:
        story += [Spacer(1,10), Paragraph("NOTES", head_s), Paragraph(notes, note_s)]

    doc.build(story)

    # ── Photo pages ──
    photos = [p for p in form_data.get("photos",[]) if os.path.exists(p.get("path",""))]
    if photos:
        margin_x, margin_top, margin_bot = 18*mm, 15*mm, 15*mm
        cap_h, gap = 16, 10
        usable_w = A4_W - 2*margin_x
        slot_h   = (A4_H - margin_top - margin_bot - cap_h*2 - gap) / 2

        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp.close()
        c = rl_canvas.Canvas(tmp.name, pagesize=A4)

        def draw_slot(c, path, desc, slot_top_y):
            try:
                img = Image.open(path)
                iw, ih = img.size
                ratio  = min(usable_w/iw, slot_h/ih)
                dw, dh = iw*ratio, ih*ratio
                x = margin_x + (usable_w - dw) / 2
                y = slot_top_y - dh
                c.drawImage(path, x, y, width=dw, height=dh,
                            preserveAspectRatio=True, mask="auto")
                if desc:
                    # Use Chinese font for descriptions, with fallback
                    try:
                        c.setFont(CHINESE_FONT, 8)
                    except:
                        c.setFont("Helvetica", 8)
                    c.setFillColor(colors.HexColor("#333333"))
                    c.drawCentredString(A4_W/2, y - cap_h + 2, desc)
            except Exception as e:
                c.setFont("Helvetica", 9)
                c.setFillColor(colors.red)
                c.drawString(margin_x, slot_top_y-20, f"[Error: {e}]")

        for pi, i in enumerate(range(0, len(photos), 2)):
            if pi > 0: c.showPage()
            c.setFont("Helvetica", 7)
            c.setFillColor(colors.HexColor("#aaaaaa"))
            c.drawCentredString(A4_W/2, margin_bot/2, f"Attachment page {pi+1}")
            draw_slot(c, photos[i]["path"], photos[i].get("description",""),
                      A4_H - margin_top)
            if i+1 < len(photos):
                draw_slot(c, photos[i+1]["path"], photos[i+1].get("description",""),
                          A4_H - margin_top - slot_h - cap_h - gap)
        c.save()

        writer = PdfWriter()
        for r in [PdfReader(output_path), PdfReader(tmp.name)]:
            for page in r.pages: writer.add_page(page)
        with open(output_path, "wb") as fout: writer.write(fout)
        os.unlink(tmp.name)

# ── API Routes ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/profiles", methods=["GET"])
def api_get_profiles():
    return jsonify(load_profiles())

@app.route("/api/profiles", methods=["POST"])
def api_save_profiles():
    data = request.get_json()
    save_profiles(data)
    return jsonify({"ok": True})

@app.route("/api/upload_photo", methods=["POST"])
def api_upload_photo():
    file = request.files.get("photo")
    if not file:
        return jsonify({"error": "no file"}), 400
    ext  = os.path.splitext(file.filename)[1].lower()
    name = uuid.uuid4().hex + ext
    path = os.path.join(UPLOAD_DIR, name)
    file.save(path)
    return jsonify({"path": path, "name": file.filename})

@app.route("/api/generate_pdf", methods=["POST"])
def api_generate_pdf():
    form_data = request.get_json()
    out_name  = f"invoice_{uuid.uuid4().hex[:8]}.pdf"
    out_path  = os.path.join(OUTPUT_DIR, out_name)
    try:
        generate_pdf(form_data, out_path)
        return jsonify({"url": f"/download/{out_name}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/download/<filename>")
def download(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        return "Not found", 404
    return send_file(path, as_attachment=True,
                     download_name="invoice.pdf",
                     mimetype="application/pdf")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)
