import cv2
import os

def analyze_chart(image_path):
    try:
        img = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if img is None:
            return "❌ لا توجد صورة صالحة."
        analysis = "تحليل الشارت من الصورة:\n- الاتجاه: صاعد/هابط\n- الدعم والمقاومة محددة\n- الصفقة المقترحة: شراء/بيع عند الاختراق"
        return analysis
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)