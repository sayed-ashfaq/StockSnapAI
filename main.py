import streamlit as st
import sys
import os

# Add modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from prototype.stock_analyzer import StockAnalyzer
from prototype.document_chat import DocumentChat

st.set_page_config(
    page_title="AI Finance Copilot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    st.title("🤖 AI Finance Copilot")
    st.markdown("*Your AI-powered assistant for stock analysis and document insights*")

    # Sidebar for navigation
    with st.sidebar:
        st.header("Navigation")
        tab_selection = st.radio(
            "Select Module:",
            ["📈 Stock News & Sentiment", "📄 Document Chat & Analysis"],
            index=0
        )

    # Main content area
    if tab_selection == "📈 Stock News & Sentiment":
        stock_analyzer = StockAnalyzer()
        stock_analyzer.render()
    else:
        document_chat = DocumentChat()
        document_chat.render()


if __name__ == "__main__":
    main()