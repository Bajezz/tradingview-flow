import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(layout="wide")
st.title("📊 TradingView Flow Visualizer — Persistent Predictive Signals (Fixed)")

# --- Input ---
values_input = st.text_input("กรอกค่าตัวเลข (เช่น 8 6 5 7 9 8):",
                            "8 6 5 7 9 8 10 9 11 10")
colors_input = st.text_input("กรอกสี (b=blue, r=red, g=green เช่น b r g b g):",
                             "b r g b g r g g r")

# --- Parse input safely ---
try:
    values = [float(x) for x in values_input.split() if x.strip() != ""]
except ValueError:
    st.error("กรุณากรอกค่าตัวเลขให้ถูกต้อง (คั่นด้วยช่องว่าง)")
    st.stop()

colors_raw = [c for c in colors_input.split() if c.strip() != ""]
# align lengths
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

if len(values) < 2:
    st.warning("ต้องกรอกข้อมูลอย่างน้อย 2 ค่าเพื่อให้แอปทำงาน")
    st.stop()

# --- Compute bars (tops & bottoms) ---
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
            # fallback (copy previous)
            bottom, top = prev_bottom, prev_top

    tops.append(top)
    bottoms.append(bottom)

# midpoints (same length as values)
midpoints = [(t + b) / 2.0 for t, b in zip(tops, bottoms)]

# --- session_state for persistent predictions ---
if "predictions" not in st.session_state:
    st.session_state.predictions = []  # list of dicts: {'bar_index': int, 'direction': 'ขึ้น'/'ลง', 'pred_value': float}

# Remove predictions that are out of range (in case user reduced input)
st.session_state.predictions = [p for p in st.session_state.predictions if p["bar_index"] < len(values)]

# --- Compute current predictive signal (based on lookback slope) ---
lookback = min(5, len(values))
x = np.arange(lookback)
y = np.array(values[-lookback:])
if len(y) >= 2:
    a, b = np.polyfit(x, y, 1)
    next_value = a * lookback + b
    predicted_direction = "ขึ้น" if next_value > y[-1] else "ลง"
else:
    next_value = y[-1]
    predicted_direction = "คงที่"

# persist prediction for this bar (bar_index = last observed bar)
current_bar_index = len(values) - 1
# only append if not already have a prediction for this bar
if not any(p["bar_index"] == current_bar_index for p in st.session_state.predictions):
    st.session_state.predictions.append({
        "bar_index": current_bar_index,
        "direction": predicted_direction,
        "pred_value": float(next_value),
        "at_value": float(y[-1])
    })

# --- Plotting ---
fig, ax = plt.subplots(figsize=(12, 6))
# set dark background for figure and axes
fig.patch.set_facecolor('#0e1117')
ax.set_facecolor('#0e1117')

color_map = {'blue': 'royalblue', 'red': 'crimson', 'green': 'limegreen'}
for i, (v, c, top, bottom) in enumerate(zip(values, colors, tops, bottoms)):
    color = color_map.get(c, 'gray')
    ax.add_patch(plt.Rectangle((i - bar_width / 2, bottom),
                               bar_width, top - bottom,
                               color=color, ec='white', lw=0.6, alpha=0.95))
    ax.text(i, (top + bottom) / 2, str(v),
            color='white', ha='center', va='center', fontsize=11, fontweight='bold')

# midpoints line
ax.plot(range(len(midpoints)), midpoints, color='white', linewidth=0.9, alpha=0.6)

# --- Real reversal signals (past, actual) ---
for i in range(1, len(values) - 1):
    # low (valley)
    if values[i - 1] > values[i] < values[i + 1]:
        ax.annotate('↑', xy=(i, midpoints[i]), xytext=(i, midpoints[i] - 0.35),
                    color='lime', ha='center', fontsize=16, fontweight='bold')
    # high (peak)
    elif values[i - 1] < values[i] > values[i + 1]:
        ax.annotate('↓', xy=(i, midpoints[i]), xytext=(i, midpoints[i] + 0.35),
                    color='red', ha='center', fontsize=16, fontweight='bold')

# --- Draw all persisted predictive signals (they remain even after updates) ---
for p in st.session_state.predictions:
    idx = p["bar_index"]
    if 0 <= idx < len(midpoints):
        offset = 0.45 if p["direction"] == "ขึ้น" else -0.45
        color = 'lime' if p["direction"] == "ขึ้น" else 'red'
        # use a smaller/sem-transparent arrow to show it's a prediction made at that bar
        ax.annotate('↑' if p["direction"] == "ขึ้น" else '↓',
                    xy=(idx, midpoints[idx]),
                    xytext=(idx, midpoints[idx] + offset),
                    color=color, ha='center', fontsize=18, fontweight='bold', alpha=0.7)

# --- Also show the latest prediction as an arrow extended to future (optional) ---
# place at x = len(values) (future position) with semi transparency
future_x = len(values)
future_y_base = midpoints[-1]
future_offset = 0.45 if predicted_direction == "ขึ้น" else -0.45
ax.annotate('↑' if predicted_direction == "ขึ้น" else '↓',
            xy=(future_x - 0.2, future_y_base),
            xytext=(future_x - 0.2, future_y_base + future_offset),
            color=('lime' if predicted_direction == "ขึ้น" else 'red'),
            ha='center', fontsize=20, fontweight='bold', alpha=0.45)
# dashed line to indicate the predicted level
ax.plot([len(values) - 1, future_x - 0.2], [future_y_base, future_y_base + future_offset],
        linestyle='--', color=('lime' if predicted_direction == "ขึ้น" else 'red'), alpha=0.4)

# --- Axes styling so dark theme shows correctly ---
ax.set_xlim(-0.5, len(values) + 0.5)
ax.set_xticks(range(len(values)))
ax.set_xticklabels([str(i + 1) for i in range(len(values))], color='white')
ax.set_yticks([])
ax.tick_params(axis='x', colors='white')
for spine in ax.spines.values():
    spine.set_edgecolor('#2a2f36')

ax.set_title("TradingView Flow — Persistent Predictive Signals (fixed)", color='white', fontsize=14)

# --- Display numeric prediction summary and control buttons ---
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"**🔮 พยากรณ์แท่งถัดไป (คำนวณจาก {lookback} จุดล่าสุด):** `{next_value:.3f}`")
    st.markdown(f"**📈 สัญญาณล่วงหน้า (ปัจจุบัน):** **{predicted_direction}**")
with col2:
    if st.button("🗑 ล้างประวัติสัญญาณ"):
        st.session_state.predictions = []
        st.experimental_rerun()

# --- Show history table for easy stats collection ---
if st.session_state.predictions:
    st.markdown("### 📜 ประวัติสัญญาณที่ถูกบันทึก (prediction made at bar)")
    # show in order
    for p in st.session_state.predictions:
        st.write(f"- แท่งที่ {p['bar_index']+1} → พยากรณ์ **{p['direction']}**, ณ ค่า {p['at_value']:.3f}, ทำนาย next {p['pred_value']:.3f}")

plt.tight_layout()
st.pyplot(fig)
