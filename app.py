import streamlit as st
import pandas as pd
import datetime
import os

st.set_page_config(layout="wide", page_title="Quản lý Hồ sơ")

DATA_FILE = "ho_so_data.csv"
CHIDINH_FILE = "chi_dinh_list.txt"

# Hàm hỗ trợ
def load_chi_dinh():
    default = ["Máu", "Ure", "Đường"]
    if os.path.exists(CHIDINH_FILE):
        with open(CHIDINH_FILE, "r", encoding="utf-8") as f:
            saved = [line.strip() for line in f.readlines() if line.strip()]
            all_list = list(dict.fromkeys(default + saved))
            all_list.sort()  # <--- Sắp xếp A-Z
            return all_list
    default.sort() # <--- Sắp xếp A-Z cho danh sách mặc định
    return default

def save_all_chi_dinh(lst):
    with open(CHIDINH_FILE, "w", encoding="utf-8") as f:
        for item in lst: f.write(f"{item}\n")

# Load dữ liệu
if 'data' not in st.session_state:
    if os.path.exists(DATA_FILE): st.session_state.data = pd.read_csv(DATA_FILE)
    else: st.session_state.data = pd.DataFrame(columns=['Ngày', 'Khoa', 'Màu', 'Chỉ định'])
if 'list_chi_dinh' not in st.session_state: st.session_state.list_chi_dinh = load_chi_dinh()
# Khởi tạo mặc định màu
if 'selected_mau' not in st.session_state: st.session_state.selected_mau = "Đỏ"

# --- SIDEBAR ---
with st.sidebar:
    st.header("Nhập hồ sơ mới")
    
    def on_change_moi():
            val = st.session_state.input_moi
            if val:
                ds_moi = [x.strip() for x in val.split(',') if x.strip()]
                for item in ds_moi:
                    if item not in st.session_state.list_chi_dinh:
                        st.session_state.list_chi_dinh.append(item)
                
                st.session_state.list_chi_dinh.sort()  # <--- Tự động sắp xếp lại sau khi thêm
                save_all_chi_dinh(st.session_state.list_chi_dinh)
                st.session_state.input_moi = ""

    st.text_input("**Gõ chỉ định mới rồi nhấn Enter:**", key="input_moi", on_change=on_change_moi)

    with st.expander("⚙️ Quản lý danh sách"):
        for item in list(st.session_state.list_chi_dinh):
            col1, col2 = st.columns([3, 1])
            col1.write(f"• {item}")
            if col2.button("🗑️", key=f"del_{item}"):
                st.session_state.list_chi_dinh.remove(item)
                save_all_chi_dinh(st.session_state.list_chi_dinh)
                st.rerun()

# Form chính
    with st.form(key='form_nhap_lieu', clear_on_submit=True):
        ngay_chon = st.date_input("**Ngày**:", value=datetime.date.today())
        ngay_nhap = ngay_chon.strftime("%d/%m/%Y")
        
        khoa = st.selectbox("**Khoa**:", ["Nội tổng hợp", "Hồi sức tích cực chống độc"])
        
        # Chọn màu với index lưu trữ
        danh_sach_mau = ["Đỏ", "Xanh"]
        mau_index = danh_sach_mau.index(st.session_state.selected_mau)
        mau = st.selectbox("**Màu**:", danh_sach_mau, index=mau_index)
        
        st.write("**Chỉ định:**")
        
        # SỬ DỤNG HỆ THỐNG 2 CỘT ĐỂ TẬN DỤNG CHIỀU NGANG
        chon_checkbox = {}
        # Chia danh sách thành 2 nửa để hiển thị song song
        items = st.session_state.list_chi_dinh
        col1, col2 = st.columns(2)
        
        for i, item in enumerate(items):
            # Cột trái cho nửa đầu, cột phải cho nửa sau
            target_col = col1 if i < len(items) / 2 else col2
            chon_checkbox[item] = target_col.checkbox(item, key=f"check_{item}")
        
        submit_button = st.form_submit_button(label='Thêm hồ sơ')

    if submit_button:
        st.session_state.selected_mau = mau # Ghi nhớ màu
        # Lọc các chỉ định đã được chọn
        chon = [item for item, is_checked in chon_checkbox.items() if is_checked]
        
        if chon:
            new_row = {'Ngày': ngay_nhap, 'Khoa': khoa, 'Màu': mau, 'Chỉ định': ",".join(chon)}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
            st.session_state.data.to_csv(DATA_FILE, index=False)
            st.rerun()

# --- DASHBOARD ---
col_t, col_gear = st.columns([6, 1])
with col_t: st.title(f"📈 Tổng số hồ sơ: {len(st.session_state.data)}")
with col_gear:
    with st.popover("⚙️"):
        st.subheader("Quản lý hồ sơ")
        if st.button("❌ Xóa tất cả hồ sơ"):
            st.session_state.data = pd.DataFrame(columns=['Ngày', 'Khoa', 'Màu', 'Chỉ định'])
            st.session_state.data.to_csv(DATA_FILE, index=False)
            st.rerun()
        for idx in reversed(st.session_state.data.index):
            row = st.session_state.data.loc[idx]
            if st.button(f"🗑️ {row['Ngày']} - {row['Khoa']}", key=f"del_hoso_{idx}"):
                st.session_state.data = st.session_state.data.drop(idx)
                st.session_state.data.to_csv(DATA_FILE, index=False)
                st.rerun()

df = st.session_state.data
if not df.empty:
    c1, c2, c3 = st.columns(3)
    def draw_filter_buttons(col_name, df_data, title, container):
        with container:
            st.subheader(title)
            if col_name == 'Chỉ định':
                all_cd = [item.strip() for sublist in df_data['Chỉ định'].str.split(',') for item in sublist if item.strip()]
                counts = pd.Series(all_cd).value_counts()
            else:
                counts = df_data[col_name].value_counts()
            for val, count in counts.items():
                if st.button(f"{val} ({count})", use_container_width=True, key=f"{col_name}_{val}"):
                    st.session_state.filter = (col_name, val)

    draw_filter_buttons('Khoa', df, "Theo Khoa", c1)
    draw_filter_buttons('Màu', df, "Theo Màu", c2)
    draw_filter_buttons('Chỉ định', df, "Theo Chỉ định", c3)

    if 'filter' in st.session_state:
        col, val = st.session_state.filter
        st.subheader(f"🔍 Đang lọc: {val}")
        if st.button("❌ Bỏ lọc"): del st.session_state.filter; st.rerun()
        if col == 'Chỉ định': 
            df_view = df[df['Chỉ định'].apply(lambda x: val in [i.strip() for i in str(x).split(',')])]
        else: 
            df_view = df[df[col] == val]
    else:
        df_view = df
    
# ... (phần code trước đó của bạn)
    st.dataframe(df_view, use_container_width=True)
    
    # THÊM NÚT TẢI VỀ Ở ĐÂY (Nơi df đã tồn tại)
    st.download_button(
        label="📥 Tải file dữ liệu hiện tại (.csv)",
        data=df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'),
        file_name='ho_so_data_backup.csv',
        mime='text/csv',
    )
else:
    st.info("Chưa có dữ liệu.")