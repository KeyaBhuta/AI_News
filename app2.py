import streamlit as st
import google.generativeai as genai
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from email.utils import parsedate_to_datetime

# --- SELENIUM IMPORTS ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIG ---
try:
    # Best for deployed apps on Streamlit Community Cloud
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except (FileNotFoundError, KeyError):
    # Fallback for local development
    GOOGLE_API_KEY = "AIzaSyCNSmzxNkJrIwygDccAQdgFD6PhXzfCsIE" # Replace with your key if running locally

genai.configure(api_key=GOOGLE_API_KEY)

# --- AI PROMPT TEMPLATES ---
PROMPT_TEMPLATES = {
    "summary": "Please provide a clear and concise summary of the following news article in {style}:\n\n---\n\n{text}",
    "sentiment": "Analyze the sentiment of the following news article. Classify it as Positive, Negative, or Neutral. Then, provide a brief one-sentence explanation for your classification.\n\nArticle:\n---\n{text}",
    "entities": "From the article below, extract the following information. If none are found, state \"None found\".\n1. **Key People Mentioned:**\n2. **Key Organizations/Companies Mentioned:**\n3. **Main Topic:**\n\nArticle:\n---\n{text}",
    "qa": """
        You are a helpful Q&A assistant. Your task is to answer the user's question based *only* on the provided article text.
        - If the answer is found in the text, provide a direct and concise answer.
        - If the answer is not found in the text, you MUST state: 'The answer to that question could not be found in the provided article text.'
        - Do not use any external knowledge or make assumptions.

        Here is the article text:
        ---
        {text}
        ---
        Here is the user's question: {question}
    """
}

# --- DATA DICTIONARIES & MODEL LOADING ---
COUNTRIES = {"United States": "US", "United Kingdom": "GB", "India": "IN", "Canada": "CA", "Australia": "AU"}
CATEGORIES = ["Top Stories", "World", "U.S.", "Business", "Technology", "Entertainment", "Sports", "Science", "Health"]
def get_gemini_model():
    model_names = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"]
    for model_name in model_names:
        try:
            return genai.GenerativeModel(
                model_name=model_name,
                safety_settings={'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE'}
            )
        except Exception: continue
    return None
if 'model' not in st.session_state: st.session_state.model = get_gemini_model()
model = st.session_state.model

# --- WEB SCRAPING & DATA FETCHING ---
@st.cache_data(ttl=3600)
def get_article_text(url):
    try:
        chrome_options = Options();
        chrome_options.add_argument("--headless"); chrome_options.add_argument("--disable-gpu"); chrome_options.add_argument("window-size=1920,1080"); chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
        service = Service(ChromeDriverManager().install()); driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url); wait = WebDriverWait(driver, 10)
        try:
            time.sleep(2)
            accept_button = driver.find_element(By.XPATH, "//*[self::button or self::a or @role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'consent')]")
            accept_button.click(); time.sleep(1)
        except Exception: pass
        body = wait.until(EC.presence_of_element_located((By.TAG_NAME, "body"))); article_text = body.text; driver.quit()
        if not article_text or len(article_text) < 250: return "Extracted text was too short or empty. The page may have a paywall or advanced anti-scraping protection."
        return article_text
    except Exception as e:
        try: driver.quit()
        except NameError: pass
        return f"Scraping failed with Selenium: {str(e)[:150]}"

@st.cache_data(ttl=600)
def fetch_news(query='Top Stories', country='US'):
    search_query = query;
    if query == "Top Stories": search_query = ""
    url = f"https://news.google.com/rss/search?q=when:24h+{search_query}&hl=en-{country}&gl={country}&ceid={country}:en"
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15); res.raise_for_status()
        soup = BeautifulSoup(res.content, 'xml'); items = soup.find_all('item'); articles = []
        for item in items:
            pub_date_str = item.find('pubDate').text if item.find('pubDate') else None
            article = {'title': item.find('title').text, 'link': item.find('link').text, 'source': item.find('source').text if item.find('source') else 'Unknown', 'published_date': parsedate_to_datetime(pub_date_str) if pub_date_str else datetime.now()}
            articles.append(article)
        return articles
    except Exception as e:
        st.error(f"Failed to fetch Google News RSS: {str(e)}"); return []

# --- AI FUNCTION ---
def call_gemini_ai(prompt):
    if not model: return "Gemini model not available."
    try:
        response = model.generate_content(prompt, request_options={'timeout': 120})
        return response.text.strip()
    except Exception as e:
        error_msg = str(e);
        if "429" in error_msg or "quota" in error_msg.lower(): return "**API Quota Exceeded!** Please wait a minute."
        else: return f"AI call failed: {error_msg[:200]}..."

# --- STREAMLIT UI ---
st.set_page_config(layout="wide", page_title="Gemini News Dashboard")
st.markdown("""<style>.elegant-title{text-align:center;font-family:'Garamond','Georgia',serif;font-size:3rem;font-weight:300;letter-spacing:2px;padding-bottom:20px;}</style><h1 class="elegant-title">AI News Intelligence Dashboard</h1>""", unsafe_allow_html=True)
if not model: st.error("❌ Failed to load Gemini model. Check your GOOGLE_API_KEY."); st.stop()

col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.subheader("⚙️ Controls")
    selected_country_name = st.selectbox("**Select a Country:**", options=list(COUNTRIES.keys()))
    selected_country_code = COUNTRIES[selected_country_name]
    user_search_query = st.text_input("**(Optional) Or search for any topic:**", placeholder="e.g., 'AI safety regulations'")
    selected_category = st.selectbox("**Select a Category:**", options=CATEGORIES, disabled=(user_search_query != ""))
    st.markdown("**Article Analysis Options**")
    summary_style = st.radio("Choose summary style:", ["3 concise bullet points", "A single, informative paragraph"], horizontal=True)
    if user_search_query: topic_to_fetch = user_search_query
    else: topic_to_fetch = selected_category
    
    st.markdown("---")
    
    # --- THIS ENTIRE CHATBOT BLOCK IS NEW AND IMPROVED ---
    st.subheader("🤖 General AI Chatbot")
    st.caption("Ask anything! This chat is separate from the article analysis.")

    # Add the "New Chat" button
    if st.button("✨ New Chat", use_container_width=True):
        st.session_state.messages = []
        if 'chat_session' in st.session_state:
            del st.session_state.chat_session
        st.rerun()

    # Initialize chat history and the chat session object if they don't exist
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_session" not in st.session_state:
        st.session_state.chat_session = model.start_chat(history=[])

    # Display past messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # The chat input widget
    if prompt := st.chat_input("What would you like to know?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.chat_session.send_message(prompt)
                response_text = response.text
                st.markdown(response_text)
        
        st.session_state.messages.append({"role": "assistant", "content": response_text})

with col2:
    st.subheader(f"⚡ Latest News for: '{topic_to_fetch}' in {selected_country_name}")
    with st.spinner(f"Fetching news..."):
        articles = fetch_news(query=topic_to_fetch, country=selected_country_code)
    if not articles:
        st.warning("Couldn't find any news. Please try another search or category.")
    else:
        num_articles = st.slider("How many articles to display?", 1, len(articles), min(10, len(articles)))
        st.markdown("---")
        for i, article in enumerate(articles[:num_articles]):
            with st.container(border=True):
                st.subheader(f"{i+1}. {article['title']}")
                c1,c2 = st.columns([3,1]); c1.write(f"**Source:** {article['source']}"); c2.write(f"**Published:** {article['published_date'].strftime('%d %b %Y')}")
                
                action_cols = st.columns([1, 1, 1, 1, 1]); article_link = article['link']
                with action_cols[0]:
                    if st.button("Summarize", key=f"sum_{article_link}", use_container_width=True):
                        with st.spinner("🧠 Summarizing..."):
                            scraped_text=get_article_text(article_link)
                            if "Could not" in scraped_text or "Scraping failed" in scraped_text or "too short" in scraped_text or not scraped_text.strip():
                                st.session_state[f"summary_{article_link}"]=f"⚠️ **Scraping Error:** {scraped_text}"
                            else:
                                prompt=PROMPT_TEMPLATES["summary"].format(style=summary_style,text=scraped_text); st.session_state[f"summary_{article_link}"]=call_gemini_ai(prompt)
                with action_cols[1]:
                    if st.button("Sentiment", key=f"sen_{article_link}", use_container_width=True):
                        with st.spinner("⚖️ Analyzing..."):
                            scraped_text=get_article_text(article_link)
                            if "Could not" in scraped_text or "Scraping failed" in scraped_text or "too short" in scraped_text or not scraped_text.strip():
                                st.session_state[f"sentiment_{article_link}"]=f"⚠️ **Scraping Error:** {scraped_text}"
                            else:
                                prompt=PROMPT_TEMPLATES["sentiment"].format(text=scraped_text); st.session_state[f"sentiment_{article_link}"]=call_gemini_ai(prompt)
                with action_cols[2]:
                    if st.button("Key Info", key=f"ent_{article_link}", use_container_width=True):
                        with st.spinner("🔎 Extracting..."):
                            scraped_text=get_article_text(article_link)
                            if "Could not" in scraped_text or "Scraping failed" in scraped_text or "too short" in scraped_text or not scraped_text.strip():
                                st.session_state[f"entities_{article_link}"]=f"⚠️ **Scraping Error:** {scraped_text}"
                            else:
                                prompt=PROMPT_TEMPLATES["entities"].format(text=scraped_text); st.session_state[f"entities_{article_link}"]=call_gemini_ai(prompt)
                with action_cols[3]:
                    if st.button("Ask ❔", key=f"ask_{article_link}", use_container_width=True):
                        st.session_state.qa_active_article=article_link; st.session_state.pop(f"qa_question_{article_link}", None); st.session_state.pop(f"qa_answer_{article_link}", None)
                with action_cols[4]:
                    st.link_button("Read Full ↗️", article_link, use_container_width=True)

                if st.session_state.get('qa_active_article')==article_link:
                    user_question=st.text_input("Ask a question about this article:", key=f"qa_input_{article_link}", placeholder="e.g., 'What was the final verdict?'")
                    if user_question:
                        st.session_state[f"qa_question_{article_link}"]=user_question
                        with st.spinner("🤔 Finding the answer in the text..."):
                            scraped_text=get_article_text(article_link)
                            if "Could not" in scraped_text or "Scraping failed" in scraped_text or "too short" in scraped_text or not scraped_text.strip():
                                st.session_state[f"qa_answer_{article_link}"]=f"⚠️ **Scraping Error:** {scraped_text}"
                            else:
                                prompt=PROMPT_TEMPLATES["qa"].format(text=scraped_text,question=user_question); st.session_state[f"qa_answer_{article_link}"]=call_gemini_ai(prompt)
                        st.session_state.qa_active_article=None; st.rerun()

                answer_key=f"qa_answer_{article_link}"; question_key=f"qa_question_{article_link}"
                if f"summary_{article_link}" in st.session_state: st.expander("🤖 **AI Summary**",expanded=True).info(st.session_state[f"summary_{article_link}"])
                if f"sentiment_{article_link}" in st.session_state: st.expander("⚖️ **Sentiment Analysis**",expanded=True).success(st.session_state[f"sentiment_{article_link}"])
                if f"entities_{article_link}" in st.session_state: st.expander("🔎 **Key Information**",expanded=True).warning(st.session_state[f"entities_{article_link}"])
                if answer_key in st.session_state:
                     exp=st.expander("💬 **Question & Answer**",expanded=True); exp.markdown(f"**Your Question:** {st.session_state[question_key]}"); exp.markdown("**Gemini's Answer:**"); exp.info(st.session_state[answer_key])