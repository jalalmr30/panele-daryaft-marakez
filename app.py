import os
import streamlit as st
import pandas as pd
import jdatetime
from datetime import datetime, timedelta

# تنظیمات صفحه
st.set_page_config(page_title="سیستم پیگیری و شماره‌دهی اسناد", page_layout="wide")

# مسیر فایل‌های ذخیره‌سازی
DATA_FILE = "documents_data.csv"
UPLOAD_DIR = "uploaded_images"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# بارگذاری یا ایجاد دیتابیس اولیه
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=[
            "شماره ثبت", "نام مرکز درمانی", "تاریخ دریافت", "تاریخ ارسال به ارزیاب", 
            "مهلت پرداخت (۲ ماهه)", "نام کاربر ثبت‌کننده", "فایل تصویر"
        ])

df = load_data()

st.title("📋 پنل مدیریت و شماره‌دهی اسناد درمانی")
st.markdown("این سامانه برای ثبت، شماره‌دهی خودکار و پیگیری مدارک ارسالی به ارزیاب طراحی شده است.")

# منوی تب‌بندی شده برای راحتی کار
tab1, tab2 = st.tabs(["➕ ثبت سند جدید", "📊 لیست و پیگیری اسناد"])

with tab1:
    st.subheader("فرم ثبت سند جدید")
    
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            center_name = st.text_input("نام مرکز درمانی / بیمارستان:")
            user_role = st.selectbox("ثبت‌کننده‌ی سند:", ["شما (مدیر سیستم)", "ارزیاب"])
            
        with col2:
            # دریافت تاریخ شمسی به صورت متن یا ساده
            today_jalali = jdatetime.date.today().strftime("%Y/%m/%d")
            recv_date = st.text_input("تاریخ دریافت از مرکز (مثلاً 1403/08/20):", value=today_jalali)
            send_date = st.text_input("تاریخ ارسال به ارزیاب (مثلاً 1403/08/21):", value=today_jalali)
            
        uploaded_file = st.file_uploader("آپلود تصویر فاکتور یا مدرک (عکس/PDF):", type=["png", "jpg", "jpeg", "pdf"])
        
        submit_btn = st.form_submit_button("ثبت مدرک و صدور شماره ثبت")
        
        if submit_btn:
            if not center_name:
                st.warning("لطفاً نام مرکز درمانی را وارد کنید.")
            else:
                # تولید شماره ثبت خودکار (بر اساس آخرین شماره موجود)
                if len(df) == 0:
                    next_reg_no = 1403001
                else:
                    try:
                        max_no = df["شماره ثبت"].max()
                        next_reg_no = int(max_no) + 1
                    except:
                        next_reg_no = 1403001
                
                # ذخیره تصویر در پوشه
                file_name = ""
                if uploaded_file is not None:
                    file_name = f"{next_reg_no}_{uploaded_file.name}"
                    file_path = os.path.join(UPLOAD_DIR, file_name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                
                # محاسبه مهلت پرداخت (فرضی: ۳۰ تا ۶۰ روز بعد از دریافت)
                # در اینجا یک یادداشت ساده ثبت می‌کنیم
                new_row = {
                    "شماره ثبت": next_reg_no,
                    "نام مرکز درمانی": center_name,
                    "تاریخ دریافت": recv_date,
                    "تاریخ ارسال به ارزیاب": send_date,
                    "مهلت پرداخت (۲ ماهه)": "۲ ماه پس از دریافت",
                    "نام کاربر ثبت‌کنند": user_role,
                    "فایل تصویر": file_name
                }
                
                # اضافه کردن به دیتابیس
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                
                st.success(f"✅ سند با موفقیت ثبت شد! شماره ثبت اختصاص یافته: **{next_reg_no}**")

with tab2:
    st.subheader("لیست کلیه اسناد و وضعیت پیگیری")
    
    if len(df) > 0:
        # فیلتر و جستجو
        search_query = st.text_input("🔍 جستجو بر اساس شماره ثبت یا نام مرکز:")
        
        filtered_df = df.copy()
        if search_query:
            filtered_df = filtered_df[
                filtered_df["شماره ثبت"].astype(str).str.contains(search_query) |
                filtered_df["نام مرکز درمانی"].str.contains(search_query, na=False)
            ]
            
        st.dataframe(filtered_df, use_container_width=True)
        
        # نمایش تصویر مدارک در صورت درخواست
        st.markdown("---")
        st.subheader("مشاهده تصویر مدرک")
        selected_reg = st.selectbox("انتخاب شماره ثبت برای مشاهده فاکتور:", options=df["شماره ثبت"].tolist())
        
        if selected_reg:
            row_data = df[df["شماره ثبت"] == selected_reg].iloc[0]
            img_filename = row_data["فایل تصویر"]
            st.write(f"مرکز: **{row_data['نام مرکز درمانی']}** | تاریخ دریافت: **{row_data['تاریخ دریافت']}**")
            
            if pd.notna(img_filename) and img_filename != "":
                img_path = os.path.join(UPLOAD_DIR, str(img_filename))
                if os.path.exists(img_path):
                    if img_filename.endswith(('.png', '.jpg', '.jpeg')):
                        st.image(img_path, caption=f"فاکتور شماره ثبت {selected_reg}", width=500)
                    else:
                        st.write("فایل آپلود شده سند غیرعکسی است.")
                else:
                    st.info("تصویری برای این رکورد یافت نشد یا فایل حذف شده است.")
            else:
                st.info("هیچ فایلی برای این رکورد ضمیمه نشده است.")
    else:
        st.info("هنوز هیچ سندی ثبت نشده است.")
