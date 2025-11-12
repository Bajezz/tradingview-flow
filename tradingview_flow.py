import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

st.set_page_config(layout="wide")
st.title("📊 TradingView Flow — วิเคราะห์สัญญาณจากสีแท่งถัดไป (รองรับ g = เสมอ)")

# ==============================
# 📥 ป้อนข้อมูล
# ==============================
st.subheader("🧮 ป้อนข้อมูล")

values_input = st.text_area(
    "กรอกค่าตัวเลข (คั่นด้วยช่องว่าง):",
    "9 8 9 8 9 7 9 9 9 6 5 7 6 8 1 6 7 6 9 7 7 9 8 9"
)
colors_input = st.text_area(
    "กรอกสี (b=น้ำเงิน, r=แดง, g=เขียว=เสมอ):",
    "r r b r r r b b r b r b b b g b r r b b r r b r"
)

# ==============================
# แปลงข้อมูล
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

color_map = {'b': 'royalblue', 'r': 'crimson', 'g': 'limegreen'}
colors = [color_map.get(c, 'gray') for c in colors_raw]

# ==============================
# หา local min / max
# ==============================
signals = []
for i in range(1, len(values) - 1):
    if values[i - 1] > values[i] < values[i + 1]:
        signals.append({"index": i, "type": "up"})
    elif values[i - 1] < values[i] > values[i + 1]:
        signals.append({"index": i, "type": "down"})

# ==============================
# ประเมินผลตามสีแท่งถัดไป
# ==============================
for s in signals:
    i = s["index"]
    if i + 1 >= len(colors_raw):
        s["result"] = "neutral"
        continue
    nxt = colors_raw[i + 1]
    if s["type"] == "up":
        if nxt == "b":
            s["result"] = "win"
        elif nxt == "r":
            s["result"] = "lose"
        else:
            s["result"] = "neutral"
    elif s["type"] == "down":
        if nxt == "r":
            s["result"] = "win"
        elif nxt == "b":
            s["result"] = "lose"
        else:
            s["result"] = "neutral"

# ==============================
# คำนวณสถิติ
# ==============================
wins = sum(1 for s in signals if s["result"] == "win")
losses = sum(1 for s in signals if s["result"] == "lose")
draws = sum(1 for s in signals if s["result"] == "neutral")

# หา streak ของแพ้
lose_streaks = []
streak = 0
for s in signals:
    if s["result"] == "lose":
        streak += 1
    else:
        if streak > 0:
            lose_streaks.append(streak)
        streak = 0
if streak > 0:
    lose_streaks.append(streak)
max_lose_streak = max(lose_streaks) if lose_streaks else 0

accuracy = (wins / (wins + losses) * 100) if (wins + losses) else 0

# ==============================
# วาดกราฟ
# ==============================
fig, ax = plt.subplots(figsize=(14, 6))
ax.set_facecolor('#0e1117')
fig.patch.set_facecolor('#0e1117')

bar_width = 0.8
scale = 0.5
tops, bottoms = [], []

for i, v in enumerate(values):
    height = v * scale
    bottom = 0
    top = height
    tops.append(top)
    bottoms.append(bottom)
    ax.add_patch(plt.Rectangle((i - bar_width/2, bottom), bar_width, top - bottom, color=colors[i], ec='white', lw=0.4))

# วาดลูกศร signal
for s in signals:
    i = s["index"]
    mid_y = (tops[i] + bottoms[i]) / 2
    if s["type"] == "up":
        ax.annotate('↑', (i, mid_y), color='cyan', ha='center', fontsize=14, fontweight='bold')
    else:
        ax.annotate('↓', (i, mid_y), color='orange', ha='center', fontsize=14, fontweight='bold')

    if s["result"] == "win":
        ax.add_patch(plt.Rectangle((i - bar_width/2, bottoms[i]), bar_width, tops[i]-bottoms[i], fill=False, ec='lime', lw=2))
    elif s["result"] == "lose":
        ax.add_patch(plt.Rectangle((i - bar_width/2, bottoms[i]), bar_width, tops[i]-bottoms[i], fill=False, ec='red', lw=2))
    elif s["result"] == "neutral":
        ax.add_patch(plt.Rectangle((i - bar_width/2, bottoms[i]), bar_width, tops[i]-bottoms[i], fill=False, ec='yellow', lw=2))

ax.set_xlim(-0.5, len(values) + 0.5)
ax.set_xticks(range(len(values)))
ax.set_xticklabels([str(i + 1) for i in range(len(values))], color='white')
ax.set_yticks([])
for s in ax.spines.values():
    s.set_color('#333')

plt.tight_layout()
st.pyplot(fig)

# ==============================
# สรุปผล
# ==============================
st.markdown("---")
st.markdown("### 📈 ผลการวิเคราะห์")
st.write(f"✅ ชนะทั้งหมด: **{wins}**")
st.write(f"❌ แพ้ทั้งหมด: **{losses}**")
st.write(f"⚪ เสมอทั้งหมด: **{draws}**")
st.write(f"🎯 ความแม่นยำ (ไม่รวมเสมอ): **{accuracy:.1f}%**")
st.write(f"🔥 แพ้ติดต่อกันยาวสุด: **{max_lose_streak} ไม้**")
