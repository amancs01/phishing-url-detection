"""Tests for safe URL text feature extraction."""

from numbers import Number

from src.feature_definitions import FEATURE_NAMES
from src.feature_extractor import extract_url_features


def test_normal_https_url() -> None:
    """A normal HTTPS URL should parse as HTTPS with no subdomains."""

    features = extract_url_features("https://example.com")

    assert features["url_length"] == len("https://example.com")
    assert features["domain_length"] == len("example.com")
    assert features["uses_https_text"] == 1
    assert features["number_of_subdomains"] == 0


def test_url_without_scheme() -> None:
    """A URL without a scheme should still provide hostname and path."""

    features = extract_url_features("example.com/login")

    assert features["domain_length"] == len("example.com")
    assert features["path_length"] == len("/login")
    assert features["uses_https_text"] == 0


def test_url_with_multiple_subdomains() -> None:
    """Subdomain count should come from hostname labels."""

    features = extract_url_features("https://a.b.example.com/login")

    assert features["number_of_subdomains"] == 2
    assert features["domain_is_ip"] == 0


def test_hostname_ip_literal() -> None:
    """IP literal detection should use text parsing only."""

    features = extract_url_features("http://192.0.2.1/account")

    assert features["domain_is_ip"] == 1
    assert features["number_of_subdomains"] == 0


def test_url_with_digits() -> None:
    """Digit count and ratio should reflect URL text."""

    url = "https://example.com/user123"
    features = extract_url_features(url)

    assert features["number_of_digits"] == 3
    assert features["digit_ratio"] == 3 / len(url)


def test_url_with_query_parameters() -> None:
    """Query length and parameter count should be extracted locally."""

    features = extract_url_features("https://example.com/search?q=test&page=2")

    assert features["query_length"] == len("q=test&page=2")
    assert features["number_of_query_parameters"] == 2
    assert features["number_of_question_marks"] == 1
    assert features["number_of_equal_signs"] == 2
    assert features["number_of_ampersands"] == 1


def test_url_containing_at_symbol() -> None:
    """The extractor should count @ symbols in the original URL text."""

    features = extract_url_features("https://user@example.com/login")

    assert features["number_of_at_symbols"] == 1
    assert features["domain_length"] == len("example.com")


def test_url_with_suspicious_keywords() -> None:
    """Suspicious keyword features should use the centralized keyword list."""

    features = extract_url_features("https://example.com/secure-login/verify")

    assert features["suspicious_keyword_count"] == 3
    assert features["has_suspicious_keyword"] == 1


def test_url_with_explicit_port() -> None:
    """Explicit ports should be detected without connecting to the host."""

    features = extract_url_features("https://example.com:8443/login")

    assert features["has_port"] == 1
    assert features["domain_length"] == len("example.com")


def test_empty_or_whitespace_only_input() -> None:
    """Whitespace-only input should produce stable zero-style features."""

    features = extract_url_features("   ")

    assert features["url_length"] == 0
    assert features["domain_length"] == 0
    assert features["digit_ratio"] == 0.0
    assert features["letter_ratio"] == 0.0
    assert features["uses_https_text"] == 0


def test_feature_dictionary_contains_exact_expected_names() -> None:
    """Feature dictionaries should match FEATURE_NAMES exactly and in order."""

    features = extract_url_features("https://example.org")

    assert list(features.keys()) == FEATURE_NAMES


def test_all_returned_model_values_are_numerical() -> None:
    """Every model feature value should be numeric."""

    features = extract_url_features("https://test.example/login?code=123")

    assert all(isinstance(value, Number) for value in features.values())


def test_same_input_produces_identical_output() -> None:
    """Feature extraction should be deterministic."""

    url = "https://sub.example.com/account?user=test"

    assert extract_url_features(url) == extract_url_features(url)


def test_known_shortener_domain() -> None:
    """Known shortener detection should compare hostname text only."""

    features = extract_url_features("https://bit.ly/example")

    assert features["known_shortener_domain"] == 1
