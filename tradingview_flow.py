import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(layout="wide")
st.title("📊 TradingView Flow — ระบบสัญญาณและสถิติจริง")

# --- Input ---
values_input = st.text_area("กรอกค่าตัวเลข:", "9 9 6 8 8 8 8 8 8 7 6 9 6 8 9 4 6 5 8 9 2 9 6 1 5")
colors_input = st.text_area("กรอกสี (b=blue, r=red, g=green):", "b r b r b b b b r b r r b r r r b b b r r r b g b")

# --- Parse input ---
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

# --- เก็บข้อมูล session ---
if "signals" not in st.session_state:
    st.session_state.signals = []

# --- คำนวณกราฟ Flow (ตามโค้ดต้นฉบับของคุณ) ---
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

# --- สร้างสัญญาณย้อนหลังจริง ---
for i in range(1, len(values) - 1):
    if values[i - 1] > values[i] < values[i + 1]:
        if not any(s["index"] == i for s in st.session_state.signals):
            st.session_state.signals.append({"index": i, "type": "up", "correct": None})
    elif values[i - 1] < values[i] > values[i + 1]:
        if not any(s["index"] == i for s in st.session_state.signals):
            st.session_state.signals.append({"index": i, "type": "down", "correct": None})

# --- ตรวจสอบความแม่น ---
for s in st.session_state.signals:
    i = s["index"]
    if i < len(values) - 1:
        future_move = values[i + 1] - values[i]
        if s["type"] == "up":
            s["correct"] = future_move > 0
        elif s["type"] == "down":
            s["correct"] = future_move < 0

# --- สถิติความแม่น ---
up_acc_list = [s["correct"] for s in st.session_state.signals if s["type"] == "up" and s["correct"] is not None]
down_acc_list = [s["correct"] for s in st.session_state.signals if s["type"] == "down" and s["correct"] is not None]
up_acc = (sum(up_acc_list) / len(up_acc_list) * 100) if up_acc_list else 0
down_acc = (sum(down_acc_list) / len(down_acc_list) * 100) if down_acc_list else 0

# --- พยากรณ์แท่งถัดไป (จากแนวโน้มทั้งหมด) ---
lookback = min(len(values), 10)
x = np.arange(lookback)
y = np.array(values[-lookback:])
a, b = np.polyfit(x, y, 1)
next_value = a * lookback + b
predicted_dir = "ขึ้น" if next_value > y[-1] else "ลง"
arrow_color = 'lime' if predicted_dir == "ขึ้น" else 'red'

# --- วาดกราฟ Flow + สัญญาณ ---
fig, ax = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor('#0e1117')
ax.set_facecolor('#0e1117')

for i, (top, bottom, c) in enumerate(zip(tops, bottoms, colors)):
    ax.add_patch(plt.Rectangle((i - bar_width / 2, bottom), bar_width, top - bottom,
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

# --- แสดงสัญญาณพยากรณ์ล่วงหน้า ---
ax.annotate('↑' if predicted_dir == "ขึ้น" else '↓',
            xy=(len(values), midpoints[-1]),
            xytext=(len(values), midpoints[-1] + (0.5 if predicted_dir == "ขึ้น" else -0.5)),
            color=arrow_color, ha='center', fontsize=20, fontweight='bold', alpha=0.7)

# --- ตกแต่ง ---
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

ax.set_title("TradingView Flow — สัญญาณจริงและความแม่น", color='white', fontsize=14)
plt.tight_layout()
st.pyplot(fig)
