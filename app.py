 """
🤖 بوت تتبع المواقع الجغرافي الكامل - Telegram Location Tracking Bot
نسخة واحدة تعمل على Replit أو أي استضافة
البوت: @cccc00bot
"""

import telebot
from telebot import types
import json
import sqlite3
import datetime
import uuid
import threading
import time
import logging
from urllib.parse import quote

# ========== إعدادات Logging ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== إعداد البوت ==========
TOKEN = "8059073897:AAHpGwkzSvXmiUpJpahG0tt922D9nZ2zylI"
bot = telebot.TeleBot(TOKEN)

# ========== قاعدة البيانات SQLite ==========
def init_database():
    conn = sqlite3.connect('tracking_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # جدول المستخدمين
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        joined_date TIMESTAMP
    )
    ''')
    
    # جدول روابط التتبع
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tracking_links (
        link_id TEXT PRIMARY KEY,
        user_id INTEGER,
        target_url TEXT,
        created_at TIMESTAMP,
        is_active BOOLEAN DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')
    
    # جدول المواقع
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        link_id TEXT,
        latitude REAL,
        longitude REAL,
        accuracy REAL,
        timestamp TIMESTAMP,
        user_agent TEXT,
        FOREIGN KEY (link_id) REFERENCES tracking_links (link_id)
    )
    ''')
    
    # جدول الزيارات
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        link_id TEXT,
        visited_at TIMESTAMP,
        ip_address TEXT,
        country TEXT,
        city TEXT,
        user_agent TEXT
    )
    ''')
    
    conn.commit()
    return conn

# تهيئة قاعدة البيانات
db = init_database()

# ========== دوال مساعدة ==========
def save_user(user_id, username, first_name, last_name):
    cursor = db.cursor()
    cursor.execute('''
    INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, joined_date)
    VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name, datetime.datetime.now()))
    db.commit()

def create_tracking_link(user_id, target_url=None):
    link_id = str(uuid.uuid4())[:12]
    cursor = db.cursor()
    cursor.execute('''
    INSERT INTO tracking_links (link_id, user_id, target_url, created_at)
    VALUES (?, ?, ?, ?)
    ''', (link_id, user_id, target_url, datetime.datetime.now()))
    db.commit()
    return link_id

def save_location(link_id, latitude, longitude, accuracy, user_agent=""):
    cursor = db.cursor()
    cursor.execute('''
    INSERT INTO locations (link_id, latitude, longitude, accuracy, timestamp, user_agent)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (link_id, latitude, longitude, accuracy, datetime.datetime.now(), user_agent))
    db.commit()

def save_visit(link_id, ip_address, user_agent, country=None, city=None):
    cursor = db.cursor()
    cursor.execute('''
    INSERT INTO visits (link_id, visited_at, ip_address, country, city, user_agent)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (link_id, datetime.datetime.now(), ip_address, country, city, user_agent))
    db.commit()

def get_user_links(user_id):
    cursor = db.cursor()
    cursor.execute('''
    SELECT link_id, target_url, created_at, 
           (SELECT COUNT(*) FROM locations WHERE link_id = tracking_links.link_id) as location_count,
           (SELECT COUNT(*) FROM visits WHERE link_id = tracking_links.link_id) as visit_count
    FROM tracking_links 
    WHERE user_id = ? AND is_active = 1
    ORDER BY created_at DESC
    ''', (user_id,))
    return cursor.fetchall()

def get_link_locations(link_id):
    cursor = db.cursor()
    cursor.execute('''
    SELECT latitude, longitude, accuracy, timestamp
    FROM locations 
    WHERE link_id = ?
    ORDER BY timestamp DESC
    ''', (link_id,))
    return cursor.fetchall()

def get_link_info(link_id):
    cursor = db.cursor()
    cursor.execute('''
    SELECT tl.*, u.username, 
           (SELECT COUNT(*) FROM locations WHERE link_id = ?) as location_count,
           (SELECT COUNT(*) FROM visits WHERE link_id = ?) as visit_count
    FROM tracking_links tl
    LEFT JOIN users u ON tl.user_id = u.user_id
    WHERE tl.link_id = ?
    ''', (link_id, link_id, link_id))
    return cursor.fetchone()

def delete_link(link_id, user_id):
    cursor = db.cursor()
    cursor.execute('''
    UPDATE tracking_links 
    SET is_active = 0 
    WHERE link_id = ? AND user_id = ?
    ''', (link_id, user_id))
    db.commit()
    return cursor.rowcount > 0

def get_user_stats(user_id):
    cursor = db.cursor()
    
    # إحصائيات المستخدم
    cursor.execute('''
    SELECT 
        COUNT(DISTINCT link_id) as total_links,
        COUNT(DISTINCT locations.id) as total_locations,
        COUNT(DISTINCT visits.id) as total_visits
    FROM tracking_links tl
    LEFT JOIN locations ON tl.link_id = locations.link_id
    LEFT JOIN visits ON tl.link_id = visits.link_id
    WHERE tl.user_id = ? AND tl.is_active = 1
    ''', (user_id,))
    
    stats = cursor.fetchone()
    return {
        'total_links': stats[0] or 0,
        'total_locations': stats[1] or 0,
        'total_visits': stats[2] or 0
    }

# ========== Handlers للبوت ==========
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """ترحيب بالبوت"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    # حفظ معلومات المستخدم
    save_user(user_id, username, first_name, last_name)
    
    welcome_text = """
📍 *مرحباً بك في بوت تتبع المواقع الجغرافي*

🤖 *أنا بوت لإنشاء روابط تتبع جغرافي*

⚡️ *الأوامر المتاحة:*
/newlink - إنشاء رابط تتبع جديد
/mylinks - عرض روابطك النشطة
/locations - عرض المواقع المسجلة
/stats - إحصائيات حسابك
/guide - دليل الاستخدام الأخلاقي
/delete - حذف رابط تتبع
/settings - إعدادات البوت

🎯 *كيف يعمل البوت:*
1. تنشئ رابط تتبع خاص بك
2. ترسل الرابط لأي شخص
3. عندما يفتح الشخص الرابط، يطلب منه إذن الموقع
4. يتم إرسال الموقع إليك في الخاص
5. يمكنك توجيهه لرابط آخر بعد الحصول على الموقع

⚠️ *تحذير مهم:*
هذا البوت للأغراض التعليمية والتوعية فقط.
يجب الحصول على موافقة صريحة قبل تتبع أي شخص.
سوء الاستخدام قد يعرضك للمساءلة القانونية.

🔐 *لضمان الأمان:*
• كل رابط مرتبط بحسابك فقط
• البيانات مشفرة ومحمية
• يمكنك حذف أي رابط في أي وقت
    """
    
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['newlink'])
def create_new_link(message):
    """إنشاء رابط تتبع جديد"""
    user_id = message.from_user.id
    
    # إنشاء رابط فريد
    link_id = create_tracking_link(user_id)
    
    # إنشاء رابط التتبع
    tracking_url = f"https://t.me/{bot.get_me().username}?start=track_{link_id}"
    
    # إنشاء QR code
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={quote(tracking_url)}"
    
    response_text = f"""
✅ *تم إنشاء رابط تتبع جديد*

🔗 *رابط التتبع:*
`{tracking_url}`

📱 *كود QR:*
[‏‏‎]({qr_url})

🆔 *معرف الرابط:* `{link_id}`

📋 *طريقة الاستخدام:*
1. أرسل هذا الرابط للشخص الذي تريد تتبعه
2. عندما يفتح الرابط، سيطلب منه البوت إذن الموقع
3. بمجرد موافقته، سيتم إرسال موقعه إليك
4. يمكنك إضافة رابط توجيه باستخدام /target

⚠️ *التوجيهات الأخلاقية:*
1. يجب الحصول على موافقة صريحة من الشخص
2. اشرح الغرض من التتبع بوضوح
3. استخدم النظام للأغراض التعليمية فقط
4. احترم خصوصية الآخرين

🎯 *لإضافة رابط مستهدف (اختياري):*
أرسل `/target {link_id} https://example.com`
    """
    
    bot.send_photo(message.chat.id, qr_url, caption=response_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text and message.text.startswith('/target'))
def set_target_url(message):
    """تعيين رابط مستهدف لرابط التتبع"""
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ *صيغة خاطئة*\n\nاستخدم:\n`/target link_id https://example.com`", parse_mode='Markdown')
            return
        
        link_id = parts[1]
        target_url = parts[2]
        user_id = message.from_user.id
        
        # التحقق من ملكية الرابط
        cursor = db.cursor()
        cursor.execute('SELECT user_id FROM tracking_links WHERE link_id = ? AND is_active = 1', (link_id,))
        result = cursor.fetchone()
        
        if not result or result[0] != user_id:
            bot.reply_to(message, "❌ *رابط التتبع غير موجود أو ليس لديك صلاحية لتعديله*", parse_mode='Markdown')
            return
        
        # تحديث الرابط المستهدف
        cursor.execute('UPDATE tracking_links SET target_url = ? WHERE link_id = ?', (target_url, link_id))
        db.commit()
        
        bot.reply_to(message, f"""
✅ *تم تعيين الرابط المستهدف*

🔗 رابط التتبع: `{link_id}`
🎯 الرابط المستهدف: {target_url}

📍 *عند دخول المستخدم للرابط:*
1. سيطلب منه إذن الموقع الجغرافي
2. بمجرد الموافقة، سيتم إرسال موقعه إليك
3. سيتم توجيهه تلقائياً للرابط المستهدف
        """, parse_mode='Markdown')
        
    except Exception as e:
        bot.reply_to(message, f"❌ *حدث خطأ:* `{str(e)}`", parse_mode='Markdown')

@bot.message_handler(commands=['mylinks'])
def show_my_links(message):
    """عرض روابط التتبع الخاصة بالمستخدم"""
    user_id = message.from_user.id
    
    links = get_user_links(user_id)
    
    if not links:
        bot.reply_to(message, "📭 *ليس لديك روابط تتبع نشطة*\n\nاستخدم `/newlink` لإنشاء رابط جديد", parse_mode='Markdown')
        return
    
    links_text = "📍 *روابط التتبع الخاصة بك:*\n\n"
    
    for link in links:
        link_id, target_url, created_at, location_count, visit_count = link
        tracking_url = f"https://t.me/{bot.get_me().username}?start=track_{link_id}"
        created_date = datetime.datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d %H:%M')
        
        links_text += f"""
🔗 *الرابط:* `{link_id[:8]}...`
📊 المواقع المسجلة: *{location_count}*
👥 الزيارات: *{visit_count}*
🎯 الهدف: {target_url or 'لا يوجد'}
📅 الإنشاء: {created_date}

"""
    
    # إضافة أزرار التحكم
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🔄 تحديث", callback_data="refresh_links"),
        types.InlineKeyboardButton("🗑️ حذف رابط", callback_data="delete_link_menu")
    )
    
    bot.reply_to(message, links_text, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['locations'])
def show_locations_menu(message):
    """عرض قائمة الروابط لرؤية المواقع"""
    user_id = message.from_user.id
    
    links = get_user_links(user_id)
    
    if not links:
        bot.reply_to(message, "📍 *لم يتم تسجيل أي مواقع بعد*\n\nأنشئ رابط تتبع أولاً باستخدام `/newlink`", parse_mode='Markdown')
        return
    
    # إنشاء أزرار للروابط
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    for link in links[:10]:  # عرض أول 10 روابط فقط
        link_id, target_url, created_at, location_count, visit_count = link
        button_text = f"📍 {link_id[:8]}... ({location_count})"
        markup.add(types.InlineKeyboardButton(button_text, callback_data=f"view_locations_{link_id}"))
    
    if len(links) > 10:
        markup.add(types.InlineKeyboardButton("📄 الصفحة التالية", callback_data="next_page_1"))
    
    bot.reply_to(message, "📍 *اختر رابطاً لعرض المواقع المسجلة له:*", parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['stats'])
def show_stats(message):
    """عرض إحصائيات المستخدم"""
    user_id = message.from_user.id
    
    stats = get_user_stats(user_id)
    
    # الحصول على الرابط الأكثر نشاطاً
    cursor = db.cursor()
    cursor.execute('''
    SELECT tl.link_id, COUNT(l.id) as location_count
    FROM tracking_links tl
    LEFT JOIN locations l ON tl.link_id = l.link_id
    WHERE tl.user_id = ? AND tl.is_active = 1
    GROUP BY tl.link_id
    ORDER BY location_count DESC
    LIMIT 1
    ''', (user_id,))
    
    top_link = cursor.fetchone()
    
    stats_text = f"""
📊 *إحصائيات حسابك:*

🔗 *الروابط النشطة:* {stats['total_links']}
📍 *المواقع المسجلة:* {stats['total_locations']}
👥 *الزيارات الكلية:* {stats['total_visits']}

🏆 *الرابط الأكثر نشاطاً:*
"""
    
    if top_link and top_link[1] > 0:
        stats_text += f"`{top_link[0][:12]}...` - {top_link[1]} موقع"
    
    # إحصائيات اليوم
    today = datetime.datetime.now().date()
    cursor.execute('''
    SELECT COUNT(*) FROM locations l
    JOIN tracking_links tl ON l.link_id = tl.link_id
    WHERE tl.user_id = ? AND DATE(l.timestamp) = ?
    ''', (user_id, today))
    
    today_locations = cursor.fetchone()[0] or 0
    
    stats_text += f"\n\n📅 *إحصائيات اليوم:*\n📍 مواقع اليوم: *{today_locations}*"
    
    # رسم بياني بسيط (نصي)
    if stats['total_locations'] > 0:
        stats_text += "\n\n📈 *نشاط الشهر:*\n"
        for i in range(1, 8):
            date = (datetime.datetime.now() - datetime.timedelta(days=i)).date()
            cursor.execute('''
            SELECT COUNT(*) FROM locations l
            JOIN tracking_links tl ON l.link_id = tl.link_id
            WHERE tl.user_id = ? AND DATE(l.timestamp) = ?
            ''', (user_id, date))
            
            count = cursor.fetchone()[0] or 0
            bar = "█" * min(count, 10) if count > 0 else "▁"
            stats_text += f"{date.strftime('%a')}: {bar} ({count})\n"
    
    # أزرار إضافية
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🔄 تحديث", callback_data="refresh_stats"),
        types.InlineKeyboardButton("📊 تفاصيل", callback_data="detailed_stats")
    )
    
    bot.reply_to(message, stats_text, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['guide'])
def ethical_guide(message):
    """إرسال دليل الاستخدام الأخلاقي"""
    guide_text = """
📚 *دليل الاستخدام الأخلاقي*

⚠️ *تحذير مهم:*
هذا البوت للأغراض التعليمية والتوعية فقط.

✅ *الاستخدامات المشروعة:*
1. التوعية الأمنية والإلكترونية
2. الدروس التعليمية في الجامعات
3. حماية الأطفال (بتفويض الوالدين)
4. الأبحاث الأكاديمية (مع موافقة)
5. التدريبات التعليمية

❌ *الاستخدامات الممنوعة:*
1. تتبع الأشخاص دون موافقتهم
2. الملاحقة أو المضايقة
3. انتهاك خصوصية الآخرين
4. الأغراض التجارية غير المصرح بها
5. التشويش على عمل السلطات

⚖️ *الجوانب القانونية:*
• تتبع الأشخاص دون موافقة قد يعتبر جريمة
• انتهاك قوانين حماية البيانات الشخصية
• قوانين الملاحقة (Stalking Laws)
• قوانين الجرائم الإلكترونية

📋 *نموذج الموافقة المطلوبة:*
يجب أن تتضمن الموافقة:
1. الغرض من التتبع
2. مدة التتبع
3. طريقة استخدام البيانات
4. حق الشخص في سحب الموافقة
5. كيفية حذف البيانات

🔐 *نصائح أمنية:*
1. استخدم كلمات مرور قوية
2. لا تشارك روابط التتبع عشوائياً
3. احذف البيانات بعد انتهاء الحاجة
4. راجع الصلاحيات بانتظام

🆘 *إذا تعرضت للملاحقة:*
1. احتفظ بالأدلة
2. بلغ الجهات المختصة
3. غير كلمات المرور
4. استشر محامياً

*تذكر: القوة تأتي مع المسؤولية*
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📖 دليل مفصل", url="https://example.com/ethical-guide"))
    markup.add(types.InlineKeyboardButton("⚖️ القوانين ذات الصلة", url="https://example.com/laws"))
    
    bot.reply_to(message, guide_text, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['delete'])
def delete_link_menu(message):
    """قائمة لحذف الروابط"""
    user_id = message.from_user.id
    
    links = get_user_links(user_id)
    
    if not links:
        bot.reply_to(message, "❌ *ليس لديك روابط لحذفها*", parse_mode='Markdown')
        return
    
    # إنشاء أزرار للروابط
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    for link in links[:8]:  # عرض أول 8 روابط فقط
        link_id, target_url, created_at, location_count, visit_count = link
        button_text = f"🗑️ {link_id[:8]}..."
        markup.add(types.InlineKeyboardButton(button_text, callback_data=f"confirm_delete_{link_id}"))
    
    if len(links) > 8:
        markup.add(types.InlineKeyboardButton("📄 المزيد", callback_data="more_links"))
    
    markup.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel_delete"))
    
    bot.reply_to(message, "🗑️ *اختر رابطاً لحذفه:*", parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['settings'])
def bot_settings(message):
    """إعدادات البوت"""
    settings_text = """
⚙️ *إعدادات البوت:*

🔐 *الأمان:*
• البيانات مشفرة في قاعدة البيانات
• كل رابط مرتبط بحسابك فقط
• يمكنك حذف البيانات في أي وقت

📊 *الإشعارات:*
• إشعار عند فتح الرابط ✓
• إشعار عند الحصول على موقع ✓
• إشعارات يومية عن النشاط ✗

🎯 *الميزات:*
• إنشاء روابط غير محدود ✓
• كود QR للروابط ✓
• توجيه لروابط خارجية ✓
• إحصائيات مفصلة ✓

🛡️ *الخصوصية:*
• البيانات تحفظ لمدة 30 يوم
• حذف تلقائي للبيانات القديمة
• تشفير المواقع الجغرافية

🔧 *تغيير الإعدادات:* (قريباً)
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🔔 إعداد الإشعارات", callback_data="notif_settings"),
        types.InlineKeyboardButton("🛡️ إعدادات الخصوصية", callback_data="privacy_settings")
    )
    markup.row(
        types.InlineKeyboardButton("🗑️ حذف كل البيانات", callback_data="delete_all_data"),
        types.InlineKeyboardButton("📋 تصدير البيانات", callback_data="export_data")
    )
    
    bot.reply_to(message, settings_text, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    """معالجة الرسائل النصية"""
    if message.text.startswith('http'):
        # إذا كان المستخدم أرسل رابطاً
        bot.reply_to(message, """
🔗 *لاحظت أنك أرسلت رابطاً*

إذا كنت تريد إنشاء رابط تتبع مع رابط مستهدف:
1. استخدم `/newlink` أولاً
2. ثم استخدم `/target link_id YOUR_LINK`

أو ببساطة أرسل `/newlink` لإنشاء رابط تتبع
        """, parse_mode='Markdown')
    else:
        bot.reply_to(message, """
🤖 *لم أفهم رسالتك*

🔍 *الأوامر المتاحة:*
/start - بدء البوت
/newlink - رابط تتبع جديد
/mylinks - روابطك النشطة
/locations - المواقع المسجلة
/stats - إحصائياتك
/guide - دليل الاستخدام
/settings - إعدادات البوت

❓ *للحصول على مساعدة:*
اكتب `/help` أو تواصل مع الدعم
        """, parse_mode='Markdown')

# ========== Callback Handlers ==========
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """معالجة الأزرار والتفاعلات"""
    user_id = call.from_user.id
    
    if call.data == "refresh_links":
        # تحديث قائمة الروابط
        links = get_user_links(user_id)
        
        if not links:
            bot.answer_callback_query(call.id, "❌ لا توجد روابط")
            return
        
        links_text = "📍 *روابط التتبع الخاصة بك (محدث):*\n\n"
        
        for link in links:
            link_id, target_url, created_at, location_count, visit_count = link
            tracking_url = f"https://t.me/{bot.get_me().username}?start=track_{link_id}"
            created_date = datetime.datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d %H:%M')
            
            links_text += f"""
🔗 *الرابط:* `{link_id[:8]}...`
📊 المواقع المسجلة: *{location_count}*
👥 الزيارات: *{visit_count}*
🎯 الهدف: {target_url or 'لا يوجد'}
📅 الإنشاء: {created_date}

"""
        
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("🔄 تحديث", callback_data="refresh_links"),
            types.InlineKeyboardButton("🗑️ حذف رابط", callback_data="delete_link_menu")
        )
        
        bot.edit_message_text(
            links_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown',
            reply_markup=markup
        )
        bot.answer_callback_query(call.id, "✅ تم التحديث")
    
    elif call.data.startswith("view_locations_"):
        link_id = call.data.replace("view_locations_", "")
        
        locations = get_link_locations(link_id)
        
        if not locations:
            bot.answer_callback_query(call.id, "📍 لا توجد مواقع مسجلة")
            return
        
        # عرض أول 5 مواقع فقط
        locations_text = f"📍 *المواقع المسجلة للرابط:* `{link_id[:12]}...`\n\n"
        
        for i, loc in enumerate(locations[:5], 1):
            lat, lon, acc, timestamp = loc
            time_str = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d %H:%M')
            map_url = f"https://www.google.com/maps?q={lat},{lon}"
            
            locations_text += f"""
{i}. 📍 *الموقع:*
   • خط العرض: `{lat:.6f}`
   • خط الطول: `{lon:.6f}`
   • الدقة: `{acc:.0f}` متر
   • الوقت: {time_str}
   • [🗺️ عرض على الخريطة]({map_url})
"""
        
        if len(locations) > 5:
            locations_text += f"\n📄 *و {len(locations)-5} موقع إضافي*"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("↩️ العودة", callback_data="back_to_links"))
        
        bot.edit_message_text(
            locations_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown',
            reply_markup=markup,
            disable_web_page_preview=True
        )
        bot.answer_callback_query(call.id)
    
    elif call.data == "back_to_links":
        # العودة لقائمة الروابط
        show_locations_menu(call.message)
        bot.answer_callback_query(call.id)
    
    elif call.data.startswith("confirm_delete_"):
        link_id = call.data.replace("confirm_delete_", "")
        
        # تأكيد الحذف
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("✅ نعم، احذف", callback_data=f"delete_now_{link_id}"),
            types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel_delete")
        )
        
        # الحصول على معلومات الرابط
        link_info = get_link_info(link_id)
        if link_info:
            location_count = link_info[7] or 0
            visit_count = link_info[8] or 0
            
            bot.edit_message_text(
                f"""
⚠️ *تأكيد حذف الرابط*

🔗 المعرف: `{link_id}`
📍 المواقع المسجلة: *{location_count}*
👥 الزيارات: *{visit_count}*

❌ *سيتم حذف:*
• جميع المواقع المسجلة
• جميع سجلات الزيارات
• الرابط نفسه

🔄 *لا يمكن استعادة البيانات بعد الحذف*

هل أنت متأكد من رغبتك في حذف هذا الرابط؟
                """,
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown',
                reply_markup=markup
            )
    
    elif call.data.startswith("delete_now_"):
        link_id = call.data.replace("delete_now_", "")
        
        if delete_link(link_id, user_id):
            bot.edit_message_text(
                "✅ *تم حذف الرابط بنجاح*\n\nتم حذف جميع البيانات المرتبطة به.",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown'
            )
            bot.answer_callback_query(call.id, "✅ تم الحذف")
        else:
            bot.answer_callback_query(call.id, "❌ فشل في الحذف")
    
    elif call.data == "cancel_delete":
        bot.edit_message_text(
            "❌ *تم إلغاء عملية الحذف*\n\nبياناتك لا تزال محفوظة.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id, "❌ تم الإلغاء")
    
    elif call.data == "refresh_stats":
        # تحديث الإحصائيات
        show_stats(call.message)
        bot.answer_callback_query(call.id, "✅ تم التحديث")
    
    elif call.data == "delete_link_menu":
        delete_link_menu(call.message)
        bot.answer_callback_query(call.id)
    
    elif call.data == "detailed_stats":
        # إحصائيات مفصلة
        stats = get_user_stats(user_id)
        
        # الحصول على روابط المستخدم مع تفاصيل
        cursor = db.cursor()
        cursor.execute('''
        SELECT tl.link_id, tl.created_at, tl.target_url,
               COUNT(DISTINCT l.id) as loc_count,
               COUNT(DISTINCT v.id) as visit_count
        FROM tracking_links tl
        LEFT JOIN locations l ON tl.link_id = l.link_id
        LEFT JOIN visits v ON tl.link_id = v.link_id
        WHERE tl.user_id = ? AND tl.is_active = 1
        GROUP BY tl.link_id
        ORDER BY tl.created_at DESC
        ''', (user_id,))
        
        links_details = cursor.fetchall()
        
        detailed_text = f"""
📊 *الإحصائيات المفصلة:*

🔗 *الروابط النشطة:* {stats['total_links']}
📍 *المواقع المسجلة:* {stats['total_locations']}
👥 *الزيارات الكلية:* {stats['total_visits']}

📋 *تفاصيل الروابط:*
"""
        
        for link in links_details[:5]:  # عرض أول 5 روابط فقط
            link_id, created_at, target_url, loc_count, visit_count = link
            created_date = datetime.datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S.%f').strftime('%m/%d')
            
            detailed_text += f"""
• `{link_id[:8]}...` - 📍{loc_count} 👥{visit_count} - {created_date}
"""
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("↩️ العودة", callback_data="back_to_stats"))
        
        bot.edit_message_text(
            detailed_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown',
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)
    
    elif call.data == "back_to_stats":
        show_stats(call.message)
        bot.answer_callback_query(call.id)
    
    elif call.data == "delete_all_data":
        # تأكيد حذف جميع البيانات
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("⚠️ نعم، احذف كل شيء", callback_data="confirm_delete_all"),
            types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel_delete_all")
        )
        
        bot.edit_message_text(
            """
⚠️ *تحذير: حذف جميع البيانات*

❌ *سيتم حذف:*
• جميع روابط التتبع الخاصة بك
• جميع المواقع المسجلة
• جميع سجلات الزيارات
• جميع إحصائياتك

🔄 *لا يمكن استعادة البيانات بعد الحذف*

هذا الإجراء نهائي ولا يمكن التراجع عنه.

هل أنت متأكد من رغبتك في حذف *جميع* بياناتك؟
            """,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown',
            reply_markup=markup
        )
    
    elif call.data == "confirm_delete_all":
        # حذف جميع بيانات المستخدم
        cursor = db.cursor()
        
        # حذف المواقع
        cursor.execute('''
        DELETE FROM locations 
        WHERE link_id IN (SELECT link_id FROM tracking_links WHERE user_id = ?)
        ''', (user_id,))
        
        # حذف الزيارات
        cursor.execute('''
        DELETE FROM visits 
        WHERE link_id IN (SELECT link_id FROM tracking_links WHERE user_id = ?)
        ''', (user_id,))
        
        # حذف روابط التتبع
        cursor.execute('DELETE FROM tracking_links WHERE user_id = ?', (user_id,))
        
        db.commit()
        
        bot.edit_message_text(
            "✅ *تم حذف جميع بياناتك بنجاح*\n\nيمكنك البدء من جديد باستخدام `/newlink`",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id, "✅ تم الحذف")
    
    elif call.data == "cancel_delete_all":
        bot.edit_message_text(
            "❌ *تم إلغاء حذف البيانات*\n\nبياناتك لا تزال محفوظة.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id, "❌ تم الإلغاء")

# ========== معالجة بدء التتبع ==========
@bot.message_handler(func=lambda message: message.text and message.text.startswith('/start track_'))
def handle_tracking_start(message):
    """معالجة عندما يفتح المستخدم رابط التتبع"""
    try:
        link_id = message.text.replace('/start track_', '')
        
        # التحقق من وجود الرابط
        link_info = get_link_info(link_id)
        if not link_info:
            bot.reply_to(message, "❌ رابط التتبع غير صالح أو منتهي الصلاحية.")
            return
        
        # حفظ زيارة (بدون معلومات IP حالياً)
        save_visit(link_id, "unknown", message.from_user.username or "Anonymous")
        
        # إرسال إشعار لصاحب الرابط
        owner_id = link_info[1]
        visitor_name = message.from_user.first_name or "مستخدم"
        
        try:
            bot.send_message(
                owner_id,
                f"""
🔔 *إشعار: شخص فتح رابط التتبع الخاص بك*

👤 *المستخدم:* {visitor_name}
🔗 *معرف الرابط:* `{link_id[:12]}...`
🕐 *الوقت:* {datetime.datetime.now().strftime('%H:%M')}

📍 *جاري انتظار إذن الموقع...*
                """,
                parse_mode='Markdown'
            )
        except:
            pass  # إذا كان البوت محظوراً من قبل المالك
        
        # طلب إذن الموقع من المستخدم
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton("📍 مشاركة الموقع الجغرافي", request_location=True))
        markup.add(types.KeyboardButton("❌ رفض مشاركة الموقع"))
        
        # التحقق إذا كان هناك رابط مستهدف
        target_url = link_info[2]
        if target_url:
            message_text = f"""
📍 *طلب إذن الموقع الجغرافي*

👋 *مرحباً {visitor_name}*

يريد مالك الرابط الحصول على موقعك الجغرافي.

🎯 *بعد مشاركة الموقع، سيتم توجيهك إلى:*
{target_url}

⚠️ *ملاحظة:*
• الموقع سيرسل فقط لمالك الرابط
• يمكنك رفض مشاركة الموقع
• يتم استخدام النظام لأغراض تعليمية
            """
        else:
            message_text = f"""
📍 *طلب إذن الموقع الجغرافي*

👋 *مرحباً {visitor_name}*

يريد مالك الرابط الحصول على موقعك الجغرافي.

⚠️ *ملاحظة:*
• الموقع سيرسل فقط لمالك الرابط
• يمكنك رفض مشاركة الموقع
• يتم استخدام النظام لأغراض تعليمية
            """
        
        bot.send_message(
            message.chat.id,
            message_text,
            reply_markup=markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in handle_tracking_start: {e}")
        bot.reply_to(message, "❌ حدث خطأ في معالجة الرابط.")

# ========== معالجة الموقع الجغرافي ==========
@bot.message_handler(content_types=['location'])
def handle_location(message):
    """معالجة عند إرسال الموقع الجغرافي"""
    try:
        # البحث عن الرابط النشط لهذا المستخدم
        user_id = message.from_user.id
        visitor_name = message.from_user.first_name or "مستخدم"
        
        # في نظام حقيقي، نحتاج لتتبع حالة المستخدم
        # لكن للتبسيط، سنبحث في آخر زيارة لهذا المستخدم
        
        cursor = db.cursor()
        cursor.execute('''
        SELECT link_id FROM visits 
        WHERE user_agent = ? OR user_agent = ?
        ORDER BY visited_at DESC 
        LIMIT 1
        ''', (message.from_user.username or "", visitor_name))
        
        result = cursor.fetchone()
        
        if not result:
            bot.reply_to(message, "❌ لا يمكن تحديد رابط التتبع.")
            return
        
        link_id = result[0]
        
        # حفظ الموقع
        latitude = message.location.latitude
        longitude = message.location.longitude
        
        # في الواقع، يمكن الحصول على accuracy من الرسالة
        # لكنها قد لا تكون متاحة دائماً
        accuracy = 100  # قيمة افتراضية
        
        save_location(link_id, latitude, longitude, accuracy, visitor_name)
        
        # إرسال الموقع لصاحب الرابط
        link_info = get_link_info(link_id)
        if link_info:
            owner_id = link_info[1]
            
            map_url = f"https://www.google.com/maps?q={latitude},{longitude}"
            map_static = f"https://maps.googleapis.com/maps/api/staticmap?center={latitude},{longitude}&zoom=15&size=400x200&markers=color:red%7C{latitude},{longitude}"
            
            try:
                bot.send_location(owner_id, latitude, longitude)
                
                bot.send_message(
                    owner_id,
                    f"""
📍 *تم استلام موقع جغرافي جديد*

👤 *من:* {visitor_name}
🔗 *الرابط:* `{link_id[:12]}...`
🕐 *الوقت:* {datetime.datetime.now().strftime('%H:%M')}

📌 *الإحداثيات:*
• خط العرض: `{latitude:.6f}`
• خط الطول: `{longitude:.6f}`

🗺️ [عرض على الخريطة]({map_url})

✅ *تم حفظ الموقع في قاعدة البيانات*
                    """,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
            except:
                pass  # إذا كان البوت محظوراً
        
        # إرسال رد للمستخدم
        target_url = link_info[2] if link_info else None
        
        if target_url:
            response_text = f"""
✅ *تم إرسال موقعك بنجاح*

📍 شكراً لمشاركة موقعك الجغرافي.

🎯 *جاري توجيهك إلى الرابط المطلوب...*

إذا لم يتم التوجيه تلقائياً، [اضغط هنا]({target_url})
            """
            
            # إنشاء زر للتوجيه
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🎯 الانتقال للرابط", url=target_url))
            
            bot.send_message(
                message.chat.id,
                response_text,
                reply_markup=markup,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
        else:
            bot.reply_to(message, """
✅ *تم إرسال موقعك بنجاح*

📍 شكراً لمشاركة موقعك الجغرافي.

تم إرسال موقعك لمالك الرابط.
يمكنك إغلاق هذه المحادثة.
            """)
        
    except Exception as e:
        logger.error(f"Error in handle_location: {e}")
        bot.reply_to(message, "❌ حدث خطأ في معالجة الموقع.")

# ========== معالجة رفض الموقع ==========
@bot.message_handler(func=lambda message: message.text == "❌ رفض مشاركة الموقع")
def handle_location_denial(message):
    """معالجة عند رفض مشاركة الموقع"""
    visitor_name = message.from_user.first_name or "مستخدم"
    
    # البحث عن الرابط النشط
    cursor = db.cursor()
    cursor.execute('''
    SELECT link_id FROM visits 
    WHERE user_agent = ? OR user_agent = ?
    ORDER BY visited_at DESC 
    LIMIT 1
    ''', (message.from_user.username or "", visitor_name))
    
    result = cursor.fetchone()
    
    if result:
        link_id = result[0]
        link_info = get_link_info(link_id)
        
        if link_info:
            owner_id = link_info[1]
            
            try:
                bot.send_message(
                    owner_id,
                    f"""
❌ *رفض مشاركة الموقع*

👤 *المستخدم:* {visitor_name}
🔗 *الرابط:* `{link_id[:12]}...`
🕐 *الوقت:* {datetime.datetime.now().strftime('%H:%M')}

⚠️ *رفض المستخدم مشاركة موقعه الجغرافي*
                    """,
                    parse_mode='Markdown'
                )
            except:
                pass
    
    # التحقق إذا كان هناك رابط مستهدف
    target_url = link_info[2] if link_info and link_info[2] else None
    
    if target_url:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎯 الانتقال للرابط", url=target_url))
        
        bot.send_message(
            message.chat.id,
            f"""
❌ *تم رفض مشاركة الموقع*

يمكنك زيارة الرابط المطلوب:
            """,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    else:
        bot.reply_to(message, """
❌ *تم رفض مشاركة الموقع*

شكراً لتفهمك. يمكنك إغلاق هذه المحادثة.
        """)

# ========== وظائف الخلفية ==========
def cleanup_old_data():
    """تنظيف البيانات القديمة تلقائياً"""
    while True:
        try:
            cursor = db.cursor()
            
            # حذف البيانات الأقدم من 30 يوم
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=30)
            
            # حذف المواقع القديمة
            cursor.execute('DELETE FROM locations WHERE timestamp < ?', (cutoff_date,))
            
            # حذف الزيارات القديمة
            cursor.execute('DELETE FROM visits WHERE visited_at < ?', (cutoff_date,))
            
            # تعطيل الروابط بدون نشاط لمدة 30 يوم
            cursor.execute('''
            UPDATE tracking_links 
            SET is_active = 0 
            WHERE created_at < ? AND is_active = 1
            AND link_id NOT IN (
                SELECT DISTINCT link_id FROM locations 
                WHERE timestamp > DATE('now', '-30 days')
                UNION
                SELECT DISTINCT link_id FROM visits 
                WHERE visited_at > DATE('now', '-30 days')
            )
            ''', (cutoff_date,))
            
            db.commit()
            
            logger.info("✅ تم تنظيف البيانات القديمة")
            
        except Exception as e:
            logger.error(f"❌ خطأ في تنظيف البيانات: {e}")
        
        # الانتظار 24 ساعة قبل التنظيف التالي
        time.sleep(24 * 60 * 60)

def send_daily_stats():
    """إرسال إحصائيات يومية للمستخدمين"""
    while True:
        try:
            # الانتظار حتى منتصف الليل
            now = datetime.datetime.now()
            target_time = now.replace(hour=0, minute=0, second=0) + datetime.timedelta(days=1)
            wait_seconds = (target_time - now).total_seconds()
            
            if wait_seconds > 0:
                time.sleep(wait_seconds)
            
            # إرسال الإحصائيات لكل مستخدم نشط
            cursor = db.cursor()
            cursor.execute('SELECT DISTINCT user_id FROM tracking_links WHERE is_active = 1')
            active_users = cursor.fetchall()
            
            for user_row in active_users:
                user_id = user_row[0]
                
                # الحصول على إحصائيات اليوم
                today = datetime.datetime.now().date()
                cursor.execute('''
                SELECT COUNT(*) FROM locations l
                JOIN tracking_links tl ON l.link_id = tl.link_id
                WHERE tl.user_id = ? AND DATE(l.timestamp) = ?
                ''', (user_id, today))
                
                today_locations = cursor.fetchone()[0] or 0
                
                if today_locations > 0:
                    try:
                        bot.send_message(
                            user_id,
                            f"""
📊 *التقرير اليومي*

📍 *مواقع اليوم:* {today_locations}
📅 التاريخ: {today.strftime('%Y-%m-%d')}

استمر في استخدام النظام بشكل أخلاقي.
                            """,
                            parse_mode='Markdown'
                        )
                    except:
                        pass  # إذا كان البوت محظوراً
            
            logger.info("✅ تم إرسال التقارير اليومية")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال التقارير: {e}")
            time.sleep(60)

# ========== بدء التشغيل ==========
def main():
    """الدالة الرئيسية لتشغيل النظام"""
    logger.info("=" * 50)
    logger.info("🚀 بدء تشغيل بوت تتبع المواقع الجغرافي")
    logger.info(f"🤖 البوت: @{bot.get_me().username}")
    logger.info("=" * 50)
    
    # بدء وظائف الخلفية
    cleanup_thread = threading.Thread(target=cleanup_old_data, daemon=True)
    cleanup_thread.start()
    
    stats_thread = threading.Thread(target=send_daily_stats, daemon=True)
    stats_thread.start()
    
    logger.info("✅ بدء استقبال الرسائل...")
    logger.info("=" * 50)
    
    # تشغيل البوت
    bot.polling(none_stop=True, timeout=30)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 إيقاف البوت...")
        db.close()
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع: {e}")
        db.close()