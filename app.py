from flask import Flask, render_template, request
import requests
from deep_translator import GoogleTranslator
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup

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

        for idx, article in enumerate(data):
            title = article.get("title", "ไม่มีหัวข้อ")
            description = article.get("description", "ไม่มีคำอธิบาย")
            url = article.get("url", "#")
            image = article.get("urlToImage", "")
            source = article.get("source", {}).get("name", "ไม่ทราบแหล่งที่มา")
            published_at = article.get("publishedAt", "ไม่ทราบวันที่เผยแพร่")

            title_th = GoogleTranslator(source='en', target='th').translate(title)
            desc_th = GoogleTranslator(source='en', target='th').translate(description)

            news_list.append({
                "id": idx,  # ใช้ index เป็น id
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

def fetch_article_content(url):
    """ดึงเนื้อหาข่าวจาก URL และแปลเป็นไทย"""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        # ลองดึงเนื้อหาจากแท็ก <p>
        paragraphs = soup.find_all("p")
        content = "\n".join(p.get_text() for p in paragraphs[:5])  # เอาแค่ 5 ย่อหน้าแรก

        # แปลเนื้อหาเป็นไทย
        content_th = GoogleTranslator(source='en', target='th').translate(content)

        return content_th if content_th else "⚠️ ไม่สามารถดึงเนื้อหาข่าวนี้ได้"
    except Exception as e:
        print(f"❌ Error fetching article content: {e}")
        return "⚠️ ไม่สามารถดึงเนื้อหาข่าวนี้ได้"

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

@app.route("/article/<int:article_id>")
def article(article_id):
    """แสดงเนื้อหาข่าว"""
    news = get_news_from_api()
    
    if 0 <= article_id < len(news):
        article = news[article_id]
        content = fetch_article_content(article["url"])  # ดึงเนื้อหาข่าว
        
        return render_template("article.html", article=article, content=content)
    
    return "ไม่พบข่าวนี้", 404

if __name__ == "__main__":
    app.run(debug=True)
from datetime import datetime
import pytz

def get_news_from_api():
    """ดึงข่าวจาก API และแปลงวันที่เป็นเวลาประเทศไทย"""
    try:
        response = requests.get(NEWS_API)
        data = response.json().get("articles", [])
        news_list = []

        bangkok_tz = pytz.timezone("Asia/Bangkok")

        for idx, article in enumerate(data):
            title = article.get("title", "ไม่มีหัวข้อ")
            description = article.get("description", "ไม่มีคำอธิบาย")
            url = article.get("url", "#")
            image = article.get("urlToImage", "")
            published_at = article.get("publishedAt", "")

            # แปลงวันที่ให้เป็นเวลาประเทศไทย
            if published_at:
                dt_utc = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
                dt_bkk = dt_utc.replace(tzinfo=pytz.utc).astimezone(bangkok_tz)
                published_at_th = dt_bkk.strftime("%d/%m/%Y %H:%M น.")
            else:
                published_at_th = "ไม่ระบุ"

            # แปลเป็นภาษาไทย
            title_th = GoogleTranslator(source='en', target='th').translate(title)
            desc_th = GoogleTranslator(source='en', target='th').translate(description)

            news_list.append({
                "id": idx,
                "title": title_th,
                "description": desc_th,
                "url": url,
                "image": image,
                "published_at_th": published_at_th
            })

        return news_list
    except Exception as e:
        print(f"❌ Error fetching API news: {e}")
        return []
import deepl

DEEPL_API_KEY = "your-deepl-api-key"  # 🔹 ใส่ API Key ของคุณ

def translate_text_deepl(text):
    try:
        translator = deepl.Translator(DEEPL_API_KEY)
        result = translator.translate_text(text, target_lang="TH")  # แปลเป็นไทย
        return result.text
    except Exception as e:
        print(f"❌ DeepL Error: {e}")
        return text  # ถ้าแปลไม่ได้ ให้คืนค่าเดิม

