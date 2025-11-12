import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# ==============================
# 📊 TradingView Flow (เวอร์ชันใหม่สุด)
# ==============================

st.set_page_config(layout="wide")
st.title("📊 TradingView Flow — วิเคราะห์สัญญาณ + สีตัดสิน (เวอร์ชันเรียงถูก)")

# 🖼️ Upload ภาพ (สำรอง)
st.sidebar.header("🖼️ อัปโหลดภาพ (ไม่จำเป็น)")
uploaded_file = st.sidebar.file_uploader("วางหรืออัปโหลดภาพ:", type=["png", "jpg", "jpeg"])
if uploaded_file is not None:
    img = Image.open(uploaded_file)
    st.sidebar.image(img, caption="ภาพที่อัปโหลด", use_column_width=True)

# ==============================
# 📥 Input
# ==============================
st.subheader("🧮 ป้อนข้อมูล")

values_input = st.text_area(
    "ค่าตัวเลข (คั่นด้วยช่องว่าง):",
    "9 8 9 8 9 7 9 9 9 6 5 7 6 8 1 6 7 6 9 7 7 9 8 9"
)
colors_input = st.text_area(
    "สี (b=ชนะ, r=แพ้, g=เสมอ):",
    "r r b r r r b b r b r b b b g b r r b b r r b r"
)

# ==============================
# 🧩 แปลงข้อมูล
# ==============================
try:
    values = [float(v) for v in values_input.split()]
except ValueError:
    st.error("❌ กรุณากรอกค่าตัวเลขให้ถูกต้อง")
    st.stop()

colors_raw = [c.lower() for c in colors_input.split()]
if len(colors_raw) < len(values):
    colors_raw += ["g"] * (len(values) - len(colors_raw))
elif len(colors_raw) > len(values):
    colors_raw = colors_raw[:len(values)]

color_map = {'b': 'royalblue', 'r': 'crimson', 'g': 'gray'}
colors = [color_map.get(c, 'gray') for c in colors_raw]

if len(values) < 3:
    st.warning("ต้องมีอย่างน้อย 3 ค่า")
    st.stop()

# ==============================
# 📈 สร้างกราฟต่อเนื่อง (ไม่มั่ว)
# ==============================
bar_width = 0.8
scale = 0.5
tops, bottoms = [], []

for i, v in enumerate(values):
    height = abs(v) * scale
    if i == 0:
        bottom, top = 0, height
    else:
        prev_top = tops[-1]
        prev_bottom = bottoms[-1]
        if values[i] > values[i - 1]:
            bottom = prev_top
            top = bottom + height
        elif values[i] < values[i - 1]:
            top = prev_bottom
            bottom = top - height
        else:
            bottom, top = prev_bottom, prev_top
    bottoms.append(bottom)
    tops.append(top)

midpoints = [(t + b) / 2 for t, b in zip(tops, bottoms)]

# ==============================
# 🔺 ตรวจหาสัญญาณย้อนหลัง
# ==============================
signals = []
for i in range(1, len(values) - 1):
    if values[i - 1] > values[i] < values[i + 1]:
        signals.append({"index": i, "type": "up"})
    elif values[i - 1] < values[i] > values[i + 1]:
        signals.append({"index": i, "type": "down"})

# ==============================
# 🎯 ตรวจผลจากสีของแท่ง “ถัดไป”
# ==============================
for s in signals:
    i = s["index"]
    if i + 1 < len(colors_raw):
        next_color = colors_raw[i + 1]
        if next_color == 'g':
            s["result"] = "draw"
        elif s["type"] == "up":
            s["result"] = "win" if next_color == 'b' else "lose"
        elif s["type"] == "down":
            s["result"] = "win" if next_color == 'r' else "lose"
    else:
        s["result"] = "unknown"

# ==============================
# 📊 สถิติ
# ==============================
win = sum(1 for s in signals if s["result"] == "win")
lose = sum(1 for s in signals if s["result"] == "lose")
draw = sum(1 for s in signals if s["result"] == "draw")

st.markdown(f"""
### 📋 สรุปผล
- ชนะ: ✅ {win}
- แพ้: ❌ {lose}
- เสมอ: ⚪ {draw}
- รวมทั้งหมด: {len(signals)}
""")

# 🔥 หาชุดแพ้ต่อเนื่อง (สีแดง r)
r_positions = [i + 1 for i, c in enumerate(colors_raw) if c == 'r']
streaks = []
cur, start = 0, None
for i, c in enumerate(colors_raw):
    if c == 'r':
        if cur == 0:
            start = i + 1
        cur += 1
    else:
        if cur > 0:
            streaks.append((start, i, cur))
        cur = 0
if cur > 0:
    streaks.append((start, len(colors_raw), cur))

max_streak = max((s[2] for s in streaks), default=0)
st.markdown(f"**📉 แพ้ติดต่อกันยาวสุด:** {max_streak} ไม้")

# ==============================
# 🔮 พยากรณ์แท่งอนาคต
# ==============================
if len(values) >= 3:
    if values[-3] > values[-2] < values[-1]:
        next_signal = "up"
    elif values[-3] < values[-2] > values[-1]:
        next_signal = "down"
    else:
        next_signal = None
else:
    next_signal = None

# ==============================
# 🎨 วาดกราฟ
# ==============================
fig, ax = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor('#0e1117')
ax.set_facecolor('#0e1117')

for i, (top, bottom, c) in enumerate(zip(tops, bottoms, colors)):
    ax.add_patch(plt.Rectangle(
        (i - bar_width / 2, bottom),
        bar_width, top - bottom,
        color=c, ec='white', lw=0.6, alpha=0.9
    ))

# เส้นกลาง
ax.plot(range(len(midpoints)), midpoints, color='white', linewidth=0.7, alpha=0.5)

# สัญญาณย้อนหลัง
for s in signals:
    i = s["index"]
    if s["type"] == "up":
        symbol, yoffset = '↑', -0.4
    else:
        symbol, yoffset = '↓', +0.4
    color = {'win': 'lime', 'lose': 'red', 'draw': 'gray', 'unknown': 'yellow'}[s["result"]]
    ax.annotate(symbol, xy=(i, midpoints[i]), xytext=(i, midpoints[i] + yoffset),
                color=color, ha='center', fontsize=16, fontweight='bold')

# สัญญาณอนาคต
if next_signal:
    i = len(values)
    if next_signal == "up":
        ax.annotate('↑', xy=(i, midpoints[-1]), xytext=(i, midpoints[-1] - 0.6),
                    color='cyan', ha='center', fontsize=22, fontweight='bold', alpha=0.8)
    elif next_signal == "down":
        ax.annotate('↓', xy=(i, midpoints[-1]), xytext=(i, midpoints[-1] + 0.6),
                    color='orange', ha='center', fontsize=22, fontweight='bold', alpha=0.8)

ax.set_xlim(-0.5, len(values) + 0.5)
ax.set_xticks(range(len(values)))
ax.set_xticklabels([str(i + 1) for i in range(len(values))], color='white')
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_edgecolor('#2a2f36')

ax.set_title("TradingView Flow — กราฟต่อเนื่อง + สัญญาณจริง", color='white')
plt.tight_layout()
st.pyplot(fig)
