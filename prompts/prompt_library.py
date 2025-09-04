from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from datetime import datetime

# PROMPT FOR NEWS SUMMARIZER

# Search for news about all stocks
PORTFOLIO_ANALYSER_PROMPT = [HumanMessage(content="""
            Search for the latest news about these stocks: {portfolio} and provide a comprehensive portfolio analysis.

            Please provide the analysis in the following JSON format:
            {{
                "portfolio_analysis": {{
                    "analysis_date": "{current_date}",
                    "portfolio_stocks": {portfolio},
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

# RAG prompt with chat history support

RAG_PROMPT = ChatPromptTemplate.from_messages([
            ("system", """You are an AI assistant specialized in analyzing financial and business documents. 
            Use the provided context to answer questions accurately and provide insights.

            Guidelines:
            - Answer based primarily on the provided context
            - Use conversation history for continuity
            - If information is not in the context, clearly state this
            - Provide specific citations when possible
            - Highlight important financial metrics, trends, and red flags
            - Be concise but comprehensive
            - Focus on factual information from the documents
            
            Conversation History:
            {chat_history}

            Context: {context}"""),
            ("human", "{question}")
        ])

from langchain_core.prompts import ChatPromptTemplate



SUMMARY_PROMPT= ChatPromptTemplate.from_messages([
            ("system", """You are an expert financial analyst. Create a comprehensive summary of the provided document.

            Structure your summary with these sections:
            1. **Document Type & Overview**: Identify the document type and main purpose
            2. **Key Financial Highlights**: Important metrics, performance indicators
            3. **Key Points**: Main findings, decisions, or statements
            4. **Red Flags & Concerns**: Potential risks, warnings, or concerning trends
            5. **Future Outlook**: Forward-looking statements or guidance

            Be specific and include actual numbers/percentages when available.
            Focus on actionable insights and important details."""),
            ("human", "Summarize this document:\n\n{content}")
        ])

## CENTRAL DICTIONARY TO REGISTER PROMPTS

# PROMPT_REGISTRY = {
#     "news_summarizer_prompt": document_summarize_prompt,
#     "contextualize_qa_prompt ": contextualize_prompt,
#     "context_history_qa_prompt": qa_context_prompt,
# }