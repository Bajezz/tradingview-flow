import streamlit as st
import matplotlib.pyplot as plt
from PIL import Image

st.set_page_config(layout="wide")
st.title("📊 TradingView Flow — วิเคราะห์สัญญาณจากแท่งถัดไป (อัปเดตเรียลไทม์)")

# ==============================
# 📥 Input
# ==============================
values_input = st.text_area("ค่าตัวเลข:", "9 8 9 8 9 7 9 9 9 6 5 7 6 8 1 6 7 6 9 7 7 9 8 9")
colors_input = st.text_area("สีแท่ง (b=น้ำเงิน, r=แดง, g=เขียว=เสมอ):", "r r b r r r b b r b r b b b g b r r b b r r b r")

# ถ้ายังไม่มีข้อมูลเลย ก็ไม่หยุด แค่เตือน
if not values_input.strip():
    st.info("🕐 กรุณากรอกค่าตัวเลขเพื่อเริ่มวิเคราะห์...")
    st.stop()

try:
    values = [float(x) for x in values_input.split() if x.strip()]
except:
    st.error("❌ ตัวเลขไม่ถูกต้อง")
    st.stop()

colors_raw = [c.lower() for c in colors_input.split() if c.strip()]

# ถ้ายังพิมพ์สีไม่ครบ ระบบจะเติม g (เสมอ)
if len(colors_raw) < len(values):
    colors_raw += ["g"] * (len(values) - len(colors_raw))
elif len(colors_raw) > len(values):
    colors_raw = colors_raw[:len(values)]

color_map = {'b': 'royalblue', 'r': 'crimson', 'g': 'limegreen'}
colors = [color_map.get(c, 'gray') for c in colors_raw]

# ==============================
# flow chart ต่อเนื่อง
# ==============================
bar_width = 0.8
scale = 0.5
tops, bottoms = [], []

for i, (v, c) in enumerate(zip(values, colors_raw)):
    height = v * scale
    if i == 0:
        bottom, top = 0, height
    else:
        prev_c = colors_raw[i - 1]
        prev_top, prev_bottom = tops[-1], bottoms[-1]
        if c == "b":
            bottom = prev_top
            top = bottom + height
        elif c == "r":
            top = prev_bottom
            bottom = top - height
        else:
            bottom, top = prev_bottom, prev_top
    tops.append(top)
    bottoms.append(bottom)

midpoints = [(t + b) / 2 for t, b in zip(tops, bottoms)]

# ==============================
# หา signal จุดกลับตัว
# ==============================
signals = []
for i in range(1, len(values) - 1):
    if values[i - 1] > values[i] < values[i + 1]:
        signals.append({"index": i, "type": "up"})
    elif values[i - 1] < values[i] > values[i + 1]:
        signals.append({"index": i, "type": "down"})

# ==============================
# ประเมินจากแท่งถัดไป
# ==============================
for s in signals:
    i = s["index"]
    if i + 1 >= len(colors_raw):
        s["result"] = "neutral"
        continue

    next_color = colors_raw[i + 1]
    if s["type"] == "up":
        s["result"] = "win" if next_color == "b" else "lose" if next_color == "r" else "neutral"
    elif s["type"] == "down":
        s["result"] = "win" if next_color == "r" else "lose" if next_color == "b" else "neutral"

# ==============================
# สถิติ
# ==============================
wins = sum(1 for s in signals if s["result"] == "win")
losses = sum(1 for s in signals if s["result"] == "lose")
draws = sum(1 for s in signals if s["result"] == "neutral")
lose_streaks, streak = [], 0
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
fig.patch.set_facecolor('#0e1117')
ax.set_facecolor('#0e1117')

for i, (b, t, c) in enumerate(zip(bottoms, tops, colors)):
    ax.add_patch(plt.Rectangle((i - bar_width/2, b), bar_width, t - b, color=c, ec='white', lw=0.5))

for s in signals:
    i = s["index"]
    mid_y = midpoints[i]
    if s["type"] == "up":
        ax.annotate('↑', (i, mid_y - 0.3), color='cyan', ha='center', fontsize=14, fontweight='bold')
    else:
        ax.annotate('↓', (i, mid_y + 0.3), color='orange', ha='center', fontsize=14, fontweight='bold')
    color_box = {"win": "lime", "lose": "red", "neutral": "yellow"}[s["result"]]
    ax.add_patch(plt.Rectangle((i - bar_width/2, bottoms[i]), bar_width, tops[i] - bottoms[i], fill=False, ec=color_box, lw=2))

ax.plot(range(len(midpoints)), midpoints, color='white', lw=0.8, alpha=0.4)
ax.set_xlim(-0.5, len(values) - 0.5)
ax.set_xticks(range(len(values)))
ax.set_xticklabels([str(i + 1) for i in range(len(values))], color='white')
ax.set_yticks([])
for s in ax.spines.values():
    s.set_color('#333')
ax.set_title("📈 Flow Graph — กรอบสีคือผลลัพธ์ (เขียว=ชนะ, แดง=แพ้, เหลือง=เสมอ)", color='white')
plt.tight_layout()
st.pyplot(fig)

# ==============================
# แสดงสถิติ
# ==============================
st.markdown("### 📊 สรุปผล")
st.write(f"✅ ชนะทั้งหมด: **{wins}**")
st.write(f"❌ แพ้ทั้งหมด: **{losses}**")
st.write(f"⚪ เสมอทั้งหมด: **{draws}**")
st.write(f"🎯 ความแม่นยำ (ไม่รวมเสมอ): **{accuracy:.1f}%**")
st.write(f"🔥 แพ้ติดกันยาวสุด: **{max_lose_streak} ไม้**")
