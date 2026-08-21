"""Tests for offline registrable-domain extraction."""

import inspect

from src import domain_utils
from src.domain_utils import extract_registrable_domain


def test_subdomains_map_to_same_registrable_domain() -> None:
    """A subdomain should group with its registrable base domain."""

    assert extract_registrable_domain("https://example.com") == "example.com"
    assert extract_registrable_domain("https://sub.example.com") == "example.com"


def test_co_uk_public_suffix_handling() -> None:
    """Public Suffix List parsing should preserve example.co.uk."""

    assert extract_registrable_domain("https://example.co.uk") == "example.co.uk"
    assert (
        extract_registrable_domain("https://sub.example.co.uk/path")
        == "example.co.uk"
    )


def test_ip_literal_gets_stable_grouping_key() -> None:
    """IP literals should not be treated as normal domains or resolved."""

    assert extract_registrable_domain("http://192.0.2.1/account") == "ip:192.0.2.1"


def test_missing_scheme_still_parses_hostname() -> None:
    """Existing local parser should handle scheme-less domain-like text."""

    assert extract_registrable_domain("sub.example.com/login") == "example.com"


def test_localhost_and_blank_inputs_are_stable() -> None:
    """Localhost-like and blank strings should return stable non-network keys."""

    assert extract_registrable_domain("localhost/test") == "localhost"
    assert extract_registrable_domain("   ") == "unknown"


def test_punycode_text_is_preserved_as_text() -> None:
    """Punycode hostnames should be grouped textually without IDNA lookup."""

    assert (
        extract_registrable_domain("https://sub.xn--example-ova.com/path")
        == "xn--example-ova.com"
    )


def test_domain_utils_does_not_fetch_public_suffix_list() -> None:
    """The module should use bundled PSL data and never call fetch()."""

    source = inspect.getsource(domain_utils)

    assert ".fetch(" not in source
    assert "urllib.request" not in source
    assert "requests" not in source
    assert "socket" not in source
