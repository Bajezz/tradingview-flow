import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# ================
# แสดงเฉพาะกราฟ (no extra outputs)
# ================

st.set_page_config(layout="wide")
st.title("📊 Flow Graph — กราฟอย่างเดียว")

# ---------- Input ----------
values_input = st.text_area("ค่าตัวเลข (คั่นด้วยช่องว่าง):",
                            "9 8 9 8 9 7 9 9 9 6 5 7 6 8 1 6 7 6 9 7 7 9 8 9")
colors_input = st.text_area("สีแท่ง (b=น้ำเงิน, r=แดง, g=เสมอ):",
                            "r r b r r r b b r b r b b b g b r r b b r r b r")

# ---------- Parse ----------
try:
    values = [float(x) for x in values_input.split() if x.strip()]
except Exception:
    st.error("❌ ตัวเลขไม่ถูกต้อง — ตรวจรูปแบบแล้วลองใหม่")
    st.stop()

colors_raw = [c.lower() for c in colors_input.split() if c.strip()]
# pad/truncate to match length
if len(colors_raw) < len(values):
    colors_raw += ["g"] * (len(values) - len(colors_raw))
elif len(colors_raw) > len(values):
    colors_raw = colors_raw[:len(values)]

color_map = {"b": "royalblue", "r": "crimson", "g": "limegreen"}
colors = [color_map.get(c, "gray") for c in colors_raw]

if len(values) < 3:
    st.warning("ต้องมีข้อมูลอย่างน้อย 3 ค่า")
    st.stop()

# ---------- Compute continuous flow positions ----------
bar_width = 0.8
scale = 0.5
tops = []
bottoms = []

for i, v in enumerate(values):
    height = v * scale
    if i == 0:
        bottom, top = 0.0, height
    else:
        prev_top = tops[-1]
        prev_bottom = bottoms[-1]
        # Use color of current bar to decide stacking direction,
        # but keep consistent continuous layout:
        c = colors_raw[i]
        if c == "b":           # blue -> stack upward
            bottom = prev_top
            top = bottom + height
        elif c == "r":         # red -> stack downward
            top = prev_bottom
            bottom = top - height
        else:                  # g or unknown -> flat (use prev)
            bottom, top = prev_bottom, prev_top
    bottoms.append(bottom)
    tops.append(top)

midpoints = [(t + b) / 2.0 for t, b in zip(tops, bottoms)]

# ---------- Find local min/max signals ----------
signals = []
for i in range(1, len(values) - 1):
    if values[i - 1] > values[i] < values[i + 1]:
        signals.append({"index": i, "type": "up"})
    elif values[i - 1] < values[i] > values[i + 1]:
        signals.append({"index": i, "type": "down"})

# ---------- Evaluate each signal by next bar color (for visual box) ----------
for s in signals:
    i = s["index"]
    if i + 1 >= len(colors_raw):
        s["result"] = "neutral"
    else:
        next_color = colors_raw[i + 1]
        if s["type"] == "up":
            s["result"] = "win" if next_color == "b" else ("lose" if next_color == "r" else "neutral")
        else:
            s["result"] = "win" if next_color == "r" else ("lose" if next_color == "b" else "neutral")

# ---------- Draw only the figure ----------
fig, ax = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor("#0e1117")
ax.set_facecolor("#0e1117")

# draw bars
for i, (b, t, c) in enumerate(zip(bottoms, tops, colors)):
    ax.add_patch(plt.Rectangle((i - bar_width / 2, b), bar_width, t - b,
                               color=c, ec="white", lw=0.5))

# draw midpoints line
ax.plot(range(len(midpoints)), midpoints, color="white", lw=0.8, alpha=0.4)

# annotate signals and draw result frame (green=win, red=lose, yellow=neutral)
for s in signals:
    i = s["index"]
    mid_y = midpoints[i]
    # arrow up/down
    if s["type"] == "up":
        ax.annotate("↑", (i, mid_y - 0.35), color="cyan", ha="center", fontsize=14, fontweight="bold")
    else:
        ax.annotate("↓", (i, mid_y + 0.35), color="orange", ha="center", fontsize=14, fontweight="bold")

    # result box color
    box_color = {"win": "lime", "lose": "red", "neutral": "yellow"}.get(s["result"], "yellow")
    ax.add_patch(plt.Rectangle((i - bar_width / 2, bottoms[i]), bar_width, tops[i] - bottoms[i],
                               fill=False, ec=box_color, lw=2))

# final formatting: only the graph
ax.set_xlim(-0.5, len(values) - 0.5)
ax.set_xticks(range(len(values)))
ax.set_xticklabels([str(i + 1) for i in range(len(values))], color="white")
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_edgecolor("#2a2f36")
ax.set_title("Flow Graph — (กรอบสี = ผลจากแท่งถัดไป)", color="white")

plt.tight_layout()
st.pyplot(fig)
