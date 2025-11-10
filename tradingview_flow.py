import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

st.title("📊 TradingView Flow Visualizer + Pattern Analyzer + ML Forecast (No sklearn)")

# ช่องให้ใส่ข้อมูล
values_input = st.text_input("กรอกค่าตัวเลข (เช่น 8 6 5 7 9):", "8 6 5 7 9 8")
colors_input = st.text_input("กรอกสี (ใช้ b = blue, r = red, g = green เช่น b r g b g):", "b r g b g r")

# แปลงข้อมูล
values = [float(x) for x in values_input.split()]
colors = []
for c in colors_input.split():
    if c.lower() == 'b':
        colors.append('blue')
    elif c.lower() == 'r':
        colors.append('red')
    elif c.lower() == 'g':
        colors.append('green')
    else:
        colors.append('gray')

# --- สร้างกราฟแท่งแบบ Flow ---
bar_width = 0.8
scale = 0.5
tops, bottoms = [], []

for i, (v, c) in enumerate(zip(values, colors)):
    height = v * scale
    if i == 0:
        bottom = 0
        top = height
    else:
        prev_color = colors[i-1]
        prev_top = tops[-1]
        prev_bottom = bottoms[-1]

        if c == 'blue':
            bottom = prev_top if prev_color == 'blue' else prev_bottom
            top = bottom + height
        elif c == 'red':
            top = prev_top if prev_color == 'blue' else prev_bottom
            bottom = top - height
        elif c == 'green':
            bottom = prev_top if prev_color in ['blue', 'green'] else prev_bottom
            top = bottom + height * 1.2

    tops.append(top)
    bottoms.append(bottom)

# --- แสดงกราฟ ---
fig, ax = plt.subplots(figsize=(10,6))
for i, (v, c, top, bottom) in enumerate(zip(values, colors, tops, bottoms)):
    color_map = {'blue': 'royalblue', 'red': 'crimson', 'green': 'limegreen'}
    rect = plt.Rectangle((i - bar_width/2, bottom),
                         bar_width, top - bottom,
                         color=color_map.get(c, 'gray'), ec='white', lw=0.6, alpha=0.9)
    ax.add_patch(rect)
    ax.text(i, (top + bottom)/2, str(v),
            color='white', ha='center', va='center', fontsize=12, fontweight='bold')

midpoints = [(t + b)/2 for t, b in zip(tops, bottoms)]
ax.plot(range(len(values)), midpoints, color='white', linewidth=0.8, alpha=0.5)
ax.set_xlim(-0.5, len(values)-0.5)
ax.set_facecolor('#0e1117')
ax.grid(True, linestyle='--', color='gray', alpha=0.3)
ax.set_xticks(range(len(values)))
ax.set_xticklabels([str(i+1) for i in range(len(values))])
ax.set_yticks([])
ax.set_title("TradingView-Style Flow + Forecast (No sklearn)", color='white', fontsize=14)
st.pyplot(fig)

# --- 🔍 ส่วนวิเคราะห์สัญญาณ ---
st.subheader("📈 การวิเคราะห์สัญญาณ")

# 1. ค่าเฉลี่ยและแนวโน้ม
mean_val = np.mean(values)
trend = "ขึ้น" if values[-1] > values[-2] else "ลง"
st.write(f"- ค่าเฉลี่ยทั้งหมด: **{mean_val:.2f}**")
st.write(f"- แนวโน้มล่าสุด: **{trend}**")

# 2. ตรวจ pattern ซ้ำ
pattern_length = 3
patterns = [tuple(colors[i:i+pattern_length]) for i in range(len(colors)-pattern_length+1)]
pattern_counts = Counter(patterns)
common_pattern, count = pattern_counts.most_common(1)[0]
if count > 1:
    st.success(f"🌀 พบรูปแบบซ้ำ: {common_pattern} เกิดขึ้น {count} ครั้ง")
else:
    st.info("ℹ️ ยังไม่พบรูปแบบที่เกิดซ้ำบ่อย")

# 3. วิเคราะห์แนวโน้มถัดไปแบบ Markov Chain
transitions = {}
for i in range(len(colors)-1):
    c1, c2 = colors[i], colors[i+1]
    if c1 not in transitions:
        transitions[c1] = Counter()
    transitions[c1][c2] += 1

last_color = colors[-1]
if last_color in transitions:
    probs = {k: v/sum(transitions[last_color].values()) for k, v in transitions[last_color].items()}
    next_color = max(probs, key=probs.get)
    st.write(f"🎯 ความน่าจะเป็นสีถัดไป (Markov แบบง่าย): **{next_color} ({probs[next_color]*100:.1f}%)**")
else:
    st.write("ยังไม่มีข้อมูลพอสำหรับการทำนายสีถัดไป")

# 4. Machine Learning Forecast (คำนวณเอง ไม่ใช้ sklearn)
st.subheader("🤖 พยากรณ์ค่าถัดไป (Linear Regression Manual)")

x = np.arange(len(values))
y = np.array(values)

if len(values) >= 3:
    # ใช้ polyfit หาเส้นตรง y = a*x + b
    a, b = np.polyfit(x, y, 1)
    next_value = a * len(values) + b

    st.write(f"🔮 ค่าที่คาดว่าจะเกิดถัดไป: **{next_value:.2f}**")

    if next_value > values[-1]:
        st.success("✅ คาดว่าแนวโน้มยัง 'ขึ้น' ต่อเนื่อง")
    elif next_value < values[-1]:
        st.warning("⚠️ คาดว่าแนวโน้มอาจ 'ลง'")
    else:
        st.info("🔄 คาดว่าแนวโน้มคงที่")
else:
    st.info("ต้องมีข้อมูลอย่างน้อย 3 จุดเพื่อให้พยากรณ์ได้")

# 5. สรุปสัญญาณรวม
st.subheader("📊 สรุปสัญญาณรวม")
if trend == "ขึ้น" and (last_color in ['blue', 'green']):
    st.success("แนวโน้มแข็งแรง และคาดว่าจะขึ้นต่อ ✅")
elif trend == "ลง" and last_color == 'red':
    st.warning("แนวโน้มขาลงต่อเนื่อง ⚠️")
else:
    st.info("สัญญาณผสม อาจเข้าสู่ช่วงเปลี่ยนทิศ 🔄")
