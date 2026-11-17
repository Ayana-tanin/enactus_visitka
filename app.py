from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
import json
import os
import smtplib
import re
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# Email настройки
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': os.environ.get('SENDER_EMAIL', ''),
    'sender_password': os.environ.get('SENDER_PASSWORD', ''),  # Пароль приложения Gmail (из переменной окружения)
    'sender_name': 'Enactus KSLA'
}

@app.route('/images/<filename>')
def images(filename):
    """Статический маршрут для изображений"""
    return send_from_directory('images', filename)

# Путь к файлу для хранения заявок
APPLICATIONS_FILE = 'applications.json'

def load_applications():
    """Загружает заявки из файла"""
    if os.path.exists(APPLICATIONS_FILE):
        with open(APPLICATIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def is_valid_email(email):
    """Проверяет валидность email адреса"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_welcome_email(recipient_email, recipient_name):
    """Отправляет приветственное письмо новому участнику"""
    try:
        # Создаем сообщение
        msg = MIMEMultipart()
        msg['From'] = f"{EMAIL_CONFIG['sender_name']} <{EMAIL_CONFIG['sender_email']}>"
        msg['To'] = recipient_email
        msg['Subject'] = "Поздравляем! Добро пожаловать в команду Enactus KSLA"
        
        # HTML содержимое письма
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #B22222; margin-bottom: 10px;">Поздравляем, {recipient_name}!</h1>
                    <h2 style="color: #666; font-weight: normal;">Добро пожаловать в команду Enactus KSLA!</h2>
                </div>
                
                <div style="background: #f9f9f9; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <p style="margin-bottom: 15px;">Мы рады вашему интересу к нашей организации!</p>
                    <p style="margin-bottom: 15px;">Enactus — это международная платформа, где студенты разрабатывают социально-предпринимательские проекты, комбинируя бизнес-мышление и общественную пользу.</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <p style="font-size: 18px; margin-bottom: 20px;"><strong>Следующий шаг:</strong></p>
                    <p style="margin-bottom: 20px;">Заполните форму для вступления в команду:</p>
                    <a href="https://docs.google.com/forms/d/e/1FAIpQLScqZXtD9wmYD7vTsvNDjANmRo-wlLFg_AiGSgrNN_9OdhVlaQ/viewform?fbclid=PAZXh0bgNhZW0CMTEAAacBg3gHgLNkMIffRSy2fm5Yjej3FeeGWldM5eD1uV4bddY0rBD5twryMxs_Lg_aem_88Ks9KBy1tAsZqS5sxy87w" 
                       style="display: inline-block; background: #B22222; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Заполнить форму вступления
                    </a>
                </div>
                
                <div style="border-top: 1px solid #ddd; padding-top: 20px; margin-top: 30px;">
                    <p style="margin-bottom: 10px;"><strong>Контакты:</strong></p>
                    <p style="margin: 5px 0;">📧 Email: enactusKSLA@gmail.com</p>
                    <p style="margin: 5px 0;">📱 Телефон: +996 551 996 106</p>
                    <a href="https://www.instagram.com/enactus_ksla/" style="margin: 5px 0;">📍 Instagram: @enactus_ksla</a>
                </div>
                
                <div style="text-align: center; margin-top: 30px; color: #666; font-size: 14px;">
                    <p>С уважением,<br>Команда Enactus KSLA</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        # Отправляем письмо
        if EMAIL_CONFIG['sender_password']:
            server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
            server.starttls()
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
            server.quit()
            return True
        else:
            print(f"Email не отправлен - не установлен пароль. Получатель: {recipient_email}")
            return False
            
    except Exception as e:
        print(f"Ошибка отправки email: {e}")
        return False

def save_application(name, phone, email):
    """Сохраняет новую заявку"""
    applications = load_applications()
    new_application = {
        'id': len(applications) + 1,
        'name': name,
        'phone': phone,
        'email': email,
        'timestamp': datetime.now().isoformat(),
        'status': 'new'
    }
    applications.append(new_application)
    
    with open(APPLICATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(applications, f, ensure_ascii=False, indent=2)
    
    return new_application

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/api/apply', methods=['POST'])
def apply():
    """API для подачи заявки на вступление"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        
        if not name or not phone or not email:
            return jsonify({
                'success': False,
                'message': 'Пожалуйста, заполните все поля'
            }), 400
        
        # Валидация email
        if not is_valid_email(email):
            return jsonify({
                'success': False,
                'message': 'Введите корректный email адрес'
            }), 400
        
        # Сохраняем заявку
        application = save_application(name, phone, email)
        
        # Автоматически отправляем приветственное письмо
        email_sent = send_welcome_email(email, name)
        
        # Формируем ответ
        if email_sent:
            message = 'Спасибо! Мы отправили вам письмо с дальнейшими инструкциями на указанный email.'
        else:
            message = 'Заявка принята! Письмо не удалось отправить, но мы свяжемся с вами по указанным контактам.'
        
        return jsonify({
            'success': True,
            'message': message,
            'application_id': application['id'],
            'email_sent': email_sent
        })
        
    except Exception as e:
        print(f"Ошибка в apply(): {e}")
        return jsonify({
            'success': False,
            'message': 'Произошла ошибка. Попробуйте позже.'
        }), 500

@app.route('/api/stats')
def stats():
    """API для получения статистики"""
    applications = load_applications()
    return jsonify({
        'total_applications': len(applications),
        'new_applications': len([app for app in applications if app['status'] == 'new']),
        'members': 120,
        'projects': 18,
        'founded_year': 2012
    })

@app.route('/admin')
def admin():
    """Админ панель для просмотра заявок"""
    applications = load_applications()
    email_configured = bool(EMAIL_CONFIG['sender_password'])
    return render_template('admin.html', 
                         applications=applications, 
                         email_configured=email_configured)

@app.route('/email_setup.md')
def email_setup():
    """Отдает инструкцию по настройке email"""
    return send_from_directory('.', 'email_setup.md')

@app.route('/api/test-email', methods=['POST'])
def test_email():
    """Тестирует отправку email"""
    try:
        data = request.get_json()
        test_email_addr = data.get('email', '').strip()
        
        if not test_email_addr or not is_valid_email(test_email_addr):
            return jsonify({
                'success': False,
                'message': 'Введите корректный email адрес'
            }), 400
        
        success = send_welcome_email(test_email_addr, 'Тестовый пользователь')
        
        return jsonify({
            'success': success,
            'message': 'Тестовое письмо отправлено!' if success else 'Ошибка отправки письма'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)