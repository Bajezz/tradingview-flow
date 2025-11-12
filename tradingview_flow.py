import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# ==============================
# 📊 TradingView Flow — วิเคราะห์ตามสัญญาณ + สีแท่งถัดไป
# ==============================

st.set_page_config(layout="wide")
st.title("📊 TradingView Flow — วิเคราะห์สัญญาณจากสีแท่งถัดไป")

# ==============================
# 🖼️ อัปโหลดภาพ (ไม่จำเป็น)
# ==============================
st.sidebar.header("🖼️ อัปโหลดภาพ (ไม่จำเป็น)")
uploaded_file = st.sidebar.file_uploader("วางหรืออัปโหลดภาพ:", type=["png", "jpg", "jpeg"])
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.sidebar.image(image, caption="ภาพที่อัปโหลด", use_column_width=True)
    st.sidebar.info("📌 ยังไม่มี OCR — ระบบพร้อมสำหรับอ่านค่าจากภาพในอนาคต")

# ==============================
# 📥 ป้อนข้อมูลด้วยตนเอง
# ==============================
st.subheader("🧮 ป้อนข้อมูลเอง")

values_input = st.text_area(
    "กรอกค่าตัวเลข (คั่นด้วยช่องว่าง):",
    "9 8 9 8 9 7 9 9 9 6 5 7 6 8 1 6 7 6 9 7 7 9 8 9"
)
colors_input = st.text_area(
    "กรอกสี (b=น้ำเงิน, r=แดง, g=กลาง):",
    "r r b r r r b b r b r b b b g b r r b b r r b r"
)

# ==============================
# แปลงค่าและตรวจสอบ
# ==============================
try:
    values = [float(x) for x in values_input.split() if x.strip()]
except ValueError:
    st.error("❌ กรุณากรอกตัวเลขให้ถูกต้อง (คั่นด้วยช่องว่าง)")
    st.stop()

colors_raw = [c.lower() for c in colors_input.split() if c.strip()]
if len(colors_raw) < len(values):
    colors_raw += ["g"] * (len(values) - len(colors_raw))
elif len(colors_raw) > len(values):
    colors_raw = colors_raw[:len(values)]

color_map = {'b': 'royalblue', 'r': 'crimson', 'g': 'gray'}
colors = [color_map.get(c, 'gray') for c in colors_raw]

if len(values) < 3:
    st.warning("ต้องมีข้อมูลอย่างน้อย 3 ค่าเพื่อวิเคราะห์")
    st.stop()

# ==============================
# คำนวณกราฟ flow
# ==============================
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
        else:
            bottom, top = prev_bottom, prev_top
    tops.append(top)
    bottoms.append(bottom)

midpoints = [(t + b) / 2.0 for t, b in zip(tops, bottoms)]

# ==============================
# 🔺 หาสัญญาณ (local min/max)
# ==============================
signals = []
for i in range(1, len(values) - 1):
    if values[i - 1] > values[i] < values[i + 1]:
        signals.append({"index": i, "type": "up", "correct": None})
    elif values[i - 1] < values[i] > values[i + 1]:
        signals.append({"index": i, "type": "down", "correct": None})

# ==============================
# ✅ ประเมินผลตาม "สีแท่งถัดไป"
# ==============================
for s in signals:
    i = s["index"]
    next_i = i + 1
    if next_i >= len(colors_raw):
        s["correct"] = None
        continue

    col_next = colors_raw[next_i]
    if s["type"] == "up":
        s["correct"] = (col_next == 'b')  # ต้องเป็นน้ำเงินถึงจะชนะ
    elif s["type"] == "down":
        s["correct"] = (col_next == 'r')  # ต้องเป็นแดงถึงจะชนะ

# ==============================
# 📊 คำนวณสถิติรวม
# ==============================
total_signals = len(signals)
correct_signals = [s for s in signals if s["correct"] is True]
wrong_signals = [s for s in signals if s["correct"] is False]
neutral_signals = [s for s in signals if s["correct"] is None]

accuracy = (len(correct_signals) / len(correct_signals + wrong_signals)
            * 100) if (correct_signals or wrong_signals) else 0

# ==============================
# 🔥 คำนวณ streak ของการ "แพ้" (wrong signals)
# ==============================
lose_streaks = []
cur_streak = 0
for s in signals:
    if s["correct"] is False:
        cur_streak += 1
    else:
        if cur_streak > 0:
            lose_streaks.append(cur_streak)
        cur_streak = 0
if cur_streak > 0:
    lose_streaks.append(cur_streak)

max_lose_streak = max(lose_streaks) if lose_streaks else 0

# ==============================
# 📈 วาดกราฟ
# ==============================
fig, ax = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor('#0e1117')
ax.set_facecolor('#0e1117')

for i, (top, bottom, c) in enumerate(zip(tops, bottoms, colors)):
    ax.add_patch(plt.Rectangle((i - bar_width / 2, bottom),
                               bar_width, top - bottom,
                               color=c, ec='white', lw=0.5, alpha=0.9))

ax.plot(range(len(midpoints)), midpoints, color='white', linewidth=0.8, alpha=0.4)

for s in signals:
    i = s["index"]
    if s["type"] == "up":
        ax.annotate('↑', xy=(i, midpoints[i]), xytext=(i, midpoints[i] - 0.35),
                    color='cyan', ha='center', fontsize=14, fontweight='bold')
    elif s["type"] == "down":
        ax.annotate('↓', xy=(i, midpoints[i]), xytext=(i, midpoints[i] + 0.35),
                    color='orange', ha='center', fontsize=14, fontweight='bold')

    # วาดกรอบตามผล
    if s["correct"] is True:
        ax.add_patch(plt.Rectangle((i - bar_width/2, bottoms[i]), bar_width, tops[i]-bottoms[i],
                                   fill=False, ec='lime', lw=2))
    elif s["correct"] is False:
        ax.add_patch(plt.Rectangle((i - bar_width/2, bottoms[i]), bar_width, tops[i]-bottoms[i],
                                   fill=False, ec='red', lw=2))

ax.set_xlim(-0.5, len(values) + 0.5)
ax.set_xticks(range(len(values)))
ax.set_xticklabels([str(i + 1) for i in range(len(values))], color='white')
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_edgecolor('#2a2f36')

ax.set_title("TradingView Flow — ประเมินจากสีแท่งถัดไป", color='white')
plt.tight_layout()
st.pyplot(fig)

# ==============================
# 🧾 สรุปผล
# ==============================
st.markdown("---")
st.markdown(f"### 📊 สรุปผลรวม")
st.write(f"- จำนวนสัญญาณทั้งหมด: **{total_signals}**")
st.write(f"- ✅ ชนะ: **{len(correct_signals)}**")
st.write(f"- ❌ แพ้: **{len(wrong_signals)}**")
st.write(f"- ⚪ ไม่ตัดสิน: **{len(neutral_signals)}**")
st.write(f"- 🎯 ความแม่นยำโดยรวม: **{accuracy:.1f}%**")
st.write(f"- 🔥 แพ้ติดต่อกันยาวสุด: **{max_lose_streak} ไม้**")
