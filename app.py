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
import random
from dateutil import parser as date_parser
import concurrent.futures
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# --- Config ---
st.set_page_config(page_title="AI Morning Coffee", layout="wide", page_icon="☕")

# --- UI Dictionary ---
ui = {
    "title": {"English": "☕ AI Morning Coffee", "中文": "☕ AI 早咖啡"},
    "desc": {"English": "Brewing the latest AI trends to kickstart a brand new day, and empowering every job seeker to unlock a brand new career and life.", 
             "中文": "为您萃取全球最新的 AI 动态，用前沿科技「为您打开全新的一天」，更助力每一位求职者「打开全新的人生」。"},
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
    "top_headlines": {"English": "🔥 Daily Must-Reads (Most Important)", "中文": "🔥 每日必读 (重磅精选)"},
    "topic_dist_chart": {"English": "AI Domain Distribution", "中文": "AI 细分领域分布"},
    "company_mentions_chart": {"English": "Company Mentions", "中文": "热门公司提及热度"},
    "wordcloud_chart": {"English": "Keyword Frequency Analysis", "中文": "高频词汇云分析"},
    "tab_glossary": {"English": "📖 AI Glossary & Learning", "中文": "📖 AI 概念科普与学习"},
    "tab_career": {"English": "💼 Career & Interview Guide", "中文": "💼 岗位技能与面试指南"},
    "tab_cases": {"English": "💡 Business Case Studies", "中文": "💡 商业落地案例库"},
    "glossary_intro": {"English": "Transitioning to AI? Master the core concepts to decode industry news and job descriptions.", "中文": "准备转型 AI 领域求职？掌握这些核心概念与行话，助你快速看懂行业新闻与招聘要求。"},
    "word_of_day": {"English": "🌟 Word of the Day", "中文": "🌟 每日一词推荐"},
    "mark_learned": {"English": "✅ I've mastered this!", "中文": "✅ 我已掌握，今日打卡！"},
    "learned_success": {"English": "🎉 Awesome! You've learned something new today. Keep it up!", "中文": "🎉 太棒了！今天又进步了一点点，继续保持！"}
}

# --- Navigation & Language ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/cafe.png", width=60)
    lang = st.radio("Language / 语言", ["中文", "English"], label_visibility="collapsed")
    st.divider()
    
    st.markdown("**Navigation / 导航**")
    nav_options = [
        ui["tab_news"][lang], 
        ui["tab_analytics"][lang], 
        ui["tab_glossary"][lang],
        ui["tab_career"][lang],
        ui["tab_cases"][lang]
    ]
    selected_page = st.radio("Navigation", nav_options, label_visibility="collapsed")
    st.divider()

st.title(ui["title"][lang])
st.markdown(ui["desc"][lang])

# --- Whitelists based on user list ---
# Use internal keys for logic, and map them to display strings
TOPICS = [
    "Agent", "Open Source Models", "Closed Source Models", "Multimodal", "Inference", 
    "Training/Data", "AI Chips/Compute", "AI Apps/Products", 
    "Regulation/Policy", "Funding/M&A", "Healthcare AI", "Autonomous Driving/Robotics"
]

TOPICS_ZH = {
    "Agent": "智能代理 (Agent)",
    "Open Source Models": "开源模型",
    "Closed Source Models": "闭源模型",
    "Multimodal": "多模态",
    "Inference": "推理/加速",
    "Training/Data": "训练/数据",
    "AI Chips/Compute": "AI芯片/算力",
    "AI Apps/Products": "AI应用/产品",
    "Regulation/Policy": "监管/政策",
    "Funding/M&A": "投融资/并购",
    "Healthcare AI": "医疗AI",
    "Autonomous Driving/Robotics": "自动驾驶/机器人"
}

COMPANIES = [
    "OpenAI", "Anthropic", "Google", "DeepMind", "Microsoft", 
    "NVIDIA", "Meta", "Apple", "xAI", "Perplexity", "Mistral", "Tesla"
]

REGIONS = [
    "US / North America", "China / Asia", "Europe / EU", "Middle East"
]

REGIONS_ZH = {
    "US / North America": "美国 / 北美",
    "China / Asia": "中国 / 亚洲",
    "Europe / EU": "欧洲 / 欧盟",
    "Middle East": "中东"
}

SOURCE_TYPES = [
    "Mainstream Media", "Tech Forums", "Research Papers"
]

SOURCE_TYPES_ZH = {
    "Mainstream Media": "主流媒体",
    "Tech Forums": "技术社区",
    "Research Papers": "学术论文"
}

TIME_RANGES = {
    "Last 24 Hours": 1,
    "Last 48 Hours": 2,
    "Last 3 Days": 3,
    "Last 7 Days": 7
}

TIME_RANGES_ZH = {
    "Last 24 Hours": "过去 24 小时",
    "Last 48 Hours": "过去 48 小时",
    "Last 3 Days": "过去 3 天",
    "Last 7 Days": "过去 7 天"
}

# --- AI Glossary Data ---
STRUCTURED_GLOSSARY = {
    "1. Foundations & Theory / 基础理论": {
        "Artificial Intelligence (AI / 人工智能)": {
            "English": "The broader concept of machines being able to carry out tasks in a way that we would consider 'smart'.",
            "中文": "让机器具备人类智能的广义概念，能像人一样感知、认知、决策和执行。AI 是所有相关技术的总称。"
        },
        "Machine Learning (ML / 机器学习)": {
            "English": "A subset of AI based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention.",
            "中文": "AI 的一个核心分支。核心思想是“不用写死规则，让机器自己从数据中找规律并学会预测”。"
        },
        "Deep Learning (DL / 深度学习)": {
            "English": "A subset of ML that uses multi-layered artificial neural networks to deliver state-of-the-art accuracy in tasks like object detection and speech recognition.",
            "中文": "机器学习的进阶版。利用多层“人工神经网络”来模拟人脑，是目前 ChatGPT 等大模型背后的绝对主力技术。"
        },
        "Neural Network (神经网络)": {
            "English": "Computing systems with interconnected nodes that work much like neurons in the human brain.",
            "中文": "模仿人脑神经元结构的计算系统。信息在成千上万的“节点”中层层传递和计算，最终得出结果。"
        },
        "Transformer": {
            "English": "The foundational deep learning architecture behind modern LLMs, introduced by Google in 2017, relying on an 'attention mechanism'.",
            "中文": "Google 在 2017 年提出的一种深度学习架构，是目前几乎所有主流大模型（包括 GPT 系列）的基础底座，其核心是“注意力机制（Attention）”。"
        },
        "Token (词元)": {
            "English": "The basic building blocks of text that LLMs process. A token can be a word, part of a word, or just a single character.",
            "中文": "大模型处理文本的基本单位。一个 token 可能是一个汉字、一个英文单词或词的一部分。目前绝大多数大模型的 API 计费都是基于处理了多少个 tokens。"
        },
        "Parameters (参数量)": {
            "English": "The internal variables that an AI model learns during training. Think of them as the 'synapses' of the AI's brain. More parameters usually mean a smarter, but more expensive model (e.g., 7B, 70B).",
            "中文": "AI 模型在训练过程中学到的内部变量。相当于 AI 大脑里的“突触”数量。参数量越大（如 7B, 70B, 千亿/万亿），模型通常越聪明，但运行成本也越高。"
        }
    },
    "2. Core Models / 核心模型": {
        "LLM (Large Language Model / 大语言模型)": {
            "English": "An AI algorithm that uses deep learning techniques and massive datasets to understand, summarize, generate, and predict content. Examples: GPT-4, Claude 3.",
            "中文": "利用深度学习技术和海量数据来理解、总结、生成和预测新内容的 AI 模型。简单来说就是“读过无数书的超级大脑”。代表作：GPT-4, Claude 3。"
        },
        "Foundation Model (基础模型)": {
            "English": "A large AI model trained on a vast quantity of unlabeled data at scale, which can be adapted (e.g., fine-tuned) to a wide range of downstream tasks.",
            "中文": "在海量无标签数据上训练出来的超大型 AI 模型，它是一个“全才底座”，可以被微调成各种特定领域的专家。"
        },
        "Multimodal (多模态模型)": {
            "English": "An AI system that can understand and generate multiple types of data formats simultaneously, such as text, images, audio, and video.",
            "中文": "不仅能看懂文字，还能看懂图片、听懂声音、甚至看懂视频的 AI 系统（如 GPT-4o, Gemini 1.5 Pro）。"
        },
        "Diffusion Model (扩散模型)": {
            "English": "A class of generative AI models used primarily for generating high-quality images and video by gradually adding and then removing noise from data (e.g., Midjourney, Stable Diffusion).",
            "中文": "目前主流的 AI 画图/视频生成技术（如 Midjourney, Sora）。原理是先把图像打成马赛克（加噪），再让 AI 学习如何把马赛克还原成清晰的高清图像（去噪）。"
        },
        "AGI (Artificial General Intelligence / 通用人工智能)": {
            "English": "A hypothetical type of AI that can understand, learn, and apply knowledge across a wide range of tasks at a level equal to or beyond human capabilities.",
            "中文": "理论上的一种 AI，能在所有智力任务上达到甚至超越人类的水平。这是目前 OpenAI 等头部公司的终极目标。"
        }
    },
    "3. Training & Tuning / 训练与优化": {
        "Pre-training (预训练)": {
            "English": "The initial phase where a model is trained on a massive dataset to learn general language patterns before being specialized.",
            "中文": "大模型“上大学”的阶段。给它喂海量的互联网文本，让它学会人类语言的规律和世界常识。这个阶段极其昂贵，动辄花费千万美元。"
        },
        "Fine-tuning (微调)": {
            "English": "The process of taking a pre-trained model and training it further on a smaller, specific dataset to adapt it for a particular task or domain.",
            "中文": "大模型“考研/考证”的阶段。在预训练模型基础上，用特定领域的小数据集（如医疗病历、法律文书）再训练一次，让它成为某个领域的专家。"
        },
        "RLHF (Reinforcement Learning from Human Feedback)": {
            "English": "A method to align an AI model's behavior with human values by rewarding it for generating outputs that human reviewers rate highly.",
            "中文": "基于人类反馈的强化学习。就是雇佣人类老师给 AI 的回答打分，AI 为了拿高分就会不断调整自己的行为，从而变得更有礼貌、更符合人类价值观。"
        },
        "Hallucination (幻觉)": {
            "English": "When an AI model confidently generates false, nonsensical, or unverified information.",
            "中文": "指 AI 模型“一本正经地胡说八道”，生成看似合理但实际上完全错误、捏造的信息。"
        }
    },
    "4. AI Engineering & App / 工程与应用": {
        "Prompt Engineering (提示词工程)": {
            "English": "The practice of designing and refining the text inputs (prompts) given to an AI to get the most accurate and useful outputs.",
            "中文": "设计和优化输入给 AI 的指令（提示词），引导模型输出最准确结果的技术，被称为“与 AI 沟通的魔法”。"
        },
        "RAG (Retrieval-Augmented Generation / 检索增强生成)": {
            "English": "A technique that connects an LLM to external databases, allowing it to reference up-to-date or private information before generating an answer, reducing hallucinations.",
            "中文": "一种核心工程技术。让大模型在回答问题前，先去企业内部知识库里“查阅资料”，再根据资料回答。有效解决大模型乱编（幻觉）和数据不更新的问题。"
        },
        "Agent (智能体)": {
            "English": "An AI system capable of autonomous action, tool use (like browsing the web or running code), and decision-making to achieve a specific goal.",
            "中文": "能够自主行动、使用工具（如上网搜索、写代码）并做出决策以实现特定目标的 AI 系统。它不仅仅是“聊天机器人”，而是能帮你干活的“数字打工人”。"
        },
        "Vector Database (向量数据库)": {
            "English": "A specialized database that stores data as mathematical vectors, allowing AI to quickly search for conceptually similar information.",
            "中文": "专为 AI 时代打造的数据库。它把文字、图片变成一串串数学数字（向量），AI 通过对比数字的距离，就能瞬间找出“意思最相近”的内容。"
        },
        "Copilot (AI 助手/副驾驶)": {
            "English": "An AI tool integrated into software applications to assist users with tasks like writing code, drafting emails, or analyzing data.",
            "中文": "集成在软件里的 AI 助手。它不像自动驾驶那样完全接管，而是作为“副驾驶”辅助你完成写代码、做 PPT 等工作（如 GitHub Copilot, Microsoft 365 Copilot）。"
        }
    },
    "5. Compute & Hardware / 算力与基建": {
        "GPU (Graphics Processing Unit / 图形处理器)": {
            "English": "Originally for gaming, GPUs excel at processing many calculations simultaneously, making them the engine of choice for training and running AI models.",
            "中文": "显卡芯片（如英伟达 H100）。由于它非常擅长“同时处理大量简单的数学题”，成为了目前训练和运行 AI 模型不可或缺的算力引擎。"
        },
        "Inference (推理)": {
            "English": "The phase where a trained AI model is put to work, generating predictions or outputs based on new, unseen data (like answering your prompt).",
            "中文": "AI 训练好之后，实际上线为用户提供服务、回答问题的过程。如果你在使用 ChatGPT，你的每一次提问，都在消耗服务器的“推理算力”。"
        },
        "FLOPS (每秒浮点运算次数)": {
            "English": "Floating-point operations per second. A measure of computer performance, crucial for understanding the immense computational power required for AI.",
            "中文": "衡量计算机算力速度的指标。AI 模型的训练通常需要极高的 FLOPS，标志着极度密集的数学计算能力。"
        }
    }
}

# --- Career & Interview Data ---
CAREER_GUIDE = {
    "AI Product Manager / AI 产品经理": {
        "desc": {
            "English": "Responsible for bridging the gap between AI technical capabilities and user needs, defining product vision, and managing the AI product lifecycle.",
            "中文": "负责将 AI 技术能力转化为解决用户痛点的产品。不仅要懂业务和用户体验，还要懂模型的边界和能力。"
        },
        "skills": {
            "English": ["Product Strategy", "Understanding of LLM/Generative AI capabilities", "Prompt Engineering", "Data-driven Decision Making", "Cross-functional Communication"],
            "中文": ["产品战略规划", "熟悉大模型(LLM)及生成式AI的能力与边界", "提示词工程 (Prompt Engineering)", "数据驱动决策与指标设计", "跨部门沟通与敏捷管理"]
        },
        "interview_q": {
            "English": [
                "How do you define the success metrics for an AI-powered feature?",
                "Describe a situation where the AI model's output is unpredictable. How do you design the UX to handle this?",
                "What is your framework for deciding whether to build a custom model or use an existing API like OpenAI?"
            ],
            "中文": [
                "如果要在现有 App 中加入 AI 助手，你会如何定义这个功能的成功指标（北极星指标）？",
                "大模型的输出具有随机性（甚至幻觉），在产品 UX/交互设计上，你会如何规避或缓解这种风险？",
                "在评估是直接接入 OpenAI API 还是自己微调（Fine-tune）一个开源模型时，你的决策框架是什么？"
            ]
        }
    },
    "AI Prompt Engineer / 提示词工程师": {
        "desc": {
            "English": "Specializes in designing, testing, and refining prompts to get the optimal performance out of Large Language Models.",
            "中文": "专门研究如何给 AI 下指令的专家。通过不断测试和优化提示词，让大模型稳定、高质量地输出符合业务需求的结果。"
        },
        "skills": {
            "English": ["Advanced Prompting (Few-shot, CoT)", "Understanding LLM behaviors", "Python (Basic)", "A/B Testing", "Domain Knowledge"],
            "中文": ["高级提示词技巧 (如 Few-shot, 思维链 CoT)", "深刻理解不同大模型的脾气与特性", "基础 Python 编程", "A/B 测试与批量评估能力", "特定领域的业务知识"]
        },
        "interview_q": {
            "English": [
                "Explain 'Chain of Thought' prompting and when you would use it.",
                "How do you evaluate and measure the quality of a prompt's output at scale?",
                "If a model keeps ignoring a specific constraint in your prompt, how do you debug and fix it?"
            ],
            "中文": [
                "请解释什么是“思维链 (Chain of Thought)”提示，并在什么场景下使用它最有效？",
                "当你在批量处理 1000 条数据时，如何量化和评估你的提示词输出质量？",
                "如果大模型总是忽略你提示词中的某一条特定约束（比如“字数不超过50字”），你会如何调试和修改指令？"
            ]
        }
    },
    "AI Operations & Marketing / AI 运营与营销": {
        "desc": {
            "English": "Leverages AI tools to 10x marketing efficiency, manage communities, generate content, and drive growth for AI-native products.",
            "中文": "利用各种 AI 工具（如 ChatGPT, Midjourney）将运营和营销效率提升十倍，同时负责 AI 原生产品的用户增长和社区管理。"
        },
        "skills": {
            "English": ["Content Generation with AI", "Growth Hacking", "Community Management", "Data Analytics", "Familiarity with AI tool landscape"],
            "中文": ["利用 AI 工具批量生成高质量图文/视频", "增长黑客与裂变玩法", "社区运营 (Discord/微信群)", "数据分析", "对最新 AI 工具生态极度敏感"]
        },
        "interview_q": {
            "English": [
                "Which AI tools do you use daily to improve your workflow, and what are their limitations?",
                "How would you design a go-to-market strategy for a new B2B AI writing assistant?",
                "How do you balance AI-generated content with human authenticity to engage a community?"
            ],
            "中文": [
                "你每天都在使用哪些 AI 工具来提升工作效率？它们目前的局限性是什么？",
                "如果要为一款全新的 B2B 垂直领域 AI 写作助手制定冷启动/推向市场 (Go-to-market) 策略，你会怎么做？",
                "在社区运营中，你如何平衡 AI 生成内容的“高效率”和真人互动的“真实感”？"
            ]
        }
    },
    "AI Solutions Architect / AI 解决方案架构师": {
        "desc": {
            "English": "Works closely with clients to understand their business problems and designs technical AI solutions (like RAG pipelines) to solve them.",
            "中文": "对接企业客户，深入理解他们的业务痛点，并利用现有的 AI 技术栈（如 RAG、Agent、大模型 API）为客户设计落地的技术方案。"
        },
        "skills": {
            "English": ["System Architecture (RAG, Agents)", "Cloud Platforms (AWS, Azure)", "Client Communication", "Python/API integration", "Business Acumen"],
            "中文": ["AI 系统架构设计 (熟悉 RAG 和 Agent 工作流)", "熟悉主流云平台及 AI 服务", "优秀的客户沟通与需求挖掘能力", "Python 开发及 API 集成能力", "深厚的商业洞察力"]
        },
        "interview_q": {
            "English": [
                "Walk me through the architecture of a Retrieval-Augmented Generation (RAG) system.",
                "A client wants to build a chatbot using their highly confidential financial data. How do you ensure data privacy?",
                "How do you estimate the token costs and latency for a high-traffic AI application?"
            ],
            "中文": [
                "请为我详细讲解一个基于企业知识库的 RAG（检索增强生成）系统的标准架构和数据流转过程。",
                "客户希望用他们极度机密的财务数据做一个内部 AI 问答机器人。在架构设计上，你如何保证数据的绝对安全和隐私？",
                "对于一个高并发的 AI 对话应用，你会如何预估和控制 Token 的 API 调用成本以及响应延迟？"
            ]
        }
    }
}

# --- Business Case Studies Data ---
BUSINESS_CASES = {
    "1. E-commerce / 电子商务": [
        {
            "title": {"English": "Personalized AI Shopping Assistant", "中文": "个性化 AI 购物助手 (导购 Agent)"},
            "problem": {"English": "High cart abandonment rates and poor product discovery for users with vague intent.", "中文": "用户只有模糊购物意图时（如“送给妈妈的生日礼物”），传统搜索效率低，导致购物车放弃率高。"},
            "solution": {"English": "Implementing an LLM-based Agent that asks clarifying questions, uses RAG to fetch real-time inventory, and recommends products matching the exact context.", "中文": "引入基于大模型的导购 Agent。通过多轮对话挖掘用户真实需求，结合 RAG（检索增强生成）实时查询企业库存并给出精准推荐。"},
            "impact": {"English": "Increased conversion rate by 20% and reduced average time-to-purchase.", "中文": "商品转化率提升 20%，用户平均决策时间大幅缩短。"}
        },
        {
            "title": {"English": "Dynamic Product Description Generation", "中文": "商品详情页动态生成"},
            "problem": {"English": "Writing SEO-optimized and engaging product descriptions for thousands of SKUs is time-consuming and expensive.", "中文": "为数以万计的 SKU 撰写吸引人且符合 SEO 规范的商品详情页，耗时极长且人工成本高昂。"},
            "solution": {"English": "Fine-tuning an open-source model (like Llama 3) on the brand's tone of voice to automatically generate product copy from basic attributes.", "中文": "使用品牌特有的语气数据微调开源大模型（如 Llama 3），只需输入基础参数（颜色、材质等），即可批量生成高质量的商品文案。"},
            "impact": {"English": "Cut content creation time by 90% and improved organic search traffic.", "中文": "文案创作时间缩减 90%，并有效提升了自然搜索流量。"}
        }
    ],
    "2. Healthcare / 医疗健康": [
        {
            "title": {"English": "AI-Assisted Medical Imaging", "中文": "AI 辅助医学影像分析"},
            "problem": {"English": "Radiologists suffer from fatigue, leading to potential misdiagnoses in subtle cases like early-stage tumors.", "中文": "放射科医生长期工作容易疲劳，在面对早期肿瘤等微小病灶时存在漏诊风险。"},
            "solution": {"English": "Deploying Computer Vision models (like ResNet or specialized Diffusion models) to highlight areas of concern in X-rays and MRIs before the doctor reviews them.", "中文": "部署计算机视觉模型（如 ResNet）对 X 光或 MRI 影像进行预处理，用热力图高亮疑似病灶区域，作为医生的“第二双眼睛”。"},
            "impact": {"English": "Reduced diagnostic error rates by 15% and sped up image review times.", "中文": "早期病灶漏诊率降低 15%，极大加快了医生的阅片速度。"}
        },
        {
            "title": {"English": "Clinical Documentation Automation", "中文": "智能病历与临床文档自动生成"},
            "problem": {"English": "Doctors spend up to 2 hours a day typing patient notes and updating electronic health records (EHR).", "中文": "医生每天需花费长达 2 小时手动录入病历和更新电子健康档案 (EHR)，严重挤压了看病时间。"},
            "solution": {"English": "Using an ambient AI scribe (speech-to-text + LLM) to listen to the doctor-patient consultation and automatically draft structured clinical notes.", "中文": "使用环境级 AI 记录员（语音识别 + 大模型提取），在医患问诊时自动旁听，并在问诊结束后自动生成结构化的标准病历草稿。"},
            "impact": {"English": "Saved doctors 1.5 hours daily, significantly reducing physician burnout.", "中文": "平均每天为医生节省 1.5 小时文书工作时间，大幅降低了职业倦怠。"}
        }
    ],
    "3. Finance / 金融服务": [
        {
            "title": {"English": "Automated Investment Research", "中文": "智能投研分析与研报生成"},
            "problem": {"English": "Analysts spend countless hours reading earnings call transcripts, news, and 10-K reports to find actionable insights.", "中文": "金融分析师需要耗费大量时间阅读冗长的财报、电话会议记录和宏观新闻，难以快速提炼投资逻辑。"},
            "solution": {"English": "A RAG-powered system that ingests financial documents and allows analysts to query specific metrics, automatically synthesizing multi-document reports.", "中文": "构建专属的金融 RAG 系统，将海量研报和新闻向量化。分析师可直接向 AI 提问（如“对比A公司和B公司的毛利率”），AI 会自动提取多篇文档并生成对比摘要。"},
            "impact": {"English": "Reduced research cycle time by 40%, enabling faster investment decisions.", "中文": "单份深度研报的资料收集时间缩短 40%，决策效率大幅提升。"}
        },
        {
            "title": {"English": "Real-time Fraud Detection", "中文": "实时交易反欺诈检测"},
            "problem": {"English": "Rule-based fraud detection systems flag too many false positives and struggle to catch novel scam patterns.", "中文": "传统的基于规则的反欺诈系统“误杀率”太高，且面对新型的诈骗手法反应迟钝。"},
            "solution": {"English": "Training Graph Neural Networks (GNNs) and deep learning models on transaction histories to detect anomalous behaviors and hidden network rings in real-time.", "中文": "利用图神经网络 (GNN) 和深度学习模型分析交易链路，在毫秒级内识别异常行为模式和隐藏的洗钱网络。"},
            "impact": {"English": "Decreased false positives by 30% while catching 25% more novel fraud cases.", "中文": "误报率降低 30%，同时对新型欺诈案件的拦截率提升了 25%。"}
        }
    ]
}

# RSS Feeds List (Expanded Set for more volume)
# Modify queries to only fetch recent news (when:2d instead of when:7d for Google News)
RSS_FEEDS = [
    # Google News (Mixed EN/CN) - Restricted to 2 days for freshness
    {"url": "https://news.google.com/rss/search?q=%E6%99%BA%E8%83%BD%E4%BB%A3%E7%90%86%20OR%20AI%20Agent+when:2d&hl=zh-CN&gl=US&ceid=US:zh-Hans", "source": "Google News (ZH)"},
    {"url": "https://news.google.com/rss/search?q=%E5%BC%80%E6%BA%90%20%E6%A8%A1%E5%9E%8B%20OR%20open-source%20model+when:2d&hl=zh-CN&gl=US&ceid=US:zh-Hans", "source": "Google News (ZH)"},
    {"url": "https://news.google.com/rss/search?q=AI%20%E8%8A%AF%E7%89%87%20OR%20NVIDIA%20GPU+when:2d&hl=zh-CN&gl=US&ceid=US:zh-Hans", "source": "Google News (ZH)"},
    {"url": "https://news.google.com/rss/search?q=%E5%8C%BB%E7%96%97%20AI%20OR%20medical%20AI+when:2d&hl=zh-CN&gl=US&ceid=US:zh-Hans", "source": "Google News (ZH)"},
    {"url": "https://news.google.com/rss/search?q=%E8%87%AA%E5%8A%A8%E9%A9%BE%E9%A9%B6%20OR%20robotaxi+when:2d&hl=zh-CN&gl=US&ceid=US:zh-Hans", "source": "Google News (ZH)"},
    {"url": "https://news.google.com/rss/search?q=AI%20Act%20OR%20regulation+when:2d&hl=en-US&gl=US&ceid=US:en", "source": "Google News (EN)"},
    {"url": "https://news.google.com/rss/search?q=AI%20funding%20OR%20Series%20A+when:2d&hl=en-US&gl=US&ceid=US:en", "source": "Google News (EN)"},
    {"url": "https://news.google.com/rss/search?q=OpenAI%20OR%20ChatGPT+when:2d&hl=en-US&gl=US&ceid=US:en", "source": "Google News (EN)"},
    {"url": "https://news.google.com/rss/search?q=Anthropic%20OR%20Claude+when:2d&hl=en-US&gl=US&ceid=US:en", "source": "Google News (EN)"},
    {"url": "https://news.google.com/rss/search?q=Google%20DeepMind%20AI+when:2d&hl=en-US&gl=US&ceid=US:en", "source": "Google News (EN)"},
    
    # Hacker News (inherently sorted by newest)
    {"url": "https://hnrss.org/newest?q=AI%20agent", "source": "Hacker News"},
    {"url": "https://hnrss.org/newest?q=OpenAI", "source": "Hacker News"},
    {"url": "https://hnrss.org/newest?q=NVIDIA", "source": "Hacker News"},
    {"url": "https://hnrss.org/newest?q=Llama%20OR%20open-source", "source": "Hacker News"},
    
    # arXiv (inherently sorted by newest submissions)
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
    if any(k in text_lower for k in ["open-source", "开源", "llama", "mistral"]): found_topics.append("Open Source Models")
    if any(k in text_lower for k in ["chip", "gpu", "h100", "b200", "芯片", "算力"]): found_topics.append("AI Chips/Compute")
    if any(k in text_lower for k in ["regulation", "law", "act", "监管", "法规", "政策"]): found_topics.append("Regulation/Policy")
    if any(k in text_lower for k in ["funding", "series a", "venture", "融资", "风投", "并购"]): found_topics.append("Funding/M&A")
    if any(k in text_lower for k in ["medical", "health", "fda", "医疗", "健康"]): found_topics.append("Healthcare AI")
    if any(k in text_lower for k in ["robot", "autonomous", "fsd", "机器人", "自动驾驶"]): found_topics.append("Autonomous Driving/Robotics")
    
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

# --- Main Routing ---
if selected_page in [ui["tab_news"][lang], ui["tab_analytics"][lang]]:
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
            
            # Prepare translated options for selectboxes
            def get_display_opts(keys_list, zh_dict):
                if lang == "中文":
                    return [ui["all"][lang]] + [zh_dict.get(k, k) for k in keys_list]
                return [ui["all"][lang]] + keys_list
                
            time_opts_display = get_display_opts(list(TIME_RANGES.keys()), TIME_RANGES_ZH)
            selected_time_display = st.selectbox("Time", time_opts_display, label_visibility="collapsed")
            # Map back to internal key
            selected_time = list(TIME_RANGES.keys())[time_opts_display.index(selected_time_display) - 1] if selected_time_display != ui["all"][lang] else ui["all"][lang]
            
            st.markdown("---")
            
            # Topic & Company Filters
            st.markdown(f"**{ui['topic_filter'][lang]} & {ui['company_filter'][lang]}**")
            topic_opts_display = get_display_opts(TOPICS, TOPICS_ZH)
            selected_topic_display = st.selectbox("Topic", topic_opts_display, label_visibility="collapsed")
            selected_topic = TOPICS[topic_opts_display.index(selected_topic_display) - 1] if selected_topic_display != ui["all"][lang] else ui["all"][lang]
            
            selected_company = st.selectbox("Company", [ui["all"][lang]] + COMPANIES, label_visibility="collapsed")
                
            st.markdown("---")
            
            # Region & Source Type Filters
            st.markdown(f"**{ui['region_filter'][lang]} & {ui['source_type_filter'][lang]}**")
            
            region_opts_display = get_display_opts(REGIONS, REGIONS_ZH)
            selected_region_display = st.selectbox("Region", region_opts_display, label_visibility="collapsed")
            selected_region = REGIONS[region_opts_display.index(selected_region_display) - 1] if selected_region_display != ui["all"][lang] else ui["all"][lang]
            
            source_type_opts_display = get_display_opts(SOURCE_TYPES, SOURCE_TYPES_ZH)
            selected_source_type_display = st.selectbox("Source", source_type_opts_display, label_visibility="collapsed")
            selected_source_type = SOURCE_TYPES[source_type_opts_display.index(selected_source_type_display) - 1] if selected_source_type_display != ui["all"][lang] else ui["all"][lang]
            
            st.markdown("---")
            if st.button("Reset Filters" if lang == "English" else "重置所有筛选"):
                st.rerun()

        # --- Main Area Search & Sort ---
        col_search, col_sort = st.columns([3, 1], vertical_alignment="bottom")
        with col_search:
            search_query = st.text_input("Search", placeholder=ui["search"][lang], label_visibility="collapsed")
        with col_sort:
            sort_options = [ui["sort_time_desc"][lang], ui["sort_time_asc"][lang], ui["sort_sentiment"][lang]]
            selected_sort = st.selectbox("Sort", sort_options, label_visibility="collapsed")

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
        if selected_page == ui["tab_news"][lang]:
                # --- Top Headlines Section ---
                # Show top 3 most important articles based on recency and sentiment
                # We filter for 'Positive' or 'Neutral' and sort by Date first, then Sentiment
                positive_news = filtered_df[filtered_df['Sentiment'] != 'Negative'].sort_values(
                    by=['Published_Date', 'Sentiment_Score'], ascending=[False, False]
                )
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
                        
                    # Create tag badges (translate if needed)
                    def translate_tag(t):
                        if lang == "中文":
                            if t in TOPICS: return TOPICS_ZH.get(t, t)
                            if t in REGIONS: return REGIONS_ZH.get(t, t)
                        return t
                        
                    tags = row['Topics'] + row['Companies'] + row['Regions']
                    tag_str = " ".join([f"`{translate_tag(t)}`" for t in tags]) if tags else ""
                    
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
                            
        elif selected_page == ui["tab_analytics"][lang]:
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
                            # Translate topics for the chart if in Chinese mode
                            if lang == "中文":
                                topic_counts = [(TOPICS_ZH.get(t, t), c) for t, c in topic_counts]
                                
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
elif selected_page == ui["tab_glossary"][lang]:
    st.subheader(ui["tab_glossary"][lang])
    st.markdown(ui["glossary_intro"][lang])
    
    # --- Daily Word of the Day ---
    # Use current date as random seed so it changes only once per day
    today = datetime.datetime.now().date()
    random.seed(today.toordinal())
    
    # Flatten glossary to pick a random term
    flat_glossary = []
    for category, terms in STRUCTURED_GLOSSARY.items():
        for term, desc in terms.items():
            flat_glossary.append((category, term, desc))
    
    daily_cat, daily_term, daily_desc = random.choice(flat_glossary)
    
    # Initialize session state for tracking learning progress
    if 'learned_words' not in st.session_state:
        st.session_state.learned_words = set()
    
    st.markdown("---")
    st.markdown(f"### {ui['word_of_day'][lang]} ({today.strftime('%b %d, %Y')})")
    with st.container(border=True):
        st.markdown(f"#### {daily_term}")
        cat_en, cat_zh = daily_cat.split(" / ")
        st.caption(f"Category: {cat_zh if lang == '中文' else cat_en}")
        st.info(daily_desc[lang])
        
        # Check if the user has marked it as learned today
        if daily_term not in st.session_state.learned_words:
            if st.button(ui["mark_learned"][lang], key="btn_learn_daily", type="primary"):
                st.session_state.learned_words.add(daily_term)
                st.balloons()
                st.rerun()
        else:
            st.success(ui["learned_success"][lang])
            
    st.markdown("---")
    st.markdown("### 📚 Browse the Full Dictionary")
    
    search_term = st.text_input("🔍 Search terms / 搜索名词", key="glossary_search").strip()
    
    for category, terms in STRUCTURED_GLOSSARY.items():
        # Extract localized category name
        cat_en, cat_zh = category.split(" / ")
        display_cat = cat_zh if lang == "中文" else cat_en
        
        # Filter terms in this category based on search
        matching_terms = {}
        for term, desc in terms.items():
            if not search_term or search_term.lower() in term.lower() or search_term.lower() in desc[lang].lower():
                matching_terms[term] = desc
                
        # If there are matches, display the category header and the terms
        if matching_terms:
            st.markdown(f"#### {display_cat}")
            for term, desc in matching_terms.items():
                with st.expander(f"**{term}**"):
                    st.write(desc[lang])
            st.markdown("<br>", unsafe_allow_html=True)
            
elif selected_page == ui["tab_career"][lang]:
    st.subheader(ui["tab_career"][lang])
    st.markdown("Explore emerging AI roles, required skills, and common interview questions to prepare for your next career move." if lang == "English" else "探索新兴的 AI 岗位、核心技能树以及常见的面试题，为你的下一次职业飞跃做好准备。")
    st.markdown("---")
    
    for role, data in CAREER_GUIDE.items():
        role_en, role_zh = role.split(" / ")
        display_role = role_zh if lang == "中文" else role_en
        
        with st.expander(f"**{display_role}**", expanded=False):
            st.info(data["desc"][lang])
            
            col_sk, col_iq = st.columns(2)
            with col_sk:
                st.markdown("**🛠️ Core Skills / 核心技能树**" if lang == "中文" else "**🛠️ Core Skills**")
                for skill in data["skills"][lang]:
                    st.markdown(f"- {skill}")
                    
            with col_iq:
                st.markdown("**❓ Mock Interview / 模拟面试题**" if lang == "中文" else "**❓ Mock Interview**")
                for q in data["interview_q"][lang]:
                    st.markdown(f"- {q}")
                    
elif selected_page == ui["tab_cases"][lang]:
    st.subheader(ui["tab_cases"][lang])
    st.markdown("Learn how AI is solving real-world business problems across different industries." if lang == "English" else "了解 AI 技术是如何在不同行业的真实业务场景中解决痛点并创造商业价值的。")
    st.markdown("---")
    
    for industry, cases in BUSINESS_CASES.items():
        ind_en, ind_zh = industry.split(" / ")
        display_ind = ind_zh if lang == "中文" else ind_en
        
        st.markdown(f"#### {display_ind}")
        
        for case in cases:
            with st.expander(f"**{case['title'][lang]}**", expanded=False):
                st.markdown("**🚨 Problem / 业务痛点:**" if lang == "English" else "**🚨 业务痛点:**")
                st.write(case['problem'][lang])
                st.markdown("**💡 AI Solution / AI 解决方案:**" if lang == "English" else "**💡 AI 解决方案:**")
                st.info(case['solution'][lang])
                st.markdown("**📈 Business Impact / 商业价值:**" if lang == "English" else "**📈 商业价值:**")
                st.success(case['impact'][lang])
        st.markdown("<br>", unsafe_allow_html=True)
    
