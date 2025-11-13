import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# ==============================
# ⚙️ ตั้งค่าหน้าเว็บ
# ==============================
st.set_page_config(layout="wide")
st.title("📈 Flow Pro — Momentum Bias Mode")
st.caption("เวอร์ชัน: วิเคราะห์แนวโน้ม + คำนวณเปอร์เซ็นต์มั่นใจแท่งถัดไป (Next Bar Prediction)")

# ==============================
# 📥 Input
# ==============================
st.sidebar.header("📥 ป้อนข้อมูล")

values_input = st.sidebar.text_area("ค่าตัวเลข (ความแรงแต่ละแท่ง):", "8 8 4 4 9 6 6 9 3 8 8 6 8 3 9 8")
colors_input = st.sidebar.text_area("สีแท่ง (b=น้ำเงิน, r=แดง, g=เขียว=เสมอ):", "r r r r b r r b r b r b r b r b")

mode = st.sidebar.radio("🧭 เลือกโหมดวิเคราะห์:", 
                        ["Real-Time", "Momentum Bias Mode (แนะนำ)"], index=1)

# ==============================
# 🔄 แปลงข้อมูล
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
# 📊 สร้าง Flow Graph
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

midpoints = np.array([(t + b) / 2 for t, b in zip(tops, bottoms)])

# ==============================
# 📈 Momentum Bias Algorithm
# ==============================
def momentum_bias(values, colors):
    """คำนวณโมเมนตัมของกราฟ เพื่อเดาทิศทางแท่งถัดไป"""
    weights = np.linspace(0.5, 1.5, len(values))
    momentum = np.sum(np.array(values) * weights * np.where(np.array(colors) == 'b', 1, -1))
    bias = "ขึ้น (Blue)" if momentum > 0 else "ลง (Red)"
    
    # normalize confidence
    conf = min(99, abs(momentum) / (np.mean(values) * len(values) / 2) * 100)
    return bias, conf

bias, confidence = momentum_bias(values, colors_raw)

# ==============================
# 🔍 หา signal จุดกลับตัว
# ==============================
signals = []
for i in range(1, len(values) - 1):
    if values[i - 1] > values[i] < values[i + 1]:
        signals.append({"index": i, "type": "up"})
    elif values[i - 1] < values[i] > values[i + 1]:
        signals.append({"index": i, "type": "down"})

# ==============================
# 📊 แสดงผลกราฟ
# ==============================
fig, ax = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor('#0e1117')
ax.set_facecolor('#0e1117')

for i, (b, t, c) in enumerate(zip(bottoms, tops, colors)):
    ax.add_patch(plt.Rectangle((i - bar_width / 2, b), bar_width, t - b, color=c, ec='white', lw=0.5))

for s in signals:
    i = s["index"]
    mid_y = midpoints[i]
    if s["type"] == "up":
        ax.annotate('↑', (i, mid_y - 0.3), color='cyan', ha='center', fontsize=14, fontweight='bold')
    else:
        ax.annotate('↓', (i, mid_y + 0.3), color='orange', ha='center', fontsize=14, fontweight='bold')

ax.plot(range(len(midpoints)), midpoints, color='white', lw=0.8, alpha=0.4)
ax.set_xlim(-0.5, len(values) - 0.5)
ax.set_xticks(range(len(values)))
ax.set_xticklabels([str(i + 1) for i in range(len(values))], color='white')
ax.set_yticks([])
for s in ax.spines.values():
    s.set_color('#333')
ax.set_title(f"Flow Momentum Visualization — Mode: {mode}", color='white')
plt.tight_layout()
st.pyplot(fig)

# ==============================
# 📊 สรุปผลการวิเคราะห์
# ==============================
st.markdown("---")
st.subheader("📊 สรุปผลการวิเคราะห์")

col1, col2 = st.columns(2)
with col1:
    st.metric("🧭 แนวโน้มหลัก (Momentum Bias)", bias)
with col2:
    st.metric("🎯 ความมั่นใจ", f"{confidence:.1f}%")

# ==============================
# 🧩 วิเคราะห์สรุปเชิงลึก
# ==============================
if confidence >= 75:
    st.success("✅ สัญญาณแข็งแรง — แนวโน้มมีโอกาสสูงมากที่จะต่อเนื่องไปในทิศทางเดียวกัน")
elif confidence >= 50:
    st.warning("⚠️ สัญญาณปานกลาง — อาจมีการรีบาวด์หรือสวิงระยะสั้นได้")
else:
    st.error("❌ สัญญาณอ่อน — ควรรอจังหวะยืนยันแท่งถัดไปก่อนเข้าไม้")

st.markdown("""
**💡 คำอธิบาย:**
- Momentum Bias ใช้โมเดลน้ำหนักล่าสุด (Weighted Momentum) เพื่อวิเคราะห์แนวโน้มต่อเนื่อง
- ค่าความมั่นใจ (%) ยิ่งสูง ยิ่งมีโอกาสที่แท่งถัดไปจะไปในทิศทางเดียวกับ Bias
- ใช้ร่วมกับ “Confirm Next Bar” ได้เพื่อกรองสัญญาณหลอก
""")
