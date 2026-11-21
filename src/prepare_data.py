"""Bước 1 – Làm sạch dữ liệu OULAD và tạo đặc trưng cảnh báo sớm (4 tuần đầu khóa).

Chạy: python src/prepare_data.py
Đầu vào : data/raw/studentInfo.csv, studentAssessment.csv, assessments.csv, studentVle_weekly.csv
Đầu ra  : data/processed/oulad_features.csv (mỗi dòng = 1 lượt đăng ký môn học)
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAW, OUT = Path("data/raw"), Path("data/processed")
KEY = ["code_module", "code_presentation", "id_student"]
SO_TUAN = 4  # chỉ dùng dữ liệu của 4 tuần đầu (ngày 0–27) để mô phỏng cảnh báo sớm


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    info = pd.read_csv(RAW / "studentInfo.csv").drop_duplicates()
    info["id_student"] = info["id_student"].astype(int)

    # Làm sạch: điền nhãn thiếu, gom nhãn imd_band bị ghi thiếu dấu %
    info["imd_band"] = info["imd_band"].fillna("unknown").replace({"10-20": "10-20%"})
    info["dat"] = info["final_result"].isin(["Pass", "Distinction"]).astype(int)

    # Lượt click trong 4 tuần đầu (đã tổng hợp theo tuần từ 10,6 triệu bản ghi studentVle)
    vle = pd.read_csv(RAW / "studentVle_weekly.csv")
    early = vle[(vle["week"] >= 0) & (vle["week"] < SO_TUAN)]
    clicks = early.groupby(KEY).agg(clicks_4w=("clicks", "sum"), active_days_4w=("active_days", "sum"),
                                    weeks_active_4w=("week", "nunique")).reset_index()
    before = vle[vle["week"] < 0].groupby(KEY)["clicks"].sum().rename("clicks_before_start").reset_index()

    # Điểm các bài kiểm tra có hạn nộp trong 4 tuần đầu
    sa = pd.read_csv(RAW / "studentAssessment.csv").dropna(subset=["score"])
    asm = pd.read_csv(RAW / "assessments.csv")
    sa = sa.merge(asm[["id_assessment", "code_module", "code_presentation", "date"]], on="id_assessment")
    sa = sa[sa["date"] < SO_TUAN * 7]
    score = sa.groupby(KEY).agg(early_score=("score", "mean"), early_submitted=("score", "size")).reset_index()

    df = info.merge(clicks, on=KEY, how="left").merge(before, on=KEY, how="left").merge(score, on=KEY, how="left")
    for c in ["clicks_4w", "active_days_4w", "weeks_active_4w", "clicks_before_start", "early_submitted"]:
        df[c] = df[c].fillna(0).astype(int)
    df["has_early_score"] = df["early_score"].notna().astype(int)
    df["early_score"] = df["early_score"].fillna(0)
    df["log_clicks_4w"] = np.log1p(df["clicks_4w"])
    df.to_csv(OUT / "oulad_features.csv", index=False)
    print(f"Đã tạo {OUT/'oulad_features.csv'}: {len(df)} dòng, tỷ lệ đạt {df['dat'].mean():.1%}")


if __name__ == "__main__":
    main()
