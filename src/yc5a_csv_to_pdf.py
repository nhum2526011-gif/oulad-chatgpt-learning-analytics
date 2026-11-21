"""YC5a – Đọc dataset CSV và tự động sinh báo cáo PDF.

Cách chạy:
    python src/yc5a_csv_to_pdf.py data/raw/studentInfo.csv results/yc5a_bao_cao_oulad.pdf

Đầu vào: studentInfo.csv của bộ OULAD (Kuzilek và cộng sự, 2017; CC BY 4.0).
Đầu ra: báo cáo PDF gồm tiêu đề, mô tả, bảng dữ liệu, biểu đồ và kết luận.
Thư viện: pandas, matplotlib, reportlab.
"""
import sys
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

# ---------- 1. Cấu hình font tiếng Việt ----------
FONT_DIR = Path(matplotlib.get_data_path()) / "fonts" / "ttf"  # DejaVu đi kèm matplotlib
pdfmetrics.registerFont(TTFont("DejaVu", str(FONT_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                     "axes.spines.top": False, "axes.spines.right": False})

KET_QUA = {"Distinction": "Xuất sắc", "Pass": "Đạt", "Fail": "Không đạt", "Withdrawn": "Bỏ học"}
THU_TU = ["Xuất sắc", "Đạt", "Không đạt", "Bỏ học"]
HOC_VAN = {"No Formal quals": "Chưa có bằng cấp", "Lower Than A Level": "Dưới A Level",
           "A Level or Equivalent": "A Level hoặc tương đương",
           "HE Qualification": "Có bằng đại học (HE)",
           "Post Graduate Qualification": "Sau đại học"}
XANH, XAM = "#1f6feb", "#8c959f"


def vn(x, d=1):
    """Định dạng số kiểu Việt Nam: 1.234,5"""
    s = f"{x:,.{d}f}"
    return s.replace(",", "#").replace(".", ",").replace("#", ".")


# ---------- 2. Đọc và chuẩn bị dữ liệu ----------
def doc_du_lieu(path):
    df = pd.read_csv(path)
    so_dong_goc = len(df)
    df = df.drop_duplicates()
    df["ket_qua"] = df["final_result"].map(KET_QUA)
    df["hoc_van"] = df["highest_education"].map(HOC_VAN)
    df["dat"] = df["final_result"].isin(["Pass", "Distinction"])
    return df, so_dong_goc


# ---------- 3. Tính bảng thống kê ----------
def thong_ke(df):
    b1 = (df["ket_qua"].value_counts().reindex(THU_TU).rename("so_sv").to_frame())
    b1["ty_le"] = b1["so_sv"] / b1["so_sv"].sum() * 100
    b2 = (df.groupby("hoc_van").agg(so_sv=("dat", "size"), ty_le_dat=("dat", "mean"))
            .reindex(list(HOC_VAN.values())))
    b2["ty_le_dat"] *= 100
    b3 = (df.groupby("num_of_prev_attempts")["dat"].mean() * 100)
    return b1, b2, b3


# ---------- 4. Vẽ biểu đồ ----------
def ve_bieu_do(b1, b2, out_dir):
    fig, ax = plt.subplots(figsize=(8, 3.6), layout="constrained")
    mau = [XANH, XANH, XAM, XAM]
    cot = ax.bar(b1.index, b1["ty_le"], color=mau)
    ax.set_ylabel("Tỷ lệ sinh viên (%)")
    ax.set_title("Hình 1. Phân bố kết quả cuối khóa", loc="left")
    for r, v in zip(cot, b1["ty_le"]):
        ax.text(r.get_x() + r.get_width() / 2, v + 0.8, vn(v) + "%", ha="center")
    ax.set_ylim(0, b1["ty_le"].max() * 1.18)
    f1 = out_dir / "hinh1_ket_qua.png"; fig.savefig(f1, dpi=200); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 3.6), layout="constrained")
    cot = ax.barh(b2.index, b2["ty_le_dat"], color=XANH)
    ax.invert_yaxis(); ax.set_xlim(0, 100)
    ax.set_xlabel("Tỷ lệ Đạt hoặc Xuất sắc (%)")
    ax.set_title("Hình 2. Tỷ lệ đạt theo trình độ học vấn đầu vào", loc="left")
    for r, v in zip(cot, b2["ty_le_dat"]):
        ax.text(v + 1, r.get_y() + r.get_height() / 2, vn(v) + "%", va="center")
    f2 = out_dir / "hinh2_hoc_van.png"; fig.savefig(f2, dpi=200); plt.close(fig)
    return f1, f2


# ---------- 5. Dựng file PDF ----------
def tao_pdf(df, so_dong_goc, b1, b2, b3, hinh, out_pdf):
    st = {
        "tieu_de": ParagraphStyle("t", fontName="DejaVu-Bold", fontSize=17, leading=22, spaceAfter=4),
        "phu": ParagraphStyle("p", fontName="DejaVu", fontSize=9.5, textColor=colors.grey, spaceAfter=10),
        "h": ParagraphStyle("h", fontName="DejaVu-Bold", fontSize=12.5, leading=16, spaceBefore=8, spaceAfter=4),
        "n": ParagraphStyle("n", fontName="DejaVu", fontSize=10.5, leading=15, spaceAfter=5),
    }
    W = A4[0] - 4 * cm

    def bang(rows, widths):
        t = Table(rows, colWidths=widths, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("FONT", (0, 0), (-1, -1), "DejaVu", 10), ("FONT", (0, 0), (-1, 0), "DejaVu-Bold", 10),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCE6F2")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9AA4AE")),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
        return t

    tong = len(df)
    ty_le_dat = df["dat"].mean() * 100
    tot, kem = b2["ty_le_dat"].idxmax(), b2["ty_le_dat"].idxmin()
    lan0, lan1 = b3.get(0, float("nan")), b3[b3.index >= 1].mean()

    e = [Paragraph("Báo cáo tự động: Kết quả học tập trực tuyến của sinh viên OULAD", st["tieu_de"]),
         Paragraph(f"Sinh tự động bằng Python (pandas, matplotlib, reportlab) · Ngày tạo: {date.today():%d/%m/%Y}", st["phu"]),
         Paragraph("1. Mô tả dữ liệu", st["h"]),
         Paragraph(f"Báo cáo đọc file <b>studentInfo.csv</b> của bộ Open University Learning Analytics Dataset "
                   f"(OULAD; Kuzilek và cộng sự, 2017; giấy phép CC BY 4.0). File gồm {vn(so_dong_goc, 0)} lượt đăng ký "
                   f"của sinh viên vào {df['code_module'].nunique()} môn học trong {df['code_presentation'].nunique()} kỳ "
                   f"(2013–2014). Sau khi loại dòng trùng còn {vn(tong, 0)} dòng. Kết quả cuối khóa được nhóm thành "
                   f"<i>Đạt</i> (Đạt hoặc Xuất sắc) và <i>Chưa đạt</i> (Không đạt hoặc Bỏ học).", st["n"]),
         Paragraph("2. Bảng dữ liệu", st["h"]),
         Paragraph("Bảng 1. Phân bố kết quả cuối khóa", st["n"]),
         bang([["Kết quả", "Số sinh viên", "Tỷ lệ (%)"]] +
              [[k, vn(r.so_sv, 0), vn(r.ty_le)] for k, r in b1.iterrows()] +
              [["Tổng", vn(tong, 0), "100,0"]], [W * .45, W * .3, W * .25]),
         Spacer(1, 8),
         Paragraph("Bảng 2. Tỷ lệ đạt theo trình độ học vấn đầu vào", st["n"]),
         bang([["Trình độ học vấn", "Số sinh viên", "Tỷ lệ đạt (%)"]] +
              [[k, vn(r.so_sv, 0), vn(r.ty_le_dat)] for k, r in b2.iterrows()], [W * .45, W * .3, W * .25]),
         Paragraph("3. Biểu đồ minh họa", st["h"]),
         Image(str(hinh[0]), width=W, height=W * 3.6 / 8),
         Image(str(hinh[1]), width=W, height=W * 3.6 / 8),
         Paragraph("4. Kết luận", st["h"]),
         Paragraph(f"Tỷ lệ sinh viên đạt chung là {vn(ty_le_dat)}%, nghĩa là cứ 10 sinh viên thì khoảng "
                   f"{round(10 - ty_le_dat / 10)} người chưa đạt. Bỏ học chiếm {vn(b1.loc['Bỏ học', 'ty_le'])}%, "
                   f"là nhóm chưa đạt lớn nhất. Trình độ đầu vào liên quan rõ đến kết quả: nhóm <i>{tot}</i> đạt "
                   f"{vn(b2.loc[tot, 'ty_le_dat'])}%, trong khi nhóm <i>{kem}</i> chỉ đạt {vn(b2.loc[kem, 'ty_le_dat'])}%. "
                   f"Sinh viên học lần đầu đạt {vn(lan0)}%, cao hơn nhóm đã học lại ({vn(lan1)}% trung bình).", st["n"]),
         Paragraph("Các con số trên là thống kê mô tả, chỉ cho thấy mối liên hệ, chưa chứng minh quan hệ nhân quả. "
                   "Bước tiếp theo nên kết hợp dữ liệu lượt truy cập học liệu (studentVle) để dự báo sớm sinh viên có nguy cơ chưa đạt.", st["n"])]
    SimpleDocTemplate(str(out_pdf), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                      topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                      title="Báo cáo tự động OULAD").build(e)


def main():
    inp = Path(sys.argv[1] if len(sys.argv) > 1 else "studentInfo.csv")
    out = Path(sys.argv[2] if len(sys.argv) > 2 else "bao_cao_oulad.pdf")
    out.parent.mkdir(parents=True, exist_ok=True)
    df, n0 = doc_du_lieu(inp)
    b1, b2, b3 = thong_ke(df)
    hinh = ve_bieu_do(b1, b2, out.parent)
    tao_pdf(df, n0, b1, b2, b3, hinh, out)
    print(f"Đã tạo {out} từ {len(df)} dòng dữ liệu")


if __name__ == "__main__":
    main()
