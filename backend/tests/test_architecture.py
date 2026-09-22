from app.core.cache import FeedCache
from app.core.config import CATEGORIES, COUNTRY_CODES, load_settings
from app.services.validation import validate_category, validate_country_codes

def test_country_validation_normalizes_and_deduplicates():
    assert validate_country_codes([" nl ", "NL", "DE"]) == ["NL", "DE"]
def test_category_validation_is_case_insensitive():
    assert validate_category(" SPORTS ") == "sports"
def test_feed_cache():
    cache=FeedCache(60)
    cache.set("key",[{"id":"1"}])
    assert cache.get("key")==[{"id":"1"}]
    cache.clear()
    assert cache.get("key") is None
def test_supported_domains_are_non_empty():
    assert "NL" in COUNTRY_CODES
    assert "adult" in CATEGORIES
    assert load_settings().database_url
