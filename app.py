"""
بوت تتبع المواقع - Telegram Location Tracking Bot
نسخة subprocess تعمل على Render
البوت: @cccc00bot
"""

from flask import Flask, jsonify
import logging
import os
import sys
import subprocess
import time

# ========== إعدادات Logging ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

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
        <br><br>
        <a href="/start_bot">▶️ تشغيل البوت</a>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'bot': '@cccc00bot',
        'bot_running': True,
        'service': 'telegram-tracking-bot'
    })

@app.route('/start_bot')
def start_bot():
    """تشغيل البوت يدوياً"""
    try:
        # تشغيل البوت في عملية منفصلة
        bot_process = subprocess.Popen(
            [sys.executable, '-c', """
import telebot
import os
import time

BOT_TOKEN = os.environ.get('BOT_TOKEN', '8059073897:AAHpGwkzSvXmiUpJpahG0tt922D9nZ2zylI')
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='Markdown')

print("🚀 بدء تشغيل البوت...")
print(f"🤖 البوت: @cccc00bot")

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ *البوت يعمل على Render!*")

@bot.message_handler(commands=['newlink'])
def newlink(message):
    bot.reply_to(message, "🔗 *رابط التتبع قريباً*")

@bot.message_handler(commands=['ping'])
def ping(message):
    bot.reply_to(message, "🏓 *Pong!* البوت نشط ✅")

print("🎯 بدء استقبال الرسائل...")
bot.infinity_polling(timeout=30, long_polling_timeout=30)
            """],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # قراءة الإخراج في الخلفية
        def read_output():
            for line in bot_process.stdout:
                logger.info(f"🤖 البوت: {line.strip()}")
        
        import threading
        output_thread = threading.Thread(target=read_output, daemon=True)
        output_thread.start()
        
        logger.info("✅ بدأ تشغيل البوت في عملية منفصلة")
        return jsonify({
            'success': True,
            'message': 'تم تشغيل البوت',
            'pid': bot_process.pid
        })
        
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل البوت: {e}")
        return jsonify({'error': str(e)}), 500

# ========== بدء البوت تلقائياً ==========
def auto_start_bot():
    """تشغيل البوت تلقائياً عند البدء"""
    time.sleep(5)  # انتظار Flask ليبدأ أولاً
    logger.info("🔧 محاولة تشغيل البوت تلقائياً...")
    
    # محاولة تشغيل البوت
    try:
        import requests
        response = requests.get('https://telegram-tracking-bot-35hp.onrender.com/start_bot', timeout=10)
        if response.status_code == 200:
            logger.info("✅ تم تشغيل البوت بنجاح")
        else:
            logger.warning("⚠️ لم يتم تشغيل البوت تلقائياً")
    except:
        logger.info("ℹ️ البوت يحتاج تشغيل يدوي من /start_bot")

# ========== بدء التشغيل ==========
if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("🚀 بدء تشغيل نظام التتبع...")
    logger.info(f"🌐 الرابط: https://telegram-tracking-bot-35hp.onrender.com")
    logger.info("=" * 50)
    
    # بدء البوت تلقائياً
    import threading
    auto_start_thread = threading.Thread(target=auto_start_bot, daemon=True)
    auto_start_thread.start()
    
    # تشغيل خادم Flask
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 بدء خادم Flask على port {port}")
    logger.info("=" * 50)
    logger.info("✅ النظام جاهز!")
    logger.info("🤖 لتشغيل البوت: اضغط /start_bot")
    logger.info("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)