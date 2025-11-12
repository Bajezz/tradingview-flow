import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# ==============================
# 📊 TradingView Flow — วิเคราะห์โดยใช้สีเป็นตัวตัดสิน (b=ชนะ, r=แพ้)
# ==============================

st.set_page_config(layout="wide")
st.title("📊 TradingView Flow — วิเคราะห์สัญญาณตามสี (Blue=Win / Red=Lose)")

# ==============================
# 🖼️ อัปโหลดภาพ (Optional)
# ==============================
st.sidebar.header("🖼️ อัปโหลดภาพ (ถ้ามี)")
uploaded_file = st.sidebar.file_uploader("วางหรืออัปโหลดภาพ:", type=["png", "jpg", "jpeg"])
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.sidebar.image(image, caption="ภาพที่อัปโหลด", use_column_width=True)
    st.sidebar.info("📌 โหลดภาพสำเร็จ (ยังไม่มี OCR อ่านอัตโนมัติ)")

# ==============================
# 📥 ป้อนข้อมูลเอง
# ==============================
st.subheader("🧮 ป้อนข้อมูลด้วยตนเอง")

values_input = st.text_area(
    "กรอกค่าตัวเลข (คั่นด้วยช่องว่าง):",
    "9 8 9 8 9 7 9 9 9 6 5 7 6 8 1 6 7 6 9 7 7 9 8 9"
)
colors_input = st.text_area(
    "กรอกสี (ใช้ b=blue / r=red / g=green):",
    "r r b r r r b b r b r b b b g b r r b b r r b r"
)

try:
    values = [float(x) for x in values_input.split() if x.strip()]
except ValueError:
    st.error("❌ กรุณากรอกตัวเลขให้ถูกต้อง")
    st.stop()

colors_raw = [c.lower() for c in colors_input.split() if c.strip()]
if len(colors_raw) < len(values):
    colors_raw += ["g"] * (len(values) - len(colors_raw))
elif len(colors_raw) > len(values):
    colors_raw = colors_raw[:len(values)]

color_map = {'b': 'royalblue', 'r': 'crimson', 'g': 'gray'}
colors = [color_map.get(c, 'gray') for c in colors_raw]

# ==============================
# 🔥 คำนวณผลและ streak
# ==============================
total_r = sum(1 for c in colors_raw if c == 'r')
total_b = sum(1 for c in colors_raw if c == 'b')
total_g = sum(1 for c in colors_raw if c == 'g')

# หา streak ของ "แพ้" (r)
streaks = []
cur = 0
start = None
for i, c in enumerate(colors_raw):
    if c == 'r':
        if cur == 0:
            start = i + 1
        cur += 1
    else:
        if cur > 0:
            streaks.append((start, i, cur))
        cur = 0
        start = None
if cur > 0:
    streaks.append((start, len(colors_raw), cur))

max_streak_len = max((slen for (_, _, slen) in streaks), default=0)

# ==============================
# 📈 วาดกราฟแท่งสี
# ==============================
bar_width = 0.8
scale = 0.5
tops, bottoms = [], []
for i, v in enumerate(values):
    height = v * scale
    if i == 0:
        bottom, top = 0.0, height
    else:
        prev_top, prev_bottom = tops[-1], bottoms[-1]
        bottom, top = prev_bottom, prev_bottom + height
    tops.append(top)
    bottoms.append(bottom)

fig, ax = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor('#0e1117')
ax.set_facecolor('#0e1117')

for i, (top, bottom, c) in enumerate(zip(tops, bottoms, colors)):
    ax.add_patch(plt.Rectangle(
        (i - bar_width / 2, bottom),
        bar_width, top - bottom,
        color=c, ec='white', lw=0.5, alpha=0.95
    ))

ax.set_xlim(-0.5, len(values) + 0.5)
ax.set_xticks(range(len(values)))
ax.set_xticklabels([str(i + 1) for i in range(len(values))], color='white')
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_edgecolor('#2a2f36')

ax.set_title("Flow Graph (b=ชนะ, r=แพ้, g=เสมอ)", color='white', fontsize=14)
plt.tight_layout()
st.pyplot(fig)

# ==============================
# 🧾 สรุปผล
# ==============================
st.markdown("### 🧾 สรุปผลรวม")
st.write(f"- ✅ ชนะ (น้ำเงิน): **{total_b}** ครั้ง")
st.write(f"- ❌ แพ้ (แดง): **{total_r}** ครั้ง")
st.write(f"- ⚪ เสมอ/กลาง (เทา): **{total_g}** ครั้ง")
st.write(f"- 🔺 แพ้ติดต่อกันยาวสุด: **{max_streak_len}** ไม้")
st.write(f"- 📍 ตำแหน่งแดงทั้งหมด: {[i+1 for i,c in enumerate(colors_raw) if c=='r']}")
