from flask import Flask, render_template, jsonify
import requests
import smtplib
import os
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
import threading
import time

app = Flask(__name__)

# 設定你的票務網址
TICKET_URL = "https://ticketplus.com.tw/order/42bc0a3283e8bc84372608fb016042bb/a70fad4c7f7ff618d6ba63f83f1e4f3b"

# 設定 Email 通知（使用環境變數來保護敏感資訊）
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

if not EMAIL_SENDER or not EMAIL_PASSWORD or not EMAIL_RECEIVER:
    raise ValueError("請設定 EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER 環境變數！")

found_ticket = False

def send_email_notification(message):
    try:
        msg = MIMEText(message)
        msg["Subject"] = "票務通知"
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
    except Exception as e:
        print(f"發送郵件失敗: {e}")

def check_ticket_availability():
    global found_ticket
    while True:
        try:
            response = requests.get(TICKET_URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            if "售罄" not in soup.text:
                if not found_ticket:
                    send_email_notification("有票了！快去購買！")
                found_ticket = True
            else:
                if found_ticket:
                    send_email_notification("票已售罄，將在 10 分鐘後重新檢查...")
                found_ticket = False
        except requests.RequestException as e:
            print(f"網絡請求失敗: {e}")
        
        time.sleep(600)  # 每 10 分鐘檢查一次

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/status')
def status():
    return jsonify({"ticket_found": found_ticket})

if __name__ == '__main__':
    threading.Thread(target=check_ticket_availability, daemon=True).start()
    app.run(debug=True, host='0.0.0.0', port=5000)
