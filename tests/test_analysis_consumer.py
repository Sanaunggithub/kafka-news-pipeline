import pytest
import pytest
from consumers.analysis.main import (
    analyze_article,
    extract_categories,
    extract_companies,
    extract_keywords,
    extract_sentiment,
    extract_summary,
    extract_urgency,
)
from shared.models import AnalysisResult


def test_extract_sentiment_positive():
    text = "This is excellent and great news for everyone."
    assert extract_sentiment(text) == "positive"


def test_extract_sentiment_negative():
    text = "This is terrible and awful."
    assert extract_sentiment(text) == "negative"


def test_extract_urgency_normal():
    text = "A regular update about the market."
    assert extract_urgency(text) == "normal"


def test_extract_urgency_high():
    text = "There is a major announcement today."
    assert extract_urgency(text) == "high"


def test_extract_urgency_urgent():
    text = "This is a breaking emergency crisis situation."
    assert extract_urgency(text) == "urgent"


def test_extract_keywords_returns_list():
    text = "Artificial intelligence and software are transforming companies."
    result = extract_keywords(text)
    assert isinstance(result, list)


def test_extract_keywords_max_10():
    text = (
        "technology software intelligence analytics machine learning cloud "
        "cybersecurity data science automation innovation platform startup "
        "digital transformation enterprise research development"
    )
    result = extract_keywords(text)
    assert len(result) <= 10


def test_extract_keywords_filters_short():
    text = "AI is a new tool for data and cloud services."
    result = extract_keywords(text)
    assert all(len(word) >= 4 for word in result)


def test_extract_categories_technology():
    text = "Artificial intelligence software platform"
    result = extract_categories(text)
    assert "technology" in result


def test_extract_categories_multiple():
    text = "Technology and healthcare are both growing rapidly."
    result = extract_categories(text)
    assert "technology" in result
    assert "health" in result


def test_extract_companies_found():
    text = "Google and Microsoft announced a new partnership."
    result = extract_companies(text)
    assert "google" in [item.lower() for item in result]
    assert "microsoft" in [item.lower() for item in result]


def test_extract_companies_not_found():
    text = "No company names appear here."
    result = extract_companies(text)
    assert result == []


def test_extract_summary_two_sentences():
    text = (
        "This is the first sentence. "
        "This is the second sentence. "
        "This is the third sentence. "
        "This is the fourth sentence."
    )
    result = extract_summary(text)
    assert result == "This is the first sentence. This is the second sentence."


@pytest.mark.asyncio
async def test_analyze_article_returns_result(sample_news_event):
    result = await analyze_article(sample_news_event)

    assert isinstance(result, AnalysisResult)
    assert result.article_id == sample_news_event.id