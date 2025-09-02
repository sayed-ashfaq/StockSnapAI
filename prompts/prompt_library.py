from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from datetime import datetime

# PROMPT FOR NEWS SUMMARIZER

# Search for news about all stocks
STOCKANALYZER_PROMPT = [HumanMessage(content=f"""
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
                        "quick_summary": "2-3 line key bullet point summary that can help traders to analyze stock",
                        "key_news_category": "earnings/regulatory/product/general",
                        "price_impact": "BULLISH/NEUTRAL/BEARISH",
                        "source link": [source_links],
                        "published_date": [last_published_date],
                    }}
                ]
            }}

            Instructions:
            - Focus on the most recent and impactful news for each stock
            - Provide portfolio-level insights that consider correlations and sector trends
            - Keep individual stock summaries concise but informative
            - Identify common themes across the portfolio
            - Consider both individual stock performance and broader market implications
            - Everything should be in a way that is helpful to trader to analyze stocks
            """)]
## CENTRAL DICTIONARY TO REGISTER PROMPTS

# PROMPT_REGISTRY = {
#     "news_summarizer_prompt": document_summarize_prompt,
#     "contextualize_qa_prompt ": contextualize_prompt,
#     "context_history_qa_prompt": qa_context_prompt,
# }