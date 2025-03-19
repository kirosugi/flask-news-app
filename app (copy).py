from flask import Flask, render_template, request
import requests
from deep_translator import GoogleTranslator
import os
from dotenv import load_dotenv

# โหลดค่าตัวแปรจาก .env
load_dotenv()

app = Flask(__name__)

# API Key สำหรับดึงข่าว
API_KEY = os.getenv("NEWS_API_KEY")

if not API_KEY:
    raise ValueError("❌ ERROR: กรุณาตั้งค่า NEWS_API_KEY ในไฟล์ .env")

# URL แหล่งข่าว (เฉพาะข่าวเทคโนโลยี)
NEWS_API = f"https://newsapi.org/v2/top-headlines?category=technology&language=en&apiKey={API_KEY}"

def get_news_from_api():
    """ดึงข่าวจาก API และแปลเป็นไทย"""
    try:
        response = requests.get(NEWS_API)
        data = response.json().get("articles", [])
        news_list = []

        for article in data:
            title = article.get("title", "ไม่มีหัวข้อ")
            description = article.get("description", "ไม่มีคำอธิบาย")
            url = article.get("url", "#")
            image = article.get("urlToImage", "")
            source = article.get("source", {}).get("name", "ไม่ทราบแหล่งที่มา")
            published_at = article.get("publishedAt", "ไม่ทราบวันที่เผยแพร่")

            title_th = GoogleTranslator(source='en', target='th').translate(title)
            desc_th = GoogleTranslator(source='en', target='th').translate(description)

            news_list.append({
                "title": title_th,
                "description": desc_th,
                "url": url,
                "image": image,
                "source": source,
                "published_at": published_at
            })

        return news_list
    except Exception as e:
        print(f"❌ Error fetching API news: {e}")
        return []

@app.route("/")
def home():
    """หน้าหลัก + แบ่งหน้าแสดงข่าว"""
    news = get_news_from_api()
    
    # การแบ่งหน้า
    page = request.args.get("page", 1, type=int)
    per_page = 9  # แสดงข่าวละ 9 ข่าวต่อหน้า
    total_pages = (len(news) + per_page - 1) // per_page  # คำนวณจำนวนหน้าทั้งหมด
    start = (page - 1) * per_page
    end = start + per_page
    news_paginated = news[start:end]  # ดึงข่าวเฉพาะหน้าที่ต้องการ

    return render_template("index.html", news=news_paginated, page=page, total_pages=total_pages)

if __name__ == "__main__":
    app.run(debug=True)

