import json 
import praw
import datetime
#from newsapi import NewsApiClient
import joblib
from transformers import AutoTokenizer, AutoModel
import torch
import openai
import time
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import openai

load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tokenizer = AutoTokenizer.from_pretrained("yiyanghkust/finbert-tone")
model = AutoModel.from_pretrained("yiyanghkust/finbert-tone")
#newsapi = NewsApiClient(api_key=os.getenv("newsapi_client_id"))
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),           
    client_secret=os.getenv('REDDIT_SECRET_KEY'),
    user_agent='StockScraper/1.0'
)

def get_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
        # Use the [CLS] token embedding
        return outputs.last_hidden_state[:, 0, :].squeeze().numpy()

def scrape_subreddit(subreddit_name="stocks", limit=50):
    posts = []
    now = datetime.datetime.utcnow()
    today = now.date()
    yesterday = today - datetime.timedelta(days=1)
    for submission in reddit.subreddit(subreddit_name).hot(limit=limit):
        created_date = datetime.datetime.utcfromtimestamp(submission.created_utc).date()
        if created_date == today or created_date == yesterday:
            posts.append({
                "source": "Reddit",
                "title": submission.title,
                "text": submission.selftext,
                "created": datetime.datetime.fromtimestamp(submission.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
                "url": submission.url
            })
    return posts

def scrape_newsapi(query="stock", from_days_ago=1):
    all_articles = newsapi.get_everything(q=query,
                                          from_param=(datetime.datetime.now() - datetime.timedelta(days=from_days_ago)).strftime('%Y-%m-%d'),
                                          to=datetime.datetime.now().strftime('%Y-%m-%d'),
                                          language='en',
                                          sort_by='relevancy',
                                          page_size=100)
    articles = []
    for article in all_articles['articles']:
        articles.append({
            "source": "NewsAPI",
            "title": article['title'],
            "text": article['description'],
            "created": article['publishedAt'],
            "url": article['url']
        })
    return articles

def extract_tickers_with_gpt(text, max_retries=3):
    prompt = f"""
You are a financial text analyst. Given the following post or article text, extract any referenced publicly traded companies or stock tickers. Return a Python list of ticker symbols (e.g., ["AAPL", "TSLA", "GOOGL"]). If no stocks are mentioned, return an empty list.

Text:
\"\"\"{text}\"\"\"

Stocks:
"""

    for _ in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
            )

            content = response.choices[0].message.content.strip()

            # Evaluate string safely
            try:
                result = eval(content, {"__builtins__": {}})
                return result if isinstance(result, list) else []
            except:
                return []

        except Exception as e:
            print(f"Error: {e} — retrying...")
            time.sleep(2)

    return []


def fetch_news_and_reddit():
    reddit_posts = scrape_subreddit()
    #newsapi_posts = scrape_newsapi()
    all_posts = reddit_posts 
    return all_posts

def insert_prediction(post, label):
    try: 
        response = supabase.table("predictions").upsert({
            "date": post["created"].split(" ")[0],
            "tickers": post.get("tickers", []),
            "title": post["title"],
            "text": post["text"],
            "url": post["url"],
            "label": label
        }, on_conflict=["url"]).execute()
    except Exception as e:
        print(f"Error inserting prediction: {e}")



def run_pipeline():
    print("Fetching news and Reddit posts...")
    lr = joblib.load("lr_model.pkl")
    posts = fetch_news_and_reddit()           
    results = []

    for post in posts:  
        # Extract tickers using GPT
        tickers = extract_tickers_with_gpt(post["text"])
        post["tickers"] = tickers
        # Check if tickers are empty
        if not tickers:
            print(f"No tickers found in post: {post['title']}")
            continue

        print(f"Processing post: {post['title']}")
        emb = get_embedding(post["text"])
        label = lr.predict([emb])[0]
        insert_prediction(post, int(label))

if __name__ == "__main__":
    results = run_pipeline()



