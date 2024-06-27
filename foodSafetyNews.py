import schedule
import time
from linebot import LineBotApi
from linebot.models import TextSendMessage
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import urllib.parse

# LINE Bot API 設定
line_bot_api = LineBotApi("RVq3XdWGlHfJzEPKocce/x6Gj8QhRZi1ER4fysHLb/Pg6mcVpgVj4pk6dBNJM0EmuS/7r8ORpDwUWLsgg7emCsSata8C+jRUUDSqWzfY6oDaseAJ0fk/MOpMzvdBaOhOoHFEg1/rB+xp55jDaVgVvwdB04t89/1O/w1cDnyilFU=")

# 設定時區為台灣時間
tw_tz = pytz.timezone('Asia/Taipei')

def shorten_url(url):
    tiny_url = f"http://tinyurl.com/api-create.php?url={url}"
    response = requests.get(tiny_url)
    return response.text

def get_news():
    # 定義關鍵字
    keywords = ["食品", "食品衛生", "食安", "食品安全", "衛生局", "食藥署"]
    # 使用 OR 運算符組合關鍵字
    query = " OR ".join(keywords)
    # URL 編碼查詢字符串
    encoded_query = urllib.parse.quote(query)
    
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, features="xml")
    
    news_list = []
    items = soup.find_all('item')
    
    for item in items:
        title = item.title.text
        link = item.link.text
        pub_date = datetime.strptime(item.pubDate.text, "%a, %d %b %Y %H:%M:%S %Z")
        pub_date = pub_date.replace(tzinfo=pytz.UTC).astimezone(tw_tz)
        
        news_list.append({
            'title': title,
            'link': link,
            'time': pub_date
        })
    
    return news_list

def send_news():
    news_list = get_news()
    
    # 過濾3小時內的新聞
    three_hours_ago = datetime.now(tw_tz) - timedelta(hours=3)
    filtered_news = [news for news in news_list if news['time'] > three_hours_ago]
    
    if not filtered_news:
        # 如果沒有新聞，發送指定訊息
        message = "3個小時又平安地過去了，感謝鳥腦袋的努力，努咕誰唷。"
        line_bot_api.push_message("Ub7c41bb9111ee503807aa0cd5ffc6b37", TextSendMessage(text=message))
        return
    
    # 只取最新的30則
    filtered_news = filtered_news[:30]
    
    # 將新聞分成每10則一組
    news_groups = [filtered_news[i:i+10] for i in range(0, len(filtered_news), 10)]
    
    # 初始化總編號
    total_count = 1
    
    for group in news_groups:
        message = "最新食品安全相關新聞：\n\n"
        for news in group:
            short_url = shorten_url(news['link'])
            message += f"{total_count}. {news['title']}\n{short_url}\n\n"
            total_count += 1
        
        line_bot_api.push_message("Ub7c41bb9111ee503807aa0cd5ffc6b37", TextSendMessage(text=message.strip()))

# 設定每3小時執行一次
schedule.every(3).hours.do(send_news)

# 立即執行一次，以便測試
send_news()

while True:
    schedule.run_pending()
    time.sleep(1)