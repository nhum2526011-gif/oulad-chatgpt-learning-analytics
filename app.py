"""Dashboard Streamlit – Hành vi học tập trực tuyến và nhận thức về ChatGPT.

Chạy local: streamlit run app.py
"""
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Học trực tuyến & ChatGPT", layout="wide")
KQ = {"Distinction": "Xuất sắc", "Pass": "Đạt", "Fail": "Không đạt", "Withdrawn": "Bỏ học"}
BIEN = {"highest_education": "Trình độ học vấn", "age_band": "Nhóm tuổi", "imd_band": "Mức thiếu thốn (IMD)",
        "gender": "Giới tính", "disability": "Khuyết tật", "num_of_prev_attempts": "Số lần học lại",
        "code_module": "Môn học"}


@st.cache_data
def load():
    f = pd.read_csv("data/processed/oulad_features.csv")
    f["ket_qua"] = f["final_result"].map(KQ)
    w = pd.read_csv("data/raw/studentVle_weekly.csv")
    w = w.merge(f[["code_module", "code_presentation", "id_student", "ket_qua"]],
                on=["code_module", "code_presentation", "id_student"])
    n = f.groupby("ket_qua").size()
    wk = (w.groupby(["ket_qua", "week"])["clicks"].sum() / n).rename("click_tb").reset_index()
    return f, wk


f, wk = load()
st.title("Hành vi học tập trực tuyến và nhận thức về ChatGPT của sinh viên")
st.caption("Dữ liệu: OULAD (Kuzilek và cộng sự, 2017, CC BY 4.0) · Khảo sát ChatGPT toàn cầu (Ravšelj và cộng sự, CC BY 4.0)")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Lượt đăng ký môn", f"{len(f):,}".replace(",", "."))
c2.metric("Tỷ lệ đạt", f"{f['dat'].mean():.1%}".replace(".", ","))
c3.metric("Môn học", f["code_module"].nunique())
c4.metric("Kỳ học", f["code_presentation"].nunique())

t1, t2, t3, t5, t4 = st.tabs(["Tỷ lệ đạt theo biến", "Hành vi theo tuần", "Mô hình dự báo", "Khảo sát ChatGPT", "Tải báo cáo"])

with t1:
    b = st.selectbox("Chọn biến", list(BIEN), format_func=BIEN.get)
    g = f.groupby(b).agg(so_sv=("dat", "size"), ty_le_dat=("dat", "mean")).reset_index()
    g["ty_le_dat"] *= 100
    fig = px.bar(g, x=b, y="ty_le_dat", text=g["ty_le_dat"].round(1), labels={b: BIEN[b], "ty_le_dat": "Tỷ lệ đạt (%)"})
    fig.update_traces(marker_color="#1f6feb"); fig.update_yaxes(range=[0, 100])
    st.plotly_chart(fig, width="stretch")
    st.dataframe(g.rename(columns={b: BIEN[b], "so_sv": "Số SV", "ty_le_dat": "Tỷ lệ đạt (%)"}), hide_index=True)

with t2:
    chon = st.multiselect("Nhóm kết quả", list(KQ.values()), default=list(KQ.values()))
    d = wk[wk["ket_qua"].isin(chon)]
    fig = px.line(d, x="week", y="click_tb", color="ket_qua",
                  labels={"week": "Tuần (tính từ ngày bắt đầu khóa)", "click_tb": "Lượt click TB / sinh viên", "ket_qua": "Kết quả"})
    st.plotly_chart(fig, width="stretch")
    st.caption("Lượt click tổng hợp theo tuần từ 10,6 triệu bản ghi studentVle.")

with t3:
    m = json.load(open("results/metrics.json"))
    a, b_, c = st.columns(3)
    a.metric("Độ chính xác", f"{m['accuracy']:.1%}".replace(".", ","), f"nền {m['baseline_accuracy']:.1%}".replace(".", ","))
    b_.metric("Recall nhóm Chưa đạt", f"{m['recall_chua_dat']:.1%}".replace(".", ","))
    c.metric("ROC-AUC", f"{m['roc_auc']:.3f}".replace(".", ","))
    l, r = st.columns(2)
    l.image("results/fig_importance.png"); r.image("results/fig_confusion.png")
    st.caption("Decision Tree (độ sâu 5) chỉ dùng dữ liệu 4 tuần đầu khóa; 80% huấn luyện, 20% kiểm tra.")

with t5:
    sm = json.load(open("results/survey_summary.json", encoding="utf-8"))
    a, b_, c = st.columns(3)
    a.metric("Phản hồi khảo sát", f"{sm['so_phan_hoi']:,}".replace(",", "."))
    b_.metric("Đã dùng ChatGPT", f"{sm['ty_le_da_dung']:.1f}%".replace(".", ","))
    c.metric("Spearman mức dùng ~ tự đánh giá học tốt", f"{sm['spearman_Q15_Q35a']:.3f}".replace(".", ","))
    loai = st.radio("Xem", ["Mục đích sử dụng", "Lo ngại", "Mức dùng và tự đánh giá học tốt"], horizontal=True)
    if loai == "Mục đích sử dụng":
        d = pd.read_csv("results/survey_tasks.csv")
        fig = px.bar(d, x="ty_le_thuong_xuyen", y="nhiem_vu", orientation="h",
                     labels={"ty_le_thuong_xuyen": "Dùng thường xuyên hoặc luôn luôn (%)", "nhiem_vu": ""})
    elif loai == "Lo ngại":
        d = pd.read_csv("results/survey_concerns.csv")
        fig = px.bar(d, x="ty_le_dong_y", y="lo_ngai", orientation="h",
                     labels={"ty_le_dong_y": "Đồng ý hoặc rất đồng ý (%)", "lo_ngai": ""})
    else:
        d = pd.read_csv("results/survey_usage_success.csv")
        fig = px.bar(d, x="muc_dung", y="ty_le_thanh_cong",
                     labels={"muc_dung": "Mức dùng ChatGPT", "ty_le_thanh_cong": "Tự đánh giá học tốt (%)"})
        fig.update_yaxes(range=[0, 100])
    fig.update_traces(marker_color="#1f6feb")
    st.plotly_chart(fig, width="stretch")
    st.caption("Kết quả học tập trong khảo sát là tự đánh giá; tương quan không phải nhân quả.")

with t4:
    pdf = Path("results/bao_cao_mini_project.pdf")
    if pdf.exists():
        st.download_button("Tải báo cáo PDF", pdf.read_bytes(), file_name=pdf.name, mime="application/pdf")
    else:
        st.info("Chạy `python src/make_report.py` để sinh báo cáo PDF.")
