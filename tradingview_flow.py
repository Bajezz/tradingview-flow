import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("📊 TradingView Flow — Confirm Next Bar (เร็วขึ้นแต่ยังแม่น)")

# ==============================
# 📥 Input
# ==============================
st.subheader("🧮 ป้อนข้อมูล")
values_input = st.text_area("ค่าตัวเลข:", "9 9 9 8 8 6 6 7 8 9 4 6 8 9 9 7")
colors_input = st.text_area("สีแท่ง (b=น้ำเงิน, r=แดง, g=เขียว=เสมอ):", "r b r r b b g b r b b b r r r b")

# ==============================
# แปลงข้อมูล
# ==============================
try:
    values = [float(x) for x in values_input.split() if x.strip()]
except:
    st.error("❌ ตัวเลขไม่ถูกต้อง")
    st.stop()

colors_raw = [c.lower() for c in colors_input.split() if c.strip()]
if len(colors_raw) < len(values):
    colors_raw += ["g"] * (len(values) - len(colors_raw))
elif len(colors_raw) > len(values):
    colors_raw = colors_raw[:len(values)]

color_map = {'b': 'royalblue', 'r': 'crimson', 'g': 'limegreen'}
colors = [color_map.get(c, 'gray') for c in colors_raw]

# ==============================
# สร้างกราฟแท่ง Flow
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
        else:  # g
            bottom, top = prev_bottom, prev_top
    tops.append(top)
    bottoms.append(bottom)

midpoints = [(t + b) / 2 for t, b in zip(tops, bottoms)]

# ==============================
# หาสัญญาณกลับตัว (รวมแท่งสุดท้ายแบบคาดการณ์)
# ==============================
signals = []
for i in range(1, len(values) - 1):
    if values[i - 1] > values[i] < values[i + 1]:
        signals.append({"index": i, "type": "up", "confirmed": True})
    elif values[i - 1] < values[i] > values[i + 1]:
        signals.append({"index": i, "type": "down", "confirmed": True})

# สัญญาณคาดการณ์แท่งล่าสุด (ยังไม่ยืนยัน)
if len(values) >= 2:
    i = len(values) - 1
    if values[i - 1] > values[i]:
        signals.append({"index": i, "type": "up", "confirmed": False})
    elif values[i - 1] < values[i]:
        signals.append({"index": i, "type": "down", "confirmed": False})

# ==============================
# ประเมินผล (แท่งถัดไป)
# ==============================
for s in signals:
    i = s["index"]
    if i + 1 < len(colors_raw):  # มีแท่งถัดไป → ยืนยันผล
        next_color = colors_raw[i + 1]
        s["confirmed"] = True
    else:  # ไม่มีแท่งถัดไป → ยังไม่ยืนยัน
        next_color = None
        s["confirmed"] = False

    if s["type"] == "up":
        if next_color == "b":
            s["result"] = "win"
        elif next_color == "r":
            s["result"] = "lose"
        elif next_color == "g":
            s["result"] = "neutral"
        else:
            s["result"] = "pending"
    elif s["type"] == "down":
        if next_color == "r":
            s["result"] = "win"
        elif next_color == "b":
            s["result"] = "lose"
        elif next_color == "g":
            s["result"] = "neutral"
        else:
            s["result"] = "pending"

# ==============================
# วาดกราฟ Flow
# ==============================
fig, ax = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor('#0e1117')
ax.set_facecolor('#0e1117')

# วาดแท่ง
for i, (b, t, c) in enumerate(zip(bottoms, tops, colors)):
    ax.add_patch(plt.Rectangle((i - bar_width/2, b), bar_width, t - b, color=c, ec='white', lw=0.5))

# วาดสัญญาณ
for s in signals:
    i = s["index"]
    mid_y = midpoints[i]
    if s["type"] == "up":
        arrow = '↑'
        color_arrow = 'cyan' if not s["confirmed"] else 'lime'
    else:
        arrow = '↓'
        color_arrow = 'orange' if not s["confirmed"] else 'red'

    ax.annotate(arrow, (i, mid_y), color=color_arrow, ha='center', fontsize=14, fontweight='bold')

    # กรอบผลลัพธ์
    if s["result"] == "win":
        ec_color = "lime"
    elif s["result"] == "lose":
        ec_color = "red"
    elif s["result"] == "neutral":
        ec_color = "yellow"
    else:
        ec_color = "gray"
    ax.add_patch(plt.Rectangle((i - bar_width/2, bottoms[i]),
                               bar_width, tops[i] - bottoms[i],
                               fill=False, ec=ec_color, lw=2))

ax.plot(range(len(midpoints)), midpoints, color='white', lw=0.8, alpha=0.4)
ax.set_xlim(-0.5, len(values) - 0.5)
ax.set_xticks(range(len(values)))
ax.set_xticklabels([str(i + 1) for i in range(len(values))], color='white')
ax.set_yticks([])
for s in ax.spines.values():
    s.set_color('#333')

ax.set_title("📈 Confirm Next Bar (แสดงทันที + อัปเดตเมื่อยืนยัน)", color='white')
plt.tight_layout()
st.pyplot(fig)

# ==============================
# สรุปผล
# ==============================
confirmed_signals = [s for s in signals if s["confirmed"] and s["result"] in ["win", "lose"]]
wins = sum(1 for s in confirmed_signals if s["result"] == "win")
losses = sum(1 for s in confirmed_signals if s["result"] == "lose")
draws = sum(1 for s in confirmed_signals if s["result"] == "neutral")
accuracy = (wins / (wins + losses) * 100) if (wins + losses) else 0

st.markdown("---")
st.markdown("### 📊 ผลสรุป (ยืนยันแล้วเท่านั้น)")
st.write(f"✅ ชนะทั้งหมด: **{wins}**")
st.write(f"❌ แพ้ทั้งหมด: **{losses}**")
st.write(f"⚪ เสมอทั้งหมด: **{draws}**")
st.write(f"🎯 ความแม่นยำ (ไม่รวมเสมอ): **{accuracy:.1f}%**")

# ==============================
# ตารางผลแต่ละสัญญาณ
# ==============================
rows = []
for s in signals:
    rows.append({
        "แท่งที่": s["index"] + 1,
        "ประเภท": s["type"],
        "ผลลัพธ์": s["result"],
        "สถานะ": "✅ ยืนยันแล้ว" if s["confirmed"] else "⏳ รอสัญญาณถัดไป"
    })
st.table(rows)
