# ==============================================================
# 🔧 IMPORT MODULES
# ==============================================================
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import gspread
import traceback
from google.oauth2.service_account import Credentials
from datetime import datetime
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.linear_model import LinearRegression

# ==============================================================
# 🔗 เชื่อมต่อ Google Sheets
# ==============================================================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

try:
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )
    client = gspread.authorize(creds)
    sheet = client.open("TradingView_Signals").sheet1
    st.success("✅ เชื่อม Google Sheets สำเร็จ!")
    st.session_state["gsheet_connected"] = True
except Exception:
    st.error("⚠️ ไม่สามารถเชื่อม Google Sheets ได้:")
    st.code(traceback.format_exc())
    sheet = None
    st.session_state["gsheet_connected"] = False

# ==============================================================
# ⚙️ ตั้งค่า Streamlit
# ==============================================================
st.set_page_config(layout="wide")
st.title("📊 TradingView Flow — ระบบสัญญาณและสถิติจริง (ล่วงหน้า)")

# ==============================================================
# 🧮 รับข้อมูลจากผู้ใช้
# ==============================================================
values_input = st.text_area("กรอกค่าตัวเลข:", "8 6 5 7 9 8 7 6 9 10 8 7 9")
colors_input = st.text_area("กรอกสี (b=blue, r=red, g=green):", "b r b r b b g r b r g b r")

try:
    values = [float(x) for x in values_input.split() if x.strip()]
except ValueError:
    st.error("❌ กรุณากรอกค่าตัวเลขให้ถูกต้อง")
    st.stop()

colors_raw = [c for c in colors_input.split() if c.strip()]
color_map = {'b': 'royalblue', 'r': 'crimson', 'g': 'limegreen'}
colors = [color_map.get(c.lower(), 'gray') for c in colors_raw]
if len(colors) < len(values):
    colors += ['gray'] * (len(values) - len(colors))

if len(values) < 3:
    st.warning("ต้องมีข้อมูลอย่างน้อย 3 ค่าเพื่อวิเคราะห์")
    st.stop()

# ==============================================================
# 🔮 วิเคราะห์ข้อมูลเชิงพยากรณ์ — เลือกโมเดล
# ==============================================================
st.subheader("🔮 วิเคราะห์ข้อมูลเชิงพยากรณ์ — เลือกโมเดลทำนายอนาคต")
model_option = st.selectbox(
    "เลือกโมเดลที่ใช้พยากรณ์:",
    [
        "Polynomial Regression (สมการโค้ง)",
        "Exponential Smoothing (แนวโน้มเวลา)",
        "ML จากข้อมูล Google Sheets (เรียนรู้ย้อนหลัง)"
    ]
)

next_value = None
predicted_dir = None

try:
    lookback = min(len(values), 8)
    x = np.arange(lookback)
    y = np.array(values[-lookback:])

    if model_option.startswith("Polynomial"):
        # 🧮 Polynomial Regression
        degree = st.slider("เลือกองศาโค้ง Polynomial:", 1, 5, 3)
        coeffs = np.polyfit(x, y, degree)
        poly = np.poly1d(coeffs)
        next_value = poly(lookback)
        predicted_dir = "up" if next_value > y[-1] else "down"

    elif model_option.startswith("Exponential"):
        # 📊 Exponential Smoothing
        model = ExponentialSmoothing(y, trend="add", seasonal=None)
        fit = model.fit()
        next_value = fit.forecast(1)[0]
        predicted_dir = "up" if next_value > y[-1] else "down"

    elif model_option.startswith("ML"):
        # 🧠 Machine Learning จากข้อมูลย้อนหลังใน Google Sheets
        if sheet is not None:
            records = sheet.get_all_values()
            data = []
            for row in records[1:]:
                try:
                    arr = eval(row[1])
                    if isinstance(arr, list):
                        data.append(arr)
                except:
                    pass

            values_all = np.array(
                [v for sub in data for v in sub if isinstance(v, (int, float, float))]
            )
            if len(values_all) > 10:
                X, y_ml = [], []
                for i in range(len(values_all) - 5):
                    X.append(values_all[i:i + 5])
                    y_ml.append(values_all[i + 5])
                model = LinearRegression().fit(X, y_ml)
                next_value = model.predict([values[-5:]])[0]
                predicted_dir = "up" if next_value > values[-1] else "down"
            else:
                st.warning("⚠️ ยังไม่มีข้อมูลในชีตมากพอสำหรับ ML (ต้องมากกว่า 10 ค่า)")
        else:
            st.warning("⚠️ ยังไม่เชื่อมต่อ Google Sheets")

except Exception:
    st.error("⚠️ เกิดข้อผิดพลาดในการพยากรณ์:")
    st.code(traceback.format_exc())

# ==============================================================
# แสดงผลลัพธ์การพยากรณ์
# ==============================================================
if next_value is not None:
    st.success(f"📈 ค่าที่คาดการณ์ถัดไป = **{next_value:.2f}** ({'📊 ขึ้น' if predicted_dir=='up' else '📉 ลง'})")

# ==============================================================
# 🔁 สัญญาณล่าสุด (anticipate)
# ==============================================================
anticipate_signal = None
if len(values) >= 3:
    last3 = values[-3:]
    if last3[0] > last3[1] < last3[2]:
        anticipate_signal = "up"
    elif last3[0] < last3[1] > last3[2]:
        anticipate_signal = "down"

# ==============================================================
# 🎨 วาดกราฟ
# ==============================================================
fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(values, color='white', marker='o', alpha=0.6)
ax.set_facecolor('#0e1117')

# แสดงสัญญาณจาก anticipate
if anticipate_signal == "up":
    ax.annotate('↑', xy=(len(values)-1, values[-1]),
                xytext=(len(values)-1, values[-1]-0.5),
                color='lime', fontsize=18, ha='center')
elif anticipate_signal == "down":
    ax.annotate('↓', xy=(len(values)-1, values[-1]),
                xytext=(len(values)-1, values[-1]+0.5),
                color='red', fontsize=18, ha='center')

# แสดงค่าพยากรณ์แท่งถัดไป
if next_value is not None:
    ax.scatter(len(values), next_value, color='cyan' if predicted_dir == "up" else 'orange', s=100)
    ax.text(len(values), next_value,
            f"{'▲' if predicted_dir == 'up' else '▼'} {next_value:.2f}",
            color='cyan' if predicted_dir == "up" else 'orange',
            fontsize=14, fontweight='bold', ha='center', va='bottom' if predicted_dir == 'up' else 'top')

st.pyplot(fig)
