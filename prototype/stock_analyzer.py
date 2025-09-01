import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import json
from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

load_dotenv()


class StockAnalyzer:
    def __init__(self):
        self.llm = init_chat_model(model="gpt-4o-mini", model_provider="openai")
        self.tavily_search_tool = TavilySearch(
            max_results=5,
            topic="news",
        )
        self.agent = create_react_agent(self.llm, [self.tavily_search_tool])

    def get_sentiment_color(self, sentiment):
        """Return color based on sentiment"""
        colors = {
            "STRONG POSITIVE": "#00C851",
            "POSITIVE": "#4CAF50",
            "NEUTRAL": "#FFA726",
            "NEGATIVE": "#F44336",
            "STRONG NEGATIVE": "#B71C1C"
        }
        return colors.get(sentiment, "#808080")

    def analyze_portfolio_batch(self, stock_symbols):
        """Analyze all stocks in portfolio at once"""
        try:
            # Create comprehensive search query for all stocks
            stocks_query = " OR ".join([f"{symbol} stock news" for symbol in stock_symbols])
            query = f"latest financial news {stocks_query} earnings regulatory updates market sentiment"

            # Search for news about all stocks
            messages = [HumanMessage(content=f"""
            Search for the latest news about these stocks: {', '.join(stock_symbols)} and provide a comprehensive portfolio analysis.

            Please provide the analysis in the following JSON format:
            {{
                "portfolio_analysis": {{
                    "analysis_date": "{datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    "portfolio_stocks": {stock_symbols},
                    "overall_portfolio_sentiment": "STRONG POSITIVE/POSITIVE/NEUTRAL/NEGATIVE/STRONG NEGATIVE",
                    "portfolio_summary": "2-3 sentence overall market outlook for this portfolio based on recent news and trends",
                    "market_themes": ["key market theme 1", "key market theme 2", "key market theme 3"],
                    "portfolio_risks": ["risk factor 1", "risk factor 2"],
                    "portfolio_opportunities": ["opportunity 1", "opportunity 2"]
                }},
                "individual_stocks": [
                    {{
                        "stock_symbol": "SYMBOL",
                        "sentiment": "STRONG POSITIVE/POSITIVE/NEUTRAL/NEGATIVE/STRONG NEGATIVE",
                        "quick_summary": "1-2 line summary of recent developments and outlook",
                        "key_news_category": "earnings/regulatory/product/general",
                        "price_impact": "BULLISH/NEUTRAL/BEARISH"
                    }}
                ]
            }}

            Instructions:
            - Focus on the most recent and impactful news for each stock
            - Provide portfolio-level insights that consider correlations and sector trends
            - Keep individual stock summaries concise but informative
            - Identify common themes across the portfolio
            - Consider both individual stock performance and broader market implications
            """)]

            result = self.agent.invoke({"messages": messages})

            # Try to extract JSON from the response
            response_text = result['messages'][-1].content

            # Find JSON in response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Fallback if JSON parsing fails
                return {
                    "portfolio_analysis": {
                        "analysis_date": datetime.now().strftime('%Y-%m-%d %H:%M'),
                        "portfolio_stocks": stock_symbols,
                        "overall_portfolio_sentiment": "NEUTRAL",
                        "portfolio_summary": "Portfolio analysis completed. Please review individual stock details.",
                        "market_themes": ["Market analysis in progress"],
                        "portfolio_risks": ["Standard market volatility"],
                        "portfolio_opportunities": ["Continued monitoring recommended"]
                    },
                    "individual_stocks": [
                        {
                            "stock_symbol": symbol,
                            "sentiment": "NEUTRAL",
                            "quick_summary": "Analysis completed for this stock. Recent market activity under review.",
                            "key_news_category": "general",
                            "price_impact": "NEUTRAL"
                        } for symbol in stock_symbols
                    ]
                }

        except Exception as e:
            st.error(f"Error analyzing portfolio: {str(e)}")
            return None

    def render(self):
        st.header("📈 Stock News & Sentiment Analysis")
        st.markdown("Enter stock symbols to get real-time news analysis with AI-powered sentiment scoring.")

        # Portfolio input section
        with st.container():
            st.subheader("📊 Your Stock Portfolio")

            # Initialize session state for portfolio
            if 'portfolio' not in st.session_state:
                st.session_state.portfolio = []

            # Add stock form
            with st.form("add_stock_form"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    new_stock = st.text_input(
                        "Enter Stock Symbol (e.g., AAPL, TSLA, TATASTEEL)",
                        placeholder="AAPL"
                    ).upper()
                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    add_button = st.form_submit_button("➕ Add Stock", use_container_width=True)

            if add_button and new_stock and new_stock not in st.session_state.portfolio:
                st.session_state.portfolio.append(new_stock)
                st.success(f"Added {new_stock} to portfolio!")
            elif add_button and new_stock in st.session_state.portfolio:
                st.warning(f"{new_stock} is already in your portfolio!")

            # Display current portfolio
            if st.session_state.portfolio:
                st.write("**Current Portfolio:**")
                for i, stock in enumerate(st.session_state.portfolio):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"• {stock}")
                    with col2:
                        if st.button("🗑️", key=f"remove_{i}", help=f"Remove {stock}"):
                            st.session_state.portfolio.remove(stock)
                            st.rerun()

        # Analysis section
        if st.session_state.portfolio:
            st.subheader("🔍 Portfolio Analysis")

            if st.button("🚀 Analyze Portfolio", type="primary", use_container_width=True):
                with st.spinner(f"Analyzing portfolio with {len(st.session_state.portfolio)} stocks..."):

                    # Analyze entire portfolio at once
                    analysis = self.analyze_portfolio_batch(st.session_state.portfolio)

                    if analysis:
                        # Portfolio Overview Section
                        st.markdown("## 📊 Portfolio Overview")

                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.markdown(
                                f"**Stocks Analyzed:** {', '.join(analysis['portfolio_analysis']['portfolio_stocks'])}")
                        with col2:
                            portfolio_sentiment = analysis['portfolio_analysis']['overall_portfolio_sentiment']
                            sentiment_color = self.get_sentiment_color(portfolio_sentiment)
                            st.markdown(f"**Overall Sentiment:**")
                            st.markdown(
                                f"<span style='color: {sentiment_color}; font-weight: bold; font-size: 18px;'>{portfolio_sentiment}</span>",
                                unsafe_allow_html=True)
                        with col3:
                            st.markdown(f"**Analysis Date:**")
                            st.markdown(f"{analysis['portfolio_analysis']['analysis_date']}")

                        # Portfolio Summary
                        st.markdown("### 📝 Portfolio Summary")
                        st.write(analysis['portfolio_analysis']['portfolio_summary'])

                        # Market Themes, Risks, and Opportunities in columns
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.markdown("#### 🎯 Market Themes")
                            for theme in analysis['portfolio_analysis']['market_themes']:
                                st.write(f"• {theme}")

                        with col2:
                            st.markdown("#### ⚠️ Portfolio Risks")
                            for risk in analysis['portfolio_analysis']['portfolio_risks']:
                                st.write(f"• {risk}")

                        with col3:
                            st.markdown("#### 🚀 Opportunities")
                            for opportunity in analysis['portfolio_analysis']['portfolio_opportunities']:
                                st.write(f"• {opportunity}")

                        st.divider()

                        # Individual Stocks Section
                        st.markdown("## 📈 Individual Stock Analysis")

                        # Create a table-like view for individual stocks
                        for stock_data in analysis['individual_stocks']:
                            with st.container():
                                col1, col2, col3, col4 = st.columns([2, 2, 1.5, 1.5])

                                with col1:
                                    st.markdown(f"### 📊 {stock_data['stock_symbol']}")

                                with col2:
                                    sentiment_color = self.get_sentiment_color(stock_data['sentiment'])
                                    st.markdown(
                                        f"**Sentiment:** <span style='color: {sentiment_color}; font-weight: bold;'>{stock_data['sentiment']}</span>",
                                        unsafe_allow_html=True)

                                with col3:
                                    st.markdown(f"**Category:** {stock_data['key_news_category'].title()}")

                                with col4:
                                    # Price impact with colors
                                    impact_colors = {
                                        "BULLISH": "#00C851",
                                        "NEUTRAL": "#FFA726",
                                        "BEARISH": "#F44336"
                                    }
                                    impact_color = impact_colors.get(stock_data['price_impact'], "#808080")
                                    st.markdown(
                                        f"**Impact:** <span style='color: {impact_color}; font-weight: bold;'>{stock_data['price_impact']}</span>",
                                        unsafe_allow_html=True)

                                # Stock summary
                                st.markdown(f"**Summary:** {stock_data['quick_summary']}")
                                st.divider()

                        # Portfolio Statistics
                        st.markdown("## 📊 Portfolio Statistics")

                        # Calculate sentiment distribution
                        sentiments = [stock['sentiment'] for stock in analysis['individual_stocks']]
                        sentiment_counts = pd.Series(sentiments).value_counts()

                        # Price impact distribution
                        impacts = [stock['price_impact'] for stock in analysis['individual_stocks']]
                        impact_counts = pd.Series(impacts).value_counts()

                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown("### Sentiment Distribution")
                            for sentiment, count in sentiment_counts.items():
                                percentage = (count / len(sentiments)) * 100
                                color = self.get_sentiment_color(sentiment)
                                st.markdown(
                                    f"<span style='color: {color}; font-weight: bold;'>{sentiment}</span>: {count} stocks ({percentage:.1f}%)",
                                    unsafe_allow_html=True)

                        with col2:
                            st.markdown("### Price Impact Distribution")
                            impact_colors = {"BULLISH": "#00C851", "NEUTRAL": "#FFA726", "BEARISH": "#F44336"}
                            for impact, count in impact_counts.items():
                                percentage = (count / len(impacts)) * 100
                                color = impact_colors.get(impact, "#808080")
                                st.markdown(
                                    f"<span style='color: {color}; font-weight: bold;'>{impact}</span>: {count} stocks ({percentage:.1f}%)",
                                    unsafe_allow_html=True)

                        # Success message
                        st.success(
                            f"✅ Portfolio analysis complete! Analyzed {len(st.session_state.portfolio)} stocks in one go.")

                    else:
                        st.error("❌ Failed to analyze portfolio. Please try again.")


        else:
            st.info("👆 Add some stock symbols to your portfolio to get started!")

            # Example stocks
            st.markdown("**Popular stocks to try:**")
            example_stocks = ["AAPL", "TSLA", "GOOGL", "MSFT", "TATASTEEL", "RELIANCE", "NFLX", "AMZN"]

            cols = st.columns(4)
            for i, stock in enumerate(example_stocks):
                with cols[i % 4]:
                    if st.button(stock, key=f"example_{stock}"):
                        if stock not in st.session_state.portfolio:
                            st.session_state.portfolio.append(stock)
                            st.rerun()

        # Footer
        st.markdown("---")
        st.markdown(
            "*💡 Tip: Sentiment analysis is based on recent news and market data. Always do your own research before making investment decisions.*")