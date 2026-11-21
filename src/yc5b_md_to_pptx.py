"""YC5b – Tự động tạo slide từ file văn bản (.md hoặc .txt).

Cách chạy:
    python src/yc5b_md_to_pptx.py docs/thuyet_trinh.md results/yc5b_thuyet_trinh.pptx

Quy ước file đầu vào:
    # Tiêu đề          -> slide tiêu đề (các dòng thường ngay sau là phụ đề)
    ## Tiêu đề phụ     -> một slide nội dung mới
    - Ý chính          -> gạch đầu dòng
    ![chú thích](hinh.png) -> chèn hình/biểu đồ (đường dẫn tính từ thư mục của file .md)
    Dòng chữ thường    -> đoạn văn
Thư viện: python-pptx.
"""
import sys
import re
from pathlib import Path

from PIL import Image as PILImage
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

NAVY, XANH, XAM = RGBColor(0x1F, 0x3A, 0x5F), RGBColor(0x1F, 0x6F, 0xEB), RGBColor(0x57, 0x60, 0x6A)
FONT = "Arial"
W, H = Inches(13.333), Inches(7.5)
IMG = re.compile(r"!\[(.*?)\]\((.*?)\)")


# ---------- 1. Đọc file văn bản thành danh sách slide ----------
def doc_noi_dung(path):
    slides, cur = [], None
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("# "):
            cur = {"loai": "tieu_de", "tieu_de": line[2:], "dong": []}; slides.append(cur)
        elif line.startswith("## "):
            cur = {"loai": "noi_dung", "tieu_de": line[3:], "dong": []}; slides.append(cur)
        elif cur is not None:
            m = IMG.fullmatch(line)
            if m:
                cur["dong"].append(("hinh", m.group(1), m.group(2)))
            elif line.startswith(("- ", "* ")):
                cur["dong"].append(("y", line[2:]))
            else:
                cur["dong"].append(("doan", line))
    return slides


# ---------- 2. Các hàm vẽ thành phần ----------
def chu(tf, text, size, bold=False, color=None, first=False):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    r = p.add_run(); r.text = text
    r.font.size, r.font.bold, r.font.name = Pt(size), bold, FONT
    if color is not None:
        r.font.color.rgb = color
    return p


def thanh_mau(slide, top, height):
    s = slide.shapes.add_shape(1, 0, top, W, height)
    s.fill.solid(); s.fill.fore_color.rgb = NAVY; s.line.fill.background()
    return s


def slide_tieu_de(prs, d):
    sl = prs.slides.add_slide(prs.slide_layouts[6])
    thanh_mau(sl, Inches(2.3), Inches(2.6))
    tf = sl.shapes.add_textbox(Inches(0.8), Inches(2.5), Inches(11.7), Inches(2.3)).text_frame
    tf.word_wrap = True
    chu(tf, d["tieu_de"], 36, True, RGBColor(255, 255, 255), first=True)
    for _, *t in d["dong"]:
        chu(tf, t[0], 18, False, RGBColor(0xDD, 0xE6, 0xF2))


def slide_noi_dung(prs, d, base_dir, so):
    sl = prs.slides.add_slide(prs.slide_layouts[6])
    thanh_mau(sl, 0, Inches(1.1))
    tf = sl.shapes.add_textbox(Inches(0.6), Inches(0.2), Inches(12), Inches(0.8)).text_frame
    chu(tf, d["tieu_de"], 28, True, RGBColor(255, 255, 255), first=True)
    hinh = [x for x in d["dong"] if x[0] == "hinh"]
    chu_dong = [x for x in d["dong"] if x[0] != "hinh"]
    if chu_dong:
        w = Inches(5.9) if hinh else Inches(12.1)
        tf = sl.shapes.add_textbox(Inches(0.6), Inches(1.5), w, Inches(5.4)).text_frame
        tf.word_wrap = True
        for i, x in enumerate(chu_dong):
            p = chu(tf, ("• " if x[0] == "y" else "") + x[1], 20, first=(i == 0))
            p.space_after = Pt(10)
    for _, cap, rel in hinh[:1]:  # mỗi slide một hình
        path = (base_dir / rel)
        iw, ih = PILImage.open(path).size
        box_l = Inches(6.8) if chu_dong else Inches(0.6)
        box_w = Inches(5.9) if chu_dong else Inches(12.1)
        box_h = Inches(5.0)
        scale = min(box_w / iw, box_h / ih)
        pw, ph = int(iw * scale), int(ih * scale)
        sl.shapes.add_picture(str(path), box_l + (box_w - pw) // 2, Inches(1.4), pw, ph)
        tf = sl.shapes.add_textbox(box_l, Inches(1.45) + ph, box_w, Inches(0.5)).text_frame
        p = chu(tf, cap, 14, color=XAM, first=True); p.alignment = 2
    tf = sl.shapes.add_textbox(Inches(12.3), Inches(7.0), Inches(0.8), Inches(0.4)).text_frame
    chu(tf, str(so), 12, color=XAM, first=True)


# ---------- 3. Chương trình chính ----------
def main():
    inp = Path(sys.argv[1] if len(sys.argv) > 1 else "thuyet_trinh.md")
    out = Path(sys.argv[2] if len(sys.argv) > 2 else inp.with_suffix(".pptx"))
    prs = Presentation(); prs.slide_width, prs.slide_height = W, H
    slides = doc_noi_dung(inp)
    for i, d in enumerate(slides, 1):
        (slide_tieu_de(prs, d) if d["loai"] == "tieu_de" else slide_noi_dung(prs, d, inp.parent, i))
    prs.save(out)
    print(f"Đã tạo {out}: {len(slides)} slide")


if __name__ == "__main__":
    main()
