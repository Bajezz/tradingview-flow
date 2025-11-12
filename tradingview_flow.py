# ==============================================================
# 📦 IMPORT ที่จำเป็น
# ==============================================================
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import gspread
import traceback
from google.oauth2.service_account import Credentials
from datetime import datetime

# ✅ สำหรับโมเดลพยากรณ์
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

    sheets = client.openall()
    st.write([s.title for s in sheets])

    sheet = client.open("TradingView_Signals").sheet1
    sheet.append_row(["✅ Streamlit Connected", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    st.success("✅ เชื่อม Google Sheets สำเร็จ!")
    st.session_state["gsheet_connected"] = True

except Exception as e:
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

values_input = st.text_area("กรอกค่าตัวเลข:", "9 9 6 8 8 8 8 8 8 7 6 9 6 8 9 4 6 5 8 9 2 9 6 1 5")
colors_input = st.text_area("กรอกสี (b=blue, r=red, g=green):", "b r b r b b b b r b r r b r r r b b b r r r b g b")

try:
    values = [float(x) for x in values_input.split() if x.strip()]
except ValueError:
    st.error("❌ กรุณากรอกค่าตัวเลขให้ถูกต้อง")
    st.stop()

colors_raw = [c for c in colors_input.split() if c.strip()]
if len(colors_raw) < len(values):
    colors_raw += ["gray"] * (len(values) - len(colors_raw))
elif len(colors_raw) > len(values):
    colors_raw = colors_raw[:len(values)]

color_map = {'b': 'royalblue', 'r': 'crimson', 'g': 'limegreen'}
colors = [color_map.get(c.lower(), 'gray') for c in colors_raw]

if len(values) < 3:
    st.warning("ต้องมีข้อมูลอย่างน้อย 3 ค่าเพื่อวิเคราะห์")
    st.stop()

# ==============================================================
# 📈 คำนวณกราฟและสัญญาณ
# ==============================================================

if "signals" not in st.session_state:
    st.session_state.signals = []

bar_width = 0.8
scale = 0.5
tops, bottoms = [], []

for i, (v, c) in enumerate(zip(values, colors)):
    height = v * scale
    if i == 0:
        bottom, top = 0.0, height
    else:
        prev_color = colors[i - 1]
        prev_top, prev_bottom = tops[-1], bottoms[-1]
        if c == 'royalblue':
            bottom = prev_top if prev_color == 'royalblue' else prev_bottom
            top = bottom + height
        elif c == 'crimson':
            top = prev_top if prev_color == 'royalblue' else prev_bottom
            bottom = top - height
        elif c == 'limegreen':
            bottom = prev_top if prev_color in ['royalblue', 'limegreen'] else prev_bottom
            top = bottom + height * 1.2
        else:
            bottom, top = prev_bottom, prev_top
    tops.append(top)
    bottoms.append(bottom)

midpoints = [(t + b) / 2.0 for t, b in zip(tops, bottoms)]

# --- สร้างสัญญาณย้อนหลัง ---
for i in range(1, len(values) - 1):
    if values[i - 1] > values[i] < values[i + 1]:
        if not any(s["index"] == i for s in st.session_state.signals):
            st.session_state.signals.append({"index": i, "type": "up", "correct": None})
    elif values[i - 1] < values[i] > values[i + 1]:
        if not any(s["index"] == i for s in st.session_state.signals):
            st.session_state.signals.append({"index": i, "type": "down", "correct": None})

# --- ตรวจสอบความแม่นย้อนหลัง ---
for s in st.session_state.signals:
    i = s["index"]
    if i < len(values) - 1:
        future_move = values[i + 1] - values[i]
        if s["type"] == "up":
            s["correct"] = future_move > 0
        elif s["type"] == "down":
            s["correct"] = future_move < 0

# --- คำนวณเปอร์เซ็นต์ความแม่น ---
up_acc_list = [s["correct"] for s in st.session_state.signals if s["type"] == "up" and s["correct"] is not None]
down_acc_list = [s["correct"] for s in st.session_state.signals if s["type"] == "down" and s["correct"] is not None]
up_acc = (sum(up_acc_list) / len(up_acc_list) * 100) if up_acc_list else 0
down_acc = (sum(down_acc_list) / len(down_acc_list) * 100) if down_acc_list else 0

# ==============================================================
# 🔮 วิเคราะห์ข้อมูลเชิงพยากรณ์ — เลือกโมเดลทำนายอนาคต
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
        degree = st.slider("เลือกองศาโค้ง Polynomial:", 1, 5, 3)
        coeffs = np.polyfit(x, y, degree)
        poly = np.poly1d(coeffs)
        next_value = poly(lookback)
        predicted_dir = "up" if next_value > y[-1] else "down"

    elif model_option.startswith("Exponential"):
        model = ExponentialSmoothing(y, trend="add", seasonal=None)
        fit = model.fit()
        next_value = fit.forecast(1)[0]
        predicted_dir = "up" if next_value > y[-1] else "down"

    elif model_option.startswith("ML"):
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

            values_all = np.array([v for sub in data for v in sub if isinstance(v, (int, float, float))])
            if len(values_all) > 10:
                X, y_ml = [], []
                for i in range(len(values_all) - 5):
                    X.append(values_all[i:i+5])
                    y_ml.append(values_all[i+5])
                model = LinearRegression().fit(X, y_ml)
                next_value = model.predict([values[-5:]])[0]
                predicted_dir = "up" if next_value > values[-1] else "down"
            else:
                st.warning("⚠️ ยังไม่มีข้อมูลในชีตมากพอสำหรับ ML (ต้องมากกว่า 10 ค่า)")
        else:
            st.warning("⚠️ ยังไม่เชื่อมต่อ Google Sheets")

except Exception as e:
    st.error("⚠️ เกิดข้อผิดพลาดในการพยากรณ์:")
    st.code(traceback.format_exc())

# ==============================================================
# 💾 บันทึกลง Google Sheets
# ==============================================================

if st.session_state.get("gsheet_connected"):
    try:
        sheet.append_row([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            str(values[-5:]),
            predicted_dir,
            "-",
            f"{up_acc:.1f}%",
            f"{down_acc:.1f}%"
        ])
        st.success("✅ บันทึกข้อมูลลง Google Sheets สำเร็จ!")
    except Exception as e:
        st.error("⚠️ บันทึกข้อมูลไม่สำเร็จ:")
        st.code(traceback.format_exc())

# ==============================================================
# 🎨 วาดกราฟ
# ==============================================================

fig, ax = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor('#0e1117')
ax.set_facecolor('#0e1117')

for i, (top, bottom, c) in enumerate(zip(tops, bottoms, colors)):
    ax.add_patch(plt.Rectangle((i - bar_width / 2, bottom),
                               bar_width, top - bottom,
                               color=c, ec='white', lw=0.5, alpha=0.9))

ax.plot(range(len(midpoints)), midpoints, color='white', linewidth=0.8, alpha=0.4)

# --- แสดงสัญญาณย้อนหลัง ---
for s in st.session_state.signals:
    i = s["index"]
    if i < len(midpoints):
        if s["type"] == "up":
            ax.annotate('↑', xy=(i, midpoints[i]), xytext=(i, midpoints[i] - 0.35),
                        color='lime', ha='center', fontsize=16, fontweight='bold')
        elif s["type"] == "down":
            ax.annotate('↓', xy=(i, midpoints[i]), xytext=(i, midpoints[i] + 0.35),
                        color='red', ha='center', fontsize=16, fontweight='bold')

# --- พยากรณ์แท่งถัดไป ---
ax.annotate('↑' if predicted_dir == "up" else '↓',
            xy=(len(values), midpoints[-1]),
            xytext=(len(values), midpoints[-1] + (0.5 if predicted_dir == "up" else -0.5)),
            color='lime' if predicted_dir == "up" else 'red',
            ha='center', fontsize=22, fontweight='bold', alpha=0.7)

ax.set_xlim(-0.5, len(values) + 0.5)
ax.set_xticks(range(len(values)))
ax.set_xticklabels([str(i + 1) for i in range(len(values))], color='white', fontsize=9)
ax.tick_params(axis='x', colors='white')
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_edgecolor('#2a2f36')

ax.text(len(values) - 1, max(tops) * 1.05,
        f"📈 Up: {up_acc:.1f}%   📉 Down: {down_acc:.1f}%",
        color='white', ha='right', va='top', fontsize=12)

ax.set_title("TradingView Flow — สัญญาณล่วงหน้าและสถิติจริง", color='white', fontsize=14)
plt.tight_layout()
st.pyplot(fig)
