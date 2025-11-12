# --- พยากรณ์แท่งถัดไป ---
st.subheader("🔮 วิเคราะห์ข้อมูลเชิงพยากรณ์ — เลือกโมเดลทำนายอนาคต")

model_option = st.selectbox(
    "เลือกโมเดลที่ใช้พยากรณ์:",
    [
        "Polynomial Regression (สมการโค้ง)",
        "Exponential Smoothing (แนวโน้มเวลา)",
        "ML จากข้อมูล Google Sheets (เรียนรู้ย้อนหลัง)"
    ]
)

next_value = None
predicted_dir = None

try:
    lookback = min(len(values), 8)
    x = np.arange(lookback)
    y = np.array(values[-lookback:])

    if model_option.startswith("Polynomial"):
        # 🧮 Polynomial Regression
        degree = st.slider("เลือกองศาโค้ง Polynomial:", 1, 5, 3)
        coeffs = np.polyfit(x, y, degree)
        poly = np.poly1d(coeffs)
        next_value = poly(lookback)
        predicted_dir = "up" if next_value > y[-1] else "down"

    elif model_option.startswith("Exponential"):
        # 📊 Exponential Smoothing
        model = ExponentialSmoothing(y, trend="add", seasonal=None)
        fit = model.fit()
        next_value = fit.forecast(1)[0]
        predicted_dir = "up" if next_value > y[-1] else "down"

    elif model_option.startswith("ML"):
        # 🧠 Machine Learning จากข้อมูลย้อนหลัง
        if sheet is not None:
            records = sheet.get_all_values()
            data = []
            for row in records[1:]:
                try:
                    arr = eval(row[1])
                    if isinstance(arr, list):
                        data.append(arr)
                except:
                    pass

            values_all = np.array([v for sub in data for v in sub if isinstance(v, (int, float, float))])
            if len(values_all) > 10:
                X, y_ml = [], []
                for i in range(len(values_all) - 5):
                    X.append(values_all[i:i+5])
                    y_ml.append(values_all[i+5])
                model = LinearRegression().fit(X, y_ml)
                next_value = model.predict([values[-5:]])[0]
                predicted_dir = "up" if next_value > values[-1] else "down"
            else:
                st.warning("⚠️ ยังไม่มีข้อมูลในชีตมากพอสำหรับ ML (ต้องมากกว่า 10 ค่า)")
        else:
            st.warning("⚠️ ยังไม่เชื่อมต่อ Google Sheets")

except Exception as e:
    st.error("⚠️ เกิดข้อผิดพลาดในการพยากรณ์:")
    st.code(traceback.format_exc())

# --- สัญญาณล่วงหน้าแท่งล่าสุด ---
anticipate_signal = None
if len(values) >= 3:
    last3 = values[-3:]
    if last3[0] > last3[1] < last3[2]:
        anticipate_signal = "up"
    elif last3[0] < last3[1] > last3[2]:
        anticipate_signal = "down"
