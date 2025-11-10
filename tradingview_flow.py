import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.title("📊 TradingView Flow Visualizer + Signal Detector")

# --- Input ---
values_input = st.text_input("กรอกค่าตัวเลข (เช่น 8 6 5 7 9):", "8 6 5 7 9 8 10 9")
colors_input = st.text_input("กรอกสี (b=blue, r=red, g=green เช่น b r g b g):", "b r g b g r g")

# --- Parse inputs ---
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

# --- Graph parameters ---
bar_width = 0.8
scale = 0.5
tops, bottoms = [], []

# --- Compute bar positions ---
for i, (v, c) in enumerate(zip(values, colors)):
    height = v * scale
    if i == 0:
        bottom, top = 0, height
    else:
        prev_color = colors[i - 1]
        prev_top, prev_bottom = tops[-1], bottoms[-1]

        if c == 'blue':  # ขาขึ้น
            bottom = prev_top if prev_color == 'blue' else prev_bottom
            top = bottom + height
        elif c == 'red':  # ขาลง
            top = prev_top if prev_color == 'blue' else prev_bottom
            bottom = top - height
        elif c == 'green':  # ขึ้นแรง
            bottom = prev_top if prev_color in ['blue', 'green'] else prev_bottom
            top = bottom + height * 1.2
        else:
            bottom, top = prev_bottom, prev_top

    tops.append(top)
    bottoms.append(bottom)

# --- สร้างกราฟ ---
fig, ax = plt.subplots(figsize=(10, 6))

for i, (v, c, top, bottom) in enumerate(zip(values, colors, tops, bottoms)):
    color_map = {'blue': 'royalblue', 'red': 'crimson', 'green': 'limegreen'}
    color = color_map.get(c, 'gray')
    rect = plt.Rectangle((i - bar_width / 2, bottom),
                         bar_width, top - bottom,
                         color=color, ec='white', lw=0.6, alpha=0.9)
    ax.add_patch(rect)
    ax.text(i, (top + bottom) / 2, str(v),
            color='white', ha='center', va='center', fontsize=12, fontweight='bold')

midpoints = [(t + b) / 2 for t, b in zip(tops, bottoms)]
ax.plot(range(len(values)), midpoints, color='white', linewidth=0.8, alpha=0.5)

# --- ลูกศรสัญญาณขึ้น-ลง ---
for i in range(1, len(values) - 1):
    if values[i - 1] > values[i] < values[i + 1]:
        ax.annotate('↑', xy=(i, midpoints[i]), xytext=(i, midpoints[i] - 0.3),
                    color='lime', ha='center', fontsize=16, fontweight='bold')
    elif values[i - 1] < values[i] > values[i + 1]:
        ax.annotate('↓', xy=(i, midpoints[i]), xytext=(i, midpoints[i] + 0.3),
                    color='red', ha='center', fontsize=16, fontweight='bold')

# --- พยากรณ์ค่าถัดไป (ไม่ใช้ sklearn) ---
x = np.arange(len(values))
y = np.array(values)
a, b = np.polyfit(x, y, 1)  # linear regression (manual)
next_value = a * len(values) + b
direction = "📈 แนวโน้มขึ้น" if a > 0 else "📉 แนวโน้มลง"

# --- Display prediction result ---
st.markdown(f"**🔮 ค่าพยากรณ์ถัดไป:** `{next_value:.2f}`")
st.markdown(f"**📊 ทิศทางแนวโน้ม:** {direction}")

# --- จัดรูปกราฟ ---
ax.set_xlim(-0.5, len(values) - 0.5)
ax.set_facecolor('#0e1117')
ax.grid(True, linestyle='--', color='gray', alpha=0.3)
ax.set_xticks(range(len(values)))
ax.set_xticklabels([str(i + 1) for i in range(len(values))])
ax.set_yticks([])
ax.set_title("TradingView-Style Flow + Signal Arrows", color='white', fontsize=14)

st.pyplot(fig)
