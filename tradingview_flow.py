import cv2
import pytesseract
from PIL import Image
import numpy as np

st.sidebar.header("🖼️ อ่านข้อมูลจากภาพ")
uploaded_file = st.sidebar.file_uploader("อัปโหลดภาพตารางผล (PNG/JPG):", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    img_np = np.array(image)
    img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    st.image(image, caption="📸 ภาพที่อัปโหลด", use_column_width=True)

    # --- ตรวจจับวงกลม ---
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=20,
                               param1=100, param2=20, minRadius=10, maxRadius=40)

    values_detected, colors_detected = [], []

    if circles is not None:
        circles = np.uint16(np.around(circles[0, :]))
        detected_data = []

        for (x, y, r) in circles:
            # Crop วงกลมเฉพาะบริเวณ
            crop = img_cv[y - r:y + r, x - r:x + r]
            if crop.size == 0:
                continue

            # อ่านตัวเลขในวงกลม
            num = pytesseract.image_to_string(crop, config="--psm 10 digits").strip()
            if not num.isdigit():
                continue

            # วิเคราะห์สีโดยดูค่าเฉลี่ยรอบขอบ
            border_color = np.mean([
                img_cv[y - r, x], img_cv[y + r, x],
                img_cv[y, x - r], img_cv[y, x + r]
            ], axis=0)

            b, g, r_c = border_color
            if r_c > 150 and r_c > g and r_c > b:
                color = 'r'
            elif b > 150 and b > g and b > r_c:
                color = 'b'
            elif g > 150 and g > r_c and g > b:
                color = 'g'
            else:
                color = 'gray'

            detected_data.append((x, y, int(num), color))

        # --- เรียงจากซ้ายไปขวา, บนลงล่าง ---
        detected_data.sort(key=lambda c: (c[0] // 100, c[1]))

        values_detected = [d[2] for d in detected_data]
        colors_detected = [d[3] for d in detected_data]

        st.success("✅ อ่านข้อมูลจากภาพสำเร็จ!")
        st.write("**ค่าที่อ่านได้:**", values_detected)
        st.write("**สีที่อ่านได้:**", colors_detected)

        # ใส่ค่าแทน input เดิม
        values_input = " ".join(map(str, values_detected))
        colors_input = " ".join(colors_detected)

    else:
        st.error("❌ ไม่พบวงกลมในภาพ — ลองใช้ภาพที่ชัดกว่านี้")

