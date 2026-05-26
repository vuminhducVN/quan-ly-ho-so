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
            return list(dict.fromkeys(default + saved))
    return default

def save_all_chi_dinh(lst):
    with open(CHIDINH_FILE, "w", encoding="utf-8") as f:
        for item in lst: f.write(f"{item}\n")

# Load dữ liệu
if 'data' not in st.session_state:
    if os.path.exists(DATA_FILE): st.session_state.data = pd.read_csv(DATA_FILE)
    else: st.session_state.data = pd.DataFrame(columns=['Ngày', 'Khoa', 'Màu', 'Chỉ định'])
if 'list_chi_dinh' not in st.session_state: st.session_state.list_chi_dinh = load_chi_dinh()

# --- SIDEBAR ---
with st.sidebar:
    st.header("Nhập hồ sơ mới")
    
    # Logic thêm chỉ định
    def on_change_moi():
        val = st.session_state.input_moi
        if val:
            ds_moi = [x.strip() for x in val.split(',') if x.strip()]
            for item in ds_moi:
                if item not in st.session_state.list_chi_dinh:
                    st.session_state.list_chi_dinh.append(item)
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

    # Form chính với các tiêu đề in đậm, viết hoa
    with st.form(key='form_nhap_lieu', clear_on_submit=True):
        ngay_nhap = st.text_input("**Ngày**:", value=datetime.date.today().strftime("%d/%m/%Y"))
        khoa = st.selectbox("**Khoa**:", ["Nội tổng hợp", "Hồi sức tích cực chống độc"])
        mau = st.selectbox("**Màu**:", ["Đỏ", "Xanh"])
        
        st.write("**Chỉ định**:")
        cols = st.columns(2)
        chon_checkbox = {item: cols[i % 2].checkbox(item, key=f"check_{item}") for i, item in enumerate(st.session_state.list_chi_dinh)}
        submit_button = st.form_submit_button(label='Thêm hồ sơ')

    if submit_button:
        chon = [item for item, is_checked in chon_checkbox.items() if is_checked]
        if chon:
            new_row = {'Ngày': ngay_nhap, 'Khoa': khoa, 'Màu': mau, 'Chỉ định': ",".join(chon)}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
            st.session_state.data.to_csv(DATA_FILE, index=False)
            st.rerun()

# --- DASHBOARD ---
# Nút bánh răng quản lý hồ sơ
col_t, col_gear = st.columns([6, 1])
with col_t: st.title(f"📈 Tổng số hồ sơ: {len(st.session_state.data)}")
with col_gear:
    with st.popover("⚙️"):
        st.subheader("Quản lý hồ sơ")
        if st.button("❌ Xóa tất cả hồ sơ"):
            st.session_state.data = pd.DataFrame(columns=['Ngày', 'Khoa', 'Màu', 'Chỉ định'])
            st.session_state.data.to_csv(DATA_FILE, index=False)
            st.rerun()
        st.write("Xóa từng hồ sơ:")
        # Đảo ngược danh sách để hồ sơ mới nhất nằm trên cùng
        for idx in reversed(st.session_state.data.index):
            row = st.session_state.data.loc[idx]
            if st.button(f"🗑️ {row['Ngày']} - {row['Khoa']}", key=f"del_hoso_{idx}"):
                st.session_state.data = st.session_state.data.drop(idx)
                st.session_state.data.to_csv(DATA_FILE, index=False)
                st.rerun()

df = st.session_state.data
if not df.empty:
    c1, c2, c3 = st.columns(3)
    
    # Hàm hỗ trợ để đếm và hiển thị
    def draw_filter_buttons(col_name, df_data, title, container):
        with container:
            st.subheader(title)
            # Tính count
            if col_name == 'Chỉ định':
                all_cd = [item.strip() for sublist in df_data['Chỉ định'].str.split(',') for item in sublist if item.strip()]
                counts = pd.Series(all_cd).value_counts()
            else:
                counts = df_data[col_name].value_counts()
            
            # Hiển thị nút kèm số lượng
            for val, count in counts.items():
                if st.button(f"{val} ({count})", use_container_width=True, key=f"{col_name}_{val}"):
                    st.session_state.filter = (col_name, val)

    draw_filter_buttons('Khoa', df, "Theo Khoa", c1)
    draw_filter_buttons('Màu', df, "Theo Màu", c2)
    draw_filter_buttons('Chỉ định', df, "Theo Chỉ định", c3)

    # --- PHẦN LỌC DỮ LIỆU (GIỮ NGUYÊN) ---
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
    
    st.dataframe(df_view, use_container_width=True)
else:
    st.info("Chưa có dữ liệu.")