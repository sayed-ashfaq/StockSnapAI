import streamlit as st
import sys
import os

# Add modules to path - so that sys consider the modules as well
sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))


from modules.stock_analyzer import StockAnalyzer
from modules.document_chat import DocumentChat

st.set_page_config(
    page_title="AI Finance Copilot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
) # Setup the page or canvas you can say


def main():
    st.title("🤖 AI Finance Copilot")
    st.markdown("*Your AI-powered assistant for stock analysis and document insights*")

    # Sidebar for API keys and navigation
    with st.sidebar:
        st.header("🔑 API Configuration")
        st.markdown("*Enter your API keys to get started*")

        # OpenAI API Key
        openai_key = st.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="sk-...",
            help="Required for document embeddings and analysis"
        )
        if not openai_key:
            st.markdown("👆 [Get OpenAI API Key](https://platform.openai.com/api-keys)")
        else:
            os.environ["OPENAI_API_KEY"] = openai_key
            st.success("✅ OpenAI key configured")

        # Google AI API Key
        google_key = st.text_input(
            "Google AI API Key",
            type="password",
            placeholder="AI...",
            help="Required for Gemini model (document analysis)"
        )
        if not google_key:
            st.markdown("👆 [Get Google AI API Key](https://makersuite.google.com/app/apikey)")
        else:
            os.environ["GOOGLE_API_KEY"] = google_key
            st.success("✅ Google AI key configured")

        # Tavily API Key
        tavily_key = st.text_input(
            "Tavily Search API Key",
            type="password",
            placeholder="tvly-...",
            help="Required for real-time stock news search"
        )
        if not tavily_key:
            st.markdown("👆 [Get Tavily API Key](https://app.tavily.com/)")
        else:
            os.environ["TAVILY_API_KEY"] = tavily_key
            st.success("✅ Tavily key configured")

        # Check if all keys are provided
        all_keys_provided = bool(openai_key and google_key and tavily_key)

        if not all_keys_provided:
            st.warning("⚠️ Please provide all API keys to use the app")
            st.markdown("""
            **Why these APIs?**
            - **OpenAI**: Document embeddings & analysis
            - **Google AI**: Fast Gemini model for chat
            - **Tavily**: Real-time stock news search
            """)

        st.divider()

        # Navigation
        st.header("📱 Navigation")
        tab_selection = st.radio(
            "Select Module:",
            ["📈 Stock News & Sentiment", "📄 Document Chat & Analysis"],
            index=0,
            disabled=not all_keys_provided
        )

        if not all_keys_provided:
            st.info("🔒 Enter API keys above to unlock modules")

    # Main content area
    if all_keys_provided:
        if tab_selection == "📈 Stock News & Sentiment":
            stock_analyzer = StockAnalyzer()
            stock_analyzer.render()
        else:
            document_chat = DocumentChat()
            document_chat.render()
    else:
        # Show getting started guide when API keys are missing
        st.markdown("## 🚀 Welcome to AI Finance Copilot!")
        st.markdown("""
        This app helps traders and analysts with:

        ### 📈 Stock News & Sentiment Analysis
        - Add multiple stocks to your portfolio
        - Get real-time news analysis with AI sentiment scoring
        - Receive portfolio-level insights and individual stock summaries
        - Identify market themes, risks, and opportunities

        ### 📄 Document Chat & Analysis  
        - Upload financial documents (earnings reports, annual reports, etc.)
        - Get AI-powered summaries with red flag detection
        - Chat with documents using natural language
        - Export analysis and chat history

        ---

        ### 🔑 Getting Started

        **Step 1:** Get your API keys (all are free to start):

        1. **[OpenAI API Key](https://platform.openai.com/api-keys)** 
           - Sign up for OpenAI account
           - Go to API Keys section
           - Create new secret key
           - Free tier: $5 credit for new accounts

        2. **[Google AI API Key](https://makersuite.google.com/app/apikey)**
           - Sign in with Google account  
           - Go to "Get API key" 
           - Create API key for new project
           - Free tier: Generous usage limits

        3. **[Tavily Search API Key](https://app.tavily.com/)**
           - Create free account
           - Get API key from dashboard
           - Free tier: 1,000 searches/month

        **Step 2:** Enter your API keys in the sidebar ← 

        **Step 3:** Start analyzing stocks and documents!

        ---

        ### 💡 Pro Tips
        - All processing happens securely - keys are only stored during your session
        - Start with popular stocks like AAPL, TSLA, GOOGL for testing
        - Upload financial documents in PDF or TXT format
        - Free tiers are generous enough for regular use

        ### 📞 Need Help?
        - Check API provider documentation if you have issues
        - Ensure API keys are valid and have sufficient quota
        - Contact respective API providers for account-specific questions
        """)

        # Quick links section
        st.markdown("### 🔗 Quick Links")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            **OpenAI**
            - [API Keys](https://platform.openai.com/api-keys)
            - [Documentation](https://platform.openai.com/docs)
            - [Pricing](https://openai.com/pricing)
            """)

        with col2:
            st.markdown("""
            **Google AI**
            - [Get API Key](https://makersuite.google.com/app/apikey)
            - [Documentation](https://ai.google.dev/)
            - [Pricing](https://ai.google.dev/pricing)
            """)

        with col3:
            st.markdown("""
            **Tavily Search**
            - [Get API Key](https://app.tavily.com/)
            - [Documentation](https://docs.tavily.com/)
            - [Pricing](https://tavily.com/pricing)
            """)


if __name__ == "__main__":
    main()