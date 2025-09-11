
import sys
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnablePassthrough
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from prompts.prompt_library import STOCKANALYZER_PROMPT
from utils.model_loader import ModelLoader
from utils.tool_loader import TavilySearchTool
from src.portfolio_summarizer.schemas import PortfolioAnalysis

from exceptions.custom_exception import PortfolioAnalyzerError
from logger import GLOBAL_LOGGER as log

from dotenv import load_dotenv

load_dotenv()


class StockAnalyzer:
    def __init__(self, session_id: Optional[str] = None):
        try:
            self.session_id = session_id or str(uuid.uuid4())

            # Initialize model loader
            self.loader = ModelLoader()
            self.llm = self.loader.load_llm()

            # Load tavily search tool
            self.tavily_search = TavilySearchTool()
            self.search_tool = self.tavily_search.load_tavily_tool()

            # Prepare parsers
            self.parser = JsonOutputParser(pydantic_object=PortfolioAnalysis)
            # self.fixing_parser = PydanticOutputParser.from_llm(parser=self.parser, llm=self.llm)

            # Bring prompt
            self.prompt = STOCKANALYZER_PROMPT

            # Create a memory checkpointer for conversation persistence
            self.memory = MemorySaver()

            # Create agent with memory
            self.agent_executor = create_react_agent(
                model=self.llm,
                tools=[self.search_tool],
                checkpointer=self.memory
            )

            # Thread config for memory management
            self.thread_config = {"configurable": {"thread_id": self.session_id}}

            # Analysis cache for recent results
            self.analysis_cache = {}
            self.cache_ttl_minutes = 15

            # Initialize analysis chain
            self._setup_analysis_chain()

            log.info(f"StockAnalyzer initialized successfully with session: {self.session_id}")

        except Exception as e:
            log.error(f"Error initializing StockAnalyzer")
            raise PortfolioAnalyzerError(f"Error in StockAnalyzer initialization: {e}", sys)

    def _setup_analysis_chain(self):
        """Setup the analysis chain with proper error handling and memory"""
        try:
            # Create a structured analysis chain
            self.analysis_chain = (
                    RunnablePassthrough.assign(
                        formatted_prompt=lambda x: self._format_portfolio_prompt(x)
                    )
                    | self._execute_analysis
                    | self._parse_response
            )

            log.info("Analysis chain setup completed")

        except Exception as e:
            log.error(f"Error setting up analysis chain")
            raise PortfolioAnalyzerError(f"Failed to setup analysis chain: {e}", sys)

    def _format_portfolio_prompt(self, input_data: Dict[str, Any]) -> str:
        """Format the portfolio analysis prompt"""
        symbols = input_data.get('portfolio', [])
        request_time = input_data.get('request_time', datetime.now().isoformat())

        return f"""
        Analyze the following stock portfolio: {', '.join(symbols)}
        Analysis requested at: {request_time}

        Please provide comprehensive analysis in the specified JSON format.
        Focus on recent news, market sentiment, and portfolio-level insights.
        """

    def _execute_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the analysis using the agent"""
        try:
            formatted_prompt = input_data.get('formatted_prompt', '')

            # Create message for agent
            messages = [HumanMessage(content=formatted_prompt)]

            # Invoke agent with memory
            result = self.agent_executor.invoke(
                {"messages": messages},
                config=self.thread_config
            )

            return {
                "agent_response": result,
                "original_input": input_data
            }

        except Exception as e:
            log.error(f"Error executing analysis: {e}")
            raise PortfolioAnalyzerError("Analysis execution failed", sys)

    def _parse_response(self, agent_output: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and structure the agent response"""
        try:
            # Extract response content
            agent_result = agent_output.get('agent_response', {})
            messages = agent_result.get('messages', [])

            if not messages:
                raise ValueError("No response from agent")

            # Get the last AI message
            last_message = messages[-1]
            response_text = last_message.content if hasattr(last_message, 'content') else str(last_message)

            # Try to extract JSON from response
            parsed_json = self._extract_json_from_response(response_text)

            if parsed_json:
                return parsed_json
            else:
                # Use fixing parser as fallback
                return self.parser.parse(response_text)

        except Exception as e:
            log.warning(f"Error parsing response, using fallback: {e}")
            original_input = agent_output.get('original_input', {})
            symbols = original_input.get('portfolio', [])
            return self._fallback_analysis(symbols)

    def _extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from agent response"""
        try:
            # Find JSON boundaries
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)

            return None

        except json.JSONDecodeError:
            return None

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached analysis is still valid"""
        if cache_key not in self.analysis_cache:
            return False

        cached_time = self.analysis_cache[cache_key].get('timestamp')
        if not cached_time:
            return False

        time_diff = (datetime.now() - cached_time).total_seconds() / 60
        return time_diff < self.cache_ttl_minutes

    def _get_cache_key(self, symbols: List[str]) -> str:
        """Generate cache key for symbol list"""
        sorted_symbols = sorted(symbols)
        return f"portfolio_{'_'.join(sorted_symbols)}"

    def get_sentiment_color(self, sentiment: str) -> str:
        """Return color based on sentiment"""
        colors = {
            "STRONG POSITIVE": "#00C851",
            "POSITIVE": "#4CAF50",
            "NEUTRAL": "#FFA726",
            "NEGATIVE": "#F44336",
            "STRONG NEGATIVE": "#B71C1C"
        }
        return colors.get(sentiment, "#808080")

    def _validate_symbols(self, symbols: List[str]) -> List[str]:
        """Validate and clean stock symbols"""
        if not symbols:
            raise ValueError("No stock symbols provided")

        cleaned = [s.strip().upper() for s in symbols if isinstance(s, str) and s.strip()]
        unique_symbols = list(dict.fromkeys(cleaned))  # Remove duplicates while preserving order

        if not unique_symbols:
            raise ValueError("No valid stock symbols found")

        if len(unique_symbols) > 50:  # Reasonable limit for scalability
            log.warning(f"Large portfolio detected: {len(unique_symbols)} symbols")

        return unique_symbols

    def _fallback_analysis(self, symbols: List[str]) -> Dict[str, Any]:
        """Safe fallback if the LLM/chain fails"""
        log.warning("Using fallback analysis due to processing error")

        return {
            "portfolio_analysis": {
                "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "portfolio_stocks": symbols,
                "overall_portfolio_sentiment": "NEUTRAL",
                "portfolio_summary": "Analysis temporarily unavailable. Portfolio monitoring continues.",
                "market_themes": ["Market analysis in progress"],
                "portfolio_risks": ["Standard market volatility", "Analysis service temporarily limited"],
                "portfolio_opportunities": ["Regular monitoring recommended", "Manual research suggested"]
            },
            "individual_stocks": [
                {
                    "stock_symbol": symbol,
                    "sentiment": "NEUTRAL",
                    "quick_summary": f"Analysis for {symbol} temporarily unavailable. Please retry later.",
                    "key_news_category": "general",
                    "price_impact": "NEUTRAL"
                }
                for symbol in symbols
            ],
            "analysis_status": "FALLBACK",
            "session_id": self.session_id
        }

    def analyze_portfolio_batch(self, stock_symbols: List[str], use_cache: bool = True) -> Dict[str, Any]:
        """
        Analyze portfolio with enhanced error handling and caching

        Args:
            stock_symbols: List of stock symbols to analyze
            use_cache: Whether to use cached results if available

        Returns:
            Dict containing portfolio analysis results
        """
        try:
            # Validate input symbols
            validated_symbols = self._validate_symbols(stock_symbols)
            log.info(f"Analyzing portfolio: {validated_symbols}")

            # Check cache if enabled
            cache_key = self._get_cache_key(validated_symbols)
            if use_cache and self._is_cache_valid(cache_key):
                log.info(f"Returning cached analysis for {cache_key}")
                return self.analysis_cache[cache_key]['data']

            # Prepare analysis payload
            invoke_payload = {
                "portfolio": validated_symbols,
                "request_time": datetime.now().isoformat(),
                "session_id": self.session_id
            }

            # Execute analysis chain
            log.info("Starting portfolio analysis chain execution")
            response = self.analysis_chain.invoke(invoke_payload)

            # Add metadata to response
            response.update({
                "analysis_status": "SUCCESS",
                "session_id": self.session_id,
                "cache_key": cache_key
            })

            # Cache the result
            if use_cache:
                self.analysis_cache[cache_key] = {
                    'data': response,
                    'timestamp': datetime.now()
                }
                log.info(f"Analysis cached with key: {cache_key}")

            log.info(f"Portfolio analysis completed successfully for {len(validated_symbols)} symbols")
            return response

        except ValueError as ve:
            log.error(f"Validation error in portfolio analysis: {ve}")
            raise PortfolioAnalyzerError(f"Input validation failed: {ve}", sys)

        except Exception as e:
            log.error(f"Error in portfolio analysis: {e}")
            # Return fallback analysis instead of failing completely
            try:
                validated_symbols = self._validate_symbols(stock_symbols)
                return self._fallback_analysis(validated_symbols)
            except:
                return self._fallback_analysis([])

    def get_analysis_history(self) -> List[Dict[str, Any]]:
        """Get analysis history for current session"""
        try:
            # This would typically fetch from a database
            # For now, return recent cache entries
            history = []
            for cache_key, cache_data in self.analysis_cache.items():
                history.append({
                    "cache_key": cache_key,
                    "timestamp": cache_data['timestamp'].isoformat(),
                    "symbols_count": len(cache_data['data'].get('portfolio_analysis', {}).get('portfolio_stocks', [])),
                    "sentiment": cache_data['data'].get('portfolio_analysis', {}).get('overall_portfolio_sentiment',
                                                                                      'UNKNOWN')
                })

            # Sort by timestamp, most recent first
            history.sort(key=lambda x: x['timestamp'], reverse=True)
            return history

        except Exception as e:
            log.error(f"Error retrieving analysis history: {e}")
            return []

    def clear_cache(self) -> bool:
        """Clear analysis cache"""
        try:
            self.analysis_cache.clear()
            log.info("Analysis cache cleared")
            return True
        except Exception as e:
            log.error(f"Error clearing cache: {e}")
            return False

    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information"""
        return {
            "session_id": self.session_id,
            "cache_entries": len(self.analysis_cache),
            "cache_ttl_minutes": self.cache_ttl_minutes,
            "initialized_at": datetime.now().isoformat()
        }

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        try:
            self.clear_cache()
            log.info(f"StockAnalyzer session {self.session_id} cleaned up")
        except Exception as e:
            log.error(f"Error during cleanup: {e}")


# Usage example and factory function
def create_stock_analyzer(session_id: Optional[str] = None) -> StockAnalyzer:
    """Factory function to create StockAnalyzer instance"""
    try:
        return StockAnalyzer(session_id=session_id)
    except Exception as e:
        log.error(f"Failed to create StockAnalyzer: {e}")
        raise


# Example usage for testing
if __name__ == "__main__":
    # Example usage
    try:
        with create_stock_analyzer() as analyzer:
            symbols = ["AAPL", "GOOGL", "TSLA"]
            result = analyzer.analyze_portfolio_batch(symbols)
            print("="*25, result, "="*25)
            print(f"Analysis completed: {result.get('analysis_status')}")
            print(f"Session: {analyzer.get_session_info()}")

    except Exception as e:
        print(f"Error: {e}")