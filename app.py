from flask import Flask, render_template, request, redirect, session, url_for, flash
#import mysql.connector
import pandas as pd
from config import Config
import re
#import MySQLdb
from flask_mysqldb import MySQL
from werkzeug.middleware.proxy_fix import ProxyFix
import os
from MySQLdb.cursors import DictCursor
import openpyxl

# conn = mysql.connector.connect(
#     host="localhost",
#     user="root",
#     password="",
#     database="chatbot"
# )

app = Flask(__name__)
app.config.from_object(Config)

# Session ayarları
app.secret_key = Config.SECRET_KEY
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 dakika

# Render için proxy ayarları
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

mysql = MySQL(app)

# Güvenlik başlıklarını ekle
@app.after_request
def add_security_headers(response):
    for header, value in Config.SECURITY_HEADERS.items():
        response.headers[header] = value
    return response

# Verileri Excel'e kaydetme fonksiyonu
def save_to_excel(data):
    try:
        excel_file = 'chatbot_data.xlsx'
        
        # Eğer dosya varsa, mevcut verileri oku
        if os.path.exists(excel_file):
            df_existing = pd.read_excel(excel_file)
        else:
            # Yeni DataFrame oluştur
            df_existing = pd.DataFrame(columns=['Öğrenci No', 'Soru', 'Cevap', 'Geribildirim', 'Konu'])
        
        # Yeni veriyi DataFrame'e ekle
        new_data = {
            'Öğrenci No': data['student_number'],
            'Soru': data['question'],
            'Cevap': data['answer'],
            'Geribildirim': data['sentiment'],
            'Konu': data['topic'],
        }
        df_existing = pd.concat([df_existing, pd.DataFrame([new_data])], ignore_index=True)
        
        # Excel dosyasına kaydet
        df_existing.to_excel(excel_file, index=False)
        print(f"Veri Excel dosyasına kaydedildi: {excel_file}")
        
    except Exception as e:
        print(f"Excel'e kaydetme hatası: {e}")

@app.route('/', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        print("POST isteği alındı")  # Debug
        print("Form verileri:", request.form)  # Debug
        
        if 'student_number' in request.form and 'password' in request.form:
            student_number = request.form['student_number']
            password = request.form['password']
            print(f"Giriş denemesi - Öğrenci No: {student_number}")  # Debug
            
            cursor = mysql.connection.cursor(DictCursor)
            cursor.execute('SELECT * FROM users_tb WHERE student_number = %s AND password = %s', (student_number, password))
            account = cursor.fetchone()
            
            print("Veritabanı sonucu:", account)  # Debug
            
            if account:
                session['loggedin'] = True
                session['student_number'] = account['student_number']
                print("Session oluşturuldu:", session)  # Debug
                msg = 'Başarıyla giriş yapıldı!'
                return redirect('/chatbot')
            else:
                msg = 'Geçersiz kullanıcı adı veya şifre!'
        else:
            print("Eksik form verileri")  # Debug
            msg = 'Lütfen tüm alanları doldurun!'
    
    return render_template('login.html', msg=msg)

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'student_number' in request.form and 'password' in request.form and 'name' in request.form:
        student_number = request.form['student_number']
        password = request.form['password']
        name = request.form['name']
        cursor = mysql.connection.cursor(DictCursor)
        cursor.execute('SELECT * FROM users_tb WHERE student_number = %s', (student_number,))
        account = cursor.fetchone()
        if account:
            msg = 'Bu öğrenci numarası zaten kayıtlı!'
        elif not re.match(r'[0-9]+', student_number):
            msg = 'Öğrenci numarası sadece rakamlardan oluşmalıdır!'
        elif not re.match(r'[A-Za-z\s]+', name):
            msg = 'İsim sadece harflerden oluşmalıdır!'
        elif not student_number or not password or not name:
            msg = 'Tüm alanlar doldurulmalıdır!'
        else:
            cursor.execute('INSERT INTO users_tb (student_number, password, name) VALUES (%s, %s, %s)', (student_number, password, name))
            mysql.connection.commit()
            msg = 'Başarıyla kayıt oldunuz!'
            return redirect('/')
    return render_template('register.html', msg=msg)

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    print("\nChatbot route'una erişildi")  # Debug
    print("Session durumu:", session)  # Debug
    print("Request method:", request.method)  # Debug
    
    if not session.get('loggedin'):
        print("Kullanıcı giriş yapmamış, login sayfasına yönlendiriliyor")  # Debug
        return redirect('/')
    
    msg = ''
    if request.method == 'POST':
        print("POST verileri:", request.form)  # Debug
        name = request.form.get('name')
        question = request.form.get('question')
        answer = request.form.get('answer')
        sentiment = request.form.get('sentiment')
        topic = request.form.get('topic')

        try:
            # MySQL'e kaydet
            cursor = mysql.connection.cursor(DictCursor)
            cursor.execute(
                'INSERT INTO questions_tb (ogrenci_ID, questions, answers, Feedback, topic) VALUES (%s, %s, %s, %s, %s)',
                (session['student_number'], question, answer, sentiment, topic),
            )
            mysql.connection.commit()
            
            # Excel'e kaydet
            excel_data = {
                'student_number': session['student_number'],
                'question': question,
                'answer': answer,
                'sentiment': sentiment,
                'topic': topic
            }
            save_to_excel(excel_data)
            
            msg = 'Soru başarıyla eklendi!'
            print("Soru başarıyla kaydedildi")  # Debug
        except Exception as e:
            print(f"Hata oluştu: {e}")  # Debug
            msg = 'Bir hata oluştu!'
    
    return render_template('chatbot.html', msg=msg)

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    msg = ''
    if request.method == 'POST' and 'student_number' in request.form and 'new_password' in request.form:
        student_number = request.form['student_number']
        new_password = request.form['new_password']
        
        cursor = mysql.connection.cursor(DictCursor)
        cursor.execute('SELECT * FROM users_tb WHERE student_number = %s', (student_number,))
        account = cursor.fetchone()
        
        if account:
            cursor.execute('UPDATE users_tb SET password = %s WHERE student_number = %s', (new_password, student_number))
            mysql.connection.commit()
            msg = 'Şifreniz başarıyla sıfırlandı!'
        else:
            msg = 'Öğrenci numaranız bulunamadı!'
    
    return render_template('reset_password.html', msg=msg)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('student_number', None)
    return redirect('/')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)