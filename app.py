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
    "search": {"English": "Search keyword in titles...", "中文": "搜索标题中的关键词..."},
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
    "read_more": {"English": "Read Original Article", "中文": "阅读原文"},
    "summary": {"English": "Summary:", "中文": "摘要:"},
    "source": {"English": "Source:", "中文": "来源平台:"},
    "published": {"English": "Published:", "中文": "发布时间:"},
    "sentiment_label": {"English": "Sentiment:", "中文": "情绪:"},
    "tags": {"English": "Tags:", "中文": "标签:"}
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

# RSS Feeds List (Minimal Set)
RSS_FEEDS = [
    # Google News (Mixed EN/CN)
    {"url": "https://news.google.com/rss/search?q=%E6%99%BA%E8%83%BD%E4%BB%A3%E7%90%86%20OR%20AI%20Agent&hl=zh-CN&gl=US&ceid=US:zh-Hans", "source": "Google News (ZH)"},
    {"url": "https://news.google.com/rss/search?q=%E5%BC%80%E6%BA%90%20%E6%A8%A1%E5%9E%8B%20OR%20open-source%20model&hl=zh-CN&gl=US&ceid=US:zh-Hans", "source": "Google News (ZH)"},
    {"url": "https://news.google.com/rss/search?q=AI%20%E8%8A%AF%E7%89%87%20OR%20NVIDIA%20GPU&hl=zh-CN&gl=US&ceid=US:zh-Hans", "source": "Google News (ZH)"},
    {"url": "https://news.google.com/rss/search?q=AI%20Act%20OR%20regulation&hl=en-US&gl=US&ceid=US:en", "source": "Google News (EN)"},
    {"url": "https://news.google.com/rss/search?q=AI%20funding%20OR%20Series%20A&hl=en-US&gl=US&ceid=US:en", "source": "Google News (EN)"},
    
    # Hacker News
    {"url": "https://hnrss.org/newest?q=AI%20agent", "source": "Hacker News"},
    {"url": "https://hnrss.org/newest?q=OpenAI", "source": "Hacker News"},
    {"url": "https://hnrss.org/newest?q=NVIDIA", "source": "Hacker News"},
    
    # arXiv (Research Papers)
    {"url": "https://export.arxiv.org/rss/cs.LG", "source": "arXiv (Machine Learning)"},
    {"url": "https://export.arxiv.org/rss/cs.RO", "source": "arXiv (Robotics)"}
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
    
    # Limit items per feed to avoid overloading the dashboard (e.g., max 15 per feed)
    for entry in feed.entries[:15]:
        title = BeautifulSoup(entry.title, "html.parser").get_text()
        
        summary_html = entry.get('summary', '')
        summary_text = BeautifulSoup(summary_html, "html.parser").get_text()
        if not summary_text or summary_text == title:
             summary_text = f"Read the full article at the source link."
             
        try:
            pub_date = date_parser.parse(entry.published)
        except:
            pub_date = datetime.datetime.now()
            
        topics, comps, regions = tag_article(title + " " + summary_text)
        
        items.append({
            "Title_EN": title,
            "Summary_EN": summary_text[:300] + "..." if len(summary_text) > 300 else summary_text,
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
def translate_texts(texts):
    translator = GoogleTranslator(source='auto', target='zh-CN')
    translated = []
    chunk_size = 20 
    
    for i in range(0, len(texts), chunk_size):
        chunk = texts[i:i+chunk_size]
        delimiter = " |^^| "
        combined_text = delimiter.join(chunk)
        try:
            if i > 0: time.sleep(0.5)
            trans_combined = translator.translate(combined_text)
            if trans_combined:
                parts = re.split(r'\s*\|\^\^\|\s*', trans_combined)
                if len(parts) == len(chunk):
                    translated.extend(parts)
                else:
                    for t in chunk:
                        translated.append(translator.translate(t))
            else:
                 translated.extend(chunk)
        except Exception as e:
            for t in chunk:
                try:
                    time.sleep(0.1)
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
        'say', 'says', 'said', 'who', 'why', 'when', 'where', 'which', 'hn', 'show'
    ])
    
    keywords = [w for w in text.split() if w not in stopwords and len(w) > 3]
    top_keywords = Counter(keywords).most_common(20)
    
    return df, top_keywords

# --- Main Workflow ---
with st.spinner(ui["scraping"][lang]):
    df_news = fetch_all_news()

if not df_news.empty:
    df_news, top_keywords = analyze_trends(df_news)
    
    df_news['Date_Str'] = df_news['Published_Date'].dt.strftime('%Y-%m-%d %H:%M')
    df_news['Day'] = df_news['Published_Date'].dt.strftime('%Y-%m-%d')
    
    if lang == "中文":
        with st.spinner(ui["translating"][lang]):
            df_news["Title"] = translate_texts(df_news["Title_EN"].tolist())
            df_news["Summary"] = df_news["Summary_EN"] 
    else:
        df_news["Title"] = df_news["Title_EN"]
        df_news["Summary"] = df_news["Summary_EN"]
        
    # --- Sidebar Filters & Search ---
    with st.sidebar:
        st.header(ui["filters"][lang])
        
        search_query = st.text_input(ui["search"][lang], "")
        
        # Topic & Company Filters
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            selected_topic = st.selectbox(ui["topic_filter"][lang], [ui["all"][lang]] + TOPICS)
        with col_f2:
            selected_company = st.selectbox(ui["company_filter"][lang], [ui["all"][lang]] + COMPANIES)
            
        # Region & Source Type Filters
        col_f3, col_f4 = st.columns(2)
        with col_f3:
            selected_region = st.selectbox(ui["region_filter"][lang], [ui["all"][lang]] + REGIONS)
        with col_f4:
            selected_source_type = st.selectbox(ui["source_type_filter"][lang], [ui["all"][lang]] + SOURCE_TYPES)
            
        # Time Range Filter
        selected_time = st.selectbox(ui["time_range_filter"][lang], [ui["all"][lang]] + list(TIME_RANGES.keys()))
        
        sort_options = [ui["sort_time_desc"][lang], ui["sort_time_asc"][lang], ui["sort_sentiment"][lang]]
        selected_sort = st.selectbox(ui["sort_by"][lang], sort_options)

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
        # --- Visualizations ---
        st.subheader("📊 Analytics Dashboard")
        tab1, tab2 = st.tabs(["Sentiment & Keywords", "Time & Sources"])
        
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
                df_keywords = pd.DataFrame(top_keywords[:10], columns=['Keyword', 'Count']) 
                df_keywords = df_keywords.sort_values(by='Count', ascending=True)
                fig_keywords = px.bar(
                    df_keywords, x='Count', y='Keyword', orientation='h',
                    color='Count', color_continuous_scale=px.colors.sequential.Blues,
                    title=ui["keyword_chart"][lang]
                )
                fig_keywords.update_layout(margin=dict(t=40, b=0, l=0, r=0))
                st.plotly_chart(fig_keywords, use_container_width=True)
                
        with tab2:
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
            
        st.divider()
        
        # --- Expandable News Feed ---
        st.subheader(ui["table_title"][lang])
        st.markdown(ui["table_desc"][lang])
        
        for idx, row in filtered_df.iterrows():
            sentiment_val = row['Sentiment']
            if sentiment_val == 'Positive':
                badge_color = "green"
                sent_text = "积极" if lang == "中文" else "Positive"
            elif sentiment_val == 'Negative':
                badge_color = "red"
                sent_text = "消极" if lang == "中文" else "Negative"
            else:
                badge_color = "blue"
                sent_text = "中立" if lang == "中文" else "Neutral"
                
            # Create tag badges
            tags = row['Topics'] + row['Companies'] + row['Regions']
            tag_str = " | ".join([f"`{t}`" for t in tags]) if tags else ""
            
            with st.expander(f"**{row['Title']}**"):
                st.markdown(f"**{ui['published'][lang]}** {row['Date_Str']} | **{ui['source'][lang]}** {row['Source']} | **{ui['sentiment_label'][lang]}** :{badge_color}[{sent_text}]")
                if tag_str:
                    st.markdown(f"**{ui['tags'][lang]}** {tag_str}")
                st.markdown(f"**{ui['summary'][lang]}**")
                st.info(row['Summary'])
                st.markdown(f"🔗 [{ui['read_more'][lang]}]({row['Link']})")
    else:
        st.warning(ui["no_data"][lang])
else:
    st.warning(ui["no_data"][lang])