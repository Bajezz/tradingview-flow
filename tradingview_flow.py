import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.title("📊 TradingView Flow Visualizer — Persistent + Predictive Signals")

# --- Input ---
values_input = st.text_input("กรอกค่าตัวเลข (เช่น 8 6 5 7 9 8):", "8 6 5 7 9 8 10 9 11 10")
colors_input = st.text_input("กรอกสี (b=blue, r=red, g=green เช่น b r g b g):", "b r g b g r g g r")

# --- Parse input ---
values = [float(x) for x in values_input.split()]
colors_raw = colors_input.split()

if len(colors_raw) < len(values):
    colors_raw += ["gray"] * (len(values) - len(colors_raw))
elif len(colors_raw) > len(values):
    colors_raw = colors_raw[:len(values)]

colors = []
for c in colors_raw:
    if c.lower() == 'b':
        colors.append('blue')
    elif c.lower() == 'r':
        colors.append('red')
    elif c.lower() == 'g':
        colors.append('green')
    else:
        colors.append('gray')

# --- Graph setup ---
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

        if c == 'blue':
            bottom = prev_top if prev_color == 'blue' else prev_bottom
            top = bottom + height
        elif c == 'red':
            top = prev_top if prev_color == 'blue' else prev_bottom
            bottom = top - height
        elif c == 'green':
            bottom = prev_top if prev_color in ['blue', 'green'] else prev_bottom
            top = bottom + height * 1.2
        else:
            bottom, top = prev_bottom, prev_top

    tops.append(top)
    bottoms.append(bottom)

# --- Plot base chart ---
fig, ax = plt.subplots(figsize=(10, 6))
color_map = {'blue': 'royalblue', 'red': 'crimson', 'green': 'limegreen'}

for i, (v, c, top, bottom) in enumerate(zip(values, colors, tops, bottoms)):
    color = color_map.get(c, 'gray')
    ax.add_patch(plt.Rectangle((i - bar_width / 2, bottom),
                               bar_width, top - bottom,
                               color=color, ec='white', lw=0.6, alpha=0.9))
    ax.text(i, (top + bottom) / 2, str(v),
            color='white', ha='center', va='center', fontsize=11, fontweight='bold')

midpoints = [(t + b) / 2 for t, b in zip(tops, bottoms)]
ax.plot(range(len(midpoints)), midpoints, color='white', linewidth=0.8, alpha=0.5)

# --- สัญญาณย้อนหลัง ---
for i in range(1, len(values) - 1):
    if values[i - 1] > values[i] < values[i + 1]:
        # จุดกลับตัวขึ้น
        ax.annotate('↑', xy=(i, midpoints[i]), xytext=(i, midpoints[i] - 0.3),
                    color='lime', ha='center', fontsize=16, fontweight='bold')
    elif values[i - 1] < values[i] > values[i + 1]:
        # จุดกลับตัวลง
        ax.annotate('↓', xy=(i, midpoints[i]), xytext=(i, midpoints[i] + 0.3),
                    color='red', ha='center', fontsize=16, fontweight='bold')

# --- พยากรณ์แท่งถัดไป ---
lookback = min(5, len(values))
x = np.arange(lookback)
y = np.array(values[-lookback:])
a, b = np.polyfit(x, y, 1)

next_value = a * lookback + b
predicted_direction = "ขึ้น" if next_value > y[-1] else "ลง"

# --- วาดลูกศรพยากรณ์ (โปร่ง) ---
arrow_color = 'lime' if predicted_direction == "ขึ้น" else 'red'
arrow_y = midpoints[-1] + (0.4 if predicted_direction == "ขึ้น" else -0.4)
ax.annotate('↑' if predicted_direction == "ขึ้น" else '↓',
            xy=(len(values), midpoints[-1]),
            xytext=(len(values), arrow_y),
            color=arrow_color, ha='center', fontsize=22, fontweight='bold', alpha=0.6)

# --- เส้นต่อแนวโน้ม ---
ax.plot([len(values)-1, len(values)],
        [midpoints[-1], arrow_y],
        linestyle='--', color=arrow_color, alpha=0.6)

# --- แสดงข้อความ ---
st.markdown(f"**🔮 พยากรณ์แท่งถัดไป:** {next_value:.2f}")
st.markdown(f"**📈 แนวโน้มล่วงหน้า:** {predicted_direction}")

# --- Styling ---
ax.set_xlim(-0.5, len(values) + 0.8)
ax.set_facecolor('#0e1117')
ax.grid(True, linestyle='--', color='gray', alpha=0.3)
ax.set_xticks(range(len(values)))
ax.set_xticklabels([str(i + 1) for i in range(len(values))])
ax.set_yticks([])
ax.set_title("TradingView Flow — Persistent & Predictive Signals", color='white', fontsize=14)

st.pyplot(fig)
