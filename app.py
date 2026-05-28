import streamlit as st
import pandas as pd
import datetime
import os
import re
import io

# Cấu hình trang
st.set_page_config(layout="wide", page_title="Quản lý Hồ sơ", page_icon="🏥")

DATA_FILE = "ho_so_data.csv"
CHIDINH_FILE = "chi_dinh_list.txt"

# --- HÀM HỖ TRỢ ---
def load_chi_dinh():
    default = ["Máu", "Ure", "Đường"]
    if os.path.exists(CHIDINH_FILE):
        with open(CHIDINH_FILE, "r", encoding="utf-8") as f:
            saved = [line.strip() for line in f.readlines() if line.strip()]
            all_list = list(dict.fromkeys(default + saved))
            all_list.sort()
            return all_list
    default.sort()
    return default

def save_all_chi_dinh(lst):
    with open(CHIDINH_FILE, "w", encoding="utf-8") as f:
        for item in lst: f.write(f"{item}\n")

# --- KHỞI TẠO SESSION STATE ---
if 'data' not in st.session_state:
    if os.path.exists(DATA_FILE): 
        st.session_state.data = pd.read_csv(DATA_FILE)
    else: 
        st.session_state.data = pd.DataFrame(columns=['Ngày', 'Khoa', 'Màu', 'Chỉ định'])

if 'list_chi_dinh' not in st.session_state: 
    st.session_state.list_chi_dinh = load_chi_dinh()

if 'selected_mau' not in st.session_state: 
    st.session_state.selected_mau = "Đỏ"

# --- SIDEBAR: NHẬP LIỆU ---
with st.sidebar:
    st.header("📝 Nhập hồ sơ mới")
    
    def on_change_moi():
        val = st.session_state.input_moi
        if val:
            ds_moi = [x.strip() for x in val.split(',') if x.strip()]
            for item in ds_moi:
                if item not in st.session_state.list_chi_dinh:
                    st.session_state.list_chi_dinh.append(item)
            st.session_state.list_chi_dinh.sort()
            save_all_chi_dinh(st.session_state.list_chi_dinh)
            st.session_state.input_moi = ""

    st.text_input("✨ Gõ chỉ định mới rồi nhấn Enter:", key="input_moi", on_change=on_change_moi)

    with st.expander("⚙️ Quản lý danh mục chỉ định"):
        for item in list(st.session_state.list_chi_dinh):
            col1, col2 = st.columns([4, 1])
            col1.write(f"• {item}")
            if col2.button("❌", key=f"del_{item}", help=f"Xóa {item}"):
                st.session_state.list_chi_dinh.remove(item)
                save_all_chi_dinh(st.session_state.list_chi_dinh)
                st.rerun()

    st.divider()

    with st.form(key='form_nhap_lieu', clear_on_submit=True):
        ngay_chon = st.date_input("**Ngày**:", value=datetime.date.today())
        ngay_nhap = ngay_chon.strftime("%d/%m/%Y")
        khoa = st.selectbox("**Khoa**:", ["Nội tổng hợp", "Hồi sức tích cực chống độc"])
        
        danh_sach_mau = ["Đỏ", "Xanh"]
        mau_index = danh_sach_mau.index(st.session_state.selected_mau)
        mau = st.selectbox("**Màu**:", danh_sach_mau, index=mau_index)
        
        st.write("**Chỉ định:**")
        chon_checkbox = {}
        
        # Chia 2 cột gọn gàng trong sidebar
        col_c1, col_c2 = st.columns(2)
        items = st.session_state.list_chi_dinh
        for i, item in enumerate(items):
            target_col = col_c1 if i < len(items) / 2 else col_c2
            chon_checkbox[item] = target_col.checkbox(item, key=f"check_{item}")
        
        submit_button = st.form_submit_button(label='➕ Thêm hồ sơ', use_container_width=True)

    if submit_button:
        st.session_state.selected_mau = mau
        chon = [item for item, is_checked in chon_checkbox.items() if is_checked]
        if chon:
            new_row = {'Ngày': ngay_nhap, 'Khoa': khoa, 'Màu': mau, 'Chỉ định': ", ".join(chon)}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
            st.session_state.data.to_csv(DATA_FILE, index=False)
            st.success("Đã thêm thành công!")
            st.rerun()

# --- MAIN DASHBOARD ---
df = st.session_state.data

tab_ho_so, tab_thong_ke = st.tabs(["📋 Hồ sơ", "📊 Thống kê"])

with tab_ho_so:
    # 1. Header & Nút hành động
    col_title, col_action = st.columns([4, 1])
    with col_title:
        st.title("📈 Bảng Cáo Cáo Hồ Sơ")
    with col_action:
        st.write("")  # Căn chỉnh cho đẹp
        with st.popover("⚙️ Quản lý & Xóa dữ liệu"):
            st.markdown("**Xóa dữ liệu cẩn thận!**")
            if st.button("🗑️ Xóa tất cả hồ sơ", type="primary", use_container_width=True):
                st.session_state.data = pd.DataFrame(columns=['Ngày', 'Khoa', 'Màu', 'Chỉ định'])
                st.session_state.data.to_csv(DATA_FILE, index=False)
                st.rerun()
            st.divider()
            st.write("Xóa từng dòng:")
            for idx in reversed(st.session_state.data.index):
                row = st.session_state.data.loc[idx]
                if st.button(f"Xóa: {row['Ngày']} - {row['Khoa']}", key=f"del_hoso_{idx}"):
                    st.session_state.data = st.session_state.data.drop(idx)
                    st.session_state.data.to_csv(DATA_FILE, index=False)
                    st.rerun()

    # Hiển thị số lượng tổng quan
    if not df.empty:
        st.metric("Tổng số hồ sơ", len(df))
        # Giữ biến này để phục vụ đếm số lượng cho Menu thả xuống bên dưới
        all_cd_flat = [item.strip() for sublist in df['Chỉ định'].dropna().str.split(',') for item in sublist if item.strip()]

    st.divider()

    # 2. Vùng Lọc Dữ Liệu
    if not df.empty:
        st.subheader("🔍 Lọc Dữ Liệu")

        # Chuẩn bị dữ liệu hiển thị kèm số đếm cho Selectbox
        khoa_counts = df['Khoa'].value_counts()
        khoa_options = ["Tất cả"] + [f"{k} ({v})" for k, v in khoa_counts.items()]

        mau_counts = df['Màu'].value_counts()
        mau_options = ["Tất cả"] + [f"{k} ({v})" for k, v in mau_counts.items()]

        cd_counts = pd.Series(all_cd_flat).value_counts()
        cd_options = ["Tất cả"] + [f"{k} ({v})" for k, v in cd_counts.items()]

        f1, f2, f3, f4 = st.columns([1, 1, 1, 0.5])

        with f1:
            loc_khoa = st.selectbox("Theo Khoa:", khoa_options)
        with f2:
            loc_mau = st.selectbox("Theo Màu:", mau_options)
        with f3:
            loc_cd = st.selectbox("Theo Chỉ định:", cd_options)
        with f4:
            st.write("")  # Dóng hàng nút bấm với input
            st.write("")
            if st.button("🔄 Bỏ lọc", use_container_width=True):
                st.rerun()

        # Xử lý logic lọc
        df_view = df.copy()
        if loc_khoa != "Tất cả":
            truename_khoa = loc_khoa.rsplit(" (", 1)[0]
            df_view = df_view[df_view['Khoa'] == truename_khoa]
        if loc_mau != "Tất cả":
            truename_mau = loc_mau.rsplit(" (", 1)[0]
            df_view = df_view[df_view['Màu'] == truename_mau]
        if loc_cd != "Tất cả":
            truename_cd = loc_cd.rsplit(" (", 1)[0]
            df_view = df_view[df_view['Chỉ định'].apply(lambda x: truename_cd in [i.strip() for i in str(x).split(',')])]

        st.caption(f"Đang hiển thị **{len(df_view)}** kết quả phù hợp.")

        # 3. Hiển thị bảng
        st.dataframe(
            df_view,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Ngày": st.column_config.TextColumn("Ngày lập", width="medium"),
                "Khoa": st.column_config.TextColumn("Tên Khoa", width="large"),
                "Màu": st.column_config.TextColumn("Phân loại (Màu)", width="small"),
                "Chỉ định": st.column_config.TextColumn("Danh sách Chỉ định", width="large"),
            }
        )

        st.download_button(
            label="📥 Tải file dữ liệu hiện tại (.csv)",
            data=df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'),
            file_name='ho_so_data_backup.csv',
            mime='text/csv',
        )
    else:
        st.info("👋 Bảng dữ liệu đang trống. Hãy nhập hồ sơ mới từ thanh công cụ bên trái nhé!")

with tab_thong_ke:
    st.title("🔎 Bóc tách số liệu")

    st.caption("Upload file Excel/CSV có cột `YLENH`, nhập bộ lọc và bấm **Lọc Dữ Liệu** để trích xuất số lượng thuốc theo đúng mẫu `... x [Số lượng] [Đơn vị]`.")

    def doc_y_lenh(text, ten_thuoc, don_vi=''):
        ket_qua = []
        if pd.isna(text): return ket_qua
        
        # 1. DANH SÁCH ĐEN (Blacklist): Bỏ qua các đơn vị đo lường thể tích, khối lượng
        ignore = r'ml|mg|g|mcg|l|gam|lit|iu|ui'
        
        # 2. REGEX NÂNG CẤP: Chỉ bắt số lượng với điều kiện đơn vị KHÔNG nằm trong danh sách đen
        regex = r'(?i)((?:(?!\bx\s*\d+\s*(?!(?:' + ignore + r')\b)[a-zA-ZÀ-ỹ]+).)*?)\bx\s*0*(\d+)\s*((?!(?:' + ignore + r')\b)[a-zA-ZÀ-ỹ]+)'
        matches = re.findall(regex, str(text))
        
        for m in matches:
            pre_text, so_luong, donvi_tim_thay = m
            # Check bộ lọc 1: Tên thuốc
            if ten_thuoc.lower() in pre_text.lower():
                # Check bộ lọc 2: Đơn vị (nếu có nhập)
                if not don_vi or don_vi.lower() in donvi_tim_thay.lower():
                    # Clean up text: Cắt bằng dấu "-" và giữ lại đoạn chứa tên thuốc
                    parts = pre_text.split('-')
                    drug_part = " - ".join([p for p in parts if ten_thuoc.lower() in p.lower()]).strip()
                    if not drug_part: drug_part = pre_text.strip()
                    
                    ket_qua.append({
                        'Chi tiết Y lệnh': f"{drug_part} x {so_luong} {donvi_tim_thay}",
                        'Số lượng': int(so_luong),
                        'Đơn vị': donvi_tim_thay
                    })
        return ket_qua

    up = st.file_uploader("📤 Upload file dữ liệu (Excel hoặc CSV)", type=["xlsx", "xls", "csv"])

    c1, c2 = st.columns([1, 1])
    with c1:
        ten_thuoc = st.text_input("Bộ lọc 1 (bắt buộc): Tên thuốc", placeholder="Ví dụ: Kali, Glucose...")
    with c2:
        don_vi = st.text_input("Bộ lọc 2 (tùy chọn): Đơn vị", placeholder="Ví dụ: Ống, Viên, Chai... (để trống = lấy tất cả)")

    col_btn, col_hint = st.columns([1, 3])
    with col_btn:
        do_filter = st.button("🔎 Lọc Dữ Liệu", type="primary", use_container_width=True)
    with col_hint:
        st.write("")
        st.caption("Gợi ý: nếu file có nhiều sheet, hãy lưu về CSV hoặc để dữ liệu ở sheet đầu tiên.")

    @st.cache_data(show_spinner=False)
    def _read_uploaded(file_name: str, raw_bytes: bytes) -> pd.DataFrame:
        bio = io.BytesIO(raw_bytes)
        if file_name.lower().endswith((".xlsx", ".xls")):
            try:
                return pd.read_excel(bio)
            except ImportError as e:
                # Pandas cần engine (thường là openpyxl) để đọc .xlsx
                raise ImportError(
                    "Thiếu thư viện để đọc Excel. Hãy cài `openpyxl` rồi thử lại."
                ) from e
        return pd.read_csv(bio, encoding="utf-8-sig")

    if do_filter:
        if up is None:
            st.warning("Bạn chưa upload file. Hãy chọn file Excel/CSV trước.")
        elif not ten_thuoc.strip():
            st.warning("Bạn chưa nhập **Tên thuốc** (bộ lọc bắt buộc).")
        else:
            try:
                df_src = _read_uploaded(up.name, up.getvalue())
            except Exception as e:
                st.error(f"Không đọc được file. Vui lòng kiểm tra định dạng Excel/CSV. Chi tiết: {e}")
                df_src = None

            if df_src is not None:
                if "YLENH" not in df_src.columns:
                    st.error("File không có cột tên là `YLENH`. Hãy kiểm tra lại file đầu vào.")
                else:
                    with st.spinner("Đang quét và bóc tách dữ liệu..."):
                        records: list[dict] = []
                        dv = don_vi.strip()
                        tt = ten_thuoc.strip()

                        for _, row in df_src.iterrows():
                            y = row.get("YLENH", None)
                            found = doc_y_lenh(y, tt, dv)
                            if not found:
                                continue

                            mabn = row.get("MABN", "")
                            hoten = row.get("HOTEN", "")
                            for item in found:
                                records.append({
                                    "MABN": mabn,
                                    "HOTEN": hoten,
                                    "Tên thuốc": tt,
                                    **item,
                                })

                    df_kq = pd.DataFrame.from_records(records, columns=["MABN", "HOTEN", "Tên thuốc", "Chi tiết Y lệnh", "Số lượng", "Đơn vị"])

                    st.divider()
                    m1, m2 = st.columns(2)
                    with m1:
                        st.metric("Tổng số lần kê y lệnh", int(len(df_kq)))
                    with m2:
                        st.metric("Tổng số lượng thuốc đã dùng", int(df_kq["Số lượng"].sum()) if not df_kq.empty else 0)

                    st.divider()
                    st.dataframe(df_kq, use_container_width=True, hide_index=True)

                    st.download_button(
                        label="📥 Tải kết quả (.csv)",
                        data=df_kq.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                        file_name=f"ket_qua_{tt}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
