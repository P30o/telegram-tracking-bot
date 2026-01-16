from flask import Flask, jsonify
import telebot
import threading
import logging
import os
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN', '7628474532:AAHQMH9nJHYqB25X89kQYtE8Ms3x5e6m7TY')
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='Markdown')

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
        'bot_running': True,
        'time': '2026-01-16T08:44:49.734404'
    })

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ *البوت يعمل!* أرسل `/newlink`")

@bot.message_handler(commands=['newlink'])
def newlink(message):
    bot.reply_to(message, "🔗 *سيتم إنشاء رابط قريباً*")

def run_bot():
    """تشغيل البوت"""
    time.sleep(3)
    logger.info("🚀 بدء تشغيل البوت...")
    
    try:
        bot_info = bot.get_me()
        logger.info(f"✅ البوت متصل: @{bot_info.username}")
        logger.info("🎯 بدء استقبال الرسائل...")
        bot.infinity_polling(timeout=30, long_polling_timeout=30)
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")

if __name__ == '__main__':
    # بدء البوت
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("✅ بدأ خيط البوت")
    
    # تشغيل الخادم
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 بدء الخادم على port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)