import cv2
import os

def analyze_chart(image_path):
    try:
        img = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if img is None:
            return "❌ لا توجد صورة صالحة."
        # مكان التحليل الفعلي (يمكنك توسعته لاحقاً)
        analysis = (
            "تحليل الشارت من الصورة:\n"
            "- الاتجاه: صاعد/هابط (تحليل مبدئي)\n"
            "- الدعم والمقاومة محددة (تقديري)\n"
            "- الصفقة المقترحة: شراء/بيع بناءً على التحليل\n"
            "- *ملاحظة*: التحليل الآلي قد لا يكون دقيقاً دائماً!"
        )
        return analysis
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)
