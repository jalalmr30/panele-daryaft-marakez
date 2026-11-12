import os
import pandas as pd
import streamlit as st
import jdatetime

# تنظیمات صفحه
st.set_page_config(
    page_title="پنل مدیریت و شماره‌دهی اسناد درمانی",
    page_icon="📋",
    layout="wide"
)

# پوشه ذخیره تصاویر فاکتورها
UPLOAD_FOLDER = "uploaded_images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DATA_FILE = "documents_data.csv"

# بارگذاری یا ایجاد فایل داده‌ها
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=[
            "شماره ثبت", "نام مرکز درمانی", "ثبت‌کننده", 
            "تاریخ دریافت از مرکز", "تاریخ ارسال به ارزیاب", 
            "تصویر فاکتور", "تاریخ ثبت سیستمی"
        ])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# تولید شماره ثبت خودکار (شروع از 1403001)
def generate_registration_number(df):
    if df.empty or "شماره ثبت" not in df.columns:
        return "1403001"
    
    # استخراج آخرین شماره ثبت
    last_no = df["شماره ثبت"].astype(str).max()
    try:
        new_no = int(last_no) + 1
        return str(new_no)
    except:
        return "1403001"

def main():
    st.title("📋 پنل مدیریت و شماره‌دهی اسناد درمانی مراکز")
    st.markdown("این پنل جهت ثبت، شماره‌دهی و پیگیری اسناد دریافتی از مراکز درمانی طراحی شده است.")

    df = load_data()

    tab1, tab2 = st.tabs(["➕ ثبت سند جدید", "📊 لیست و پیگیری اسناد"])

    with tab1:
        st.subheader("فرم ثبت فاکتور / سند جدید")
        
        with st.form("entry_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                center_name = st.text_input("نام مرکز درمانی / داروخانه *")
                recorder = st.selectbox("ثبت‌کننده *", ["شما (مدیر سیستم)", "ارزیاب"])
            
            with col2:
                # تاریخ‌های شمسی با استفاده از jdatetime
                today_jalali = jdatetime.date.today().strftime("%Y/%m/%d")
                received_date = st.text_input("تاریخ دریافت از مرکز (مثال: 1403/08/01)", value=today_jalali)
                sent_date = st.text_input("تاریخ ارسال به ارزیاب (مثال: 1403/08/03)", value=today_jalali)

            uploaded_file = st.file_uploader("آپلود تصویر یا PDF فاکتور/سند", type=["png", "jpg", "jpeg", "pdf"])
            
            submitted = st.form_submit_button("ثبت سند و صدور شماره")
            
            if submitted:
                if not center_name:
                    st.error("لطفاً نام مرکز درمانی را وارد کنید.")
                else:
                    new_reg_no = generate_registration_number(df)
                    
                    file_path = ""
                    if uploaded_file is not None:
                        file_extension = uploaded_file.name.split(".")[-1]
                        file_name = f"{new_reg_no}.{file_extension}"
                        file_path = os.path.join(UPLOAD_FOLDER, file_name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                    
                    new_row = {
                        "شماره ثبت": new_reg_no,
                        "نام مرکز درمانی": center_name,
                        "ثبت‌کننده": recorder,
                        "تاریخ دریافت از مرکز": received_date,
                        "تاریخ ارسال به ارزیاب": sent_date,
                        "تصویر فاکتور": file_path,
                        "تاریخ ثبت سیستمی": jdatetime.datetime.now().strftime("%Y/%m/%d %H:%M")
                    }
                    
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(df)
                    
                    st.success(f"✅ سند با موفقیت ثبت شد! شماره ثبت اختصاص یافته: **{new_reg_no}**")

    with tab2:
        st.subheader("لیست اسناد ثبت‌شده و پیگیری")
        
        if df.empty:
            st.info("هنوز هیچ سندی ثبت نشده است.")
        else:
            # فیلتر و جستجو
            search_query = st.text_input("🔍 جستجو بر اساس نام مرکز یا شماره ثبت:")
            
            filtered_df = df.copy()
            if search_query:
                filtered_df = filtered_df[
                    filtered_df["شماره ثبت"].astype(str).str.contains(search_query, na=False) |
                    filtered_df["نام مرکز درمانی"].str.contains(search_query, na=False)
                ]

            st.dataframe(filtered_df.drop(columns=["تصویر فاکتور"]), use_container_width=True)
            
            st.markdown("---")
            st.subheader("مشاهده تصویر فاکتور سند")
            
            selected_reg_no = st.selectbox("انتخاب شماره ثبت برای مشاهده سند:", options=df["شماره ثبت"].astype(str).tolist())
            
            if selected_reg_no:
                row = df[df["شماره ثبت"].astype(str) == selected_reg_no].iloc[0]
                st.write(f"**نام مرکز:** {row['نام مرکز درمانی']} | **تاریخ دریافت:** {row['تاریخ دریافت از مرکز']}")
                
                img_path = row["تصویر فاکتور"]
                if pd.notna(img_path) and os.path.exists(str(img_path)):
                    if img_path.lower().endswith('.pdf'):
                        st.info("این سند به صورت فایل PDF است.")
                        with open(img_path, "rb") as f:
                            st.download_button("دانلود فایل PDF فاکتور", f, file_name=os.path.basename(img_path))
                    else:
                        st.image(img_path, caption=f"فاکتور مربوط به شماره ثبت: {selected_reg_no}", use_container_width=True)
                else:
                    st.warning("تصویری برای این سند آپلود نشده است.")

            st.markdown("---")
            st.info("💡 **یادآوری قانونی:** طبق رویه، تسویه حساب و پرداخت نهایی اسناد دریافتی مراکز باید ظرف حداکثر **۲ ماه** از تاریخ دریافت سند انجام گیرد.")

if __name__ == "__main__":
    main()
