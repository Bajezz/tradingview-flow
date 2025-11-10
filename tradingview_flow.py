import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(layout="wide")
st.title("📊 TradingView Flow — แนวรับแนวต้าน + โซนสวนมนุษย์ (Stable Edition)")

# --- Input ---
values_input = st.text_area("กรอกค่าตัวเลข (เช่น 8 6 5 7 9 8 10 9 11 10):",
                            "8 6 5 7 9 8 10 9 11 10 12 11 13 14 13 15 14 16 17 18 17 16 15 14 13")
colors_input = st.text_area("กรอกสี (b=blue, r=red, g=green):",
                            "b r g b g r g g r b b g b r g g g r b r g b g r g")

# --- Parse input ---
try:
    values = [float(x) for x in values_input.split() if x.strip()]
except ValueError:
    st.error("❌ กรุณากรอกค่าตัวเลขให้ถูกต้อง")
    st.stop()

colors_raw = [c for c in colors_input.split() if c.strip()]
if len(colors_raw) < len(values):
    colors_raw += ["gray"] * (len(values) - len(colors_raw))
elif len(colors_raw) > len(values):
    colors_raw = colors_raw[:len(values)]

color_map = {'b': 'royalblue', 'r': 'crimson', 'g': 'limegreen'}
colors = [color_map.get(c.lower(), 'gray') for c in colors_raw]

if len(values) < 3:
    st.warning("ต้องมีข้อมูลอย่างน้อย 3 ค่าเพื่อวิเคราะห์แนวรับแนวต้าน")
    st.stop()

# --- เตรียมข้อมูลแท่ง ---
bar_width = 0.8
scale = 0.5
tops, bottoms = [], []
for i, (v, c) in enumerate(zip(values, colors)):
    height = v * scale
    if i == 0:
        bottom, top = 0, height
    else:
        prev_color = colors[i - 1]
        prev_top, prev_bottom = tops[-1], bottoms[-1]
        if c == 'royalblue':
            bottom = prev_top if prev_color == 'royalblue' else prev_bottom
            top = bottom + height
        elif c == 'crimson':
            top = prev_top if prev_color == 'royalblue' else prev_bottom
            bottom = top - height
        elif c == 'limegreen':
            bottom = prev_top if prev_color in ['royalblue', 'limegreen'] else prev_bottom
            top = bottom + height * 1.2
        else:
            bottom, top = prev_bottom, prev_top
    tops.append(top)
    bottoms.append(bottom)

midpoints = np.array([(t + b) / 2 for t, b in zip(tops, bottoms)])

# --- หาจุดแนวรับแนวต้าน ---
resistance_levels, support_levels = [], []
for i in range(1, len(midpoints) - 1):
    if midpoints[i] > midpoints[i - 1] and midpoints[i] > midpoints[i + 1]:
        resistance_levels.append((i, midpoints[i]))
    elif midpoints[i] < midpoints[i - 1] and midpoints[i] < midpoints[i + 1]:
        support_levels.append((i, midpoints[i]))

# --- วาดกราฟ ---
fig, ax = plt.subplots(figsize=(15, 7))
fig.patch.set_facecolor('#0e1117')
ax.set_facecolor('#0e1117')

for i, (v, c, top, bottom) in enumerate(zip(values, colors, tops, bottoms)):
    ax.add_patch(plt.Rectangle((i - bar_width / 2, bottom),
                               bar_width, top - bottom,
                               color=c, ec='white', lw=0.5, alpha=0.9))
    if len(values) <= 50:  # ถ้าข้อมูลเยอะไม่ต้องแสดงตัวเลข
        ax.text(i, (top + bottom) / 2, str(v),
                color='white', ha='center', va='center', fontsize=9)

ax.plot(range(len(midpoints)), midpoints, color='white', linewidth=0.8, alpha=0.5)

# --- แสดงแนวรับแนวต้าน ---
for _, level in resistance_levels:
    ax.axhline(level, color='red', linestyle='--', linewidth=0.8, alpha=0.4)
for _, level in support_levels:
    ax.axhline(level, color='lime', linestyle='--', linewidth=0.8, alpha=0.4)

# --- ตรวจหาโซนสวนมนุษย์ ---
current_price = midpoints[-1]
if len(midpoints) > 2:
    avg_range = np.mean(np.abs(np.diff(midpoints)))
else:
    avg_range = 1
threshold = avg_range * 1.5

nearest_res = min(resistance_levels, key=lambda x: abs(x[1] - current_price), default=None)
nearest_sup = min(support_levels, key=lambda x: abs(x[1] - current_price), default=None)

# ป้องกันกรณีไม่มีแนวรับแนวต้านเลย
if nearest_res and abs(nearest_res[1] - current_price) < threshold:
    ax.annotate("🔻 SHORT ZONE",
                xy=(len(values) - 1, current_price),
                xytext=(len(values) - 1, current_price + avg_range),
                color='red', fontsize=14, fontweight='bold', ha='center')
    ax.axhspan(nearest_res[1] - avg_range/2, nearest_res[1] + avg_range/2,
               color='red', alpha=0.12)
elif nearest_sup and abs(nearest_sup[1] - current_price) < threshold:
    ax.annotate("🔺 LONG ZONE",
                xy=(len(values) - 1, current_price),
                xytext=(len(values) - 1, current_price - avg_range),
                color='lime', fontsize=14, fontweight='bold', ha='center')
    ax.axhspan(nearest_sup[1] - avg_range/2, nearest_sup[1] + avg_range/2,
               color='lime', alpha=0.12)

# --- ตกแต่ง ---
ax.set_xlim(-0.5, len(values) - 0.5)
ax.set_xticks(range(0, len(values), max(1, len(values)//20)))
ax.set_xticklabels([str(i+1) for i in range(0, len(values), max(1, len(values)//20))], color='white')
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_edgecolor('#2a2f36')
ax.set_title("Smart Support/Resistance + Contrarian Zone", color='white', fontsize=14)

plt.tight_layout()
st.pyplot(fig)
