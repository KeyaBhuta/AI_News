# AI News Intelligence Dashboard 📰✨

This is a powerful, interactive web application built with Streamlit and powered by the Google Gemini API. It serves as an intelligent news dashboard that allows users to fetch, read, summarize, and analyze news articles from around the world in real-time.

The dashboard provides multiple AI-powered tools to dissect any article, including summarization, sentiment analysis, key entity extraction, and a contextual Q&A feature.


<img width="1919" height="912" alt="image" src="https://github.com/user-attachments/assets/d8981c75-5c3a-497d-9ab3-cd2e077c2e76" />


---

## 📋 Table of Contents

- [Key Features](#-key-features)
- [How It Works](#-how-it-works)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Future Improvements](#-future-improvements)
- [License](#-license)
- [Acknowledgments](#-acknowledgments)

---

## ✨ Key Features

-   **Dynamic News Feed:** Fetches the latest news from Google News RSS based on selected countries, categories, or custom search queries.
-   **Advanced Article Scraping:** Uses Selenium to bypass simple anti-scraping measures and extract the full text content from article URLs.
-   **Multi-Faceted AI Analysis (via Gemini Pro):**
    -   **Summarization:** Generates concise summaries in either bullet-point or paragraph form.
    -   **Sentiment Analysis:** Classifies article sentiment as `Positive`, `Negative`, or `Neutral` with a justification.
    -   **Key Information Extraction:** Identifies and lists key people and organizations mentioned in the text.
    -   **Contextual Q&A:** Allows you to ask specific questions about an article and get answers based *only* on the provided text.
-   **Analyze Any URL:** A dedicated feature to scrape and analyze any news article from a URL you provide.
-   **General AI Chatbot:** Includes a separate, persistent chatbot for general-purpose questions powered by Gemini.
-   **Interactive & Responsive UI:** Built with Streamlit for a clean, fast, and user-friendly experience.

---

## ⚙️ How It Works

1.  **News Fetching:** The app first pings the Google News RSS feed using the `requests` library to get a list of recent articles based on the user's selection.
2.  **Article Scraping:** When a user requests an AI analysis (e.g., "Summarize"), the app uses `Selenium` and `webdriver-manager` to launch a headless Chrome browser instance. It navigates to the article's URL and extracts the full body text. This is more robust than simple HTTP requests.
3.  **AI Interaction:** The extracted text is then packaged into a carefully crafted prompt and sent to the Google Gemini API. The prompt template varies depending on the user's requested action (summarize, analyze sentiment, etc.).
4.  **Stateful UI:** The entire interface is built with `Streamlit`. It cleverly uses `st.session_state` to keep track of user inputs, scraped text, and AI-generated responses, providing a smooth, interactive experience without constant page reloads for every action.

---

## 🛠️ Tech Stack

-   **Language:** Python 3.9+
-   **Web Framework:** [Streamlit](https://streamlit.io/)
-   **LLM API:** [Google Gemini API](https://ai.google.dev/) (`google-generativeai`)
-   **Web Scraping:**
    -   [Selenium](https://www.selenium.dev/) (for dynamic page content)
    -   [Requests](https://requests.readthedocs.io/en/latest/) (for RSS feeds)
    -   [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) (for parsing XML)
-   **Browser Automation:** [webdriver-manager](https://github.com/SergeyPirogov/webdriver_manager) (to automatically manage browser drivers for Selenium)

---

## 🚀 Getting Started

Follow these instructions to get a copy of the project up and running on your local machine for development and testing.

### Prerequisites

-   **Python 3.9 or higher.**
-   **Google Chrome** installed on your system (for Selenium to control).
-   **A Google Gemini API Key:**
    -   Get your key from [Google AI Studio](https://ai.google.dev/).

### Installation

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/your-username/gemini-news-dashboard.git
    cd gemini-news-dashboard
    ```

2.  **Create and activate a virtual environment (recommended):**
    -   **macOS / Linux:**
        ```sh
        python3 -m venv venv
        source venv/bin/activate
        ```
    -   **Windows:**
        ```sh
        python -m venv venv
        .\venv\Scripts\activate
        ```

3.  **Install the required dependencies:**
    The project uses a `requirements.txt` file to manage its dependencies.
    ```sh
    pip install -r requirements.txt
    ```

4.  **Set up your environment variables:**
    Create a file named `.env` in the root directory of the project. Add your Google Gemini API key to this file.

    Your `.env` file should contain:
    ```
    GOOGLE_API_KEY="YOUR_GEMINI_API_KEY_HERE"
    ```
    *This project is configured to use `python-dotenv` locally, which will automatically load this key. The provided `.gitignore` file will prevent this file from being uploaded to GitHub.*

---

## 🖥️ Usage

Once the installation is complete, you can run the Streamlit application with a single command:

```sh
streamlit run app.py
