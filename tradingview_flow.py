import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(layout="wide")
st.title("📊 TradingView Flow — สถิติความแม่นของสัญญาณจริง")

# --- Input ---
values_input = st.text_input("กรอกค่าตัวเลข (เช่น 8 6 5 7 9 8):", "8 6 5 7 9 8 10 9 11 10")
colors_input = st.text_input("กรอกสี (b=blue, r=red, g=green เช่น b r g b g):", "b r g b g r g g r")

# --- Parse input ---
try:
    values = [float(x) for x in values_input.split() if x.strip() != ""]
except ValueError:
    st.error("กรุณากรอกค่าตัวเลขให้ถูกต้อง (คั่นด้วยช่องว่าง)")
    st.stop()

colors_raw = [c for c in colors_input.split() if c.strip() != ""]
if len(colors_raw) < len(values):
    colors_raw += ["gray"] * (len(values) - len(colors_raw))
elif len(colors_raw) > len(values):
    colors_raw = colors_raw[:len(values)]

colors = []
for c in colors_raw:
    if c.lower() == 'b':
        colors.append('blue')
    elif c.lower() == 'r':
        colors.append('red')
    elif c.lower() == 'g':
        colors.append('green')
    else:
        colors.append('gray')

if len(values) < 3:
    st.warning("ต้องกรอกข้อมูลอย่างน้อย 3 ค่าเพื่อเริ่มเก็บสถิติ")
    st.stop()

# --- เก็บข้อมูลใน session ---
if "signals" not in st.session_state:
    st.session_state.signals = []
if "accuracy" not in st.session_state:
    st.session_state.accuracy = {"up": [], "down": []}

# --- คำนวณกราฟ ---
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

        if c == 'blue':
            bottom = prev_top if prev_color == 'blue' else prev_bottom
            top = bottom + height
        elif c == 'red':
            top = prev_top if prev_color == 'blue' else prev_bottom
            bottom = top - height
        elif c == 'green':
            bottom = prev_top if prev_color in ['blue', 'green'] else prev_bottom
            top = bottom + height * 1.2
        else:
            bottom, top = prev_bottom, prev_top

    tops.append(top)
    bottoms.append(bottom)

midpoints = [(t + b) / 2.0 for t, b in zip(tops, bottoms)]

# --- ตรวจหา “จุดสัญญาณย้อนหลังจริง” ---
for i in range(1, len(values) - 1):
    if values[i - 1] > values[i] < values[i + 1]:
        if not any(s["index"] == i for s in st.session_state.signals):
            st.session_state.signals.append({"index": i, "type": "up", "correct": None})
    elif values[i - 1] < values[i] > values[i + 1]:
        if not any(s["index"] == i for s in st.session_state.signals):
            st.session_state.signals.append({"index": i, "type": "down", "correct": None})

# --- ตรวจสอบความแม่นยำของสัญญาณ ---
for s in st.session_state.signals:
    i = s["index"]
    if i < len(values) - 1:
        future_move = values[i + 1] - values[i]
        if s["type"] == "up":
            s["correct"] = future_move > 0
        elif s["type"] == "down":
            s["correct"] = future_move < 0

# --- บันทึกสถิติความแม่น ---
up_acc_list = [s["correct"] for s in st.session_state.signals if s["type"] == "up" and s["correct"] is not None]
down_acc_list = [s["correct"] for s in st.session_state.signals if s["type"] == "down" and s["correct"] is not None]

up_acc = (sum(up_acc_list) / len(up_acc_list) * 100) if len(up_acc_list) else 0
down_acc = (sum(down_acc_list) / len(down_acc_list) * 100) if len(down_acc_list) else 0

# --- วาดกราฟ ---
fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor('#0e1117')
ax.set_facecolor('#0e1117')
color_map = {'blue': 'royalblue', 'red': 'crimson', 'green': 'limegreen'}

for i, (v, c, top, bottom) in enumerate(zip(values, colors, tops, bottoms)):
    color = color_map.get(c, 'gray')
    ax.add_patch(plt.Rectangle((i - bar_width / 2, bottom),
                               bar_width, top - bottom,
                               color=color, ec='white', lw=0.6, alpha=0.9))
    ax.text(i, (top + bottom) / 2, str(v),
            color='white', ha='center', va='center', fontsize=11, fontweight='bold')

ax.plot(range(len(midpoints)), midpoints, color='white', linewidth=0.8, alpha=0.5)

# --- แสดงสัญญาณย้อนหลัง ---
for s in st.session_state.signals:
    i = s["index"]
    if i < len(midpoints):  # ✅ ป้องกัน IndexError
        if s["type"] == "up":
            ax.annotate('↑', xy=(i, midpoints[i]), xytext=(i, midpoints[i] - 0.35),
                        color='lime', ha='center', fontsize=16, fontweight='bold')
        elif s["type"] == "down":
            ax.annotate('↓', xy=(i, midpoints[i]), xytext=(i, midpoints[i] + 0.35),
                        color='red', ha='center', fontsize=16, fontweight='bold')

# --- พยากรณ์แท่งถัดไป ---
lookback = min(len(values), 10)  # ใช้ข้อมูลทั้งหมดล่าสุด (ไม่ใช่แค่ 5)
x = np.arange(lookback)
y = np.array(values[-lookback:])
a, b = np.polyfit(x, y, 1)
next_value = a * lookback + b
predicted_dir = "ขึ้น" if next_value > y[-1] else "ลง"
arrow_color = 'lime' if predicted_dir == "ขึ้น" else 'red'

ax.annotate('↑' if predicted_dir == "ขึ้น" else '↓',
            xy=(len(values), midpoints[-1]),
            xytext=(len(values), midpoints[-1] + (0.5 if predicted_dir == "ขึ้น" else -0.5)),
            color=arrow_color, ha='center', fontsize=20, fontweight='bold', alpha=0.7)

# --- ตกแต่ง ---
ax.set_xlim(-0.5, len(values) + 0.5)
ax.set_xticks(range(len(values)))
ax.set_xticklabels([str(i + 1) for i in range(len(values))], color='white')
ax.set_yticks([])
ax.tick_params(axis='x', colors='white')
for spine in ax.spines.values():
    spine.set_edgecolor('#2a2f36')
ax.set_title("TradingView Flow — สถิติความแม่นของสัญญาณ", color='white', fontsize=14)

# --- แสดงสถิติ ---
ax.text(len(values) - 1, max(tops) * 1.05,
        f"📈 Up Accuracy: {up_acc:.1f}%\n📉 Down Accuracy: {down_acc:.1f}%",
        color='white', ha='right', va='top', fontsize=11)

plt.tight_layout()
st.pyplot(fig)
