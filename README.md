# Live Trade Contract Scanner Bot

بوت مبدئي لاكتشاف فرص عقود الأوبشن منخفضة السعر مع "برج سيولة" وفق الاستراتيجية التي وصفتها.

## ما الذي يفعله هذا الإصدار؟
- يقرأ بيانات الشموع لعقود الأوبشن (OHLCV) على فريم 1 ساعة (ويمكن 15 دقيقة).
- يطبق شروط الدخول الأساسية:
  - السعر في نطاق منخفض.
  - مسار عرضي ضيق (10–20 سنت).
  - وجود دوجي.
  - فوليوم مفاجئ (برج سيولة) 1500+.
- يطبق شروط تأكيد إضافية:
  - دايفرجنس RSI (نسخة مبسطة).
  - هامر.
  - كسر قاع شمعة السيولة ثم ارتداد.
- يطبق فلتر سيولة مخادعة مبسط:
  - إذا كان فوليوم PUT عاليًا مع فوليوم أسهم مرتفع جدًا لصالح شراء السهم، يتم خفض الثقة.
- يتابع عدة سترايكات ويختار أفضل الإشارات.

## التشغيل
```bash
python bot.py --input sample_data.json --timeframe 1h
```

## شكل البيانات
راجع `sample_data.json`.

## ملاحظة
هذا النموذج تعليمي/بحثي فقط وليس نصيحة استثمارية.


## منصة احترافية (Web Dashboard)
لتشغيل واجهة احترافية تعرض الشركات والعقود والصفقات المقترحة:

```bash
python dashboard.py --input sample_data.json --timeframe 1h --port 8080
```

ثم افتح:
`http://localhost:8080`

### API بسيط
- `GET /api/data` يعيد نفس بيانات المنصة بصيغة JSON.


## حل مشكلة ERR_CONNECTION_REFUSED
إذا ظهرت رسالة `localhost refused to connect` فهذا غالبًا يعني أن السيرفر غير شغّال أو اشتغل على بورت مختلف.

### 1) شغّل المنصة من نفس مجلد المشروع
```bash
python dashboard.py --input sample_data.json --timeframe 1h --host 127.0.0.1 --port 8080
```

### 2) افتح الرابط الصحيح
- `http://127.0.0.1:8080`
- أو `http://localhost:8080`

### 3) إذا البورت محجوز
```bash
python dashboard.py --input sample_data.json --timeframe 1h --host 127.0.0.1 --port 8081
```
ثم افتح `http://127.0.0.1:8081`.

### 4) تأكد أن الملف موجود
يجب أن يكون `sample_data.json` موجودًا في نفس المجلد أو استخدم مساره الكامل.


## حل مشكلة `python: can't open file ... dashboard.py`
هذا يعني أنك لست داخل نسخة المشروع الصحيحة أو النسخة قديمة/ناقصة.

1) تأكد من الملفات داخل المجلد (Windows):
```bat
dir
```
لازم تشوف `dashboard.py` و `bot.py` و `sample_data.json`.

2) افحص النسخة بسرعة:
```bash
python verify_install.py
```

3) إذا الملف غير موجود، حدّث النسخة:
```bat
git pull
git checkout main
```

4) ثم شغّل المنصة:
```bat
python dashboard.py --input sample_data.json --timeframe 1h --host 127.0.0.1 --port 8080
```
