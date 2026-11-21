"""Bước 3 – Thống kê mô tả khảo sát toàn cầu về ChatGPT (Ravšelj và cộng sự, CC BY 4.0).

Chạy: python src/survey_analysis.py
Đầu vào : data/raw/chatgpt_survey.csv (37 cột chọn lọc từ file gốc 174 cột; đã bỏ tên trường Q5)
Đầu ra  : results/survey_summary.json, survey_tasks.csv, survey_concerns.csv, survey_usage_success.csv
          results/fig_survey_tasks.png, fig_survey_concerns.png, fig_survey_success.png
Mã hóa: Likert 1–5; "đồng ý" = 4 hoặc 5; Q13: 1 = đã dùng, 2 = chưa dùng.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import spearmanr

RES = Path("results")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12,
                     "axes.spines.top": False, "axes.spines.right": False})
XANH = "#1f6feb"

TASK = {"Q18a": "Viết học thuật", "Q18b": "Viết email công việc", "Q18c": "Viết sáng tạo",
        "Q18d": "Sửa lỗi văn bản", "Q18e": "Tìm ý tưởng", "Q18f": "Dịch thuật", "Q18g": "Tóm tắt",
        "Q18h": "Hỗ trợ tính toán", "Q18i": "Ôn thi", "Q18j": "Tư vấn cá nhân",
        "Q18k": "Hỗ trợ nghiên cứu", "Q18l": "Hỗ trợ lập trình"}
CONCERN = {"Q22a": "Khuyến khích hành vi phi đạo đức", "Q22b": "Khuyến khích gian lận",
           "Q22c": "Khuyến khích đạo văn", "Q22d": "Đe dọa đạo đức học tập",
           "Q22e": "Đưa thông tin sai", "Q22f": "Xâm phạm quyền riêng tư",
           "Q22g": "Giảm tương tác giữa người với người", "Q22h": "Thay thế giáo dục chính quy",
           "Q22i": "Tăng cô lập xã hội", "Q22j": "Làm thay khiến SV không tự học"}
MUC_DUNG = {1: "Hiếm khi", 2: "Thỉnh thoảng", 3: "Vừa phải", 4: "Nhiều", 5: "Rất nhiều"}
HOC = {1: "Học trực tiếp", 2: "Học trực tuyến", 3: "Học kết hợp"}


def pct(s):
    s = s.dropna()
    return float((s >= 4).mean() * 100)


def luu(fig, ten):
    fig.savefig(RES / ten, dpi=200); plt.close(fig)


def main():
    RES.mkdir(exist_ok=True)
    d = pd.read_csv("data/raw/chatgpt_survey.csv")
    user = d[d["Q13"] == 1]

    tasks = pd.DataFrame({"nhiem_vu": TASK.values(),
                          "ty_le_thuong_xuyen": [pct(user[c]) for c in TASK],   # Often/Always
                          "diem_tb": [user[c].mean() for c in TASK]}).sort_values("ty_le_thuong_xuyen")
    tasks.to_csv(RES / "survey_tasks.csv", index=False)
    conc = pd.DataFrame({"lo_ngai": CONCERN.values(),
                         "ty_le_dong_y": [pct(user[c]) for c in CONCERN]}).sort_values("ty_le_dong_y")
    conc.to_csv(RES / "survey_concerns.csv", index=False)

    us = (user.dropna(subset=["Q15", "Q35a"]).groupby("Q15")["Q35a"]
          .agg(so_sv="size", ty_le_thanh_cong=lambda s: (s >= 4).mean() * 100).reset_index())
    us["muc_dung"] = us["Q15"].map(MUC_DUNG)
    us.to_csv(RES / "survey_usage_success.csv", index=False)
    pair = user[["Q15", "Q35a"]].dropna()
    rho, p = spearmanr(pair["Q15"], pair["Q35a"])
    mode = (d.dropna(subset=["Q11", "Q13"]).groupby("Q11")["Q13"].apply(lambda s: (s == 1).mean() * 100))

    summary = {"so_phan_hoi": len(d), "so_quoc_gia_hoc": int(d["Q4"].nunique()),
               "tra_loi_Q13": int(d["Q13"].notna().sum()), "da_dung": int((d["Q13"] == 1).sum()),
               "ty_le_da_dung": float((d["Q13"] == 1).sum() / d["Q13"].notna().sum() * 100),
               "dung_nhieu_tro_len": pct(user["Q15"]),
               "spearman_Q15_Q35a": float(rho), "p_value": float(p), "n_cap": len(pair),
               "dong_y_tang_hieu_qua_Q26e": pct(user["Q26e"]), "dong_y_cai_thien_diem_Q27b": pct(user["Q27b"]),
               "ty_le_da_dung_theo_hinh_thuc": {HOC[int(k)]: float(v) for k, v in mode.items()}}
    json.dump(summary, open(RES / "survey_summary.json", "w"), ensure_ascii=False, indent=2)

    fig, ax = plt.subplots(figsize=(8, 4.6), layout="constrained")
    ax.barh(tasks["nhiem_vu"], tasks["ty_le_thuong_xuyen"], color=XANH)
    ax.set_xlabel("Tỷ lệ dùng thường xuyên hoặc luôn luôn (%)"); ax.set_xlim(0, 40)
    ax.set_title(f"Sinh viên dùng ChatGPT cho việc gì (n = {len(user):,})".replace(",", "."), loc="left")
    for i, v in enumerate(tasks["ty_le_thuong_xuyen"]):
        ax.text(v + 0.6, i, f"{v:.1f}%".replace(".", ","), va="center")
    luu(fig, "fig_survey_tasks.png")

    fig, ax = plt.subplots(figsize=(8, 4.6), layout="constrained")
    ax.barh(conc["lo_ngai"], conc["ty_le_dong_y"], color="#8c959f")
    ax.set_xlabel("Tỷ lệ đồng ý hoặc rất đồng ý (%)"); ax.set_xlim(0, 60)
    ax.set_title("Lo ngại của sinh viên: ChatGPT có thể…", loc="left")
    for i, v in enumerate(conc["ty_le_dong_y"]):
        ax.text(v + 0.6, i, f"{v:.1f}%".replace(".", ","), va="center")
    luu(fig, "fig_survey_concerns.png")

    fig, ax = plt.subplots(figsize=(8, 3.8), layout="constrained")
    ax.bar(us["muc_dung"], us["ty_le_thanh_cong"], color=XANH)
    ax.set_ylabel("Tự đánh giá học tốt (%)"); ax.set_ylim(0, 100)
    ax.set_title("Mức dùng ChatGPT và tự đánh giá thành công trong học tập", loc="left")
    for i, v in enumerate(us["ty_le_thanh_cong"]):
        ax.text(i, v + 2, f"{v:.1f}%".replace(".", ","), ha="center")
    luu(fig, "fig_survey_success.png")
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    print(tasks.tail(4)); print(conc.tail(4)); print(us)


if __name__ == "__main__":
    main()
