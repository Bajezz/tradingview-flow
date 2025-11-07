import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="TradingView Flow", layout="centered")

st.title("📊 TradingView-Style Flow Chart")
st.write("ป้อนค่าตัวเลขและสี (b = blue, r = red) เพื่อสร้างกราฟ")

# --- ใช้ session_state เพื่อจำค่าที่เคยพิมพ์ไว้ ---
if "values_input" not in st.session_state:
    st.session_state.values_input = "8 6 5 7 9 8 7"
if "colors_input" not in st.session_state:
    st.session_state.colors_input = "b r r b r b r"

values_input = st.text_input("กรอกค่าตัวเลข (เช่น 8 6 5 7 9):", st.session_state.values_input)
colors_input = st.text_input("กรอกสี (b/r) ตามจำนวนตัวเลข:", st.session_state.colors_input)

# อัปเดตค่าที่พิมพ์ล่าสุดกลับเข้า session_state
st.session_state.values_input = values_input
st.session_state.colors_input = colors_input

# --- แปลงข้อมูล ---
values = [int(v) for v in values_input.split()]
colors = ["blue" if c.lower() == "b" else "red" for c in colors_input.split()]

# --- เริ่มสร้างกราฟ ---
plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(10,6))

bar_width = 0.8
scale = 0.5

tops = []
bottoms = []

for i, (v, c) in enumerate(zip(values, colors)):
    height = v * scale
    if i == 0:
        bottom, top = 0, height
    else:
        prev_color = colors[i-1]
        prev_top = tops[-1]
        prev_bottom = bottoms[-1]
        if c == "blue":
            bottom = prev_top if prev_color == "blue" else prev_bottom
            top = bottom + height
        else:  # red
            top = prev_top if prev_color == "blue" else prev_bottom
            bottom = top - height
    tops.append(top)
    bottoms.append(bottom)

# --- วาดแท่ง ---
for i, (v, c, top, bottom) in enumerate(zip(values, colors, tops, bottoms)):
    color = "royalblue" if c == "blue" else "crimson"
    height = top - bottom
    rect = plt.Rectangle((i - bar_width/2, bottom), bar_width, height,
                         color=color, ec="white", lw=0.6, alpha=0.9)
    ax.add_patch(rect)
    ax.text(i, bottom + height/2, str(v), color="white",
            ha="center", va="center", fontsize=12, fontweight="bold")

midpoints = [(t + b)/2 for t, b in zip(tops, bottoms)]
ax.plot(range(len(values)), midpoints, color="white", linewidth=0.8, alpha=0.5)

# --- ปรับแต่งกราฟ ---
ax.set_xlim(-0.5, len(values)-0.5)
ax.set_facecolor("#0e1117")
ax.grid(True, linestyle="--", color="gray", alpha=0.3)
ax.set_xticks(range(len(values)))
ax.set_xticklabels([str(i+1) for i in range(len(values))])
ax.set_yticks([])
ax.set_title("TradingView-Style Flow (จำค่าที่พิมพ์ล่าสุดได้)", color="white", fontsize=14)

st.pyplot(fig)
