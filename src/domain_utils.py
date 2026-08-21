"""Offline registrable-domain extraction utilities.

This module uses the Public Suffix List bundled with `publicsuffix2`. It does
not fetch, update, request, resolve, or otherwise contact any network resource.
"""

from __future__ import annotations

from publicsuffix2 import PublicSuffixList

from src.url_utils import get_hostname, hostname_is_ip_address, strip_url


IP_GROUP_PREFIX = "ip:"
LOCALHOST_GROUP = "localhost"
UNKNOWN_DOMAIN_GROUP = "unknown"
PUBLIC_SUFFIX_LIST = PublicSuffixList()


def normalize_hostname_text(hostname: str) -> str:
    """Normalize hostname text without DNS resolution."""

    return hostname.strip().strip(".").lower()


def extract_registrable_domain(url: str) -> str:
    """Return an offline registrable/base-domain grouping key for URL text.

    Examples:

    - `sub.example.com` -> `example.com`
    - `sub.example.co.uk` -> `example.co.uk`
    - `192.0.2.1` -> `ip:192.0.2.1`

    The Public Suffix List is the bundled list distributed with the installed
    `publicsuffix2` package. Because the public suffix list changes over time,
    future environments may use a newer package/list and should record that
    dependency version when reproducing domain-disjoint experiments.
    """

    hostname = normalize_hostname_text(get_hostname(strip_url(url)))

    if not hostname:
        return UNKNOWN_DOMAIN_GROUP

    if hostname_is_ip_address(hostname):
        return f"{IP_GROUP_PREFIX}{hostname.strip('[]')}"

    if hostname == LOCALHOST_GROUP:
        return LOCALHOST_GROUP

    registrable_domain = PUBLIC_SUFFIX_LIST.get_sld(hostname)

    if not registrable_domain:
        return hostname

    return normalize_hostname_text(registrable_domain)


def main() -> None:
    """Run small local checks."""

    examples = [
        "https://sub.example.com/login",
        "https://sub.example.co.uk/login",
        "http://192.0.2.1/account",
        "localhost/test",
    ]

    for example in examples:
        print(example, "->", extract_registrable_domain(example))


if __name__ == "__main__":
    main()
