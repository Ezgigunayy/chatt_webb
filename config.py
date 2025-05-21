# class Config:
#     DB_HOST = 'localhost'
#     DB_USER = 'root'
#     DB_PASSWORD = ''
#     DB_NAME = 'chatbot'

from dotenv import load_dotenv
import os

# .env dosyasını yükle
load_dotenv()

class Config:
    # Flask için gizli anahtar
    SECRET_KEY = os.getenv('SECRET_KEY', 'varsayilan_gizli_anahtar')

    # Flask-MySQLdb yapılandırması
    MYSQL_HOST = os.getenv('DB_HOST', 'localhost')
    MYSQL_USER = os.getenv('DB_USER', 'root')
    MYSQL_PASSWORD = os.getenv('DB_PASSWORD', '')
    MYSQL_DB = os.getenv('DB_NAME', 'chatbot_db')

    # Güvenlik başlıkları
    SECURITY_HEADERS = {
        'Content-Security-Policy': "default-src 'self'",
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block'
    }
