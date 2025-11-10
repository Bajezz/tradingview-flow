import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(layout="wide")
st.title("📊 TradingView Flow — ระบบแนวรับแนวต้านอัจฉริยะ (สวนมนุษย์)")

# --- Input ---
values_input = st.text_input("กรอกค่าตัวเลข (เช่น 8 6 5 7 9 8):", "8 6 5 7 9 8 10 9 11 10")
colors_input = st.text_input("กรอกสี (b=blue, r=red, g=green เช่น b r g b g):", "b r g b g r g g r")

# --- Parse input ---
try:
    values = [float(x) for x in values_input.split() if x.strip() != ""]
except ValueError:
    st.error("❌ กรุณากรอกค่าตัวเลขให้ถูกต้อง")
    st.stop()

colors_raw = [c for c in colors_input.split() if c.strip() != ""]
if len(colors_raw) < len(values):
    colors_raw += ["gray"] * (len(values) - len(colors_raw))
elif len(colors_raw) > len(values):
    colors_raw = colors_raw[:len(values)]

color_map = {'b': 'royalblue', 'r': 'crimson', 'g': 'limegreen'}
colors = [color_map.get(c.lower(), 'gray') for c in colors_raw]

if len(values) < 3:
    st.warning("ต้องมีข้อมูลอย่างน้อย 3 ค่าเพื่อวิเคราะห์แนวรับแนวต้าน")
    st.stop()

# --- เตรียมคำนวณแท่ง ---
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

midpoints = [(t + b) / 2 for t, b in zip(tops, bottoms)]

# --- หาจุดแนวรับแนวต้านจากโครงสร้าง ---
resistance_levels = []
support_levels = []
for i in range(1, len(midpoints) - 1):
    if midpoints[i] > midpoints[i - 1] and midpoints[i] > midpoints[i + 1]:
        resistance_levels.append((i, midpoints[i]))
    elif midpoints[i] < midpoints[i - 1] and midpoints[i] < midpoints[i + 1]:
        support_levels.append((i, midpoints[i]))

# --- วาดกราฟ ---
fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor('#0e1117')
ax.set_facecolor('#0e1117')

for i, (v, c, top, bottom) in enumerate(zip(values, colors, tops, bottoms)):
    ax.add_patch(plt.Rectangle((i - bar_width / 2, bottom),
                               bar_width, top - bottom,
                               color=c, ec='white', lw=0.6, alpha=0.9))
    ax.text(i, (top + bottom) / 2, str(v),
            color='white', ha='center', va='center', fontsize=11, fontweight='bold')

ax.plot(range(len(midpoints)), midpoints, color='white', linewidth=0.8, alpha=0.5)

# --- แสดงแนวรับแนวต้าน ---
for idx, level in resistance_levels:
    ax.axhline(level, color='red', linestyle='--', linewidth=1, alpha=0.4)
for idx, level in support_levels:
    ax.axhline(level, color='lime', linestyle='--', linewidth=1, alpha=0.4)

# --- พื้นที่สวนมนุษย์ (Contrarian Zone) ---
current = midpoints[-1]
nearest_res = min(resistance_levels, key=lambda x: abs(x[1] - current), default=None)
nearest_sup = min(support_levels, key=lambda x: abs(x[1] - current), default=None)

if nearest_res and abs(nearest_res[1] - current) < 0.3:
    ax.annotate('🔻 SHORT ZONE', xy=(len(values) - 1, current),
                xytext=(len(values) - 1, current + 0.6),
                color='red', fontsize=13, fontweight='bold', ha='center')
elif nearest_sup and abs(nearest_sup[1] - current) < 0.3:
    ax.annotate('🔺 LONG ZONE', xy=(len(values) - 1, current),
                xytext=(len(values) - 1, current - 0.6),
                color='lime', fontsize=13, fontweight='bold', ha='center')

# --- ตกแต่ง ---
ax.set_xlim(-0.5, len(values) + 0.5)
ax.set_xticks(range(len(values)))
ax.set_xticklabels([str(i + 1) for i in range(len(values))], color='white')
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_edgecolor('#2a2f36')
ax.set_title("Smart Support/Resistance + Contrarian Signal", color='white', fontsize=14)

plt.tight_layout()
st.pyplot(fig)
