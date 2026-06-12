import streamlit as st
import polars as pl
import pandas as pd

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Data Load Dashboard", layout="wide")

# ระบบรักษาความปลอดภัย
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct:
        return True

    st.markdown("<h2 style='text-align: center;'>🔒 ระบบฐานข้อมูลภายใน</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user_password = st.text_input("กรุณาใส่รหัสผ่าน:", type="password")
        if st.button("เข้าสู่ระบบ"):
            if user_password == "123456":
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("❌ รหัสผ่านไม่ถูกต้อง")
    return False

# ส่วนการประมวลผลข้อมูล
@st.cache_data(ttl=3600)
def load_and_combine_data(links):
    df_list = []
    for url in links:
        try:
            # ใช้ on_errors="skip" และ infer_schema_length=0 เพื่อข้ามปัญหาบรรทัดเสีย [cite: 36]
            single_df = pl.read_csv(
                url, 
                has_header=False, 
                infer_schema_length=0, 
                ignore_errors=True
            )
            if not single_df.is_empty():
                df_list.append(single_df)
            else:
                st.warning(f"ไฟล์ว่างเปล่าหรืออ่านไม่ได้: {url}")
        except Exception as e:
            st.error(f"Error สำหรับลิงก์ {url}: {e}")
            continue
    
    if not df_list:
        return None
    
    # รวมไฟล์ [cite: 28]
    combined_df = pl.concat(df_list, how="diagonal")
    
    # เปลี่ยนชื่อคอลัมน์
    rename_dict = {
        "column_1": "StartTime", "column_2": "EndTime", "column_3": "Tag",
        "column_4": "Description", "column_5": "Asset", "column_6": "MW", "column_7": "Duration"
    }
    available_renames = {k: v for k, v in rename_dict.items() if k in combined_df.columns}
    combined_df = combined_df.rename(available_renames)
    
    # แปลงชนิดข้อมูล [cite: 15, 29]
    if "MW" in combined_df.columns:
        combined_df = combined_df.with_columns(pl.col("MW").cast(pl.Float64, strict=False))
    if "StartTime" in combined_df.columns:
        combined_df = combined_df.with_columns(pl.col("StartTime").str.to_datetime(strict=False))
        
    return combined_df

# เริ่มทำงาน
if check_password():
    st.title("📊 Dashboard ระบบวิเคราะห์ข้อมูลโหลด (C2 Profile)")
    
    ONEDRIVE_LINKS = [
        "https://1drv.ms/x/c/a34ffb324226b8a4/IQQXNTUKAuuRT4S8IVfbW6lqAVFh0ObbHkT_igJq5SjdO74?download=1",
        "https://1drv.ms/x/c/a34ffb324226b8a4/IQR1DLpsinOxR406pGlrNiGNAdEoagHHRPKztRT3gRRKBpY?download=1",
        "https://1drv.ms/x/c/a34ffb324226b8a4/IQTjwaQDdIX0QbK6si-4IC-DAR54e4J8cQKxIk_-X3P1Wco?download=1",
        "https://1drv.ms/x/c/a34ffb324226b8a4/IQRcrIMUOz-aQbj_RQx6VtdMAQTaYv3YcIXfQJayPSP9MEk?download=1",
        "https://1drv.ms/x/c/a34ffb324226b8a4/IQTRatQc_lvcSbE1jFhlrfSlATVsHmPuMY7Xk1yqez8Q92c?download=1",
        "https://1drv.ms/x/c/a34ffb324226b8a4/IQTYBEsHXj0CQrlKmM9fCVwrAdYtfyCHRH5yvbr5LYzqabE?download=1"
    ]

    with st.spinner("กำลังโหลดข้อมูล..."):
        df = load_and_combine_data(ONEDRIVE_LINKS)

    if df is None:
        st.error("ไม่สามารถดึงข้อมูลได้ โปรดตรวจสอบลิงก์ [cite: 38, 40]")
    else:
        filter_col = "Tag" if "Tag" in df.columns else df.columns[0]
        unique_values = df[filter_col].drop_nulls().unique().to_list()
        selected_value = st.selectbox(f"เลือกกรองข้อมูลตาม [{filter_col}]:", unique_values)
        filtered_df = df.filter(pl.col(filter_col) == selected_value)

        tab1, tab2 = st.tabs(["📊 กราฟวิเคราะห์", "📋 ตารางข้อมูล"])
        with tab1:
            st.metric("จำนวนรายการ", f"{len(filtered_df):,}")
            if "MW" in filtered_df.columns:
                st.line_chart(data=filtered_df.to_pandas(), x="StartTime", y="MW")
        with tab2:
            st.dataframe(filtered_df.to_pandas(), use_container_width=True)

    if st.sidebar.button("🔄 ดึงข้อมูลใหม่ (Clear Cache)"):
        st.cache_data.clear()
        st.rerun()
