import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(layout="wide")
st.title("📊 Flow Statistic Analyzer — วิเคราะห์รูปแบบและสถิติความแม่น")

# --- Input ---
values_input = st.text_area("กรอกค่าตัวเลข (เช่น 9 9 6 8 8 8 8 8 8 7 6 9 6 8 9 4 6 5 8 9 2 9 6 1 5):",
                            "9 9 6 8 8 8 8 8 8 7 6 9 6 8 9 4 6 5 8 9 2 9 6 1 5")
colors_input = st.text_area("กรอกสี (b=blue, r=red, g=green):",
                            "b r b r b b b b r b r r b r r r b b b r r r b g b")

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
    st.warning("ต้องมีข้อมูลอย่างน้อย 3 ค่าเพื่อวิเคราะห์รูปแบบ")
    st.stop()

# --- Session เก็บสถิติ ---
if "signals" not in st.session_state:
    st.session_state.signals = []

# --- วิเคราะห์จุดกลับตัว ---
signals = []
for i in range(1, len(values) - 1):
    if values[i - 1] > values[i] < values[i + 1]:
        signals.append({"index": i, "type": "up"})
    elif values[i - 1] < values[i] > values[i + 1]:
        signals.append({"index": i, "type": "down"})

# --- ตรวจสอบความแม่นย้อนหลัง ---
for s in signals:
    i = s["index"]
    if i < len(values) - 1:
        future_move = values[i + 1] - values[i]
        s["correct"] = (s["type"] == "up" and future_move > 0) or \
                       (s["type"] == "down" and future_move < 0)
    else:
        s["correct"] = None

# --- บันทึกสถิติใน session ---
st.session_state.signals = signals

# --- คำนวณความแม่น ---
up_signals = [s for s in signals if s["type"] == "up" and s["correct"] is not None]
down_signals = [s for s in signals if s["type"] == "down" and s["correct"] is not None]

up_acc = (sum(s["correct"] for s in up_signals) / len(up_signals) * 100) if up_signals else 0
down_acc = (sum(s["correct"] for s in down_signals) / len(down_signals) * 100) if down_signals else 0

# --- วาดกราฟ ---
fig, ax = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor('#0e1117')
ax.set_facecolor('#0e1117')

x = np.arange(len(values))
ax.plot(x, values, color='white', linewidth=1.2, alpha=0.8, marker='o', markersize=4)

# --- วาดจุดสัญญาณ ---
for s in signals:
    i = s["index"]
    y = values[i]
    if s["type"] == "up":
        ax.scatter(i, y, color='lime', s=80, marker='^', edgecolor='white', linewidth=0.5)
    else:
        ax.scatter(i, y, color='red', s=80, marker='v', edgecolor='white', linewidth=0.5)

# --- แสดงสถิติความแม่น ---
ax.text(0.02, 0.95,
        f"🔺 Up Accuracy: {up_acc:.1f}%   🔻 Down Accuracy: {down_acc:.1f}%",
        transform=ax.transAxes,
        color='white', fontsize=12, fontweight='bold', ha='left', va='top')

# --- ตกแต่งกราฟ ---
ax.set_xlim(-0.5, len(values) - 0.5)
ax.set_xticks(range(0, len(values), max(1, len(values)//20)))
ax.set_xticklabels([str(i+1) for i in range(0, len(values), max(1, len(values)//20))], color='white')
ax.tick_params(axis='y', colors='white')
for spine in ax.spines.values():
    spine.set_edgecolor('#2a2f36')

ax.set_title("📈 Flow Pattern & Turning Point Statistic", color='white', fontsize=14)
plt.tight_layout()
st.pyplot(fig)
