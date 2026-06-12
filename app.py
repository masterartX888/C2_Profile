import streamlit as st
import polars as pl
import pandas as pd

# ตั้งค่าหน้าเว็บให้เป็นแบบกว้าง (Wide Mode) เพื่อให้หน้าจอแสดงผลได้สวยงามและชัดเจน
st.set_page_config(page_title="Data Load Dashboard", layout="wide")

# =========================================================================
# 1. ระบบรักษาความปลอดภัย (Password Protection)
# =========================================================================
def check_password():
    """คืนค่า True ถ้าผู้ใช้ใส่รหัสผ่านถูกต้อง"""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    # แสดงหน้าต่างกรอกรหัสผ่านแบบเต็มหน้าจอ
    st.markdown("<h2 style='text-align: center;'>🔒 ระบบฐานข้อมูลภายใน (จำกัดการเข้าถึง)</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user_password = st.text_input("กรุณาใส่รหัสผ่านเพื่อเข้าใช้งาน Dashboard:", type="password")
        
        # รหัสผ่านสำหรับเข้าใช้งานระบบ
        if st.button("เข้าสู่ระบบ (Login)", use_container_width=True):
            if user_password == "123456": 
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("❌ รหัสผ่านไม่ถูกต้อง กรุณาลองใหม่อีกครั้ง")
    return False

# =========================================================================
# 2. เริ่มทำงานเมื่อรหัสผ่านถูกต้องเท่านั้น
# =========================================================================
if check_password():

    # หัวข้อหลักของหน้า Dashboard
    st.title("📊 Dashboard ระบบวิเคราะห์ข้อมูลโหลด (C2 Profile Load Trend)")
    st.markdown("---")

    # ลิงก์ตรงจาก OneDrive ทั้ง 6 ไฟล์ที่เติม ?download=1 เรียบร้อยแล้ว
    ONEDRIVE_LINKS = [
        "https://1drv.ms/x/c/a34ffb324226b8a4/IQQXNTUKAuuRT4S8IVfbW6lqAVFh0ObbHkT_igJq5SjdO74?download=1",
        "https://1drv.ms/x/c/a34ffb324226b8a4/IQR1DLpsinOxR406pGlrNiGNAdEoagHHRPKztRT3gRRKBpY?download=1",
        "https://1drv.ms/x/c/a34ffb324226b8a4/IQTjwaQDdIX0QbK6si-4IC-DAR54e4J8cQKxIk_-X3P1Wco?download=1",
        "https://1drv.ms/x/c/a34ffb324226b8a4/IQRcrIMUOz-aQbj_RQx6VtdMAQTaYv3YcIXfQJayPSP9MEk?download=1",
        "https://1drv.ms/x/c/a34ffb324226b8a4/IQTRatQc_lvcSbE1jFhlrfSlATVsHmPuMY7Xk1yqez8Q92c?download=1",
        "https://1drv.ms/x/c/a34ffb324226b8a4/IQTYBEsHXj0CQrlKmM9fCVwrAdYtfyCHRH5yvbr5LYzqabE?download=1"
    ]

    # ฟังก์ชันดาวน์โหลดและรวมไฟล์ (เวอร์ชันแก้ไขเพื่อไฟล์ที่ไม่มีหัวตาราง + กำหนดชื่อคอลัมน์ใหม่)
    @st.cache_data(ttl=3600)
    def load_and_combine_data(links):
        df_list = []
        for url in links:
            # has_header=False บังคับให้ Polars สร้างหัวตารางจำลอง (column_1, column_2, ...) 
            # ป้องกันโครงสร้างไฟล์แต่ละช่วงตบตีกันจนพัง
            single_df = pl.read_csv(url, has_header=False, truncate_ragged_lines=True, ignore_errors=True)
            df_list.append(single_df)
        
        # รวมร่างทุกไฟล์เข้าด้วยกันในแนวตั้ง (how="diagonal" ช่วยกันเหนียวกรณีจำนวนคอลัมน์ไฟล์ไหนเยื้องเกิน)
        combined_df = pl.concat(df_list, how="diagonal")
        
        # 🎯 เปลี่ยนชื่อคอลัมน์ตามที่คุณระบุมาทั้ง 7 คอลัมน์
        rename_dict = {
            "column_1": "StartTime",
            "column_2": "EndTime",
            "column_3": "Tag",
            "column_4": "Description",
            "column_5": "Asset",
            "column_6": "MW",
            "column_7": "Duration"
        }
        
        # ตรวจสอบคอลัมน์ที่มีอยู่จริงก่อนเปลี่ยนชื่อเพื่อป้องกัน Error หลังบ้าน
        available_renames = {k: v for k, v in rename_dict.items() if k in combined_df.columns}
        if available_renames:
            combined_df = combined_df.rename(available_renames)
            
        return combined_df

    # แสดงสถานะการโหลดข้อมูลในครั้งแรก
    with st.spinner("🔄 กำลังดาวน์โหลดและประมวลผลข้อมูลโหลดพลังงานขนาดใหญ่จาก OneDrive... (ใช้เวลาสักครู่ในครั้งแรก)"):
        try:
            df = load_and_combine_data(ONEDRIVE_LINKS)
            st.success(f"✅ โหลดและรวมข้อมูลสำเร็จ! รวมทั้งสิ้น {len(df):?} แถว")
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาดในการประมวลผลข้อมูล: {e}")
            st.info("💡 คำแนะนำ: ตรวจสอบความถูกต้องของไฟล์บน OneDrive อีกครั้ง")
            st.stop()

    st.markdown("### 🔍 ตัวเลือกตัวกรองข้อมูล (Filters)")

    # =========================================================================
    # 3. ส่วนของการทำฟิลเตอร์ (กรองข้อมูลด้วยคอลัมน์ Tag)
    # =========================================================================
    # ใช้คอลัมน์ "Tag" ในการกรองหลัก หากหาไม่เจอจะสลับไปใช้คอลัมน์แรกสุดแทนโดยอัตโนมัติ
    filter_col = "Tag" if "Tag" in df.columns else df.columns[0]
    
    # ดึงค่าที่ไม่ซ้ำกันในคอลัมน์ Tag ออกมาทำตัวเลือก Dropdown บนหน้าเว็บ
    unique_values = df[filter_col].unique().to_list()
    
    col_select, col_empty = st.columns([1, 2])
    with col_select:
        selected_value = st.selectbox(f"เลือกกรองข้อมูลตาม [{filter_col}]:", unique_values)

    # ทำการกรองข้อมูลตาม Tag สถานี/อุปกรณ์ที่กดเลือก
    filtered_df = df.filter(pl.col(filter_col) == selected_value)

    st.markdown("---")
    
    # =========================================================================
    # 4. ส่วนแสดงสถิติและกราฟ (KPI & Charts)
    # =========================================================================
    st.markdown("### 📈 ข้อมูลสรุปสถิติและแนวโน้มโหลด")
    
    # แสดงตัวเลขสรุป (KPI Card)
    kpi1, kpi2 = st.columns(2)
    with kpi1:
        st.metric(label="📊 จำนวนรายการที่พบหลังกรองข้อมูล", value=f"{len(filtered_df):,} แถว")
    with kpi2:
        st.metric(label="🗂️ สัดส่วนเมื่อเทียบกับข้อมูลทั้งหมดทั้งหมด", value=f"{(len(filtered_df)/len(df))*100:.2f} %")

    # แยกหน้าจอเป็นสองฝั่ง ฝั่งซ้ายกราฟ ฝั่งขวาตารางข้อมูลดิบ
    chart_col, table_col = st.columns([1, 1])
    
    with chart_col:
        st.markdown("#### 📊 กราฟแสดงแนวโน้มค่า MW (พรีวิว 1,000 แถวแรก)")
        
        # ตรวจสอบว่าคอลัมน์ MW มีอยู่จริงเพื่อพล็อตแกน Y
        if "MW" in filtered_df.columns:
            chart_data = filtered_df.head(1000).to_pandas()
            
            # ใช้คอลัมน์ เวลา (StartTime) เป็นแกน X วาดคู่กับค่าโหลด (MW) บนแกน Y
            if "StartTime" in chart_data.columns:
                st.line_chart(data=chart_data, x="StartTime", y="MW")
            else:
                st.line_chart(data=chart_data, y="MW")
        else:
            st.info("ไม่พบชื่อคอลัมน์ 'MW' ในระบบ จึงไม่สามารถแสดงผลกราฟแนวโน้มได้")

    with table_col:
        st.markdown("#### 🔎 พรีวิวตารางข้อมูลดิบ (100 บรรทัดแรก)")
        st.dataframe(filtered_df.head(100).to_pandas(), use_container_width=True)

    # ปุ่มสำหรับกดล้างแคชที่แถบเมนูด้านข้างเพื่อบังคับดึงข้อมูลใหม่ทันทีจาก OneDrive
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 ดึงข้อมูลใหม่จาก OneDrive ทันที (Clear Cache)"):
        st.cache_data.clear()
        st.rerun()
