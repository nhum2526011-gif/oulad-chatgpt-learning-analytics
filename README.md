# Hành vi học tập trực tuyến và nhận thức về ChatGPT của sinh viên đại học

Mini-project học phần CT999 Công nghệ số nâng cao (Trường Đại học Cần Thơ). Repo chứa toàn bộ mã nguồn, dữ liệu mẫu, báo cáo PDF sinh tự động và dashboard Streamlit.

- **Dashboard:** https://oulad-chatgpt-learning-analytics-vqlsdun5zgxfxd5bzrbh38.streamlit.app/
- **Báo cáo PDF:** [`results/bao_cao_mini_project.pdf`](results/bao_cao_mini_project.pdf)

## Đề tài và mục tiêu

1. Dự báo sớm sinh viên đạt hay chưa đạt chỉ từ dữ liệu 4 tuần đầu khóa học trực tuyến.
2. Mô tả mục đích sử dụng và lo ngại của sinh viên về ChatGPT.

## Phương pháp

| Bước | Script | Công cụ |
|---|---|---|
| 1. Làm sạch, tạo đặc trưng 4 tuần đầu | `src/prepare_data.py` | pandas, numpy |
| 2. Decision Tree Đạt / Chưa đạt | `src/train_model.py` | scikit-learn |
| 3. Thống kê khảo sát ChatGPT | `src/survey_analysis.py` | pandas, scipy |
| 4. Sinh báo cáo PDF | `src/make_report.py` | reportlab, matplotlib |
| 5. Dashboard | `app.py` | Streamlit, Plotly |

## Kết quả chính

- Decision Tree đạt độ chính xác 73,2% (mức nền 52,8%), ROC-AUC 0,805. Hai yếu tố quan trọng nhất là số tuần có truy cập trong 4 tuần đầu và điểm các bài kiểm tra sớm.
- 71,4% sinh viên khảo sát đã dùng ChatGPT. Mục đích dùng thường xuyên nhất là tìm ý tưởng (29,0%). Lo ngại được đồng ý nhiều nhất là ChatGPT khuyến khích gian lận (44,9%).

## Cấu trúc thư mục

```
├── app.py                  # dashboard Streamlit
├── data/
│   ├── raw/                # dữ liệu đầu vào (CSV)
│   └── processed/          # đặc trưng đã tạo
├── docs/                   # nội dung thuyết trình (.md) cho YC5b
├── results/                # số liệu, hình, mô hình, báo cáo PDF, slide
├── src/                    # mã nguồn
├── requirements.txt
└── LICENSE
```

## Cách chạy

```bash
pip install -r requirements.txt
python src/prepare_data.py
python src/train_model.py
python src/survey_analysis.py
python src/make_report.py
streamlit run app.py
```

Hai bài cá nhân đi kèm:

```bash
python src/yc5a_csv_to_pdf.py data/raw/studentInfo.csv results/yc5a_bao_cao_oulad.pdf   # CSV -> PDF
python src/yc5b_md_to_pptx.py docs/thuyet_trinh.md results/yc5b_thuyet_trinh.pptx       # Markdown -> PPTX
```

## Dữ liệu và giấy phép

| Dữ liệu | Nguồn | Giấy phép | Xử lý trong repo |
|---|---|---|---|
| OULAD | Kuzilek, Hlosta, Zdrahal (2017), *Scientific Data*, DOI [10.1038/sdata.2017.171](https://doi.org/10.1038/sdata.2017.171) | CC BY 4.0 | Giữ 4 bảng gốc; studentVle (10,6 triệu dòng) được gộp theo tuần thành `studentVle_weekly.csv` |
| Khảo sát ChatGPT toàn cầu | Ravšelj và cộng sự, Mendeley Data, DOI [10.17632/ymg9nsn6kn.2](https://doi.org/10.17632/ymg9nsn6kn.2) | CC BY 4.0 | Giữ 37/174 cột cần dùng; bỏ cột tên trường (Q5) |

Cả hai bộ dữ liệu đã được tác giả gốc ẩn danh.

**Giấy phép:** mã nguồn phát hành theo giấy phép [MIT](LICENSE). Dữ liệu trong `data/` giữ giấy phép CC BY 4.0 của tác giả gốc; khi dùng lại cần trích dẫn nguồn như bảng trên.
