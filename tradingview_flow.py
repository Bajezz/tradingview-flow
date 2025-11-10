import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.title("📊 TradingView Flow Visualizer + Persistent Predictive Signals")

# --- Input ---
values_input = st.text_input("กรอกค่าตัวเลข (เช่น 8 6 5 7 9):", "8 6 5 7 9 8 10 9")
colors_input = st.text_input("กรอกสี (b=blue, r=red, g=green เช่น b r g b g):", "b r g b g r g")

# --- Parse inputs ---
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

midpoints = [(t + b) / 2 for t, b in zip(tops, bottoms)]

# --- เริ่ม plot ---
fig, ax = plt.subplots(figsize=(10, 6))
color_map = {'blue': 'royalblue', 'red': 'crimson', 'green': 'limegreen'}

for i, (v, c, top, bottom) in enumerate(zip(values, colors, tops, bottoms)):
    color = color_map.get(c, 'gray')
    rect = plt.Rectangle((i - bar_width / 2, bottom),
                         bar_width, top - bottom,
                         color=color, ec='white', lw=0.6, alpha=0.9)
    ax.add_patch(rect)
    ax.text(i, (top + bottom) / 2, str(v),
            color='white', ha='center', va='center', fontsize=12, fontweight='bold')

# --- สัญญาณย้อนหลัง (จุดกลับตัวจริง) ---
for i in range(1, len(values) - 1):
    if values[i - 1] > values[i] < values[i + 1]:
        ax.annotate('↑', xy=(i, midpoints[i]), xytext=(i, midpoints[i] - 0.3),
                    color='lime', ha='center', fontsize=16, fontweight='bold')
    elif values[i - 1] < values[i] > values[i + 1]:
        ax.annotate('↓', xy=(i, midpoints[i]), xytext=(i, midpoints[i] + 0.3),
                    color='red', ha='center', fontsize=16, fontweight='bold')

# --- สร้างที่เก็บสัญญาณใน session ---
if "signal_history" not in st.session_state:
    st.session_state.signal_history = []

# --- พยากรณ์แท่งถัดไป ---
lookback = min(5, len(values))
x = np.arange(lookback)
y = np.array(values[-lookback:])
a, b = np.polyfit(x, y, 1)

next_value = a * lookback + b
predicted_direction = "ขึ้น" if next_value > y[-1] else "ลง"

# --- เก็บสัญญาณพยากรณ์ (แค่ครั้งละ 1 ครั้งเมื่อข้อมูลเปลี่ยน) ---
if len(st.session_state.signal_history) < len(values):
    st.session_state.signal_history.append({
        "index": len(values) - 1,
        "direction": predicted_direction,
        "value": y[-1]
    })

# --- แสดงลูกศรพยากรณ์ทั้งหมด (จากประวัติ) ---
for sig in st.session_state.signal_history:
    color = 'lime' if sig["direction"] == "ขึ้น" else 'red'
    offset = 0.4 if sig["direction"] == "ขึ้น" else -0.4
    ax.annotate('↑' if sig["direction"] == "ขึ้น" else '↓',
                xy=(sig["index"], sig["value"]),
                xytext=(sig["index"], sig["value"] + offset),
                color=color, ha='center', fontsize=20, fontweight='bold', alpha=0.6)

# --- วาดสัญญาณใหม่ (แท่งล่าสุด) ---
arrow_color = 'lime' if predicted_direction == "ขึ้น" else 'red'
arrow_y = midpoints[-1] + (0.4 if predicted_direction == "ขึ้น" else -0.4)
ax.annotate('↑' if predicted_direction == "ขึ้น" else '↓',
            xy=(len(values), midpoints[-1]),
            xytext=(len(values), arrow_y),
            color=arrow_color, ha='center', fontsize=22, fontweight='bold', alpha=0.6)

# --- แสดงข้อความ ---
st.markdown(f"**🔮 พยากรณ์แท่งถัดไป:** {next_value:.2f}")
st.markdown(f"**📈 แนวโน้มล่วงหน้า:** {predicted_direction}")

# --- สรุปประวัติสัญญาณ ---
if st.session_state.signal_history:
    st.write("📜 **ประวัติสัญญาณที่ผ่านมา:**")
    for s in st.session_state.signal_history:
        st.write(f"• แท่งที่ {s['index']+1} → {s['direction']} (ค่า {s['value']:.2f})")

# --- Styling ---
ax.set_xlim(-0.5, len(values) + 0.8)
ax.set_facecolor('#0e1117')
ax.grid(True, linestyle='--', color='gray', alpha=0.3)
ax.set_xticks(range(len(values)))
ax.set_xticklabels([str(i + 1) for i in range(len(values))])
ax.set_yticks([])
ax.set_title("TradingView Flow — Persistent & Predictive Signals", color='white', fontsize=14)

st.pyplot(fig)
