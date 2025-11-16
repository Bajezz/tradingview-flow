# tradingview-flow.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(page_title="Flow Pro + TV Graph", layout="wide")

# =========================================================
# -------------  PART 1 : FLOW PRO AUTO MODE --------------
# =========================================================

# ------------------------- #
# Pattern detection helpers #
# ------------------------- #
def normalize(results):
    return [r for r in results if r in ("R","B")]

def longest_run_length(seq):
    if not seq:
        return 0
    max_run = 1
    cur = 1
    for i in range(1,len(seq)):
        if seq[i]==seq[i-1]:
            cur += 1
            if cur>max_run:
                max_run = cur
        else:
            cur = 1
    return max_run

def alternation_score(seq):
    if len(seq) < 2:
        return 0.0
    alt = 0
    for i in range(1,len(seq)):
        if seq[i] != seq[i-1]:
            alt += 1
    return alt / (len(seq)-1)

def block_score(seq, block=2):
    if len(seq) < block*2:
        return 0.0
    nblocks = len(seq)//block
    consistent = 0
    for i in range(nblocks):
        block_vals = seq[i*block:(i+1)*block]
        if all(x==block_vals[0] for x in block_vals):
            consistent += 1
    return consistent / max(1, nblocks)

def double_pair_score(seq):
    s2 = block_score(seq, 2)
    s3 = block_score(seq, 3)
    return max(s2, s3), 2 if s2>=s3 else 3

def detect_pattern(results):
    seq = normalize(results)
    details = {}
    n = len(seq)
    if n == 0:
        return "streak", 0.0, {"reason":"no data"}

    lr = longest_run_length(seq)
    alt = alternation_score(seq)
    dbl_score, dbl_block = double_pair_score(seq)

    details.update({
        "n":n,
        "longest_run":lr,
        "alt_ratio":round(alt,3),
        "double_score":round(dbl_score,3),
        "double_block":dbl_block
    })

    streak_score = min(1.0, (lr - 1) / max(1, min(6, n)))
    alternate_score = alt
    double_score = dbl_score

    scores = {
        "streak": round(streak_score,3),
        "alternate": round(alternate_score,3),
        "double_pair": round(double_score,3)
    }

    chosen = max(scores, key=lambda k: scores[k])
    confidence = scores[chosen]

    if max(scores.values()) < 0.35:
        chosen = "streak"
        confidence = max(scores.values())

    details["scores"] = scores
    return chosen, round(confidence,3), details

# ------------------------- #
# signal & simulate         #
# ------------------------- #
def generate_signal(results, mode="streak"):
    clean = [x for x in results if x in ["R", "B"]]
    if len(clean) < 1:
        return "R"

    signal = None

    if mode == "streak":
        if len(clean) >= 2 and clean[-1] == clean[-2]:
            signal = clean[-1]

    elif mode == "alternate":
        if len(clean) >= 2 and clean[-1] != clean[-2]:
            signal = "R" if clean[-1] == "B" else "B"

    elif mode == "double_pair":
        if len(clean) >= 4:
            if clean[-4] == clean[-3] and clean[-2] == clean[-1]:
                signal = "R" if clean[-1] == "B" else "B"

    if signal is None:
        signal = "R" if clean[-1] == "B" else "B"

    return signal

def simulate(results, mode, base_bet=5, max_m=6, balance=200):
    logs = []
    marti = 0

    for i in range(len(results)):
        past = results[:i]
        signal = generate_signal(past, mode)
        bet = base_bet * (2 ** marti)
        real = results[i]

        if real == "G":
            logs.append([i+1, signal, "เสมอ", bet, balance])
            continue

        if real == signal:
            balance += bet
            logs.append([i+1, signal, "ชนะ", bet, balance])
            marti = 0
        else:
            balance -= bet
            logs.append([i+1, signal, "แพ้", bet, balance])
            marti += 1
            if marti > max_m:
                break

    df = pd.DataFrame(logs, columns=["ไม้", "สัญญาณ", "ผล", "ไม้ทบ", "ทุนคงเหลือ"])
    next_signal = generate_signal(results, mode)
    next_bet = base_bet * (2 ** marti)
    df_next = pd.DataFrame([["NEXT", next_signal, "รอแทง", next_bet, balance]],
                           columns=["ไม้", "สัญญาณ", "ผล", "ไม้ทบ", "ทุนคงเหลือ"])
    return df, df_next, next_signal, next_bet

# =========================================================
# ------------------ UI : FLOW PRO ------------------------
# =========================================================

st.title("🎯 Flow Pro — Auto-Detect Table Pattern")

col1, col2 = st.columns([1,3])

with col1:
    st.subheader("⚙️ Settings")
    auto_mode = st.checkbox("เปิด Auto-Select สูตร (Auto)", value=True)
    manual_mode = st.selectbox("เลือกสูตร (ทับ Auto ได้)", ["(Auto)", "streak", "alternate", "double_pair"])
    base = st.number_input("ไม้แรก", 1, 9999, 5)
    balance = st.number_input("ทุนเริ่มต้น", 100, 999999, 150)
    max_m = st.number_input("ทบสูงสุด", 1, 10, 6)

with col2:
    st.subheader("📩 ป้อนผลย้อนหลัง (r/b/g)")
    raw_input = st.text_area("ผลย้อนหลัง:", "r r b b b r b r b")

results = [x.strip().upper() for x in raw_input.replace(",", " ").split() if x.strip() != ""]
clean = normalize(results)

detected, conf, details = detect_pattern(results)

# choose final mode
if auto_mode and manual_mode == "(Auto)":
    chosen_mode = detected
else:
    chosen_mode = manual_mode if manual_mode != "(Auto)" else detected

if len(results) > 0:
    df, df_next, next_signal, next_bet = simulate(results, chosen_mode, base, max_m, balance)

    total_rounds = len(df[df["ผล"] != "เสมอ"])
    win_rounds = len(df[df["ผล"] == "ชนะ"])
    win_rate = round((win_rounds / total_rounds) * 100, 2) if total_rounds > 0 else 0.0

    st.markdown(f"### 🏆 อัตราชนะ (Win Rate): **{win_rate}%**")
    st.markdown(f"## 📊 ผลทดสอบ — สูตรที่ใช้: **{chosen_mode.upper()}** {'(Auto)' if auto_mode else '(Manual)'}")
    st.markdown(f"### 🎯 สัญญาณตาถัดไป: **{next_signal}** — ไม้: **{next_bet}**")

else:
    st.info("ยังไม่มีข้อมูลย้อนหลัง — กรอก R/B/G แล้วระบบจะวิเคราะห์อัตโนมัติ")

# =========================================================
# ------------  PART 2 : FULL TRADINGVIEW GRAPH -----------
# =========================================================

st.markdown("---")
st.header("📊 TradingView Flow — กราฟวิเคราะห์แท่งจริง (แบบที่ 1)")

values_input = st.text_area("กรอกค่าตัวเลข:",
                            "9 9 6 8 8 8 8 8 8 7 6 9 6 8 9 4 6 5 8 9 2 9 6 1 5")
colors_input = st.text_area("กรอกสี (b,r,g):",
                            "b r b r b b b b r b r r b r r r b b b r r r b g b")

try:
    values = [float(x) for x in values_input.split() if x.strip()]
except ValueError:
    st.error("❌ กรุณากรอกค่าตัวเลขให้ถูกต้อง")
    st.stop()

colors_raw = colors_input.split()
if len(colors_raw) < len(values):
    colors_raw += ["gray"] * (len(values) - len(colors_raw))
elif len(colors_raw) > len(values):
    colors_raw = colors_raw[:len(values)]

color_map = {'b':'royalblue', 'r':'crimson','g':'limegreen'}
colors = [color_map.get(c.lower(),"gray") for c in colors_raw]

if len(values) < 3:
    st.warning("ต้องมีข้อมูลอย่างน้อย 3 ค่า")
    st.stop()

bar_width = 0.8
scale = 0.5
tops, bottoms = [], []

for i,(v,c) in enumerate(zip(values, colors)):
    h = v*scale
    if i==0:
        bottom, top = 0, h
    else:
        pc = colors[i-1]
        prev_top, prev_bottom = tops[-1], bottoms[-1]

        if c=='royalblue':
            bottom = prev_top if pc=='royalblue' else prev_bottom
            top = bottom + h

        elif c=='crimson':
            top = prev_top if pc=='royalblue' else prev_bottom
            bottom = top - h

        elif c=='limegreen':
            bottom = prev_top if pc in ['royalblue','limegreen'] else prev_bottom
            top = bottom + h*1.2

        else:
            bottom, top = prev_bottom, prev_top

    tops.append(top)
    bottoms.append(bottom)

midpoints = [(t+b)/2 for t,b in zip(tops,bottoms)]

if "signals" not in st.session_state:
    st.session_state.signals = []

# Generate past signals
for i in range(1,len(values)-1):
    if values[i-1] > values[i] < values[i+1]:
        if not any(s["index"]==i for s in st.session_state.signals):
            st.session_state.signals.append({"index":i,"type":"up","correct":None})
    elif values[i-1] < values[i] > values[i+1]:
        if not any(s["index"]==i for s in st.session_state.signals):
            st.session_state.signals.append({"index":i,"type":"down","correct":None})

for s in st.session_state.signals:
    i = s["index"]
    if i < len(values)-1:
        future = values[i+1] - values[i]
        s["correct"] = (future>0) if s["type"]=="up" else (future<0)

up_acc_list = [s["correct"] for s in st.session_state.signals if s["type"]=="up" and s["correct"] is not None]
down_acc_list = [s["correct"] for s in st.session_state.signals if s["type"]=="down" and s["correct"] is not None]
up_acc = (sum(up_acc_list)/len(up_acc_list)*100) if up_acc_list else 0
down_acc = (sum(down_acc_list)/len(down_acc_list)*100) if down_acc_list else 0

# Prediction next bar
lookback = min(len(values),6)
x = np.arange(lookback)
y = np.array(values[-lookback:])
a,b = np.polyfit(x,y,1)
next_value = a*lookback + b
predicted_dir = "up" if next_value > y[-1] else "down"

# Anticipate current bar
anticipate_signal = None
if len(values)>=3:
    last3 = values[-3:]
    if last3[0] > last3[1] < last3[2]:
        anticipate_signal = "up"
    elif last3[0] < last3[1] > last3[2]:
        anticipate_signal = "down"

# ----------------- DRAW CHART -----------------
fig, ax = plt.subplots(figsize=(14,6))
fig.patch.set_facecolor('#0e1117')
ax.set_facecolor('#0e1117')

for i,(top,bottom,c) in enumerate(zip(tops,bottoms,colors)):
    ax.add_patch(plt.Rectangle((i-bar_width/2, bottom),
                               bar_width, top-bottom,
                               color=c, ec='white', lw=0.5, alpha=0.9))

ax.plot(range(len(midpoints)), midpoints, color='white', linewidth=0.8, alpha=0.4)

for s in st.session_state.signals:
    i = s["index"]
    if i < len(midpoints):
        if s["type"]=="up":
            ax.annotate('↑', (i, midpoints[i]), (i, midpoints[i]-0.35),
                        color='lime', ha='center', fontsize=16, fontweight='bold')
        else:
            ax.annotate('↓', (i, midpoints[i]), (i, midpoints[i]+0.35),
                        color='red', ha='center', fontsize=16, fontweight='bold')

if anticipate_signal:
    i = len(values)-1
    if anticipate_signal=="up":
        ax.annotate('↑', (i,midpoints[i]), (i,midpoints[i]-0.5),
                    color='cyan', ha='center', fontsize=20, fontweight='bold')
    else:
        ax.annotate('↓', (i,midpoints[i]), (i,midpoints[i]+0.5),
                    color='orange', ha='center', fontsize=20, fontweight='bold')

ax.annotate('↑' if predicted_dir=="up" else '↓',
            (len(values), midpoints[-1]),
            (len(values), midpoints[-1] + (0.5 if predicted_dir=="up" else -0.5)),
            color='lime' if predicted_dir=="up" else 'red',
            ha='center', fontsize=22, fontweight='bold')

ax.set_xlim(-0.5, len(values)+0.5)
ax.set_xticks(range(len(values)))
ax.set_xticklabels([str(i+1) for i in range(len(values))], color='white', fontsize=9)
ax.set_yticks([])

for s in ax.spines.values():
    s.set_edgecolor('#2a2f36')

ax.text(len(values)-1, max(tops)*1.05,
        f"📈 Up: {up_acc:.1f}%   📉 Down: {down_acc:.1f}%",
        color='white', ha='right', fontsize=12)

ax.set_title("TradingView Flow — สัญญาณล่วงหน้าแบบที่ 1", color='white', fontsize=14)

plt.tight_layout()
st.pyplot(fig)
