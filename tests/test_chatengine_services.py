import pytest
from unittest.mock import MagicMock

from src.rag_system.chat_engine import ChatService
from src.rag_system.schemas import ChatMessage, ChatResponse
from exceptions.custom_exception import ChatError


@pytest.fixture
def mock_vector_service():
    return MagicMock()


@pytest.fixture
def mock_llm(monkeypatch):
    """Patch ModelLoader to return a mocked LLM with predictable outputs."""
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = "Mocked response with key point and risk."
    monkeypatch.setattr(
        "src.rag_system.chat_service.ModelLoader",
        lambda: MagicMock(load_llm=lambda: mock_llm)
    )
    return mock_llm


@pytest.fixture
def chat_service(mock_vector_service, mock_llm):
    return ChatService(vector_service=mock_vector_service)


def test_chat_with_document_success(chat_service, mock_vector_service):
    """End-to-end happy path with retrieved docs."""
    # Fake retrieved doc
    doc = MagicMock()
    doc.page_content = "Revenue grew by 15% in Q1 due to demand."
    doc.metadata = {"page": 1, "source": "q1_report.pdf"}
    mock_vector_service.similarity_search.return_value = [doc]

    history = [
        ChatMessage(role="human", content="What did the report say?"),
        ChatMessage(role="ai", content="It mentioned revenue."),
    ]

    response = chat_service.chat_with_document(
        document_id="doc1",
        question="How much did revenue grow?",
        chat_history=history,
    )

    assert isinstance(response, ChatResponse)
    assert "mocked response" in response.answer.lower()
    assert response.sources[0]["metadata"]["source"] == "q1_report.pdf"
    assert response.response_time_ms > 0


def test_chat_with_document_no_docs(chat_service, mock_vector_service):
    """If vector search returns nothing, raises ChatError."""
    mock_vector_service.similarity_search.return_value = []

    with pytest.raises(ChatError) as excinfo:
        chat_service.chat_with_document("doc1", "test?", [])
    assert "No relevant context" in str(excinfo.value)


def test_chat_with_document_chain_error(chat_service, mock_vector_service, mock_llm):
    """If LLM chain fails, raises ChatError."""
    doc = MagicMock()
    doc.page_content = "Dummy content"
    doc.metadata = {}
    mock_vector_service.similarity_search.return_value = [doc]

    mock_llm.invoke.side_effect = Exception("LLM crash")

    with pytest.raises(ChatError) as excinfo:
        chat_service.chat_with_document("doc1", "Q?", [])
    assert "Chat processing failed" in str(excinfo.value)


def test_generate_summary_success(chat_service, mock_llm):
    """Happy path summary generation."""
    result = chat_service.generate_summary(
        document_id="doc1",
        content="This report highlights key growth but also risk of debt."
    )

    assert "summary" in result
    assert any("key" in kp.lower() for kp in result["key_points"])
    assert any("risk" in rf.lower() for rf in result["red_flags"])


def test_generate_summary_truncates_long_content(chat_service):
    """Content longer than 8000 chars should be truncated."""
    long_content = "A" * 9000
    # Patch LLM to echo back input
    chat_service.llm.invoke = lambda payload: payload["content"]

    result = chat_service.generate_summary("doc1", long_content)
    assert len(result["summary"]) <= 8100
    assert result["summary"].endswith("...")


def test_extract_key_points_and_red_flags(chat_service):
    """Directly test helper methods."""
    summary_text = """
    - Key insight: Revenue up
    • Important note: Costs down
    Warning: Rising debt levels
    """

    key_points = chat_service._extract_key_points(summary_text)
    red_flags = chat_service._extract_red_flags(summary_text)

    assert any("revenue" in kp.lower() for kp in key_points)
    assert any("debt" in rf.lower() for rf in red_flags)


def test_format_sources(chat_service):
    """Sources should return truncated preview with metadata."""
    doc = MagicMock()
    doc.page_content = "X" * 300
    doc.metadata = {"page": 1}
    sources = chat_service._format_sources([doc])
    assert "..." in sources[0]["content_preview"]
    assert sources[0]["metadata"]["page"] == 1
