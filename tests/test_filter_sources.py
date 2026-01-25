import pytest
from services.search_service import filter_sources, get_domain

def test_filter_sources_verified_and_unverified():
    """Тест: Розділення на verified/unverified за доменами."""
    results = [
        {"link": "https://bbc.com/news", "title": "Title1", "snippet": "Snippet1", "date": "2023-01-01"},
        {"link": "https://random.com", "title": "Title2", "snippet": "Snippet2"}
    ]
    verified, unverified = filter_sources(results)
    assert len(verified) == 1
    assert "bbc.com" in verified[0]
    assert "[2023-01-01]" in verified[0]
    assert len(unverified) == 1
    assert "random.com" in unverified[0]

def test_filter_sources_empty_results():
    """Тест: Порожній вхід - порожні списки."""
    verified, unverified = filter_sources([])
    assert verified == []
    assert unverified == []

def test_filter_sources_invalid_link():
    """Тест: Невалідний link - додає до unverified."""
    results = [{"link": "invalid", "title": "Title", "snippet": "Snippet"}]
    verified, unverified = filter_sources(results)
    assert verified == []
    assert len(unverified) == 1
    assert "URL: invalid" in unverified[0]

def test_filter_sources_subdomain_matching():
    """Тест: Endswith для субдоменів (e.g., news.bbc.com)."""
    results = [{"link": "https://news.bbc.com", "title": "Title", "snippet": "Snippet"}]
    verified, unverified = filter_sources(results)
    assert len(verified) == 1
    assert "news.bbc.com" in verified[0]

def test_filter_sources_no_date():
    """Тест: Без date - без [date] в string."""
    results = [{"link": "https://bbc.com", "title": "Title", "snippet": "Snippet"}]
    verified, _ = filter_sources(results)
    assert "[ " not in verified[0]  # No date info

def test_get_domain_edge_cases():
    """Допоміжний тест: get_domain для edge-кейсів."""
    assert get_domain("https://www.example.com/path") == "example.com"
    assert get_domain("invalid") == ""
    assert get_domain("") == ""