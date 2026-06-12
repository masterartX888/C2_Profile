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

    # ลิงก์ตรงจาก OneDrive ทั้ง 6 ไฟล์
    ONEDRIVE_LINKS = [
        "https://1drv.ms/x/c/a34ffb324226b8a4/IQQXNTUKAuuRT4S8IVfbW6lqAVFh0ObbHkT_igJq5SjdO74?download=1",
        "https://1drv.ms/x/c/a34ffb324226b8a4/IQR1DLpsinOxR406pGlrNiGNAdEoagHHRPKztRT3gRRKBpY?download=1",
        "https://1drv.ms/x/c/a34ffb324226b8a4/IQTjwaQDdIX0QbK6si-4IC-DAR54e4J8cQKxIk_-X3P1Wco?download=1",
        "https://1drv.ms/x/c/a34ffb324226b8a4/IQRcrIMUOz-aQbj_RQx6VtdMAQTaYv3YcIXfQJayPSP9MEk?download=1",
        "https://1drv.ms/x/c/a34ffb324226b8a4/IQTRatQc_lvcSbE1jFhlrfSlATVsHmPuMY7Xk1yqez8Q92c?download=1",
        "https://1drv.ms/x/c/a34ffb324226b8a4/IQTYBEsHXj0CQrlKmM9fCVwrAdYtfyCHRH5yvbr5LYzqabE?download=1"
    ]

    # ฟังก์ชันดาวน์โหลดและรวมไฟล์ (เวอร์ชันป้องกัน Data Type ขัดกัน)
    @st.cache_data(ttl=3600)
    def load_and_combine_data(links):
        df_list = []
        for url in links:
            # ใช้ low_memory=False และให้อ่านค่าทุกอย่างเป็นแบบยืดหยุ่นก่อน
            single_df = pl.read_csv(url, has_header=False, truncate_ragged_lines=True, ignore_errors=True)
            
            # บังคับแปลงคอลัมน์ที่ 6 (MW) และคอลัมน์ที่ 7 (Duration) ให้เป็น String ชั่วคราวเพื่อให้รวมร่างกันได้ก่อน ไม่ทับไลน์กัน
            if len(single_df.columns) >= 7:
                single_df = single_df.with_columns([
                    pl.col("column_6").cast(pl.Utf8, strict=False),
                    pl.col("column_7").cast(pl.Utf8, strict=False)
                ])
            df_list.append(single_df)
        
        # รวมร่างทุกไฟล์เข้าด้วยกันในแนวตั้ง
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
        
        available_renames = {k: v for k, v in rename_dict.items() if k in combined_df.columns}
        if available_renames:
            combined_df = combined_df.rename(available_renames)
        
        # 🔥 ด่านสำคัญ: ล้างข้อความแปลกปลอมใน MW และ Duration ให้กลายเป็นตัวเลขถ้วน ๆ (Float)
        if "MW" in combined_df.columns:
            combined_df = combined_df.with_columns(pl.col("MW").cast(pl.Float64, strict=False))
        if "Duration" in combined_df.columns:
            combined_df = combined_df.with_columns(pl.col("Duration").cast(pl.Float64, strict=False))
            
        return combined_df

    # แสดงสถานะการโหลดข้อมูลในครั้งแรก
    with st.spinner("🔄 กำลังดาวน์โหลดและประมวลผลข้อมูลโหลดพลังงานขนาดใหญ่จาก OneDrive... (ใช้เวลาสักครู่ในครั้งแรก)"):
        try:
            df = load_and_combine_data(ONEDRIVE_LINKS)
            
            # ตรวจสอบว่ามีข้อมูลหลุดเข้ามาไหม
            if len(df) == 0:
                st.error("❌ ดึงข้อมูลได้สำเร็จ แต่ข้อมูลข้างในไฟล์ว่างเปล่า (0 แถว)")
                st.stop()
                
            st.success(f"✅ โหลดและรวมข้อมูลสำเร็จ! รวมทั้งสิ้น {len(df):?} แถว")
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาดในการประมวลผลข้อมูลหลังบ้าน: {e}")
            st.info("💡 คำแนะนำเบื้องต้น: ลองกดปุ่ม '🔄 ดึงข้อมูลใหม่' ที่แถบด้านข้างซ้ายมือดูอีกครั้งครับ")
            st.stop()

    st.markdown("### 🔍 ตัวเลือกตัวกรองข้อมูล (Filters)")

    # =========================================================================
    # 3. ส่วนของการทำฟิลเตอร์ (กรองข้อมูลด้วยคอลัมน์ Tag)
    # =========================================================================
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
        
        if "MW" in filtered_df.columns:
            # ดึงข้อมูล 1,000 แถวแรกไปแปลงเป็น ป้องกันคราวด์ค้าง และถมค่าว่างที่แปลงไม่ผ่านออกไปก่อนพล็อต
            chart_data = filtered_df.head(1000).drop_nulls(subset=["MW"]).to_pandas()
            
            if not chart_data.empty:
                if "StartTime" in chart_data.columns:
                    st.line_chart(data=chart_data, x="StartTime", y="MW")
                else:
                    st.line_chart(data=chart_data, y="MW")
            else:
                st.info("⚠️ ข้อมูลใน 1,000 แถวแรกของกลุ่มนี้ ไม่มีตัวเลขค่า MW ที่สมบูรณ์พล็อตกร๊าฟได้")
        else:
            st.info("ไม่พบชื่อคอลัมน์ 'MW' ในระบบ")

    with table_col:
        st.markdown("#### 🔎 พรีวิวตารางข้อมูลดิบ (100 บรรทัดแรก)")
        st.dataframe(filtered_df.head(100).to_pandas(), use_container_width=True)

    # ปุ่มสำหรับกดล้างแคชที่แถบเมนูด้านข้างเพื่อบังคับดึงข้อมูลใหม่ทันทีจาก OneDrive
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 ดึงข้อมูลใหม่จาก OneDrive ทันที (Clear Cache)"):
        st.cache_data.clear()
        st.rerun()
