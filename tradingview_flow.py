import streamlit as st
import matplotlib.pyplot as plt

st.title("📊 TradingView Flow Visualizer")

# ช่องให้ใส่ข้อมูล
values_input = st.text_input("กรอกค่าตัวเลข (เช่น 8 6 5 7 9):", "8 6 5 7 9")
colors_input = st.text_input("กรอกสี (ใช้ b = blue, r = red เช่น b r r b r):", "b r r b r")

# แปลงข้อมูล
values = [float(x) for x in values_input.split()]
colors = ['blue' if c == 'b' else 'red' for c in colors_input.split()]

# เริ่มสร้างกราฟ
bar_width = 0.8
scale = 0.5

tops = []
bottoms = []
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
        else:
            top = prev_top if prev_color == 'blue' else prev_bottom
            bottom = top - height
    tops.append(top)
    bottoms.append(bottom)

# วาดกราฟ
fig, ax = plt.subplots(figsize=(10,6))
for i, (v, c, top, bottom) in enumerate(zip(values, colors, tops, bottoms)):
    color = 'royalblue' if c == 'blue' else 'crimson'
    rect = plt.Rectangle((i - bar_width/2, bottom),
                         bar_width, top - bottom,
                         color=color, ec='white', lw=0.6, alpha=0.9)
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
ax.set_title("TradingView-Style Flow", color='white', fontsize=14)

st.pyplot(fig)
