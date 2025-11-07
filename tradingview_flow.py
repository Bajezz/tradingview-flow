import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="TradingView Flow", layout="wide")

st.title("📊 TradingView-Style Flow Builder")
st.markdown("ใส่ตัวเลขและสี (น้ำเงิน=น, แดง=ด) แล้วดูกราฟต่อแท่งอัตโนมัติ")

# ===== Input =====
values_str = st.text_input("ใส่ตัวเลข (คั่นด้วยช่องว่าง):", "8 6 5 6 5 7 7 6 5 9 6 1 6 8 7 9 8 7 9 7 9 5")
colors_str = st.text_input("ใส่สี (น สำหรับน้ำเงิน, ด สำหรับแดง):", "น ด ด น น น น ด ด น น น ด น น ด น น ด น ด น")

if st.button("แสดงกราฟ"):
    try:
        values = list(map(int, values_str.split()))
        colors = ['blue' if c == 'น' else 'red' for c in colors_str.split()]

        if len(values) != len(colors):
            st.error("❌ จำนวนตัวเลขและสีต้องเท่ากัน")
        else:
            plt.style.use('dark_background')
            fig, ax = plt.subplots(figsize=(10,6))

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
                        if prev_color == 'blue':
                            bottom = prev_top
                        else:
                            bottom = prev_bottom
                        top = bottom + height
                        
                    elif c == 'red':
                        if prev_color == 'blue':
                            top = prev_top
                            bottom = top - height
                        else:
                            top = prev_bottom
                            bottom = top - height
                
                tops.append(top)
                bottoms.append(bottom)

            for i, (v, c, top, bottom) in enumerate(zip(values, colors, tops, bottoms)):
                color = 'royalblue' if c == 'blue' else 'crimson'
                height = top - bottom
                rect = plt.Rectangle((i - bar_width/2, bottom),
                                     bar_width, height,
                                     color=color, ec='white', lw=0.6, alpha=0.9)
                ax.add_patch(rect)
                ax.text(i, bottom + height/2, str(v),
                        color='white', ha='center', va='center',
                        fontsize=12, fontweight='bold')

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
    except Exception as e:
        st.error(f"⚠️ เกิดข้อผิดพลาด: {e}")
