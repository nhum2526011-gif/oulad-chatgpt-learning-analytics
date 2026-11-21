"""Bước 2 – Huấn luyện Decision Tree phân loại Đạt / Chưa đạt từ dữ liệu 4 tuần đầu.

Chạy: python src/train_model.py
Đầu ra: results/metrics.json, results/feature_importance.csv, results/tree_rules.txt,
        results/fig_confusion.png, results/fig_importance.png, results/model.joblib
"""
import json
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, export_text

RES = Path("results")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12,
                     "axes.spines.top": False, "axes.spines.right": False})

SO = ["clicks_4w", "active_days_4w", "weeks_active_4w", "clicks_before_start",
      "early_score", "early_submitted", "has_early_score", "num_of_prev_attempts", "studied_credits"]
NHOM = ["gender", "age_band", "highest_education", "imd_band", "disability"]
TEN_VN = {"clicks_4w": "Lượt click 4 tuần đầu", "active_days_4w": "Số ngày truy cập 4 tuần đầu",
          "weeks_active_4w": "Số tuần có truy cập", "clicks_before_start": "Lượt click trước khi khóa bắt đầu",
          "early_score": "Điểm TB bài kiểm tra sớm", "early_submitted": "Số bài nộp sớm",
          "has_early_score": "Có bài kiểm tra sớm", "num_of_prev_attempts": "Số lần học lại",
          "studied_credits": "Số tín chỉ đăng ký"}


NHOM_VN = {"gender": "Giới tính", "age_band": "Tuổi", "highest_education": "Học vấn", "imd_band": "IMD",
           "disability": "Khuyết tật"}
GIA_TRI_VN = {"Lower Than A Level": "Dưới A Level", "No Formal quals": "Chưa có bằng cấp", "M": "Nam", "F": "Nữ",
              "A Level or Equivalent": "A Level", "HE Qualification": "Đại học", "Y": "Có", "N": "Không"}


def ten(c):
    for k in NHOM:
        if c.startswith(k + "_"):
            v = c[len(k)+1:]
            return f"{NHOM_VN[k]}: {GIA_TRI_VN.get(v, v)}"
    for k in NHOM:
        if c.startswith(k + "_"):
            return f"{k} = {c[len(k)+1:]}"
    return TEN_VN.get(c, c)


def main():
    RES.mkdir(exist_ok=True)
    df = pd.read_csv("data/processed/oulad_features.csv")
    X = pd.get_dummies(df[SO + NHOM], columns=NHOM, dtype=int)
    y = df["dat"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    model = DecisionTreeClassifier(max_depth=5, min_samples_leaf=50, class_weight="balanced", random_state=42)
    model.fit(Xtr, ytr)
    p, prob = model.predict(Xte), model.predict_proba(Xte)[:, 1]
    base = DummyClassifier(strategy="most_frequent").fit(Xtr, ytr)

    m = {"n_train": len(Xtr), "n_test": len(Xte), "accuracy": accuracy_score(yte, p),
         "precision_dat": precision_score(yte, p), "recall_dat": recall_score(yte, p),
         "recall_chua_dat": recall_score(yte, p, pos_label=0), "f1": f1_score(yte, p),
         "roc_auc": roc_auc_score(yte, prob), "baseline_accuracy": accuracy_score(yte, base.predict(Xte))}
    json.dump({k: round(float(v), 4) for k, v in m.items()}, open(RES / "metrics.json", "w"), indent=2)

    imp = (pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False))
    imp = imp[imp > 0].rename("importance").to_frame(); imp["ten"] = [ten(c) for c in imp.index]
    imp.to_csv(RES / "feature_importance.csv")
    (RES / "tree_rules.txt").write_text(export_text(model, feature_names=list(X.columns), max_depth=3), encoding="utf-8")
    joblib.dump({"model": model, "columns": list(X.columns)}, RES / "model.joblib")

    # Hình: ma trận nhầm lẫn
    cm = confusion_matrix(yte, p)
    fig, ax = plt.subplots(figsize=(4.8, 4), layout="constrained")
    ax.imshow(cm, cmap="Blues")
    lab = ["Chưa đạt", "Đạt"]
    ax.set_xticks([0, 1], lab); ax.set_yticks([0, 1], lab)
    ax.set_xlabel("Dự đoán"); ax.set_ylabel("Thực tế"); ax.set_title("Ma trận nhầm lẫn (tập kiểm tra)", loc="left")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{cm[i, j]:,}".replace(",", "."), ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black", fontsize=14)
    fig.savefig(RES / "fig_confusion.png", dpi=200); plt.close(fig)

    # Hình: mức độ quan trọng của đặc trưng
    top = imp.head(8).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 4), layout="constrained")
    ax.barh(top["ten"], top["importance"] * 100, color="#1f6feb")
    ax.set_xlabel("Mức độ quan trọng (%)"); ax.set_title("Đặc trưng quan trọng nhất của Decision Tree", loc="left")
    for i, v in enumerate(top["importance"] * 100):
        ax.text(v + 0.5, i, f"{v:.1f}%".replace(".", ","), va="center")
    fig.savefig(RES / "fig_importance.png", dpi=200); plt.close(fig)
    print(json.dumps({k: round(float(v), 3) for k, v in m.items()}, ensure_ascii=False))
    print(imp.head(8))


if __name__ == "__main__":
    main()
