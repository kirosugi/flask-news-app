from flask import Flask, render_template, request
import requests
from deep_translator import GoogleTranslator
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import deepl

# โหลดค่าตัวแปรจาก .env
load_dotenv()

app = Flask(__name__)

# API Key สำหรับดึงข่าวและ DeepL
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")  # ถ้าไม่มีจะใช้ GoogleTranslator แทน

if not NEWS_API_KEY:
    raise ValueError("❌ ERROR: กรุณาตั้งค่า NEWS_API_KEY ในไฟล์ .env")

# URL แหล่งข่าว (เฉพาะข่าวเทคโนโลยี)
NEWS_API = f"https://newsapi.org/v2/top-headlines?category=technology&language=en&apiKey={NEWS_API_KEY}"

def translate_text(text, use_deepl=True):
    """แปลข้อความโดยเลือกใช้ DeepL หรือ GoogleTranslator"""
    try:
        if use_deepl and DEEPL_API_KEY:
            translator = deepl.Translator(DEEPL_API_KEY)
            result = translator.translate_text(text, target_lang="TH")
            return result.text
        else:
            return GoogleTranslator(source='en', target='th').translate(text)
    except Exception as e:
        print(f"❌ Translation Error: {e}")
        return text  # คืนค่าเดิมถ้าแปลไม่ได้

def get_news_from_api():
    """ดึงข่าวจาก API แปลเป็นไทย และแปลงวันที่เป็นเวลาประเทศไทย"""
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
            source = article.get("source", {}).get("name", "ไม่ทราบแหล่งที่มา")
            published_at = article.get("publishedAt", "")

            # แปลงวันที่ให้เป็นเวลาประเทศไทย
            if published_at:
                dt_utc = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
                dt_bkk = dt_utc.replace(tzinfo=pytz.utc).astimezone(bangkok_tz)
                published_at_th = dt_bkk.strftime("%d/%m/%Y %H:%M น.")
            else:
                published_at_th = "ไม่ระบุ"

            # แปลเป็นภาษาไทย
            title_th = translate_text(title, use_deepl=True)
            desc_th = translate_text(description, use_deepl=True)

            news_list.append({
                "id": idx,
                "title": title_th,
                "description": desc_th,
                "url": url,
                "image": image,
                "source": source,
                "published_at_th": published_at_th
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

        # ดึงเนื้อหาจากแท็ก <p>
        paragraphs = soup.find_all("p")
        content = "\n".join(p.get_text() for p in paragraphs[:5])  # เอาแค่ 5 ย่อหน้าแรก

        # แปลเนื้อหาเป็นไทย
        content_th = translate_text(content, use_deepl=True)

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
