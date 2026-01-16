"""
🚨 نظام تتبع المواقع - للأغراض التعليمية والتوعية فقط
⚠️ يجب الحصول على موافقة صريحة قبل التتبع
البوت: @cccc00bot
"""

import os
import uuid
import json
import secrets
from datetime import datetime
from flask import Flask, request, render_template_string, jsonify, redirect
import telebot
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

# ========== إعدادات التطبيق ==========
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# ========== إعدادات Telegram ==========
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8059073897:AAHpGwkzSvXmiUpJpahG0tt922D9nZ2zylI')
bot = telebot.TeleBot(BOT_TOKEN)

# ========== قاعدة بيانات بسيطة ==========
tracking_links = {}  # {link_id: {target_url, user_id, created_at, locations: []}}
user_sessions = {}   # {user_id: {current_target, active_links}}

# ========== HTML Templates ==========
INDEX_HTML = '''
<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📍 نظام التتبع التعليمي</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }
        
        header {
            background: linear-gradient(to right, #4f46e5, #7c3aed);
            color: white;
            padding: 40px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .warning-banner {
            background: #fef3c7;
            border: 2px solid #f59e0b;
            border-radius: 10px;
            padding: 20px;
            margin: 20px auto;
            max-width: 800px;
            text-align: center;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.02); }
            100% { transform: scale(1); }
        }
        
        h1 {
            font-size: 2.8rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .subtitle {
            font-size: 1.2rem;
            opacity: 0.9;
            margin-bottom: 30px;
        }
        
        .section {
            padding: 40px;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .section-title {
            color: #4f46e5;
            font-size: 1.8rem;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .section-title i {
            font-size: 2rem;
        }
        
        .form-group {
            margin-bottom: 25px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #4b5563;
        }
        
        input[type="url"] {
            width: 100%;
            padding: 15px;
            border: 2px solid #d1d5db;
            border-radius: 12px;
            font-size: 1rem;
            transition: all 0.3s;
        }
        
        input[type="url"]:focus {
            outline: none;
            border-color: #4f46e5;
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
        }
        
        .btn {
            display: inline-block;
            padding: 15px 35px;
            background: linear-gradient(to right, #10b981, #059669);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            text-align: center;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(16, 185, 129, 0.4);
        }
        
        .btn-danger {
            background: linear-gradient(to right, #ef4444, #dc2626);
        }
        
        .btn-danger:hover {
            box-shadow: 0 10px 25px rgba(239, 68, 68, 0.4);
        }
        
        .link-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 15px;
            padding: 25px;
            margin: 15px 0;
            transition: all 0.3s;
        }
        
        .link-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }
        
        .link-code {
            background: #1f2937;
            color: #10b981;
            padding: 15px;
            border-radius: 10px;
            font-family: monospace;
            font-size: 1.1rem;
            margin: 10px 0;
            overflow-x: auto;
            direction: ltr;
        }
        
        .location-item {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .location-info {
            flex-grow: 1;
        }
        
        .location-time {
            color: #6b7280;
            font-size: 0.9rem;
        }
        
        .map-link {
            color: #3b82f6;
            text-decoration: none;
            font-weight: 600;
        }
        
        .map-link:hover {
            text-decoration: underline;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: bold;
            margin: 10px 0;
        }
        
        .stat-label {
            opacity: 0.9;
            font-size: 1rem;
        }
        
        footer {
            text-align: center;
            padding: 30px;
            color: #6b7280;
            font-size: 0.9rem;
        }
        
        .consent-checkbox {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            margin: 20px 0;
            padding: 15px;
            background: #f3f4f6;
            border-radius: 10px;
        }
        
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                border-radius: 15px;
            }
            
            header {
                padding: 30px 20px;
            }
            
            h1 {
                font-size: 2rem;
            }
            
            .section {
                padding: 25px;
            }
        }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <div class="container">
        <header>
            <h1><i class="fas fa-map-marker-alt"></i> نظام تتبع المواقع الجغرافي</h1>
            <p class="subtitle">للأغراض التعليمية والتوعية فقط - يجب الحصول على موافقة المستخدم</p>
        </header>
        
        <div class="warning-banner">
            <h3><i class="fas fa-exclamation-triangle"></i> تحذير مهم</h3>
            <p>هذا النظام مخصص للأغراض التعليمية والتوعية فقط. يمنع استخدامه لأي أغراض غير قانونية أو انتهاك خصوصية الآخرين دون موافقتهم الصريحة.</p>
        </div>
        
        <div class="section">
            <h2 class="section-title"><i class="fas fa-link"></i> إنشاء رابط تتبع جديد</h2>
            <form id="trackingForm">
                <div class="form-group">
                    <label for="targetUrl"><i class="fas fa-globe"></i> الرابط المستهدف (اختياري):</label>
                    <input type="url" id="targetUrl" name="targetUrl" 
                           placeholder="https://example.com أو اتركه فارغاً لرابط مباشر">
                </div>
                
                <div class="consent-checkbox">
                    <input type="checkbox" id="consent" name="consent" required>
                    <label for="consent">
                        <strong>أقر وأتعهد:</strong> أن استخدامي لهذا النظام هو لأغراض تعليمية وتوعية فقط، 
                        وسأحصل على موافقة صريحة من أي شخص سأرسل له رابط التتبع. أدرك أن سوء الاستخدام قد يعرضني للمساءلة القانونية.
                    </label>
                </div>
                
                <button type="submit" class="btn">
                    <i class="fas fa-plus-circle"></i> إنشاء رابط تتبع
                </button>
            </form>
        </div>
        
        <div class="section" id="trackingLinksSection" style="display:none;">
            <h2 class="section-title"><i class="fas fa-history"></i> روابط التتبع النشطة</h2>
            <div id="linksContainer"></div>
        </div>
        
        <div class="section" id="locationsSection" style="display:none;">
            <h2 class="section-title"><i class="fas fa-map-marked-alt"></i> المواقع المسجلة</h2>
            <div id="locationsContainer"></div>
        </div>
        
        <div class="section">
            <h2 class="section-title"><i class="fas fa-chart-bar"></i> إحصائيات النظام</h2>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number" id="totalLinks">0</div>
                    <div class="stat-label">روابط نشطة</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="totalLocations">0</div>
                    <div class="stat-label">موقع مسجل</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="activeUsers">0</div>
                    <div class="stat-label">مستخدم نشط</div>
                </div>
            </div>
        </div>
        
        <footer>
            <p>© 2024 نظام التتبع التعليمي - للأغراض التعليمية والتوعية فقط</p>
            <p>للاستخدام السليم والمسؤول للتكنولوجيا</p>
            <p style="margin-top: 15px;">
                <a href="/ethical_guide" class="btn" style="padding: 10px 20px; font-size: 0.9rem;">
                    <i class="fas fa-book"></i> دليل الاستخدام الأخلاقي
                </a>
            </p>
        </footer>
    </div>
    
    <script>
        // تحديث الإحصائيات
        function updateStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('totalLinks').textContent = data.active_links;
                    document.getElementById('totalLocations').textContent = data.total_locations;
                    document.getElementById('activeUsers').textContent = data.active_users;
                });
        }
        
        // إنشاء رابط تتبع
        document.getElementById('trackingForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const targetUrl = document.getElementById('targetUrl').value;
            
            fetch('/api/create_tracking_link', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ target_url: targetUrl })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('✅ تم إنشاء رابط التتبع بنجاح!');
                    updateStats();
                    loadTrackingLinks();
                } else {
                    alert('❌ ' + data.error);
                }
            });
        });
        
        // تحميل روابط التتبع
        function loadTrackingLinks() {
            fetch('/api/tracking_links')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('linksContainer');
                    if (data.links.length > 0) {
                        document.getElementById('trackingLinksSection').style.display = 'block';
                        container.innerHTML = '';
                        
                        data.links.forEach(link => {
                            const linkCard = document.createElement('div');
                            linkCard.className = 'link-card';
                            
                            const trackingUrl = `${window.location.origin}/track/${link.id}`;
                            const qrCodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(trackingUrl)}`;
                            
                            linkCard.innerHTML = `
                                <h3><i class="fas fa-link"></i> رابط التتبع</h3>
                                <div class="link-code">${trackingUrl}</div>
                                <img src="${qrCodeUrl}" alt="QR Code" style="max-width: 150px; margin: 10px 0;">
                                <p><strong>تاريخ الإنشاء:</strong> ${new Date(link.created_at).toLocaleString('ar-SA')}</p>
                                <div style="margin-top: 15px;">
                                    <button onclick="copyLink('${trackingUrl}')" class="btn" style="padding: 10px 20px;">
                                        <i class="fas fa-copy"></i> نسخ الرابط
                                    </button>
                                    <button onclick="deleteLink('${link.id}')" class="btn btn-danger" style="padding: 10px 20px;">
                                        <i class="fas fa-trash"></i> حذف
                                    </button>
                                </div>
                            `;
                            container.appendChild(linkCard);
                        });
                    }
                });
        }
        
        // تحميل المواقع
        function loadLocations() {
            fetch('/api/locations')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('locationsContainer');
                    if (data.locations.length > 0) {
                        document.getElementById('locationsSection').style.display = 'block';
                        container.innerHTML = '';
                        
                        data.locations.forEach(loc => {
                            const locationItem = document.createElement('div');
                            locationItem.className = 'location-item';
                            
                            const mapUrl = `https://www.google.com/maps?q=${loc.latitude},${loc.longitude}`;
                            const time = new Date(loc.timestamp).toLocaleString('ar-SA');
                            
                            locationItem.innerHTML = `
                                <div class="location-info">
                                    <strong>رابط: ${loc.link_id.substring(0, 8)}...</strong><br>
                                    <span>${loc.latitude}, ${loc.longitude}</span><br>
                                    <small class="location-time">${time}</small>
                                </div>
                                <div>
                                    <a href="${mapUrl}" target="_blank" class="map-link">
                                        <i class="fas fa-map"></i> عرض على الخريطة
                                    </a>
                                </div>
                            `;
                            container.appendChild(locationItem);
                        });
                    }
                });
        }
        
        // نسخ الرابط
        function copyLink(url) {
            navigator.clipboard.writeText(url).then(() => {
                alert('✅ تم نسخ الرابط إلى الحافظة');
            });
        }
        
        // حذف رابط
        function deleteLink(linkId) {
            if (confirm('⚠️ هل أنت متأكد من حذف رابط التتبع؟ سيتم حذف جميع المواقع المرتبطة به.')) {
                fetch(`/api/delete_link/${linkId}`, { method: 'DELETE' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('✅ تم الحذف بنجاح');
                            loadTrackingLinks();
                            loadLocations();
                            updateStats();
                        }
                    });
            }
        }
        
        // التحديث التلقائي
        setInterval(() => {
            updateStats();
            loadTrackingLinks();
            loadLocations();
        }, 5000);
        
        // التحميل الأولي
        document.addEventListener('DOMContentLoaded', function() {
            updateStats();
            loadTrackingLinks();
            loadLocations();
        });
    </script>
</body>
</html>
'''

TRACKING_PAGE_HTML = '''
<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📍 طلب إذن الموقع الجغرافي</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 25px;
            box-shadow: 0 30px 80px rgba(0, 0, 0, 0.4);
            width: 100%;
            max-width: 500px;
            overflow: hidden;
            animation: slideIn 0.6s ease-out;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        header {
            background: linear-gradient(to right, #4f46e5, #7c3aed);
            color: white;
            padding: 40px;
            text-align: center;
            position: relative;
        }
        
        .location-icon {
            font-size: 4rem;
            margin-bottom: 20px;
            animation: bounce 2s infinite;
        }
        
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
        
        h1 {
            font-size: 2rem;
            margin-bottom: 10px;
        }
        
        .target-url {
            background: rgba(255, 255, 255, 0.2);
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            word-break: break-all;
        }
        
        .consent-box {
            background: #fef3c7;
            border: 2px solid #f59e0b;
            border-radius: 15px;
            padding: 25px;
            margin: 20px;
        }
        
        .consent-title {
            color: #92400e;
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .consent-text {
            color: #78350f;
            line-height: 1.6;
        }
        
        .permission-buttons {
            padding: 30px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .btn {
            padding: 20px;
            border: none;
            border-radius: 15px;
            font-size: 1.2rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
        }
        
        .btn-primary {
            background: linear-gradient(to right, #10b981, #059669);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(16, 185, 129, 0.4);
        }
        
        .btn-secondary {
            background: #f3f4f6;
            color: #4b5563;
            border: 2px solid #d1d5db;
        }
        
        .btn-secondary:hover {
            background: #e5e7eb;
        }
        
        .location-data {
            padding: 20px;
            display: none;
        }
        
        .data-item {
            background: #f8fafc;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .redirect-message {
            text-align: center;
            padding: 30px;
            color: #059669;
            font-size: 1.2rem;
            display: none;
        }
        
        footer {
            text-align: center;
            padding: 20px;
            color: #6b7280;
            font-size: 0.9rem;
            border-top: 1px solid #e5e7eb;
        }
        
        .progress-bar {
            height: 5px;
            background: #e5e7eb;
            border-radius: 2.5px;
            margin: 20px 0;
            overflow: hidden;
            display: none;
        }
        
        .progress {
            height: 100%;
            background: linear-gradient(to right, #10b981, #059669);
            width: 0%;
            transition: width 0.3s;
        }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <div class="container">
        <header>
            <div class="location-icon">
                <i class="fas fa-map-marker-alt"></i>
            </div>
            <h1>طلب الإذن بالوصول للموقع</h1>
            <p>لتتمكن من المتابعة، نحتاج إذنك للحصول على موقعك الجغرافي</p>
            
            {% if target_url %}
            <div class="target-url">
                <i class="fas fa-external-link-alt"></i>
                سيتم توجيهك إلى: {{ target_url }}
            </div>
            {% endif %}
        </header>
        
        <div class="consent-box">
            <div class="consent-title">
                <i class="fas fa-shield-alt"></i>
                <h3>موافقة المستخدم</h3>
            </div>
            <div class="consent-text">
                <p>بإعطاء الإذن، أنت توافق على مشاركة موقعك الجغرافي الحالي مع مالك الرابط. هذا الموقع قد يستخدم لأغراض تعليمية وتوعية فقط.</p>
                <p><strong>⚠️ تحذير:</strong> لا تعطِ الإذن إلا للأشخاص الذين تثق بهم.</p>
            </div>
        </div>
        
        <div class="permission-buttons">
            <button onclick="requestLocation()" class="btn btn-primary">
                <i class="fas fa-check-circle"></i> أعطي الإذن للموقع
            </button>
            
            <button onclick="denyLocation()" class="btn btn-secondary">
                <i class="fas fa-times-circle"></i> رفض مشاركة الموقع
            </button>
        </div>
        
        <div class="progress-bar" id="progressBar">
            <div class="progress" id="progress"></div>
        </div>
        
        <div class="redirect-message" id="redirectMessage">
            <i class="fas fa-spinner fa-spin"></i>
            <p>جاري إرسال الموقع والتوجيه...</p>
        </div>
        
        <div class="location-data" id="locationData">
            <!-- سيتم عرض بيانات الموقع هنا -->
        </div>
        
        <footer>
            <p>📍 نظام التتبع التعليمي - للأغراض التعليمية والتوعية فقط</p>
        </footer>
    </div>
    
    <script>
        const linkId = '{{ link_id }}';
        const targetUrl = '{{ target_url or "" }}';
        
        function requestLocation() {
            document.getElementById('progressBar').style.display = 'block';
            document.getElementById('progress').style.width = '30%';
            
            if ("geolocation" in navigator) {
                navigator.geolocation.getCurrentPosition(
                    function(position) {
                        document.getElementById('progress').style.width = '60%';
                        
                        const locationData = {
                            latitude: position.coords.latitude,
                            longitude: position.coords.longitude,
                            accuracy: position.coords.accuracy,
                            timestamp: new Date().toISOString(),
                            link_id: linkId
                        };
                        
                        // إرسال الموقع إلى الخادم
                        fetch('/api/save_location', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify(locationData)
                        })
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('progress').style.width = '90%';
                            
                            if (data.success) {
                                // عرض بيانات الموقع
                                const locationDiv = document.getElementById('locationData');
                                locationDiv.style.display = 'block';
                                locationDiv.innerHTML = `
                                    <div class="data-item">
                                        <span><i class="fas fa-map-pin"></i> خط العرض:</span>
                                        <strong>${position.coords.latitude.toFixed(6)}</strong>
                                    </div>
                                    <div class="data-item">
                                        <span><i class="fas fa-map-pin"></i> خط الطول:</span>
                                        <strong>${position.coords.longitude.toFixed(6)}</strong>
                                    </div>
                                    <div class="data-item">
                                        <span><i class="fas fa-bullseye"></i> الدقة:</span>
                                        <strong>${Math.round(position.coords.accuracy)} متر</strong>
                                    </div>
                                `;
                                
                                document.getElementById('progress').style.width = '100%';
                                
                                // التوجيه إذا كان هناك رابط مستهدف
                                if (targetUrl) {
                                    document.getElementById('redirectMessage').style.display = 'block';
                                    setTimeout(() => {
                                        window.location.href = targetUrl;
                                    }, 3000);
                                } else {
                                    document.getElementById('redirectMessage').innerHTML = `
                                        <i class="fas fa-check-circle" style="color: #10b981; font-size: 3rem;"></i>
                                        <p style="margin-top: 15px;">✅ تم إرسال موقعك بنجاح</p>
                                        <button onclick="window.close()" class="btn btn-primary" style="margin-top: 20px; padding: 10px 20px;">
                                            <i class="fas fa-times"></i> إغلاق الصفحة
                                        </button>
                                    `;
                                    document.getElementById('redirectMessage').style.display = 'block';
                                }
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            alert('حدث خطأ في إرسال الموقع');
                        });
                    },
                    function(error) {
                        alert('❌ لم يتم الحصول على إذن الموقع. لا يمكن المتابعة.');
                        console.error('Geolocation error:', error);
                    },
                    {
                        enableHighAccuracy: true,
                        timeout: 10000,
                        maximumAge: 0
                    }
                );
            } else {
                alert('❌ المتصفح لا يدعم الخدمة الجغرافية');
            }
        }
        
        function denyLocation() {
            alert('تم رفض مشاركة الموقع. لن تتمكن من المتابعة.');
            if (targetUrl) {
                window.location.href = targetUrl;
            }
        }
        
        // تحذير عند مغادرة الصفحة
        window.addEventListener('beforeunload', function (e) {
            e.preventDefault();
            e.returnValue = 'إذا غادرت الآن، قد لا تتم مشاركة موقعك. هل أنت متأكد؟';
        });
    </script>
</body>
</html>
'''

ETHICAL_GUIDE_HTML = '''
<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📚 دليل الاستخدام الأخلاقي</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 25px;
            box-shadow: 0 30px 80px rgba(0, 0, 0, 0.4);
            overflow: hidden;
        }
        
        header {
            background: linear-gradient(to right, #1e40af, #1d4ed8);
            color: white;
            padding: 60px 40px;
            text-align: center;
        }
        
        h1 {
            font-size: 3rem;
            margin-bottom: 20px;
        }
        
        .subtitle {
            font-size: 1.3rem;
            opacity: 0.9;
            max-width: 800px;
            margin: 0 auto;
            line-height: 1.6;
        }
        
        .guide-section {
            padding: 40px;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .section-title {
            color: #1d4ed8;
            font-size: 2rem;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .section-content {
            line-height: 1.8;
            font-size: 1.1rem;
            color: #4b5563;
        }
        
        .do-dont {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin: 30px 0;
        }
        
        .do-box, .dont-box {
            padding: 25px;
            border-radius: 15px;
            border: 2px solid;
        }
        
        .do-box {
            border-color: #10b981;
            background: #f0fdf4;
        }
        
        .dont-box {
            border-color: #ef4444;
            background: #fef2f2;
        }
        
        .do-box h3, .dont-box h3 {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .do-box h3 {
            color: #047857;
        }
        
        .dont-box h3 {
            color: #dc2626;
        }
        
        ul {
            padding-right: 20px;
            margin: 15px 0;
        }
        
        li {
            margin-bottom: 10px;
            line-height: 1.6;
        }
        
        .video-guide {
            background: #f8fafc;
            padding: 30px;
            border-radius: 15px;
            margin: 30px 0;
            text-align: center;
        }
        
        .legal-note {
            background: #fef3c7;
            border: 2px solid #f59e0b;
            padding: 25px;
            border-radius: 15px;
            margin: 30px 0;
        }
        
        .btn {
            display: inline-block;
            padding: 15px 35px;
            background: linear-gradient(to right, #10b981, #059669);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            text-align: center;
            margin: 10px;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(16, 185, 129, 0.4);
        }
        
        footer {
            text-align: center;
            padding: 40px;
            color: #6b7280;
            background: #f9fafb;
        }
        
        @media (max-width: 768px) {
            .do-dont {
                grid-template-columns: 1fr;
            }
            
            header {
                padding: 40px 20px;
            }
            
            h1 {
                font-size: 2.2rem;
            }
        }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <div class="container">
        <header>
            <h1><i class="fas fa-graduation-cap"></i> دليل الاستخدام الأخلاقي</h1>
            <p class="subtitle">
                دليل شامل للاستخدام المسؤول والأخلاقي لنظام تتبع المواقع الجغرافي للأغراض التعليمية والتوعوية
            </p>
        </header>
        
        <div class="guide-section">
            <h2 class="section-title">
                <i class="fas fa-info-circle"></i>
                مقدمة
            </h2>
            <div class="section-content">
                <p>نظام تتبع المواقع الجغرافي هو أداة قوية يمكن استخدامها لأغراض بناءة أو هدامة. هذا الدليل يهدف إلى توجيه المستخدمين للاستخدام الأخلاقي والمسؤول للنظام.</p>
                <p><strong>تذكر:</strong> القوة تأتي مع المسؤولية. استخدامك للنظام يعني أنك تتحمل مسؤولية أخلاقية وقانونية عن كيفية استخدامه.</p>
            </div>
        </div>
        
        <div class="guide-section">
            <h2 class="section-title">
                <i class="fas fa-balance-scale"></i>
                الأخلاقيات والمسؤولية
            </h2>
            <div class="do-dont">
                <div class="do-box">
                    <h3><i class="fas fa-check-circle"></i> ما يجب فعله ✅</h3>
                    <ul>
                        <li>الحصول على موافقة صريحة ومستنيرة قبل تتبع أي شخص</li>
                        <li>التوضيح الكامل للغرض من التتبع</li>
                        <li>استخدام النظام للأغراض التعليمية والتوعوية فقط</li>
                        <li>حذف البيانات بعد انتهاء الغرض منها</li>
                        <li>احترام خصوصية الآخرين</li>
                        <li>استخدام النظام في الأبحاث الأكاديمية مع إشراف</li>
                    </ul>
                </div>
                
                <div class="dont-box">
                    <h3><i class="fas fa-times-circle"></i> ما يجب تجنبه ❌</h3>
                    <ul>
                        <li>تتبع الأشخاص دون علمهم أو موافقتهم</li>
                        <li>استخدام النظام للملاحقة أو المضايقة</li>
                        <li>انتهاك خصوصية الآخرين</li>
                        <li>استخدام البيانات لأغراض تجارية غير مصرح بها</li>
                        <li>التشويش على عمل السلطات الأمنية</li>
                        <li>انتهاك قوانين حماية البيانات</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <div class="guide-section">
            <h2 class="section-title">
                <i class="fas fa-gavel"></i>
                الجوانب القانونية
            </h2>
            <div class="section-content">
                <div class="legal-note">
                    <h3><i class="fas fa-exclamation-triangle"></i> تحذير قانوني مهم</h3>
                    <p>تتبع الأشخاص دون موافقتهم قد يعتبر جريمة في العديد من الدول والقوانين، بما في ذلك:</p>
                    <ul>
                        <li>قوانين الخصوصية وحماية البيانات</li>
                        <li>قوانين المطاردة والملاحقة (Stalking Laws)</li>
                        <li>قوانين الجرائم الإلكترونية</li>
                        <li>قوانين انتهاك حرمة الحياة الخاصة</li>
                    </ul>
                    <p><strong>العقوبات قد تشمل:</strong> غرامات مالية، سجن، سجل جنائي.</p>
                </div>
            </div>
        </div>
        
        <div class="guide-section">
            <h2 class="section-title">
                <i class="fas fa-chalkboard-teacher"></i>
                استخدامات تعليمية مشروعة
            </h2>
            <div class="section-content">
                <ul>
                    <li><strong>التوعية الأمنية:</strong> عرض كيف يمكن اختراق الخصوصية</li>
                    <li><strong>الدروس التعليمية:</strong> تعليم طلاب التقنية عن أنظمة التتبع</li>
                    <li><strong>البحوث الأكاديمية:</strong> دراسات عن أنماط الحركة مع موافقة المشاركين</li>
                    <li><strong>تدريبات الشرطة:</strong> عمليات تدريبية مشروعة</li>
                    <li><strong>حماية الأطفال:</strong> بتفويض من الوالدين فقط</li>
                    <li><strong>الأبحاث الاجتماعية:</strong> مع موافقة لجان الأخلاقيات</li>
                </ul>
            </div>
        </div>
        
        <div class="guide-section">
            <h2 class="section-title">
                <i class="fas fa-shield-alt"></i>
                أفضل الممارسات الأمنية
            </h2>
            <div class="section-content">
                <ul>
                    <li>استخدم كلمات مرور قوية للنظام</li>
                    <li>شفر البيانات الحساسة</li>
                    <li>احذف البيانات غير الضرورية</li>
                    <li>استخدم النظام في بيئات محكمة</li>
                    <li>سجل جميع عمليات الوصول</li>
                    <li>راجع الصلاحيات بانتظام</li>
                </ul>
            </div>
        </div>
        
        <div class="video-guide">
            <h3><i class="fas fa-video"></i> دليل فيديو تعليمي</h3>
            <p>شاهد هذا الفيديو التعليمي لفهم الاستخدام الأخلاقي للنظام:</p>
            <div style="max-width: 800px; margin: 20px auto; background: #000; padding: 20px; border-radius: 10px;">
                <div style="background: #333; height: 300px; display: flex; align-items: center; justify-content: center; color: white; border-radius: 8px;">
                    <i class="fas fa-play-circle" style="font-size: 4rem;"></i>
                    <p style="margin-right: 15px;">فيديو تعليمي - الاستخدام الأخلاقي للتتبع</p>
                </div>
            </div>
            <p style="margin-top: 15px; color: #666;">
                <small>ملاحظة: هذا نموذج توضيحي. في التطبيق الفعلي، سيتم إضافة فيديو تعليمي حقيقي.</small>
            </p>
        </div>
        
        <div class="guide-section">
            <h2 class="section-title">
                <i class="fas fa-file-contract"></i>
                نموذج موافقة مستخدم
            </h2>
            <div class="section-content">
                <p>نموذج موافقة يجب الحصول عليه قبل استخدام النظام:</p>
                <div style="background: #f8fafc; padding: 25px; border-radius: 10px; border: 2px dashed #d1d5db; margin: 20px 0;">
                    <h4 style="color: #1d4ed8; margin-bottom: 15px;">نموذج موافقة على التتبع الجغرافي</h4>
                    <p>أنا الموقع أدناه، أوافق على مشاركة موقعي الجغرافي مع _______________</p>
                    <p>الغرض من التتبع: ________________</p>
                    <p>مدة التتبع: من ______ إلى ______</p>
                    <p>أقر أنني:</p>
                    <ul>
                        <li>أفهم تماماً الغرض من التتبع</li>
                        <li>أعطي موافقتي طواعية ودون إكراه</li>
                        <li>لي الحق في سحب الموافقة في أي وقت</li>
                        <li>أفهم أن بياناتي ستستخدم للأغراض المذكورة فقط</li>
                    </ul>
                    <p>التوقيع: ________________</p>
                    <p>التاريخ: ________________</p>
                </div>
            </div>
        </div>
        
        <footer>
            <h3>مسؤوليتنا تجاه المجتمع الرقمي</h3>
            <p>التكنولوجيا أداة، واستخدامها يعكس قيمنا وأخلاقنا. لنكن مستخدمين مسؤولين.</p>
            <div style="margin-top: 30px;">
                <a href="/" class="btn">
                    <i class="fas fa-arrow-right"></i> العودة للنظام
                </a>
                <a href="https://www.example.com/ethical-tech" target="_blank" class="btn" style="background: linear-gradient(to right, #3b82f6, #1d4ed8);">
                    <i class="fas fa-external-link-alt"></i> موارد إضافية
                </a>
            </div>
            <p style="margin-top: 30px; font-size: 0.9rem; color: #9ca3af;">
                © 2024 - دليل الاستخدام الأخلاقي - جميع الحقوق محفوظة
            </p>
        </footer>
    </div>
</body>
</html>
'''

# ========== Telegram Bot Handlers ==========
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """ترحيب بالبوت"""
    welcome_text = """
🤖 *مرحباً بك في نظام التتبع التعليمي*

📍 *الأوامر المتاحة:*
/newlink - إنشاء رابط تتبع جديد
/mylinks - عرض روابطك النشطة
/locations - عرض المواقع المسجلة
/stats - إحصائيات النظام
/guide - دليل الاستخدام الأخلاقي
/delete_all - حذف جميع بياناتك

⚠️ *تحذير مهم:*
هذا النظام للأغراض التعليمية والتوعية فقط.
يجب الحصول على موافقة صريحة قبل تتبع أي شخص.
سوء الاستخدام قد يعرضك للمساءلة القانونية.

📚 اقرأ /guide للاستخدام الأخلاقي
    """
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['newlink'])
def new_tracking_link(message):
    """إنشاء رابط تتبع جديد"""
    try:
        user_id = message.from_user.id
        
        # إنشاء رابط فريد
        link_id = str(uuid.uuid4())[:12]
        tracking_url = f"https://telegram-tracking-bot-35hp.onrender.com/track/{link_id}"
        
        # حفظ الرابط في قاعدة البيانات
        tracking_links[link_id] = {
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'locations': [],
            'target_url': None
        }
        
        if user_id not in user_sessions:
            user_sessions[user_id] = {'active_links': [], 'current_target': None}
        
        user_sessions[user_id]['active_links'].append(link_id)
        
        # إرسال الرابط للمستخدم
        response_text = f"""
📍 *تم إنشاء رابط تتبع جديد*

🔗 *رابط التتبع:*
`{tracking_url}`

📱 *كود QR:*
https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={tracking_url}

⚠️ *التوجيهات الأخلاقية:*
1. يجب الحصول على موافقة صريحة من الشخص
2. التوضيح الكامل للغرض من التتبع
3. استخدام النظام للأغراض التعليمية فقط
4. احترام خصوصية الآخرين

📊 *لإضافة رابط مستهدف:*
أرسل `/target {link_id} https://example.com`
        """
        
        bot.reply_to(message, response_text, parse_mode='Markdown')
        
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {str(e)}")

@bot.message_handler(commands=['target'])
def set_target_url(message):
    """تعيين رابط مستهدف لرابط التتبع"""
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ صيغة خاطئة\nاستخدم: `/target link_id https://example.com`", parse_mode='Markdown')
            return
        
        link_id = parts[1]
        target_url = parts[2]
        
        if link_id in tracking_links:
            tracking_links[link_id]['target_url'] = target_url
            
            bot.reply_to(message, f"""
✅ *تم تعيين الرابط المستهدف*

🔗 رابط التتبع: `{link_id}`
🎯 الرابط المستهدف: {target_url}

📍 عند دخول المستخدم للرابط:
1. سيطلب منه إذن الموقع
2. سيتم حفظ موقعه
3. سيتم توجيهه للرابط المستهدف
            """, parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ رابط التتبع غير موجود")
            
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {str(e)}")

@bot.message_handler(commands=['mylinks'])
def show_my_links(message):
    """عرض روابط التتبع الخاصة بالمستخدم"""
    user_id = message.from_user.id
    
    if user_id not in user_sessions or not user_sessions[user_id]['active_links']:
        bot.reply_to(message, "📭 ليس لديك روابط تتبع نشطة\nاستخدم /newlink لإنشاء رابط جديد")
        return
    
    links_text = "📍 *روابط التتبع الخاصة بك:*\n\n"
    
    for link_id in user_sessions[user_id]['active_links']:
        if link_id in tracking_links:
            link = tracking_links[link_id]
            tracking_url = f"https://telegram-tracking-bot-35hp.onrender.com/track/{link_id}"
            locations_count = len(link['locations'])
            target_url = link.get('target_url', 'لا يوجد')
            
            links_text += f"""
🔗 *الرابط:* `{link_id}`
📊 المواقع المسجلة: *{locations_count}*
🎯 الرابط المستهدف: {target_url}
📅 التاريخ: {link['created_at']}
"""
    
    bot.reply_to(message, links_text, parse_mode='Markdown')

@bot.message_handler(commands=['locations'])
def show_locations(message):
    """عرض المواقع المسجلة"""
    user_id = message.from_user.id
    
    all_locations = []
    for link_id, link_data in tracking_links.items():
        if link_data['user_id'] == user_id:
            all_locations.extend(link_data['locations'])
    
    if not all_locations:
        bot.reply_to(message, "📍 لم يتم تسجيل أي مواقع بعد")
        return
    
    # عرض آخر 10 مواقع
    recent_locations = sorted(all_locations, key=lambda x: x['timestamp'], reverse=True)[:10]
    
    locations_text = "📍 *آخر المواقع المسجلة:*\n\n"
    
    for loc in recent_locations:
        map_url = f"https://www.google.com/maps?q={loc['latitude']},{loc['longitude']}"
        time = datetime.fromisoformat(loc['timestamp']).strftime("%Y-%m-%d %H:%M")
        
        locations_text += f"""
📌 *الموقع:*
• خط العرض: `{loc['latitude']}`
• خط الطول: `{loc['longitude']}`
• الدقة: `{loc['accuracy']} متر`
• التاريخ: {time}
• [عرض على الخريطة]({map_url})
"""
    
    bot.reply_to(message, locations_text, parse_mode='Markdown', disable_web_page_preview=True)

@bot.message_handler(commands=['stats'])
def show_stats(message):
    """عرض إحصائيات النظام"""
    user_id = message.from_user.id
    
    user_links = [link_id for link_id, data in tracking_links.items() if data['user_id'] == user_id]
    user_locations = sum(len(tracking_links[link_id]['locations']) for link_id in user_links)
    
    total_users = len(user_sessions)
    total_links = len(tracking_links)
    total_locations = sum(len(data['locations']) for data in tracking_links.values())
    
    stats_text = f"""
📊 *إحصائيات النظام:*

👤 *إحصائياتك الشخصية:*
• روابط التتبع: *{len(user_links)}*
• مواقع مسجلة: *{user_locations}*

🌐 *إحصائيات النظام الكلية:*
• المستخدمون النشطون: *{total_users}*
• روابط التتبع: *{total_links}*
• مواقع مسجلة: *{total_locations}*

⚠️ *تذكر:* هذه البيانات للأغراض التعليمية فقط
"""
    
    bot.reply_to(message, stats_text, parse_mode='Markdown')

@bot.message_handler(commands=['guide'])
def ethical_guide(message):
    """إرسال دليل الاستخدام الأخلاقي"""
    guide_text = """
📚 *دليل الاستخدام الأخلاقي للنظام*

🔍 *مقدمة:*
نظام تتبع المواقع أداة قوية يجب استخدامها بمسؤولية.

✅ *الاستخدامات المشروعة:*
1. الأبحاث الأكاديمية (مع موافقة)
2. التوعية الأمنية
3. حماية الأطفال (بتفويض الوالدين)
4. التدريبات التعليمية

❌ *الاستخدامات الممنوعة:*
1. تتبع الأشخاص دون موافقتهم
2. الملاحقة أو المضايقة
3. انتهاك الخصوصية
4. الأغراض التجارية غير المصرح بها

⚖️ *الجوانب القانونية:*
• تتبع الأشخاص دون موافقة قد يعتبر جريمة
• انتهاك قوانين حماية البيانات
• قوانين الملاحقة (Stalking Laws)

📋 *نموذج الموافقة:*
يجب الحصول على موافقة كتابية تتضمن:
1. الغرض من التتبع
2. مدة التتبع
3. طريقة استخدام البيانات
4. حق المستخدم في سحب الموافقة

🔗 *رابط الدليل الكامل:*
https://telegram-tracking-bot-35hp.onrender.com/ethical_guide

⚠️ *مسؤوليتك:* أنت المسؤول عن استخدام النظام
"""
    
    bot.reply_to(message, guide_text, parse_mode='Markdown')

@bot.message_handler(commands=['delete_all'])
def delete_all_data(message):
    """حذف جميع بيانات المستخدم"""
    user_id = message.from_user.id
    
    # إنشاء زر تأكيد
    from telebot import types
    markup = types.InlineKeyboardMarkup()
    confirm_btn = types.InlineKeyboardButton("✅ نعم، احذف كل شيء", callback_data="delete_confirm")
    cancel_btn = types.InlineKeyboardButton("❌ إلغاء", callback_data="delete_cancel")
    markup.add(confirm_btn, cancel_btn)
    
    bot.reply_to(message, """
⚠️ *تحذير: سيتم حذف جميع بياناتك*

❌ *سيتم حذف:*
• جميع روابط التتبع الخاصة بك
• جميع المواقع المسجلة
• جميع إحصائياتك

🔄 *لا يمكن استعادة البيانات بعد الحذف*

هل أنت متأكد من رغبتك في حذف جميع بياناتك؟
""", parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """معالجة الأزرار"""
    if call.data == "delete_confirm":
        user_id = call.from_user.id
        
        # حذف جميع بيانات المستخدم
        links_to_delete = [link_id for link_id, data in tracking_links.items() if data['user_id'] == user_id]
        
        for link_id in links_to_delete:
            del tracking_links[link_id]
        
        if user_id in user_sessions:
            del user_sessions[user_id]
        
        bot.answer_callback_query(call.id, "✅ تم حذف جميع بياناتك")
        bot.edit_message_text(
            "✅ *تم حذف جميع بياناتك بنجاح*\n\nيمكنك البدء من جديد باستخدام /newlink",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )
    
    elif call.data == "delete_cancel":
        bot.answer_callback_query(call.id, "❌ تم إلغاء الحذف")
        bot.edit_message_text(
            "❌ *تم إلغاء عملية الحذف*\n\nبياناتك لا تزال محفوظة",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )

# ========== Flask Routes ==========
@app.route('/')
def home():
    """الصفحة الرئيسية"""
    return render_template_string(INDEX_HTML)

@app.route('/ethical_guide')
def ethical_guide_page():
    """صفحة الدليل الأخلاقي"""
    return render_template_string(ETHICAL_GUIDE_HTML)

@app.route('/track/<link_id>')
def tracking_page(link_id):
    """صفحة طلب إذن الموقع"""
    if link_id not in tracking_links:
        return "❌ رابط التتبع غير صالح أو منتهي الصلاحية", 404
    
    target_url = tracking_links[link_id].get('target_url', '')
    
    return render_template_string(
        TRACKING_PAGE_HTML,
        link_id=link_id,
        target_url=target_url
    )

# ========== API Routes ==========
@app.route('/api/create_tracking_link', methods=['POST'])
def api_create_tracking_link():
    """إنشاء رابط تتبع جديد عبر API"""
    try:
        data = request.json
        target_url = data.get('target_url', '').strip()
        
        # إنشاء رابط فريد
        link_id = str(uuid.uuid4())[:12]
        
        # في الواقع، هنا يجب حفظ user_id من الجلسة
        # لكن للتبسيط سنستخدم user_id افتراضي
        user_id = 'web_user'
        
        tracking_links[link_id] = {
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'locations': [],
            'target_url': target_url if target_url else None
        }
        
        tracking_url = f"{request.host_url}track/{link_id}"
        
        return jsonify({
            'success': True,
            'link_id': link_id,
            'tracking_url': tracking_url,
            'qr_code': f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={tracking_url}"
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/save_location', methods=['POST'])
def api_save_location():
    """حفظ الموقع الجغرافي"""
    try:
        data = request.json
        link_id = data.get('link_id')
        
        if link_id not in tracking_links:
            return jsonify({'success': False, 'error': 'رابط غير صالح'}), 400
        
        # حفظ الموقع
        location_data = {
            'latitude': data['latitude'],
            'longitude': data['longitude'],
            'accuracy': data['accuracy'],
            'timestamp': data['timestamp'],
            'user_agent': request.headers.get('User-Agent', ''),
            'ip': request.remote_addr
        }
        
        tracking_links[link_id]['locations'].append(location_data)
        
        # في الواقع، هنا يجب إرسال إشعار للمستخدم عبر Telegram
        # لكن للتبسيط سنكتفي بحفظ البيانات
        
        logger.info(f"📍 موقع جديد: {location_data}")
        
        return jsonify({'success': True, 'message': 'تم حفظ الموقع'})
        
    except Exception as e:
        logger.error(f"❌ خطأ في حفظ الموقع: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tracking_links')
def api_get_tracking_links():
    """الحصول على قائمة روابط التتبع"""
    # في الواقع، هنا يجب تصفية حسب المستخدم
    links = []
    for link_id, data in tracking_links.items():
        links.append({
            'id': link_id,
            'created_at': data['created_at'],
            'locations_count': len(data['locations']),
            'target_url': data.get('target_url')
        })
    
    return jsonify({'links': links})

@app.route('/api/locations')
def api_get_locations():
    """الحصول على المواقع المسجلة"""
    # في الواقع، هنا يجب تصفية حسب المستخدم
    all_locations = []
    for link_id, data in tracking_links.items():
        for loc in data['locations']:
            loc['link_id'] = link_id
            all_locations.append(loc)
    
    # ترتيب حسب التاريخ (الأحدث أولاً)
    all_locations.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return jsonify({'locations': all_locations[:50]})  # آخر 50 موقع فقط

@app.route('/api/stats')
def api_get_stats():
    """الحصول على إحصائيات النظام"""
    total_links = len(tracking_links)
    total_locations = sum(len(data['locations']) for data in tracking_links.values())
    active_users = len(set(data['user_id'] for data in tracking_links.values()))
    
    return jsonify({
        'active_links': total_links,
        'total_locations': total_locations,
        'active_users': active_users
    })

@app.route('/api/delete_link/<link_id>', methods=['DELETE'])
def api_delete_link(link_id):
    """حذف رابط تتبع"""
    if link_id in tracking_links:
        del tracking_links[link_id]
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'رابط غير موجود'}), 404

# ========== تشغيل البوت في Thread منفصل ==========
def run_bot():
    """تشغيل بوت Telegram في thread منفصل"""
    while True:
        try:
            logger.info("🤖 بدء تشغيل بوت Telegram...")
            bot.remove_webhook()
            bot.polling(none_stop=True, timeout=30)
        except Exception as e:
            logger.error(f"❌ خطأ في البوت: {e}")
            time.sleep(10)

# ========== بدء التشغيل ==========
if __name__ == '__main__':
    # تشغيل البوت في thread منفصل
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    logger.info("🚀 بدء تشغيل نظام التتبع الجغرافي...")
    logger.info(f"🌐 الرابط: https://telegram-tracking-bot-35hp.onrender.com")
    logger.info("🤖 البوت: @cccc00bot")
    logger.info("=" * 50)
    logger.info("✅ النظام جاهز للاستخدام!")
    
    # تشغيل خادم Flask
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)