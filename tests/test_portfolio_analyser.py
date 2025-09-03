import pytest
from src.portfolio_summarizer.portfolio_sentiment import PortfolioAnalyzer


@pytest.fixture
def analyzer():
    """Create a fresh PortfolioAnalyzer for each test"""
    return PortfolioAnalyzer()


def test_analyze_portfolio_batch_basic(analyzer):
    """Test if portfolio analysis returns expected keys"""
    symbols = ["AAPL", "GOOGL"]
    result = analyzer.analyze_portfolio_batch(symbols)

    assert "portfolio_analysis" in result
    assert "individual_stocks" in result
    assert result["analysis_status"] == "SUCCESS"
    assert result["session_id"] == analyzer.session_id


def test_cache_usage(analyzer):
    """Test if cache is used for repeated requests"""
    symbols = ["TSLA", "MSFT"]

    # First call, should compute analysis
    first_result = analyzer.analyze_portfolio_batch(symbols)

    # Second call, should hit cache
    second_result = analyzer.analyze_portfolio_batch(symbols)

    # They should be identical objects
    assert first_result == second_result
    assert "cache_key" in second_result


def test_cache_invalidation(analyzer):
    """Test cache expiration logic"""
    symbols = ["NFLX"]

    # First analysis
    result = analyzer.analyze_portfolio_batch(symbols)
    cache_key = result["cache_key"]

    # Manually expire cache
    analyzer.analysis_cache[cache_key]['timestamp'] = analyzer.analysis_cache[cache_key]['timestamp'].replace(year=2000)

    # Next analysis should recompute (different object)
    new_result = analyzer.analyze_portfolio_batch(symbols)
    assert new_result != result


def test_invalid_symbols(analyzer):
    """Test handling of empty or invalid symbols"""
    with pytest.raises(Exception):
        analyzer.analyze_portfolio_batch([])

    with pytest.raises(Exception):
        analyzer.analyze_portfolio_batch(["", "  "])
