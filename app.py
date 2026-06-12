import streamlit as st
import polars as pl
import pandas as pd

# ตั้งค่าหน้าเว็บให้เป็นแบบกว้าง (Wide Mode) เพื่อให้ Dashboard ดูสวยงาม
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
        
        # 💡 คุณสามารถเปลี่ยนรหัสผ่านที่ต้องการได้ที่นี่ (เปลี่ยนจาก '123456' เป็นรหัสอื่น)
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
    st.title("📊 Dashboard ระบบวิเคราะห์ข้อมูลโหลด (Multi-File)")
    st.markdown("---")

    # ใส่ลิงก์ตรง (Direct Download Link) จาก OneDrive ของคุณที่แปลงแล้ว
    ONEDRIVE_LINKS = [
        "https://1drv.ms/x/c/a34ffb324226b8a4/IQQXNTUKAuuRT4S8IVfbW6lqAVFh0ObbHkT_igJq5SjdO74",
        "https://1drv.ms/x/c/a34ffb324226b8a4/IQR1DLpsinOxR406pGlrNiGNAdEoagHHRPKztRT3gRRKBpY",
        "https://1drv.ms/x/c/a34ffb324226b8a4/IQTjwaQDdIX0QbK6si-4IC-DAR54e4J8cQKxIk_-X3P1Wco",
        "https://1drv.ms/x/c/a34ffb324226b8a4/IQRcrIMUOz-aQbj_RQx6VtdMAQTaYv3YcIXfQJayPSP9MEk",
        "https://1drv.ms/x/c/a34ffb324226b8a4/IQTRatQc_lvcSbE1jFhlrfSlATVsHmPuMY7Xk1yqez8Q92c",
        "https://1drv.ms/x/c/a34ffb324226b8a4/IQTYBEsHXj0CQrlKmM9fCVwrAdYtfyCHRH5yvbr5LYzqabE"
    ]

    # ฟังก์ชันดาวน์โหลดและรวมไฟล์ (ติดแคชไว้ 1 ชั่วโมง เพื่อไม่ให้เว็บโหลดช้าเวลาคนกดเล่น)
    @st.cache_data(ttl=3600)
    def load_and_combine_data(links):
        df_list = []
        for url in links:
            # ดึงข้อมูลจากเน็ตทีละไฟล์ด้วย Polars (ความเร็วสูง)
            single_df = pl.read_csv(url)
            df_list.append(single_df)
        
        # รวมร่างทุกไฟล์เข้าด้วยกันเป็นก้อนเดียวในแนวตั้ง
        combined_df = pl.concat(df_list)
        return combined_df

    # แสดงสถานะการโหลดข้อมูลในครั้งแรก
    with st.spinner("🔄 กำลังดาวน์โหลดและคำนวณข้อมูลขนาดใหญ่จาก OneDrive... (ใช้เวลาประมาณ 15-30 วินาทีในครั้งแรก)"):
        try:
            df = load_and_combine_data(ONEDRIVE_LINKS)
            st.success(f"✅ โหลดและรวมข้อมูลสำเร็จ! รวมทั้งสิ้น {len(df):,} แถว")
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
            st.info("💡 คำแนะนำ: ตรวจสอบให้แน่ใจว่าได้แปลงลิงก์ OneDrive เป็น Direct Link เรียบร้อยแล้ว")
            st.stop()

    st.markdown("### 🔍 ตัวเลือกตัวกรองข้อมูล (Filters)")

    # =========================================================================
    # 3. ส่วนของการทำฟิลเตอร์ (ปรับแต่งตามชื่อคอลัมน์จริงในไฟล์ของคุณ)
    # * ด้านล่างนี้คือตัวอย่าง สมมติว่าไฟล์ของคุณมีคอลัมน์ชื่อ 'Station' หรือ 'Type' *
    # =========================================================================
    
    # เพื่อให้โค้ดทำงานได้แม้ชื่อคอลัมน์ไม่ตรง ในที่นี้จะดึงชื่อคอลัมน์แรกมาเป็นตัวอย่างฟิลเตอร์
    all_columns = df.columns
    filter_col = all_columns[0] # ดึงคอลัมน์แรกสุดในไฟล์ CSV มาทำฟิลเตอร์
    
    # ดึงค่าที่ไม่ซ้ำกันในคอลัมน์นั้นมาทำ Dropdown
    unique_values = df[filter_col].unique().to_list()
    
    col_select, col_empty = st.columns([1, 2])
    with col_select:
        selected_value = st.selectbox(f"กรองข้อมูลตาม [{filter_col}]:", unique_values)

    # กรองข้อมูลตามที่ผู้ใช้เลือก
    filtered_df = df.filter(pl.col(filter_col) == selected_value)

    st.markdown("---")
    
    # =========================================================================
    # 4. ส่วนแสดงสถิติและกราฟ (KPI & Charts)
    # =========================================================================
    st.markdown("### 📈 ข้อมูลสรุปสถิติ")
    
    # แสดงตัวเลขสรุป (KPI Card)
    kpi1, kpi2 = st.columns(2)
    with kpi1:
        st.metric(label="📊 จำนวนรายการที่พบหลังกรอกข้อมูล", value=f"{len(filtered_df):,} แถว")
    with kpi2:
        st.metric(label="🗂️ สัดส่วนเมื่อเทียบกับข้อมูลทั้งหมด", value=f"{(len(filtered_df)/len(df))*100:.2f} %")

    # ส่วนของกราฟและการแสดงผลข้อมูล
    chart_col, table_col = st.columns([1, 1])
    
    with chart_col:
        st.markdown("#### 📊 กราฟสรุปผลเบื้องต้น")
        # ตัวอย่างการวาดกราฟเส้น: ดึงข้อมูล 1,000 แถวแรกที่กรองแล้วมาทำกราฟ
        # (หมายเหตุ: สตรีมลิตโชว์กราฟต้องแปลงเป็น pandas ชั่วคราว)
        chart_data = filtered_df.head(1000).to_pandas()
        
        # สมมติว่าต้องการดูกราฟเส้นของคอลัมน์ที่ 2 ในไฟล์ CSV
        if len(all_columns) >  1:
            st.line_chart(data=chart_data, y=all_columns[1])
        else:
            st.info("ไฟล์ข้อมูลมีคอลัมน์น้อยเกินไปไม่สามารถวาดกราฟเปรียบเทียบได้")

    with table_col:
        st.markdown("#### 🔎 พรีวิวตารางข้อมูลดิบ (100 บรรทัดแรก)")
        # แสดงตารางข้อมูลแบบInteractive เลื่อนดูได้ ขยายได้
        st.dataframe(filtered_df.head(100).to_pandas(), use_container_width=True)

    # ปุ่มสำหรับกดล้างแคชเพื่อดึงข้อมูลใหม่ทันทีจาก OneDrive
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 ดึงข้อมูลใหม่จาก OneDrive ทันที (Clear Cache)"):
        st.cache_data.clear()
        st.rerun()
