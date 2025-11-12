import streamlit as st
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np

st.set_page_config(layout="wide")
st.title("📊 TradingView Flow — ระบบสัญญาณล่วงหน้า + ประเมินด้วยสี")

# ============= Sidebar =============
st.sidebar.header("🖼️ อัปโหลดภาพ (ถ้ามี)")
uploaded_file = st.sidebar.file_uploader("วางหรืออัปโหลดภาพ:", type=["png", "jpg", "jpeg"])
if uploaded_file:
    st.sidebar.image(Image.open(uploaded_file), caption="ภาพที่อัปโหลด", use_column_width=True)

# ============= Input =============
st.subheader("🧮 ป้อนข้อมูล")
values_input = st.text_area("กรอกค่าตัวเลข (คั่นด้วยช่องว่าง):", "9 8 9 8 9 7 9 9")
colors_input = st.text_area("กรอกสี (ใช้ b=blue / r=red / g=green):", "r b r r b r b b")

# parse input
try:
    values = [float(x) for x in values_input.split()]
except:
    st.error("❌ กรุณากรอกตัวเลขให้ถูกต้อง")
    st.stop()

colors_raw = [c.lower() for c in colors_input.split()]
if len(colors_raw) < len(values):
    colors_raw += ['g'] * (len(values) - len(colors_raw))
elif len(colors_raw) > len(values):
    colors_raw = colors_raw[:len(values)]

color_map = {'b': 'royalblue', 'r': 'crimson', 'g': 'gray'}
colors = [color_map.get(c, 'gray') for c in colors_raw]

# ============= Logic: สร้างสัญญาณล่วงหน้า 1 แท่ง =============
signals = []
for i in range(1, len(values) - 1):
    # หาจุดกลับตัวจาก 3 แท่ง
    if values[i - 1] > values[i] < values[i + 1]:
        # สัญญาณขึ้นให้ล่วงหน้าที่แท่งถัดไป
        signals.append({"index": i + 1, "type": "up"})
    elif values[i - 1] < values[i] > values[i + 1]:
        # สัญญาณลงให้ล่วงหน้าที่แท่งถัดไป
        signals.append({"index": i + 1, "type": "down"})

# ============= ตรวจถูกผิดด้วยสีแท่งจริง =============
for s in signals:
    i = s["index"]
    if i >= len(colors_raw):
        s["correct"] = None  # ยังไม่มีแท่งจริง
    else:
        real_col = colors_raw[i]
        if real_col == 'g':
            s["correct"] = None
        elif s["type"] == "up":
            s["correct"] = (real_col == 'b')
        elif s["type"] == "down":
            s["correct"] = (real_col == 'r')
        s["color"] = real_col

# ============= แสดงสถิติ =============
total_signals = len(signals)
evaluated = [s for s in signals if s["correct"] is not None]
correct = sum(s["correct"] for s in evaluated if s["correct"])
acc = (correct / len(evaluated) * 100) if evaluated else 0

st.markdown("### 📈 สถิติรวม")
st.write(f"- จำนวนสัญญาณทั้งหมด: **{total_signals}**")
st.write(f"- จำนวนที่ประเมินได้: **{len(evaluated)}**")
st.write(f"- ความแม่นยำรวม: **{acc:.1f}%**")

# ============= ตารางสัญญาณ =============
rows = []
for s in signals:
    rows.append({
        "แท่ง": s["index"] + 1,
        "สัญญาณ": "↑ ขึ้น" if s["type"] == "up" else "↓ ลง",
        "สีแท่งจริง": s.get("color", "-"),
        "ผลลัพธ์": "✅ ชนะ" if s.get("correct") else ("❌ แพ้" if s.get("correct") == False else "⏳ รอแท่งถัดไป")
    })
st.table(rows)

# ============= วาดกราฟ =============
fig, ax = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor('#0e1117')
ax.set_facecolor('#0e1117')

bar_width = 0.8
scale = 0.5
tops, bottoms = [], []

for i, v in enumerate(values):
    height = v * scale
    if i == 0:
        bottom, top = 0, height
    else:
        prev_top, prev_bottom = tops[-1], bottoms[-1]
        c = colors_raw[i]
        if c == 'b':
            bottom, top = prev_top, prev_top + height
        elif c == 'r':
            top, bottom = prev_bottom, prev_bottom - height
        else:
            bottom, top = prev_bottom, prev_top
    tops.append(top)
    bottoms.append(bottom)

midpoints = [(t + b) / 2 for t, b in zip(tops, bottoms)]

# วาดแท่ง
for i, (top, bottom, c) in enumerate(zip(tops, bottoms, colors)):
    ax.add_patch(plt.Rectangle((i - bar_width / 2, bottom),
                               bar_width, top - bottom,
                               color=c, ec='white', lw=0.5))

# ลูกศรสัญญาณ
for s in signals:
    i = s["index"]
    if i < len(midpoints):
        if s["type"] == "up":
            ax.annotate('↑', xy=(i, midpoints[i]), xytext=(i, midpoints[i] - 0.5),
                        color='white', ha='center', fontsize=14, fontweight='bold')
        else:
            ax.annotate('↓', xy=(i, midpoints[i]), xytext=(i, midpoints[i] + 0.5),
                        color='white', ha='center', fontsize=14, fontweight='bold')
        if s.get("correct") is True:
            ec = 'lime'
        elif s.get("correct") is False:
            ec = 'red'
        else:
            ec = 'yellow'
        ax.add_patch(plt.Rectangle((i - bar_width / 2, bottoms[i]), bar_width, tops[i] - bottoms[i],
                                   fill=False, ec=ec, lw=2))

ax.set_xlim(-0.5, len(values) + 0.5)
ax.set_xticks(range(len(values)))
ax.set_xticklabels([str(i + 1) for i in range(len(values))], color='white')
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_edgecolor('#2a2f36')

ax.set_title("📊 Flow Visual — สัญญาณล่วงหน้า + ตรวจด้วยสีแท่งจริง", color='white')
st.pyplot(fig)

st.markdown("---")
st.info("✅ ระบบนี้จะให้สัญญาณ 'ล่วงหน้า 1 แท่ง' และจะตรวจผลเมื่อแท่งถัดไปปรากฏ (b=ชนะ, r=แพ้, g=เสมอ)")
