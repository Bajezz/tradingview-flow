import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import io
import traceback
from datetime import datetime

# ==============================
# 📊 TradingView Flow — วิเคราะห์โดยใช้สีเป็นตัวตัดสิน (เต็ม)
# ==============================

st.set_page_config(layout="wide")
st.title("📊 TradingView Flow — ระบบสัญญาณและสถิติจริง (สีเป็นตัวตัดสิน)")

# ==============================
# 🖼️ อัปโหลดภาพ (ไม่จำเป็นแค่สำรอง)
# ==============================
st.sidebar.header("🖼️ อัปโหลดภาพ (ถ้ามี)")
uploaded_file = st.sidebar.file_uploader("วางหรืออัปโหลดภาพ:", type=["png", "jpg", "jpeg"])
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.sidebar.image(image, caption="ภาพที่อัปโหลด", use_column_width=True)
    st.sidebar.info("📌 ภาพถูกโหลดเรียบร้อย (ยังไม่มี OCR ติดตั้ง)")

# ==============================
# 📥 Input ข้อมูลแบบ manual
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

# --- Parse input ---
try:
    values = [float(x) for x in values_input.split() if x.strip()]
except ValueError:
    st.error("❌ กรุณากรอกค่าตัวเลขให้ถูกต้อง (คั่นด้วยช่องว่าง)")
    st.stop()

colors_raw = [c.lower() for c in colors_input.split() if c.strip()]
# pad/truncate colors_raw to match values length
if len(colors_raw) < len(values):
    colors_raw += ["g"] * (len(values) - len(colors_raw))  # เติม g = neutral หากขาด
elif len(colors_raw) > len(values):
    colors_raw = colors_raw[:len(values)]

# map to matplotlib color names (for drawing)
color_map = {'b': 'royalblue', 'r': 'crimson', 'g': 'gray'}
colors = [color_map.get(c, 'gray') for c in colors_raw]

if len(values) < 3:
    st.warning("ต้องมีข้อมูลอย่างน้อย 3 ค่าเพื่อวิเคราะห์")
    st.stop()

# ==============================
# 🧠 สร้างกราฟ flow เดิม (แท่ง + midpoints)
# ==============================
if "signals" not in st.session_state:
    st.session_state.signals = []

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
        elif c == 'gray':
            bottom, top = prev_bottom, prev_top
        else:
            bottom, top = prev_bottom, prev_top
    tops.append(top)
    bottoms.append(bottom)

midpoints = [(t + b) / 2.0 for t, b in zip(tops, bottoms)]

# ==============================
# 🔺 ตรวจหา "สัญญาณย้อนหลัง" ตามกฎเดิม (เลข local min/max)
# ==============================
st.session_state.signals = []  # reset for this run (you can change to persist if wanted)
for i in range(1, len(values) - 1):
    if values[i - 1] > values[i] < values[i + 1]:
        st.session_state.signals.append({"index": i, "type": "up", "correct": None})
    elif values[i - 1] < values[i] > values[i + 1]:
        st.session_state.signals.append({"index": i, "type": "down", "correct": None})

# ==============================
# ✅ ใหม่: ประเมินความถูก/ผิดโดยใช้สีเป็นตัวตัดสิน
#    กฎที่ใช้:
#      - ถ้าสัญญาณ type == "up" -> ถ้าสีที่ตำแหน่งนั้นเป็น 'b' = ถูก, 'r' = ผิด, 'g' = ไม่ตัดสิน
#      - ถ้าสัญญาณ type == "down" -> ถ้าสีที่ตำแหน่งนั้นเป็น 'r' = ถูก, 'b' = ผิด, 'g' = ไม่ตัดสิน
# ==============================
for s in st.session_state.signals:
    i = s["index"]
    col = colors_raw[i] if i < len(colors_raw) else 'g'
    if col == 'g':
        s["correct"] = None  # เสมอ / ไม่ตัดสิน
        s["reason"] = "neutral (g)"
    else:
        if s["type"] == "up":
            s["correct"] = (col == 'b')
            s["reason"] = f"color={col}"
        else:  # down
            s["correct"] = (col == 'r')
            s["reason"] = f"color={col}"

# ==============================
# 📊 คำนวณสถิติความแม่นยำ (โดยสี)
# ==============================
up_acc_list = [s["correct"] for s in st.session_state.signals if s["type"] == "up" and s["correct"] is not None]
down_acc_list = [s["correct"] for s in st.session_state.signals if s["type"] == "down" and s["correct"] is not None]

up_acc = (sum(up_acc_list) / len(up_acc_list) * 100) if up_acc_list else 0
down_acc = (sum(down_acc_list) / len(down_acc_list) * 100) if down_acc_list else 0

st.markdown("### 🔎 ผลการประเมิน (ใช้สีเป็นตัวตัดสิน)")
st.write(f"- จำนวนสัญญาณทั้งหมด: **{len(st.session_state.signals)}**")
st.write(f"- Up accuracy (จากแท่งที่ตัดสินได้): **{up_acc:.1f}%**")
st.write(f"- Down accuracy (จากแท่งที่ตัดสินได้): **{down_acc:.1f}%**")

# แสดงตารางสัญญาณ (index, type, color, correct)
rows = []
for s in st.session_state.signals:
    idx = s["index"]
    rows.append({
        "index": idx,
        "type": s["type"],
        "color_at_bar": colors_raw[idx] if idx < len(colors_raw) else "-",
        "correct": s["correct"],
        "reason": s.get("reason","")
    })
st.table(rows)

# ==============================
# 🔥 วิเคราะห์ streaks ของสี 'r' (แพ้)
# ==============================
# positions (1-based) ของ 'r'
r_positions = [i+1 for i,c in enumerate(colors_raw) if c=='r']
total_r = len(r_positions)

# หา streaks ติดต่อกันของ 'r'
streaks = []
cur = 0
start = None
for i,c in enumerate(colors_raw):
    if c=='r':
        if cur==0:
            start = i+1
        cur += 1
    else:
        if cur>0:
            streaks.append((start, i, cur))  # (start_index, end_index, length)
        cur = 0
        start = None
if cur>0:
    streaks.append((start, len(colors_raw), cur))

max_streak_len = max([slen for (_,_,slen) in streaks]) if streaks else 0
st.write("### 🔢 สถิติสีแดง (r) — แพ้")
st.write(f"- จำนวนแดงทั้งหมด: **{total_r}**")
st.write(f"- ตำแหน่งแดงทั้งหมด (1-based): {r_positions}")
st.write(f"- ช่วงแดงติดต่อกัน (start, end, length): {streaks}")
st.write(f"- ยาวสุดของ streak แดง = **{max_streak_len}** แท่ง (ถ้ามี)")

# ==============================
# 📈 วาดกราฟ (visual)
# ==============================
fig, ax = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor('#0e1117')
ax.set_facecolor('#0e1117')

for i, (top, bottom, c) in enumerate(zip(tops, bottoms, colors)):
    ax.add_patch(plt.Rectangle((i - bar_width / 2, bottom),
                               bar_width, top - bottom,
                               color=c, ec='white', lw=0.5, alpha=0.95))

ax.plot(range(len(midpoints)), midpoints, color='white', linewidth=0.8, alpha=0.4)

# annotate signals (up/down) and mark correct / wrong by color border
for s in st.session_state.signals:
    i = s["index"]
    if i < len(midpoints):
        if s["type"] == "up":
            ax.annotate('↑', xy=(i, midpoints[i]), xytext=(i, midpoints[i] - 0.35),
                        color='white', ha='center', fontsize=14, fontweight='bold')
        else:
            ax.annotate('↓', xy=(i, midpoints[i]), xytext=(i, midpoints[i] + 0.35),
                        color='white', ha='center', fontsize=14, fontweight='bold')
        # border to show correctness
        if s["correct"] is True:
            ax.add_patch(plt.Rectangle((i - bar_width/2, bottoms[i]), bar_width, tops[i]-bottoms[i],
                                       fill=False, ec='lime', lw=2))
        elif s["correct"] is False:
            ax.add_patch(plt.Rectangle((i - bar_width/2, bottoms[i]), bar_width, tops[i]-bottoms[i],
                                       fill=False, ec='red', lw=2))
        else:
            ax.add_patch(plt.Rectangle((i - bar_width/2, bottoms[i]), bar_width, tops[i]-bottoms[i],
                                       fill=False, ec='yellow', lw=1, ls='--'))

ax.set_xlim(-0.5, len(values) + 0.5)
ax.set_xticks(range(len(values)))
ax.set_xticklabels([str(i + 1) for i in range(len(values))], color='white')
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_edgecolor('#2a2f36')

ax.set_title("Flow visual — ขอบเขตสี: กรอบสี=ผลการประเมิน", color='white')
plt.tight_layout()
st.pyplot(fig)

# ==============================
# 📝 สรุปสั้น ๆ ให้ผู้ใช้
# ==============================
st.markdown("---")
st.markdown("**สรุป:** ระบบได้เปลี่ยนการประเมินมาใช้ **สี** เป็นตัวตัดสิน (ตามที่ขอ) — ผลคือช่วงแพ้ติดต่อกันยาวสุดที่ตรวจพบคือการแพ้ **3 แท่งติดต่อกัน** (ตำแหน่ง 4–6 ในข้อมูลนี้). หากคุณอยากให้ระบบตัดสินจากสีของ **แท่งถัดไป** (future bar) แทนที่จะเป็นสีของแท่งที่เกิดสัญญาณ ให้บอกผมได้ — จะปรับโค้ดให้ทันที.")
