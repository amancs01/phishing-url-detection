"""Safe URL text feature extraction.

The extractor in this module converts one raw URL string into numerical
features using local text parsing only. It never opens, requests, resolves, or
contacts the URL.
"""

from src.feature_definitions import (
    FEATURE_NAMES,
    KNOWN_SHORTENER_DOMAINS,
    SUSPICIOUS_KEYWORDS,
)
from src.url_utils import (
    count_query_parameters,
    get_hostname,
    get_path,
    get_query,
    has_explicit_port,
    hostname_is_ip_address,
    strip_url,
    uses_https_scheme,
)


def count_digits(text: str) -> int:
    """Return the number of digit characters in text."""

    return sum(character.isdigit() for character in text)


def count_letters(text: str) -> int:
    """Return the number of alphabetic characters in text."""

    return sum(character.isalpha() for character in text)


def count_special_characters(text: str) -> int:
    """Return the count of non-letter, non-digit, non-space characters."""

    return sum(
        not character.isalnum() and not character.isspace()
        for character in text
    )


def count_subdomains(hostname: str) -> int:
    """Estimate the number of subdomain labels from hostname text.

    This simple project rule treats the final two hostname labels as the main
    domain and suffix, then counts any labels before them as subdomains.
    """

    if not hostname or hostname_is_ip_address(hostname):
        return 0

    labels = [label for label in hostname.split(".") if label]

    if len(labels) <= 2:
        return 0

    return len(labels) - 2


def count_suspicious_keywords(text: str) -> int:
    """Count occurrences of the centralized suspicious keywords."""

    lower_text = text.lower()
    return sum(lower_text.count(keyword) for keyword in SUSPICIOUS_KEYWORDS)


def is_known_shortener(hostname: str) -> int:
    """Return 1 when hostname text matches a known shortener domain."""

    normalized_hostname = hostname.lower().removeprefix("www.")
    return int(normalized_hostname in KNOWN_SHORTENER_DOMAINS)


def safe_ratio(part: int, whole: int) -> float:
    """Return part divided by whole, or 0.0 when the whole is empty."""

    if whole == 0:
        return 0.0

    return part / whole


def extract_url_features(url: str) -> dict[str, float | int]:
    """Extract the final URL-only model features from one raw URL string."""

    stripped_url = strip_url(url)
    hostname = get_hostname(stripped_url)
    path = get_path(stripped_url)
    query = get_query(stripped_url)

    url_length = len(stripped_url)
    digit_count = count_digits(stripped_url)
    letter_count = count_letters(stripped_url)
    suspicious_keyword_count = count_suspicious_keywords(stripped_url)

    features = {
        "url_length": url_length,
        "domain_length": len(hostname),
        "path_length": len(path),
        "query_length": len(query),
        "number_of_dots": stripped_url.count("."),
        "number_of_hyphens": stripped_url.count("-"),
        "number_of_underscores": stripped_url.count("_"),
        "number_of_slashes": stripped_url.count("/"),
        "number_of_question_marks": stripped_url.count("?"),
        "number_of_equal_signs": stripped_url.count("="),
        "number_of_at_symbols": stripped_url.count("@"),
        "number_of_ampersands": stripped_url.count("&"),
        "number_of_percent_symbols": stripped_url.count("%"),
        "number_of_digits": digit_count,
        "number_of_letters": letter_count,
        "digit_ratio": safe_ratio(digit_count, url_length),
        "letter_ratio": safe_ratio(letter_count, url_length),
        "special_character_count": count_special_characters(stripped_url),
        "number_of_subdomains": count_subdomains(hostname),
        "domain_is_ip": int(hostname_is_ip_address(hostname)),
        "uses_https_text": int(uses_https_scheme(stripped_url)),
        "has_port": int(has_explicit_port(stripped_url)),
        "number_of_query_parameters": count_query_parameters(query),
        "suspicious_keyword_count": suspicious_keyword_count,
        "has_suspicious_keyword": int(suspicious_keyword_count > 0),
        "known_shortener_domain": is_known_shortener(hostname),
    }

    return {feature_name: features[feature_name] for feature_name in FEATURE_NAMES}


def main() -> None:
    """Run manual checks with harmless example URLs."""

    example_urls = [
        "https://example.com",
        "https://sub.example.com/login?user=test",
        "http://192.0.2.1/account",
    ]

    for example_url in example_urls:
        print(example_url)
        print(extract_url_features(example_url))


if __name__ == "__main__":
    main()
