import streamlit as st
import feedparser
import pandas as pd
from textblob import TextBlob
import plotly.express as px
import re
from collections import Counter
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import time
import datetime
from dateutil import parser as date_parser
import concurrent.futures
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# --- Config ---
st.set_page_config(page_title="AI Market Trend Analyzer", layout="wide", page_icon="🤖")

# --- Language Selector ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/artificial-intelligence.png", width=60)
    lang = st.radio("Language / 语言", ["中文", "English"])
    st.divider()

# --- UI Dictionary ---
ui = {
    "title": {"English": "🤖 AI News & Market Trend Analyzer", "中文": "🤖 AI 新闻与市场趋势分析器"},
    "desc": {"English": "Aggregating from Google News, Hacker News, and arXiv to keep you updated on the AI domain.", 
             "中文": "聚合 Google News、Hacker News 和 arXiv 论文，全方位实时掌握 AI 领域最新动态。"},
    "scraping": {"English": "Fetching from multiple RSS sources (This may take a moment)...", "中文": "正在从多个数据源拉取最新资讯 (可能需要稍等片刻)..."},
    "translating": {"English": "Translating news to Chinese...", "中文": "正在将新闻翻译为中文 (首次加载可能需要几秒钟)..."},
    "total_news": {"English": "📰 Total Articles", "中文": "📰 近期抓取文章总数"},
    "sentiment": {"English": "📊 Market Sentiment Trend", "中文": "📊 市场情绪趋势"},
    "trending": {"English": "🔥 Top Trending Topic", "中文": "🔥 热门趋势话题"},
    "bullish": {"English": "Bullish 📈", "中文": "看涨 (积极) 📈"},
    "bearish": {"English": "Bearish 📉", "中文": "看跌 (消极) 📉"},
    "neutral": {"English": "Neutral ⚖️", "中文": "中立 ⚖️"},
    "sentiment_chart": {"English": "Market Sentiment Distribution", "中文": "市场情绪占比分布"},
    "keyword_chart": {"English": "Top Trending Keywords in AI", "中文": "AI 领域热门高频词汇"},
    "time_chart": {"English": "News Volume Over Time", "中文": "新闻发布时间趋势图"},
    "source_chart": {"English": "Top News Sources", "中文": "主要新闻来源分布"},
    "table_title": {"English": "📰 Latest AI News Feed", "中文": "📰 最新 AI 新闻流"},
    "table_desc": {"English": "Expand each article to read the summary and access the original source.", "中文": "展开每篇文章可阅读摘要并访问原文。"},
    "no_data": {"English": "No news found or unable to fetch data.", "中文": "未找到新闻或获取数据失败，请稍后重试。"},
    "filters": {"English": "🔍 Filters & Search", "中文": "🔍 筛选与搜索"},
    "search": {"English": "Search keywords...", "中文": "搜索关键词..."},
    "sort_by": {"English": "Sort By", "中文": "排序方式"},
    "sort_time_desc": {"English": "Newest First", "中文": "按时间降序 (最新)"},
    "sort_time_asc": {"English": "Oldest First", "中文": "按时间升序 (最旧)"},
    "sort_sentiment": {"English": "Sentiment Score (High to Low)", "中文": "按情绪得分 (从高到低)"},
    "topic_filter": {"English": "Topic", "中文": "主题"},
    "company_filter": {"English": "Company", "中文": "公司"},
    "region_filter": {"English": "Region", "中文": "国家/地区"},
    "source_type_filter": {"English": "Source Type", "中文": "信息源类型"},
    "time_range_filter": {"English": "Time Range", "中文": "时间跨度"},
    "all": {"English": "All", "中文": "全部"},
    "read_more": {"English": "Read Full Article ↗", "中文": "阅读原文 ↗"},
    "summary": {"English": "Summary", "中文": "摘要"},
    "source": {"English": "Source", "中文": "来源"},
    "published": {"English": "Published", "中文": "发布时间"},
    "sentiment_label": {"English": "Sentiment", "中文": "情绪"},
    "tags": {"English": "Tags", "中文": "标签"},
    "tab_news": {"English": "📰 News Feed", "中文": "📰 实时新闻流"},
    "tab_analytics": {"English": "📊 Data Analytics", "中文": "📊 市场数据大屏"},
    "top_headlines": {"English": "🔥 Top Headlines (Most Positive)", "中文": "🔥 今日核心利好头条"},
    "topic_dist_chart": {"English": "AI Domain Distribution", "中文": "AI 细分领域分布"},
    "company_mentions_chart": {"English": "Company Mentions", "中文": "热门公司提及热度"},
    "wordcloud_chart": {"English": "Keyword Frequency Analysis", "中文": "高频词汇云分析"}
}

st.title(ui["title"][lang])
st.markdown(ui["desc"][lang])

# --- Whitelists based on user list ---
TOPICS = [
    "Agent", "开源模型", "闭源模型", "多模态", "推理/加速 (Inference)", 
    "训练/数据 (Training/Data)", "AI芯片/算力", "AI应用/产品", 
    "监管/政策", "投融资/并购", "医疗AI", "自动驾驶/机器人"
]

COMPANIES = [
    "OpenAI", "Anthropic", "Google", "DeepMind", "Microsoft", 
    "NVIDIA", "Meta", "Apple", "xAI", "Perplexity", "Mistral", "Tesla"
]

REGIONS = [
    "US / North America", "China / Asia", "Europe / EU", "Middle East"
]

SOURCE_TYPES = [
    "Mainstream Media", "Tech Forums", "Research Papers"
]

TIME_RANGES = {
    "Last 24 Hours": 1,
    "Last 3 Days": 3,
    "Last 7 Days": 7
}

# RSS Feeds List (Expanded Set for more volume)
RSS_FEEDS = [
    # Google News (Mixed EN/CN) - Increased queries for more volume
    {"url": "https://news.google.com/rss/search?q=%E6%99%BA%E8%83%BD%E4%BB%A3%E7%90%86%20OR%20AI%20Agent&hl=zh-CN&gl=US&ceid=US:zh-Hans", "source": "Google News (ZH)"},
    {"url": "https://news.google.com/rss/search?q=%E5%BC%80%E6%BA%90%20%E6%A8%A1%E5%9E%8B%20OR%20open-source%20model&hl=zh-CN&gl=US&ceid=US:zh-Hans", "source": "Google News (ZH)"},
    {"url": "https://news.google.com/rss/search?q=AI%20%E8%8A%AF%E7%89%87%20OR%20NVIDIA%20GPU&hl=zh-CN&gl=US&ceid=US:zh-Hans", "source": "Google News (ZH)"},
    {"url": "https://news.google.com/rss/search?q=%E5%8C%BB%E7%96%97%20AI%20OR%20medical%20AI&hl=zh-CN&gl=US&ceid=US:zh-Hans", "source": "Google News (ZH)"},
    {"url": "https://news.google.com/rss/search?q=%E8%87%AA%E5%8A%A8%E9%A9%BE%E9%A9%B6%20OR%20robotaxi&hl=zh-CN&gl=US&ceid=US:zh-Hans", "source": "Google News (ZH)"},
    {"url": "https://news.google.com/rss/search?q=AI%20Act%20OR%20regulation&hl=en-US&gl=US&ceid=US:en", "source": "Google News (EN)"},
    {"url": "https://news.google.com/rss/search?q=AI%20funding%20OR%20Series%20A&hl=en-US&gl=US&ceid=US:en", "source": "Google News (EN)"},
    {"url": "https://news.google.com/rss/search?q=OpenAI%20OR%20ChatGPT&hl=en-US&gl=US&ceid=US:en", "source": "Google News (EN)"},
    {"url": "https://news.google.com/rss/search?q=Anthropic%20OR%20Claude&hl=en-US&gl=US&ceid=US:en", "source": "Google News (EN)"},
    {"url": "https://news.google.com/rss/search?q=Google%20DeepMind%20AI&hl=en-US&gl=US&ceid=US:en", "source": "Google News (EN)"},
    
    # Hacker News
    {"url": "https://hnrss.org/newest?q=AI%20agent", "source": "Hacker News"},
    {"url": "https://hnrss.org/newest?q=OpenAI", "source": "Hacker News"},
    {"url": "https://hnrss.org/newest?q=NVIDIA", "source": "Hacker News"},
    {"url": "https://hnrss.org/newest?q=Llama%20OR%20open-source", "source": "Hacker News"},
    
    # arXiv (Research Papers)
    {"url": "https://export.arxiv.org/rss/cs.AI", "source": "arXiv (AI)"},
    {"url": "https://export.arxiv.org/rss/cs.LG", "source": "arXiv (Machine Learning)"},
    {"url": "https://export.arxiv.org/rss/cs.CL", "source": "arXiv (Computation and Language)"}
]

# Simple rule-based tagger replacing GPT for speed & cost in this dashboard
def tag_article(text):
    text_lower = text.lower()
    found_topics = []
    found_companies = []
    found_regions = []
    
    # Check Topics
    if any(k in text_lower for k in ["agent", "代理"]): found_topics.append("Agent")
    if any(k in text_lower for k in ["open-source", "开源", "llama", "mistral"]): found_topics.append("开源模型")
    if any(k in text_lower for k in ["chip", "gpu", "h100", "b200", "芯片", "算力"]): found_topics.append("AI芯片/算力")
    if any(k in text_lower for k in ["regulation", "law", "act", "监管", "法规", "政策"]): found_topics.append("监管/政策")
    if any(k in text_lower for k in ["funding", "series a", "venture", "融资", "风投", "并购"]): found_topics.append("投融资/并购")
    if any(k in text_lower for k in ["medical", "health", "fda", "医疗", "健康"]): found_topics.append("医疗AI")
    if any(k in text_lower for k in ["robot", "autonomous", "fsd", "机器人", "自动驾驶"]): found_topics.append("自动驾驶/机器人")
    
    # Check Companies
    for comp in COMPANIES:
        if comp.lower() in text_lower:
            found_companies.append(comp)
            
    # Check Regions
    if any(k in text_lower for k in ["us", "usa", "america", "biden", "washington", "硅谷", "美国", "北美"]): 
        found_regions.append("US / North America")
    if any(k in text_lower for k in ["china", "chinese", "asia", "beijing", "shanghai", "shenzhen", "中国", "亚洲", "北京", "上海"]): 
        found_regions.append("China / Asia")
    if any(k in text_lower for k in ["eu", "europe", "european", "brussels", "london", "欧盟", "欧洲", "英国"]): 
        found_regions.append("Europe / EU")
    if any(k in text_lower for k in ["middle east", "uae", "saudi", "dubai", "中东", "沙特", "阿联酋", "迪拜"]): 
        found_regions.append("Middle East")
            
    return found_topics[:3], found_companies[:5], found_regions[:2]

def get_source_type(source_name):
    if "Hacker News" in source_name: return "Tech Forums"
    if "arXiv" in source_name: return "Research Papers"
    return "Mainstream Media"

def fetch_single_feed(feed_info):
    feed_url = feed_info["url"]
    source_name = feed_info["source"]
    source_type = get_source_type(source_name)
    feed = feedparser.parse(feed_url)
    items = []
    
    # Increase limit to 30 items per feed to get much more volume
    for entry in feed.entries[:30]:
        title = BeautifulSoup(entry.title, "html.parser").get_text()
        
        # 1. Try to get summary from summary field
        summary_html = entry.get('summary', '')
        summary_text = BeautifulSoup(summary_html, "html.parser").get_text().strip()
        
        # 2. Try to get content if summary is empty or too short
        if not summary_text or len(summary_text) < 50:
            if hasattr(entry, 'content') and len(entry.content) > 0:
                content_html = entry.content[0].value
                summary_text = BeautifulSoup(content_html, "html.parser").get_text().strip()
                
        # 3. Try description field
        if not summary_text or len(summary_text) < 50:
             if hasattr(entry, 'description'):
                 summary_text = BeautifulSoup(entry.description, "html.parser").get_text().strip()
                 
        # 4. Clean up Google News specific boilerplate (e.g., "Read full article on...")
        summary_text = re.sub(r'Read full article on.*?$', '', summary_text, flags=re.IGNORECASE)
        summary_text = re.sub(r'Read more.*?$', '', summary_text, flags=re.IGNORECASE)
        
        # Fallback if still empty
        if not summary_text or summary_text == title:
             summary_text = f"An article discussing {title}. Click the link to read the full details at the source."
             
        try:
            pub_date = date_parser.parse(entry.published)
        except:
            pub_date = datetime.datetime.now()
            
        topics, comps, regions = tag_article(title + " " + summary_text)
        
        items.append({
            "Title_EN": title,
            # Give a generous length for the summary, but cap at 500 chars to keep UI clean
            "Summary_EN": summary_text[:500] + "..." if len(summary_text) > 500 else summary_text,
            "Link": entry.link,
            "Published_Date": pub_date,
            "Source": source_name,
            "Source_Type": source_type,
            "Topics": topics,
            "Companies": comps,
            "Regions": regions
        })
    return items

# --- Fetch Data ---
@st.cache_data(ttl=1800) # Cache for 30 minutes
def fetch_all_news():
    all_news = []
    # Use ThreadPoolExecutor to fetch multiple RSS feeds concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(fetch_single_feed, RSS_FEEDS)
        for res in results:
            all_news.extend(res)
            
    df = pd.DataFrame(all_news)
    # Deduplicate by title
    if not df.empty:
        df = df.drop_duplicates(subset=['Title_EN'])
    return df

# --- Translate Data ---
@st.cache_data(ttl=1800)
def translate_texts(texts, target_lang):
    if not texts:
        return texts
    
    # We create a new translator instance per call to avoid state issues
    # When target_lang is 'en', we translate TO English (for Chinese sources)
    # When target_lang is 'zh-CN', we translate TO Chinese (for English sources)
    translator = GoogleTranslator(source='auto', target=target_lang)
    translated = []
    
    # Smaller chunk size for better stability
    chunk_size = 10 
    
    for i in range(0, len(texts), chunk_size):
        chunk = texts[i:i+chunk_size]
        delimiter = " |^^| "
        combined_text = delimiter.join(chunk)
        
        try:
            # Give Google API a respectful pause
            if i > 0: time.sleep(1.0) 
            
            trans_combined = translator.translate(combined_text)
            
            if trans_combined:
                parts = re.split(r'\s*\|\^\^\|\s*', trans_combined)
                if len(parts) == len(chunk):
                    translated.extend(parts)
                else:
                    # Fallback to 1-by-1 if delimiter split fails
                    for t in chunk:
                        try:
                            time.sleep(0.2)
                            translated.append(translator.translate(t))
                        except:
                            translated.append(t)
            else:
                 translated.extend(chunk)
        except Exception as e:
            # Fallback to 1-by-1 if batch fails
            for t in chunk:
                try:
                    time.sleep(0.3)
                    translated.append(translator.translate(t))
                except:
                    translated.append(t)
                    
    return translated

# --- Analyze Data ---
@st.cache_data(ttl=1800)
def analyze_trends(df):
    if df.empty: return df, []
    
    df['Sentiment_Score'] = df['Title_EN'].apply(lambda x: TextBlob(x).sentiment.polarity)
    
    def categorize_sentiment(score):
        if score > 0.1: return 'Positive'
        elif score < -0.1: return 'Negative'
        else: return 'Neutral'
        
    df['Sentiment'] = df['Sentiment_Score'].apply(categorize_sentiment)
    
    text = " ".join(df['Title_EN'].tolist()).lower()
    text = re.sub(r'[^a-z\s]', '', text)
    stopwords = set([
        'artificial', 'intelligence', 'ai', 'the', 'to', 'and', 'of', 'in', 'a', 'for', 'on', 'with', 
        'as', 'is', 'at', 'it', 'from', 'by', 'that', 'this', 'an', 'be', 'are', 'how', 'will', 'new', 
        'what', 'can', 'its', 'about', 'more', 'has', 'have', 'not', 'but', 'up', 'out', 'we', 'your',
        'say', 'says', 'said', 'who', 'why', 'when', 'where', 'which', 'hn', 'show', 'via'
    ])
    
    keywords = [w for w in text.split() if w not in stopwords and len(w) > 3]
    top_keywords = Counter(keywords).most_common(20)
    
    return df, top_keywords, " ".join(keywords)

# --- Main Workflow ---
with st.spinner(ui["scraping"][lang]):
    df_news = fetch_all_news()

if not df_news.empty:
    df_news, top_keywords, all_keywords_text = analyze_trends(df_news)
    
    # Ensure Published_Date is a datetime object before using .dt
    df_news['Published_Date'] = pd.to_datetime(df_news['Published_Date'], utc=True, errors='coerce')
    
    df_news['Date_Str'] = df_news['Published_Date'].dt.strftime('%Y-%m-%d %H:%M')
    df_news['Day'] = df_news['Published_Date'].dt.strftime('%Y-%m-%d')
    
    if lang == "中文":
        with st.spinner(ui["translating"][lang]):
            # Only translate English titles to Chinese
            df_news["Title"] = translate_texts(df_news["Title_EN"].tolist(), 'zh-CN')
            df_news["Summary"] = df_news["Summary_EN"] 
    else:
        with st.spinner("Translating Chinese sources to English..."):
            # Translate Chinese titles to English to keep the English UI consistent
            df_news["Title"] = translate_texts(df_news["Title_EN"].tolist(), 'en')
            df_news["Summary"] = df_news["Summary_EN"]
        
    # --- Sidebar Filters & Search ---
    with st.sidebar:
        st.header(ui["filters"][lang])
        
        # Moved search to main area, keeping only advanced filters here
        st.markdown(f"**{ui['time_range_filter'][lang]}**")
        selected_time = st.selectbox("Time", [ui["all"][lang]] + list(TIME_RANGES.keys()), label_visibility="collapsed")
        
        st.markdown("---")
        
        # Topic & Company Filters
        st.markdown(f"**{ui['topic_filter'][lang]} & {ui['company_filter'][lang]}**")
        selected_topic = st.selectbox("Topic", [ui["all"][lang]] + TOPICS, label_visibility="collapsed")
        selected_company = st.selectbox("Company", [ui["all"][lang]] + COMPANIES, label_visibility="collapsed")
            
        st.markdown("---")
        
        # Region & Source Type Filters
        st.markdown(f"**{ui['region_filter'][lang]} & {ui['source_type_filter'][lang]}**")
        selected_region = st.selectbox("Region", [ui["all"][lang]] + REGIONS, label_visibility="collapsed")
        selected_source_type = st.selectbox("Source", [ui["all"][lang]] + SOURCE_TYPES, label_visibility="collapsed")
        
        st.markdown("---")
        if st.button("Reset Filters" if lang == "English" else "重置所有筛选"):
            st.rerun()

    # --- Main Area Search & Sort ---
    col_search, col_sort = st.columns([3, 1])
    with col_search:
        search_query = st.text_input(ui["search"][lang], placeholder="e.g. OpenAI, GPT-5, Robot...")
    with col_sort:
        sort_options = [ui["sort_time_desc"][lang], ui["sort_time_asc"][lang], ui["sort_sentiment"][lang]]
        selected_sort = st.selectbox(ui["sort_by"][lang], sort_options, label_visibility="collapsed")

    # --- Apply Filters ---
    filtered_df = df_news.copy()
    
    if search_query:
        search_mask = filtered_df['Title_EN'].str.contains(search_query, case=False, na=False) | \
                      filtered_df['Title'].str.contains(search_query, case=False, na=False)
        filtered_df = filtered_df[search_mask]
        
    if selected_topic != ui["all"][lang]:
        filtered_df = filtered_df[filtered_df['Topics'].apply(lambda x: selected_topic in x)]
        
    if selected_company != ui["all"][lang]:
        filtered_df = filtered_df[filtered_df['Companies'].apply(lambda x: selected_company in x)]
        
    if selected_region != ui["all"][lang]:
        filtered_df = filtered_df[filtered_df['Regions'].apply(lambda x: selected_region in x)]
        
    if selected_source_type != ui["all"][lang]:
        filtered_df = filtered_df[filtered_df['Source_Type'] == selected_source_type]
        
    if selected_time != ui["all"][lang]:
        days_limit = TIME_RANGES[selected_time]
        cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_limit)
        
        # Ensure timezone awareness for comparison
        def check_date(d):
            if d.tzinfo is None:
                d = d.replace(tzinfo=datetime.timezone.utc)
            return d >= cutoff_date
            
        filtered_df = filtered_df[filtered_df['Published_Date'].apply(check_date)]
        
    # Apply Sorting
    if selected_sort == ui["sort_time_desc"][lang]:
        filtered_df = filtered_df.sort_values(by='Published_Date', ascending=False)
    elif selected_sort == ui["sort_time_asc"][lang]:
        filtered_df = filtered_df.sort_values(by='Published_Date', ascending=True)
    elif selected_sort == ui["sort_sentiment"][lang]:
        filtered_df = filtered_df.sort_values(by='Sentiment_Score', ascending=False)

    # --- Metrics Section ---
    col1, col2, col3 = st.columns(3)
    col1.metric(ui["total_news"][lang], len(filtered_df))
    
    if not filtered_df.empty:
        avg_score = filtered_df['Sentiment_Score'].mean()
        if avg_score > 0.1: trend = ui["bullish"][lang]
        elif avg_score < -0.1: trend = ui["bearish"][lang]
        else: trend = ui["neutral"][lang]
    else:
        avg_score = 0.0
        trend = ui["neutral"][lang]
        
    col2.metric(ui["sentiment"][lang], trend, f"{avg_score:.2f} Score")
    col3.metric(ui["trending"][lang], top_keywords[0][0].capitalize() if top_keywords else "N/A")
    
    st.divider()
    
    if not filtered_df.empty:
        main_tab1, main_tab2 = st.tabs([ui["tab_news"][lang], ui["tab_analytics"][lang]])
        
        with main_tab1:
            # --- Top Headlines Section ---
            # Show top 3 most positive articles if any
            positive_news = filtered_df[filtered_df['Sentiment'] == 'Positive'].sort_values(by='Sentiment_Score', ascending=False)
            if not positive_news.empty:
                st.subheader(ui["top_headlines"][lang])
                cols = st.columns(min(3, len(positive_news)))
                for idx, (i, row) in enumerate(positive_news.head(3).iterrows()):
                    with cols[idx]:
                        with st.container(border=True):
                            st.markdown(f"##### {row['Title']}")
                            st.caption(f"{row['Source']} • {row['Date_Str']}")
                            st.markdown(f"**[{ui['read_more'][lang]}]({row['Link']})**")
                st.markdown("---")

            # --- Expandable News Feed ---
            st.subheader(ui["table_title"][lang])
            
            for idx, row in filtered_df.iterrows():
                sentiment_val = row['Sentiment']
                if sentiment_val == 'Positive':
                    badge_color = "green"
                    sent_text = "🟢 Bullish" if lang == "English" else "🟢 利好"
                elif sentiment_val == 'Negative':
                    badge_color = "red"
                    sent_text = "🔴 Bearish" if lang == "English" else "🔴 利空"
                else:
                    badge_color = "blue"
                    sent_text = "⚪ Neutral" if lang == "English" else "⚪ 中立"
                    
                # Create tag badges
                tags = row['Topics'] + row['Companies'] + row['Regions']
                tag_str = " ".join([f"`{t}`" for t in tags]) if tags else ""
                
                with st.expander(f"{sent_text} | **{row['Title']}**"):
                    col_info1, col_info2 = st.columns([3, 1])
                    with col_info1:
                        if tag_str:
                            st.markdown(f"**{ui['tags'][lang]}:** {tag_str}")
                        st.markdown(f"**{ui['summary'][lang]}:**")
                        st.write(row['Summary'])
                    with col_info2:
                        st.markdown(f"**{ui['published'][lang]}:**<br>{row['Date_Str']}", unsafe_allow_html=True)
                        st.markdown(f"**{ui['source'][lang]}:**<br>{row['Source']}", unsafe_allow_html=True)
                        st.markdown(f"<br>**[{ui['read_more'][lang]}]({row['Link']})**", unsafe_allow_html=True)
                        
        with main_tab2:
            # --- Visualizations ---
            st.subheader("📊 Analytics Dashboard")
            tab1, tab2, tab3 = st.tabs(["Sentiment & Keywords", "Domain & Company Distribution", "Time & Sources"])
            
            with tab1:
                col_chart1, col_chart2 = st.columns(2)
                with col_chart1:
                    sentiment_counts = filtered_df['Sentiment'].value_counts().reset_index()
                    sentiment_counts.columns = ['Sentiment', 'Count']
                    if lang == "中文":
                        sentiment_map = {'Positive': '积极', 'Neutral': '中立', 'Negative': '消极'}
                        sentiment_counts['Sentiment'] = sentiment_counts['Sentiment'].map(sentiment_map)
                        color_map = {'积极':'#00CC96', '中立':'#636EFA', '消极':'#EF553B'}
                    else:
                        color_map = {'Positive':'#00CC96', 'Neutral':'#636EFA', 'Negative':'#EF553B'}
                        
                    fig_sentiment = px.pie(
                        sentiment_counts, names='Sentiment', values='Count',
                        color='Sentiment', color_discrete_map=color_map, hole=0.4,
                        title=ui["sentiment_chart"][lang]
                    )
                    fig_sentiment.update_layout(margin=dict(t=40, b=0, l=0, r=0))
                    st.plotly_chart(fig_sentiment, use_container_width=True)
                    
                with col_chart2:
                    # Generate WordCloud
                    if all_keywords_text.strip():
                        st.markdown(f"**{ui['wordcloud_chart'][lang]}**")
                        wordcloud = WordCloud(width=800, height=400, background_color='white', colormap='Blues', max_words=50).generate(all_keywords_text)
                        fig_wc, ax = plt.subplots(figsize=(8, 4))
                        ax.imshow(wordcloud, interpolation='bilinear')
                        ax.axis('off')
                        # Reduce padding
                        plt.tight_layout(pad=0)
                        st.pyplot(fig_wc)
                        
            with tab2:
                col_chart5, col_chart6 = st.columns(2)
                
                with col_chart5:
                    # Extract and count topics
                    all_topics = [t for sublist in filtered_df['Topics'] for t in sublist]
                    if all_topics:
                        topic_counts = Counter(all_topics).most_common(10)
                        df_topics = pd.DataFrame(topic_counts, columns=['Topic', 'Count']).sort_values(by='Count', ascending=True)
                        fig_topics = px.bar(
                            df_topics, x='Count', y='Topic', orientation='h',
                            title=ui["topic_dist_chart"][lang],
                            color='Count', color_continuous_scale=px.colors.sequential.Purples
                        )
                        fig_topics.update_layout(margin=dict(t=40, b=0, l=0, r=0))
                        st.plotly_chart(fig_topics, use_container_width=True)
                    else:
                        st.info("No topic data available for current filter." if lang == "English" else "当前筛选条件下无主题数据。")
                        
                with col_chart6:
                    # Extract and count companies
                    all_comps = [c for sublist in filtered_df['Companies'] for c in sublist]
                    if all_comps:
                        comp_counts = Counter(all_comps).most_common(10)
                        df_comps = pd.DataFrame(comp_counts, columns=['Company', 'Count']).sort_values(by='Count', ascending=True)
                        fig_comps = px.bar(
                            df_comps, x='Count', y='Company', orientation='h',
                            title=ui["company_mentions_chart"][lang],
                            color='Count', color_continuous_scale=px.colors.sequential.Oranges
                        )
                        fig_comps.update_layout(margin=dict(t=40, b=0, l=0, r=0))
                        st.plotly_chart(fig_comps, use_container_width=True)
                    else:
                        st.info("No company data available for current filter." if lang == "English" else "当前筛选条件下无公司提及数据。")

            with tab3:
                col_chart3, col_chart4 = st.columns(2)
                with col_chart3:
                    time_counts = filtered_df.groupby('Day').size().reset_index(name='Count')
                    fig_time = px.line(
                        time_counts, x='Day', y='Count', markers=True,
                        title=ui["time_chart"][lang],
                        color_discrete_sequence=['#FF7F0E']
                    )
                    fig_time.update_layout(margin=dict(t=40, b=0, l=0, r=0), xaxis_title="", yaxis_title="Articles")
                    st.plotly_chart(fig_time, use_container_width=True)
                    
                with col_chart4:
                    source_counts = filtered_df['Source'].value_counts().head(10).reset_index()
                    source_counts.columns = ['Source', 'Count']
                    fig_source = px.bar(
                        source_counts, x='Source', y='Count',
                        title=ui["source_chart"][lang],
                        color='Count', color_continuous_scale=px.colors.sequential.Teal
                    )
                    fig_source.update_layout(margin=dict(t=40, b=0, l=0, r=0), xaxis_title="", yaxis_title="Articles")
                    st.plotly_chart(fig_source, use_container_width=True)
            
    else:
        st.warning(ui["no_data"][lang])
else:
    st.warning(ui["no_data"][lang])