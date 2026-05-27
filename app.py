import streamlit as st
import pandas as pd
import datetime
import os

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

# 1. Header & Nút hành động
col_title, col_action = st.columns([4, 1])
with col_title:
    st.title("📈 Bảng Cáo Cáo Hồ Sơ")
with col_action:
    st.write("") # Căn chỉnh cho đẹp
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
        st.write("") # Dóng hàng nút bấm với input
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