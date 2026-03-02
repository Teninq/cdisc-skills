#!/usr/bin/env python3
"""Standalone CLI tool for querying the CDISC Library API.

Zero external dependencies — Python 3.9+ stdlib only.
All output (including errors) is JSON to stdout.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any
from urllib.request import Request, urlopen

BASE_URL = "https://library.cdisc.org/api"
DEFAULT_MAX_ITEMS = 100
_EXCLUDED_KEYS = frozenset({"_links", "ordinal"})


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

def validate_version(version: str, param_name: str = "version") -> str:
    version = version.strip()
    if not version:
        raise ValueError(f"{param_name} must not be empty")
    if "/" in version or ".." in version:
        raise ValueError(f"{param_name} '{version}' contains invalid characters")
    # Convert dots to dashes for user convenience (3.4 -> 3-4)
    version = version.replace(".", "-")
    return version


# ---------------------------------------------------------------------------
# HAL helpers
# ---------------------------------------------------------------------------

def hal_items(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    items = data.get("_links", {}).get(key, [])
    return [
        {
            "name": item["href"].rstrip("/").split("/")[-1],
            "title": item.get("title"),
            "type": item.get("type"),
        }
        for item in items
        if isinstance(item, dict)
    ]


# ---------------------------------------------------------------------------
# Response trimming
# ---------------------------------------------------------------------------

def trim(
    payload: dict[str, Any] | list[Any],
    max_items: int = DEFAULT_MAX_ITEMS,
) -> dict[str, Any]:
    if isinstance(payload, list):
        return _wrap_list(payload, max_items=max_items)
    return _trim_dict(payload, max_items=max_items)


def _wrap_list(items: list[Any], max_items: int) -> dict[str, Any]:
    has_more = len(items) > max_items
    kept = items[:max_items]
    trimmed_items = [_trim_value(item, max_items=max_items) for item in kept]
    return {
        "items": trimmed_items,
        "total_returned": len(trimmed_items),
        "has_more": has_more,
    }


def _trim_dict(obj: dict[str, Any], max_items: int) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in obj.items():
        if key in _EXCLUDED_KEYS:
            continue
        result[key] = _trim_value(value, max_items=max_items)
    return result


def _trim_value(value: Any, max_items: int) -> Any:
    if isinstance(value, dict):
        return _trim_dict(value, max_items=max_items)
    if isinstance(value, list):
        return _trim_list(value, max_items=max_items)
    return value


def _trim_list(items: list[Any], max_items: int) -> list[Any]:
    original_count = len(items)
    if original_count <= max_items:
        return [_trim_value(item, max_items=max_items) for item in items]
    kept_items = items[: max_items - 1]
    trimmed = [_trim_value(item, max_items=max_items) for item in kept_items]
    trimmed.append(
        {
            "_truncated": True,
            "total_count": original_count,
            "message": f"Results truncated: showing {max_items - 1} of {original_count} items.",
        }
    )
    return trimmed


# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------

def api_get(path: str, api_key: str | None = None) -> Any:
    if not api_key:
        _error_exit("CDISC_API_KEY not set. Provide --api-key or set the environment variable.")
    url = f"{BASE_URL}{path}"
    req = Request(url, headers={"api-key": api_key, "Accept": "application/json"})
    with urlopen(req) as resp:
        data = json.loads(resp.read())
        if resp.status == 401:
            _error_exit("Authentication failed: invalid CDISC API key (HTTP 401).")
        if resp.status == 404:
            _error_exit(f"Resource not found: {path} (HTTP 404).")
        if resp.status >= 400:
            _error_exit(f"HTTP error {resp.status} for {path}.")
        return data


def _error_exit(message: str) -> None:
    print(json.dumps({"error": message}))
    sys.exit(1)


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_products(api_key: str) -> dict[str, Any]:
    data = api_get("/mdr/products", api_key=api_key)
    links = data.get("_links", {})
    result: dict[str, Any] = {}
    for group_key, group_val in links.items():
        if group_key in ("self",):
            continue
        if isinstance(group_val, dict):
            group_links = group_val.get("_links", {})
            group_items: dict[str, list[str]] = {}
            for product_key, product_list in group_links.items():
                if product_key in ("self",) or not isinstance(product_list, list):
                    continue
                group_items[product_key] = [
                    item.get("title") or item.get("href", "").split("/")[-1]
                    for item in product_list
                    if isinstance(item, dict) and "href" in item
                ]
            if group_items:
                result[group_key] = group_items
        elif isinstance(group_val, list):
            result[group_key] = [
                item.get("title") or item.get("href", "").split("/")[-1]
                for item in group_val
                if isinstance(item, dict) and "href" in item
            ]
    return result


def cmd_sdtm_domains(version: str, api_key: str) -> dict[str, Any]:
    version = validate_version(version)
    data = api_get(f"/mdr/sdtmig/{version}/datasets", api_key=api_key)
    return {
        "label": data.get("label"),
        "version": data.get("version"),
        "datasets": hal_items(data, "datasets"),
    }


def cmd_sdtm_variables(version: str, domain: str, api_key: str) -> dict[str, Any]:
    version = validate_version(version)
    domain = domain.upper().strip()
    data = api_get(f"/mdr/sdtmig/{version}/datasets/{domain}/variables", api_key=api_key)
    return {
        "domain": domain,
        "label": data.get("label"),
        "variables": hal_items(data, "datasetVariables"),
    }


def cmd_sdtm_variable(version: str, domain: str, variable: str, api_key: str) -> dict[str, Any]:
    version = validate_version(version)
    domain = domain.upper().strip()
    variable = variable.upper().strip()
    data = api_get(f"/mdr/sdtmig/{version}/datasets/{domain}/variables/{variable}", api_key=api_key)
    return trim(data)


def cmd_adam_structures(version: str, api_key: str) -> dict[str, Any]:
    version = validate_version(version)
    data = api_get(f"/mdr/adam/adamig-{version}/datastructures", api_key=api_key)
    return {
        "label": data.get("label"),
        "version": data.get("version"),
        "dataStructures": hal_items(data, "dataStructures"),
    }


def cmd_adam_variable(version: str, structure: str, variable: str, api_key: str) -> dict[str, Any]:
    version = validate_version(version)
    structure = structure.upper().strip()
    variable = variable.upper().strip()
    data = api_get(f"/mdr/adam/adamig-{version}/datastructures/{structure}/variables/{variable}", api_key=api_key)
    return trim(data)


def cmd_cdash_domains(version: str, api_key: str) -> dict[str, Any]:
    version = validate_version(version)
    data = api_get(f"/mdr/cdashig/{version}/domains", api_key=api_key)
    return {
        "label": data.get("label"),
        "version": data.get("version"),
        "domains": hal_items(data, "domains"),
    }


def cmd_cdash_fields(version: str, domain: str, api_key: str) -> dict[str, Any]:
    version = validate_version(version)
    domain = domain.upper().strip()
    data = api_get(f"/mdr/cdashig/{version}/domains/{domain}/fields", api_key=api_key)
    return {
        "domain": domain,
        "label": data.get("label"),
        "fields": hal_items(data, "fields"),
    }


def cmd_ct_packages(api_key: str) -> dict[str, Any]:
    data = api_get("/mdr/ct/packages", api_key=api_key)
    packages = hal_items(data, "packages")
    return {"packages": packages, "count": len(packages)}


def cmd_codelist(package: str, codelist: str, api_key: str) -> dict[str, Any]:
    package = validate_version(package, param_name="package_id")
    codelist = validate_version(codelist, param_name="codelist_id")
    data = api_get(f"/mdr/ct/packages/{package}/codelists/{codelist}", api_key=api_key)
    return trim(data)


def cmd_codelist_terms(package: str, codelist: str, api_key: str) -> dict[str, Any]:
    package = validate_version(package, param_name="package_id")
    codelist = validate_version(codelist, param_name="codelist_id")
    data = api_get(f"/mdr/ct/packages/{package}/codelists/{codelist}/terms", api_key=api_key)
    terms = hal_items(data, "terms")
    return {
        "codelist": codelist,
        "package": package,
        "terms": terms,
        "count": len(terms),
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cdisc_query",
        description="Query the CDISC Library API. All output is JSON.",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="CDISC Library API key (overrides CDISC_API_KEY env var).",
    )
    sub = parser.add_subparsers(dest="command")

    # products
    sub.add_parser("products", help="List all CDISC standards and versions.")

    # sdtm-domains
    p = sub.add_parser("sdtm-domains", help="List SDTM domains for a version.")
    p.add_argument("--version", required=True)

    # sdtm-variables
    p = sub.add_parser("sdtm-variables", help="List variables for an SDTM domain.")
    p.add_argument("--version", required=True)
    p.add_argument("--domain", required=True)

    # sdtm-variable
    p = sub.add_parser("sdtm-variable", help="Get a specific SDTM variable definition.")
    p.add_argument("--version", required=True)
    p.add_argument("--domain", required=True)
    p.add_argument("--variable", required=True)

    # adam-structures
    p = sub.add_parser("adam-structures", help="List ADaM data structures for a version.")
    p.add_argument("--version", required=True)

    # adam-variable
    p = sub.add_parser("adam-variable", help="Get a specific ADaM variable definition.")
    p.add_argument("--version", required=True)
    p.add_argument("--structure", required=True)
    p.add_argument("--variable", required=True)

    # cdash-domains
    p = sub.add_parser("cdash-domains", help="List CDASH domains for a version.")
    p.add_argument("--version", required=True)

    # cdash-fields
    p = sub.add_parser("cdash-fields", help="List fields for a CDASH domain.")
    p.add_argument("--version", required=True)
    p.add_argument("--domain", required=True)

    # ct-packages
    sub.add_parser("ct-packages", help="List controlled terminology packages.")

    # codelist
    p = sub.add_parser("codelist", help="Get a codelist definition.")
    p.add_argument("--package", required=True)
    p.add_argument("--codelist", required=True)

    # codelist-terms
    p = sub.add_parser("codelist-terms", help="List terms in a codelist.")
    p.add_argument("--package", required=True)
    p.add_argument("--codelist", required=True)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(2)

    api_key = args.api_key or os.environ.get("CDISC_API_KEY")

    dispatch = {
        "products": lambda: cmd_products(api_key=api_key),
        "sdtm-domains": lambda: cmd_sdtm_domains(version=args.version, api_key=api_key),
        "sdtm-variables": lambda: cmd_sdtm_variables(version=args.version, domain=args.domain, api_key=api_key),
        "sdtm-variable": lambda: cmd_sdtm_variable(version=args.version, domain=args.domain, variable=args.variable, api_key=api_key),
        "adam-structures": lambda: cmd_adam_structures(version=args.version, api_key=api_key),
        "adam-variable": lambda: cmd_adam_variable(version=args.version, structure=args.structure, variable=args.variable, api_key=api_key),
        "cdash-domains": lambda: cmd_cdash_domains(version=args.version, api_key=api_key),
        "cdash-fields": lambda: cmd_cdash_fields(version=args.version, domain=args.domain, api_key=api_key),
        "ct-packages": lambda: cmd_ct_packages(api_key=api_key),
        "codelist": lambda: cmd_codelist(package=args.package, codelist=args.codelist, api_key=api_key),
        "codelist-terms": lambda: cmd_codelist_terms(package=args.package, codelist=args.codelist, api_key=api_key),
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(2)

    try:
        result = handler()
        print(json.dumps(result, indent=2))
    except SystemExit:
        raise
    except ValueError as exc:
        _error_exit(str(exc))
    except Exception as exc:
        _error_exit(f"Unexpected error: {exc}")


if __name__ == "__main__":
    main()
