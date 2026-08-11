"""Shared URL-only feature definitions for modeling and dashboard inference."""


FEATURE_NAMES = [
    "url_length",
    "domain_length",
    "path_length",
    "query_length",
    "number_of_dots",
    "number_of_hyphens",
    "number_of_underscores",
    "number_of_slashes",
    "number_of_question_marks",
    "number_of_equal_signs",
    "number_of_at_symbols",
    "number_of_ampersands",
    "number_of_percent_symbols",
    "number_of_digits",
    "number_of_letters",
    "digit_ratio",
    "letter_ratio",
    "special_character_count",
    "number_of_subdomains",
    "domain_is_ip",
    "uses_https_text",
    "has_port",
    "number_of_query_parameters",
    "suspicious_keyword_count",
    "has_suspicious_keyword",
    "known_shortener_domain",
]


SUSPICIOUS_KEYWORDS = [
    "login",
    "verify",
    "account",
    "secure",
    "update",
    "signin",
    "password",
    "bank",
    "confirm",
]


KNOWN_SHORTENER_DOMAINS = [
    "bit.ly",
    "cutt.ly",
    "goo.gl",
    "is.gd",
    "ow.ly",
    "rebrand.ly",
    "tinyurl.com",
    "t.co",
]
