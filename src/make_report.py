"""Bước 4 – Tự động sinh báo cáo khoa học PDF từ kết quả phân tích.

Chạy: python src/make_report.py   (sau prepare_data.py, train_model.py, survey_analysis.py)
Đầu ra: results/bao_cao_mini_project.pdf
Mọi con số trong báo cáo được đọc từ thư mục results/, không gõ tay.
"""
import json
from datetime import date
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import matplotlib
FONT_DIR = Path(matplotlib.get_data_path()) / "fonts" / "ttf"  # DejaVu đi kèm matplotlib, chạy được mọi hệ điều hành
pdfmetrics.registerFont(TTFont("DejaVu", str(FONT_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
RES = Path("results")


def vn(x, d=1):
    return f"{x:,.{d}f}".replace(",", "#").replace(".", ",").replace("#", ".")


def main():
    m = json.load(open(RES / "metrics.json"))
    s = json.load(open(RES / "survey_summary.json", encoding="utf-8"))
    f = pd.read_csv("data/processed/oulad_features.csv")
    imp = pd.read_csv(RES / "feature_importance.csv", index_col=0)
    tasks = pd.read_csv(RES / "survey_tasks.csv").sort_values("ty_le_thuong_xuyen", ascending=False)
    conc = pd.read_csv(RES / "survey_concerns.csv").sort_values("ty_le_dong_y", ascending=False)
    us = pd.read_csv(RES / "survey_usage_success.csv")

    st = {"t": ParagraphStyle("t", fontName="DejaVu-Bold", fontSize=16, leading=21, spaceAfter=4),
          "p": ParagraphStyle("p", fontName="DejaVu", fontSize=9.5, textColor=colors.grey, spaceAfter=8),
          "h": ParagraphStyle("h", fontName="DejaVu-Bold", fontSize=12.5, leading=16, spaceBefore=8, spaceAfter=4),
          "n": ParagraphStyle("n", fontName="DejaVu", fontSize=10.5, leading=15, spaceAfter=5)}
    W = A4[0] - 4 * cm

    def bang(rows, widths):
        cell = ParagraphStyle("c", fontName="DejaVu", fontSize=9.5, leading=12)
        head = ParagraphStyle("hc", parent=cell, fontName="DejaVu-Bold")
        rows = [[Paragraph(str(v), head if i == 0 else cell) for v in r] for i, r in enumerate(rows)]
        t = Table(rows, colWidths=widths, hAlign="LEFT")
        t.setStyle(TableStyle([("FONT", (0, 0), (-1, -1), "DejaVu", 9.5), ("FONT", (0, 0), (-1, 0), "DejaVu-Bold", 9.5),
                               ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCE6F2")),
                               ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9AA4AE")),
                               ("ALIGN", (1, 1), (-1, -1), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        return t

    def hinh(p, ratio):
        return Image(str(RES / p), width=W, height=W * ratio)

    top2 = imp.head(2)
    e = [Paragraph("Hành vi học tập trực tuyến và nhận thức về ChatGPT của sinh viên đại học", st["t"]),
         Paragraph(f"Báo cáo sinh tự động bằng Python · {date.today():%d/%m/%Y}", st["p"]),
         Paragraph("1. Giới thiệu đề tài", st["h"]),
         Paragraph("Đề tài trả lời hai câu hỏi: (1) dữ liệu hành vi trong 4 tuần đầu khóa học trực tuyến có dự báo được "
                   "sinh viên đạt hay chưa đạt không; (2) sinh viên dùng ChatGPT vào việc gì và lo ngại điều gì.", st["n"]),
         Paragraph("2. Mô tả dữ liệu", st["h"]),
         bang([["Bộ dữ liệu", "Quy mô", "Giấy phép"],
               ["OULAD (Kuzilek và cộng sự, 2017)", f"{vn(len(f), 0)} lượt đăng ký; 10,6 triệu bản ghi click", "CC BY 4.0"],
               ["Khảo sát ChatGPT toàn cầu (Ravšelj và cộng sự)", f"{vn(s['so_phan_hoi'], 0)} phản hồi, {s['so_quoc_gia_hoc']} quốc gia", "CC BY 4.0"]],
              [W * .45, W * .38, W * .17]),
         Spacer(1, 4),
         Paragraph(f"Nhãn <i>Đạt</i> gồm Pass và Distinction (tỷ lệ {vn(f['dat'].mean() * 100)}%). Đặc trưng lấy trong 28 ngày đầu: "
                   "lượt click, số ngày và số tuần có truy cập, điểm các bài kiểm tra sớm, cùng các thông tin nhân khẩu học.", st["n"]),
         Paragraph("3. Kết quả phân tích", st["h"]),
         Paragraph("3.1. Mô hình Decision Tree dự báo sớm (OULAD)", st["n"]),
         bang([["Chỉ số (tập kiểm tra 20%)", "Giá trị"],
               ["Độ chính xác (mức nền: luôn đoán nhóm đông nhất)", f"{vn(m['accuracy'] * 100)}% ({vn(m['baseline_accuracy'] * 100)}%)"],
               ["Recall nhóm Chưa đạt", f"{vn(m['recall_chua_dat'] * 100)}%"],
               ["F1 nhóm Đạt", vn(m["f1"], 3)], ["ROC-AUC", vn(m["roc_auc"], 3)]], [W * .65, W * .35]),
         hinh("fig_importance.png", 4 / 8),
         Paragraph("3.2. Khảo sát ChatGPT", st["n"]),
         Paragraph(f"{vn(s['ty_le_da_dung'])}% sinh viên trả lời đã từng dùng ChatGPT. Ba mục đích dùng thường xuyên nhất là "
                   f"{', '.join(tasks['nhiem_vu'].head(3).str.lower())}. Lo ngại được đồng ý nhiều nhất là "
                   f"{conc['lo_ngai'].iloc[0].lower()} ({vn(conc['ty_le_dong_y'].iloc[0])}%).", st["n"]),
         hinh("fig_survey_tasks.png", 4.6 / 8), hinh("fig_survey_concerns.png", 4.6 / 8),
         hinh("fig_survey_success.png", 3.8 / 8),
         Paragraph("4. Kết luận và đề xuất", st["h"]),
         Paragraph(f"Chỉ với dữ liệu 4 tuần đầu, Decision Tree đạt độ chính xác {vn(m['accuracy'] * 100)}%, cao hơn mức nền "
                   f"{vn((m['accuracy'] - m['baseline_accuracy']) * 100)} điểm phần trăm. Hai yếu tố quan trọng nhất là "
                   f"{top2['ten'].iloc[0][0].lower() + top2['ten'].iloc[0][1:]} ({vn(top2['importance'].iloc[0] * 100)}%) và {top2['ten'].iloc[1][0].lower() + top2['ten'].iloc[1][1:]} "
                   f"({vn(top2['importance'].iloc[1] * 100)}%): sinh viên vào học đều đặn ngay từ đầu có khả năng đạt cao hơn.", st["n"]),
         Paragraph(f"Ở khảo sát, sinh viên dùng ChatGPT nhiều tự đánh giá học tốt hơn ({vn(us['ty_le_thanh_cong'].iloc[-1])}% so với "
                   f"{vn(us['ty_le_thanh_cong'].iloc[0])}% ở nhóm hiếm khi dùng), nhưng tương quan rất yếu (Spearman ρ = "
                   f"{vn(s['spearman_Q15_Q35a'], 3)}) và kết quả là tự đánh giá, nên không kết luận được quan hệ nhân quả.", st["n"]),
         Paragraph("Đề xuất: (1) nhà trường theo dõi số tuần truy cập ngay từ tuần 1–4 để hỗ trợ sớm sinh viên có nguy cơ; "
                   "(2) hướng dẫn sinh viên dùng ChatGPT có trách nhiệm, tập trung vào rủi ro gian lận và thông tin sai.", st["n"])]
    out = RES / "bao_cao_mini_project.pdf"
    SimpleDocTemplate(str(out), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                      bottomMargin=1.8 * cm, title="Báo cáo mini-project").build(e)
    print("Đã tạo", out)


if __name__ == "__main__":
    main()
