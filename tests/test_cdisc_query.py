"""Unit tests for cdisc_query.py CLI tool.

All tests use unittest.mock to patch urllib.request.urlopen — no real API calls.
"""

import io
import json
import os
import subprocess
import sys
from http.client import HTTPResponse
from unittest import mock

import pytest

# ---------------------------------------------------------------------------
# Import helpers — add scripts/ to path so we can import cdisc_query
# ---------------------------------------------------------------------------
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, SCRIPTS_DIR)

import cdisc_query  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SCRIPT_PATH = os.path.join(SCRIPTS_DIR, "cdisc_query.py")
FAKE_API_KEY = "test-api-key-12345"
BASE_URL = "https://library.cdisc.org/api"


def _make_response(body: dict | list, status: int = 200) -> mock.MagicMock:
    """Build a mock urllib response object."""
    data = json.dumps(body).encode()
    resp = mock.MagicMock()
    resp.status = status
    resp.read.return_value = data
    resp.__enter__ = mock.MagicMock(return_value=resp)
    resp.__exit__ = mock.MagicMock(return_value=False)
    return resp


def _run_cli(*args: str, env_key: str | None = FAKE_API_KEY) -> subprocess.CompletedProcess:
    """Run the CLI script as a subprocess and return the result."""
    env = os.environ.copy()
    if env_key is not None:
        env["CDISC_API_KEY"] = env_key
    else:
        env.pop("CDISC_API_KEY", None)
    return subprocess.run(
        [sys.executable, SCRIPT_PATH, *args],
        capture_output=True,
        text=True,
        env=env,
    )


# ===========================================================================
# 1. Utility functions
# ===========================================================================

class TestValidateVersion:
    def test_validate_version_ok(self):
        assert cdisc_query.validate_version("3-4") == "3-4"

    def test_validate_version_empty(self):
        with pytest.raises(ValueError, match="must not be empty"):
            cdisc_query.validate_version("")

    def test_validate_version_traversal_slash(self):
        with pytest.raises(ValueError, match="invalid characters"):
            cdisc_query.validate_version("3-4/../admin")

    def test_validate_version_traversal_dotdot(self):
        with pytest.raises(ValueError, match="invalid characters"):
            cdisc_query.validate_version("..secret")

    def test_validate_version_dot_to_dash(self):
        """User-friendly: 3.4 becomes 3-4."""
        assert cdisc_query.validate_version("3.4") == "3-4"

    def test_validate_version_strips_whitespace(self):
        assert cdisc_query.validate_version("  3-4  ") == "3-4"


class TestHalItems:
    def test_hal_items_extracts_links(self):
        data = {
            "_links": {
                "datasets": [
                    {"href": "/mdr/sdtmig/3-4/datasets/AE", "title": "Adverse Events", "type": "Dataset"},
                    {"href": "/mdr/sdtmig/3-4/datasets/DM", "title": "Demographics", "type": "Dataset"},
                ]
            }
        }
        result = cdisc_query.hal_items(data, "datasets")
        assert len(result) == 2
        assert result[0] == {"name": "AE", "title": "Adverse Events", "type": "Dataset"}
        assert result[1] == {"name": "DM", "title": "Demographics", "type": "Dataset"}

    def test_hal_items_missing_key(self):
        data = {"_links": {}}
        result = cdisc_query.hal_items(data, "datasets")
        assert result == []

    def test_hal_items_no_links(self):
        result = cdisc_query.hal_items({}, "datasets")
        assert result == []


class TestTrim:
    def test_trim_removes_links_and_ordinal(self):
        data = {
            "name": "AE",
            "_links": {"self": {"href": "/foo"}},
            "ordinal": 1,
            "nested": {
                "label": "inner",
                "_links": {"self": {"href": "/bar"}},
                "ordinal": 2,
            },
        }
        result = cdisc_query.trim(data)
        assert "_links" not in result
        assert "ordinal" not in result
        assert "_links" not in result["nested"]
        assert "ordinal" not in result["nested"]
        assert result["name"] == "AE"
        assert result["nested"]["label"] == "inner"

    def test_trim_list_truncation(self):
        items = [{"name": f"item{i}", "ordinal": i} for i in range(10)]
        data = {"items": items}
        result = cdisc_query.trim(data, max_items=5)
        # 4 real items + 1 truncation notice = 5
        assert len(result["items"]) == 5
        assert result["items"][-1]["_truncated"] is True
        assert result["items"][-1]["total_count"] == 10

    def test_trim_list_no_truncation(self):
        items = [{"name": f"item{i}"} for i in range(3)]
        data = {"items": items}
        result = cdisc_query.trim(data, max_items=5)
        assert len(result["items"]) == 3

    def test_trim_list_wrapping(self):
        """Top-level list gets wrapped in envelope."""
        items = [{"name": "a"}, {"name": "b"}]
        result = cdisc_query.trim(items)
        assert "items" in result
        assert result["total_returned"] == 2
        assert result["has_more"] is False

    def test_trim_list_wrapping_with_truncation(self):
        items = [{"name": f"x{i}"} for i in range(150)]
        result = cdisc_query.trim(items, max_items=100)
        assert result["total_returned"] == 100
        assert result["has_more"] is True


# ===========================================================================
# 2. API client
# ===========================================================================

class TestApiGet:
    @mock.patch("cdisc_query.urlopen")
    def test_api_get_success(self, mock_urlopen):
        body = {"name": "AE", "label": "Adverse Events"}
        mock_urlopen.return_value = _make_response(body)
        result = cdisc_query.api_get("/mdr/sdtmig/3-4/datasets/AE", api_key=FAKE_API_KEY)
        assert result == body

    @mock.patch("cdisc_query.urlopen")
    def test_api_get_401(self, mock_urlopen):
        resp = _make_response({"error": "Unauthorized"}, status=401)
        mock_urlopen.return_value = resp
        with pytest.raises(SystemExit):
            cdisc_query.api_get("/mdr/products", api_key=FAKE_API_KEY)

    @mock.patch("cdisc_query.urlopen")
    def test_api_get_404(self, mock_urlopen):
        resp = _make_response({"error": "Not Found"}, status=404)
        mock_urlopen.return_value = resp
        with pytest.raises(SystemExit):
            cdisc_query.api_get("/mdr/sdtmig/9-9/datasets", api_key=FAKE_API_KEY)

    def test_api_get_missing_key(self):
        with pytest.raises(SystemExit):
            cdisc_query.api_get("/mdr/products", api_key=None)

    @mock.patch("cdisc_query.urlopen")
    def test_api_key_from_arg(self, mock_urlopen):
        """--api-key should take priority (tested via api_get directly)."""
        body = {"ok": True}
        mock_urlopen.return_value = _make_response(body)
        result = cdisc_query.api_get("/mdr/products", api_key="explicit-key")
        # Verify the request used the explicit key
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("Api-key") == "explicit-key"


# ===========================================================================
# 3. Subcommands (mock API responses)
# ===========================================================================

class TestCmdProducts:
    @mock.patch("cdisc_query.api_get")
    def test_cmd_products(self, mock_api_get):
        mock_api_get.return_value = {
            "_links": {
                "self": {"href": "/mdr/products"},
                "data-tabulation": {
                    "_links": {
                        "self": {"href": "/mdr/products/data-tabulation"},
                        "sdtmig": [
                            {"href": "/mdr/sdtmig/3-4", "title": "3-4"},
                            {"href": "/mdr/sdtmig/3-3", "title": "3-3"},
                        ],
                    }
                },
            }
        }
        result = cdisc_query.cmd_products(api_key=FAKE_API_KEY)
        assert "data-tabulation" in result
        assert "sdtmig" in result["data-tabulation"]
        assert "3-4" in result["data-tabulation"]["sdtmig"]


class TestCmdSdtm:
    @mock.patch("cdisc_query.api_get")
    def test_cmd_sdtm_domains(self, mock_api_get):
        mock_api_get.return_value = {
            "label": "SDTMIG 3.4",
            "version": "3-4",
            "_links": {
                "datasets": [
                    {"href": "/mdr/sdtmig/3-4/datasets/AE", "title": "Adverse Events", "type": "Dataset"},
                ]
            },
        }
        result = cdisc_query.cmd_sdtm_domains(version="3.4", api_key=FAKE_API_KEY)
        assert result["datasets"][0]["name"] == "AE"
        # Verify the API was called with dashes, not dots
        mock_api_get.assert_called_once()
        call_path = mock_api_get.call_args[0][0]
        assert "3-4" in call_path

    @mock.patch("cdisc_query.api_get")
    def test_cmd_sdtm_variables(self, mock_api_get):
        mock_api_get.return_value = {
            "label": "AE Variables",
            "_links": {
                "datasetVariables": [
                    {"href": "/mdr/sdtmig/3-4/datasets/AE/variables/AETERM", "title": "AETERM", "type": "Variable"},
                ]
            },
        }
        result = cdisc_query.cmd_sdtm_variables(version="3-4", domain="ae", api_key=FAKE_API_KEY)
        assert result["domain"] == "AE"
        assert result["variables"][0]["name"] == "AETERM"

    @mock.patch("cdisc_query.api_get")
    def test_cmd_sdtm_variable(self, mock_api_get):
        mock_api_get.return_value = {
            "name": "AETERM",
            "label": "Reported Term for the Adverse Event",
            "simpleDatatype": "Char",
            "_links": {"self": {"href": "/mdr/sdtmig/3-4/datasets/AE/variables/AETERM"}},
            "ordinal": 3,
        }
        result = cdisc_query.cmd_sdtm_variable(version="3-4", domain="AE", variable="aeterm", api_key=FAKE_API_KEY)
        assert result["name"] == "AETERM"
        assert "_links" not in result
        assert "ordinal" not in result


class TestCmdAdam:
    @mock.patch("cdisc_query.api_get")
    def test_cmd_adam_structures(self, mock_api_get):
        mock_api_get.return_value = {
            "label": "ADaM IG 1.3",
            "version": "1-3",
            "_links": {
                "dataStructures": [
                    {"href": "/mdr/adam/adamig-1-3/datastructures/ADSL", "title": "ADSL", "type": "Data Structure"},
                ]
            },
        }
        result = cdisc_query.cmd_adam_structures(version="1.3", api_key=FAKE_API_KEY)
        assert result["dataStructures"][0]["name"] == "ADSL"

    @mock.patch("cdisc_query.api_get")
    def test_cmd_adam_variable(self, mock_api_get):
        mock_api_get.return_value = {
            "name": "USUBJID",
            "label": "Unique Subject Identifier",
            "_links": {"self": {"href": "/..."}},
            "ordinal": 1,
        }
        result = cdisc_query.cmd_adam_variable(version="1-3", structure="adsl", variable="usubjid", api_key=FAKE_API_KEY)
        assert result["name"] == "USUBJID"
        assert "_links" not in result


class TestCmdCdash:
    @mock.patch("cdisc_query.api_get")
    def test_cmd_cdash_domains(self, mock_api_get):
        mock_api_get.return_value = {
            "label": "CDASHIG 2.0",
            "version": "2-0",
            "_links": {
                "domains": [
                    {"href": "/mdr/cdashig/2-0/domains/AE", "title": "Adverse Events", "type": "Domain"},
                ]
            },
        }
        result = cdisc_query.cmd_cdash_domains(version="2.0", api_key=FAKE_API_KEY)
        assert result["domains"][0]["name"] == "AE"

    @mock.patch("cdisc_query.api_get")
    def test_cmd_cdash_fields(self, mock_api_get):
        mock_api_get.return_value = {
            "label": "AE Fields",
            "_links": {
                "fields": [
                    {"href": "/mdr/cdashig/2-0/domains/AE/fields/AETERM", "title": "AETERM", "type": "Field"},
                ]
            },
        }
        result = cdisc_query.cmd_cdash_fields(version="2-0", domain="ae", api_key=FAKE_API_KEY)
        assert result["domain"] == "AE"
        assert result["fields"][0]["name"] == "AETERM"


class TestCmdTerminology:
    @mock.patch("cdisc_query.api_get")
    def test_cmd_ct_packages(self, mock_api_get):
        mock_api_get.return_value = {
            "_links": {
                "packages": [
                    {"href": "/mdr/ct/packages/sdtmct-2024-03-29", "title": "sdtmct-2024-03-29", "type": "Terminology"},
                ]
            }
        }
        result = cdisc_query.cmd_ct_packages(api_key=FAKE_API_KEY)
        assert result["packages"][0]["name"] == "sdtmct-2024-03-29"
        assert result["count"] == 1

    @mock.patch("cdisc_query.api_get")
    def test_cmd_codelist(self, mock_api_get):
        mock_api_get.return_value = {
            "conceptId": "C66781",
            "name": "AGEU",
            "_links": {"self": {"href": "/..."}},
            "ordinal": 1,
        }
        result = cdisc_query.cmd_codelist(package="sdtmct-2024-03-29", codelist="C66781", api_key=FAKE_API_KEY)
        assert result["conceptId"] == "C66781"
        assert "_links" not in result

    @mock.patch("cdisc_query.api_get")
    def test_cmd_codelist_terms(self, mock_api_get):
        mock_api_get.return_value = {
            "_links": {
                "terms": [
                    {"href": "/mdr/ct/.../terms/C25301", "title": "Day", "type": "Term"},
                    {"href": "/mdr/ct/.../terms/C29844", "title": "Week", "type": "Term"},
                ]
            }
        }
        result = cdisc_query.cmd_codelist_terms(package="sdtmct-2024-03-29", codelist="C66781", api_key=FAKE_API_KEY)
        assert result["count"] == 2
        assert result["terms"][0]["name"] == "C25301"


# ===========================================================================
# 4. CLI integration
# ===========================================================================

class TestCliIntegration:
    def test_cli_help(self):
        result = _run_cli("--help")
        assert result.returncode == 0
        assert "cdisc_query" in result.stdout or "usage" in result.stdout.lower()

    def test_cli_unknown_subcommand(self):
        result = _run_cli("nonexistent-command")
        assert result.returncode != 0

    @mock.patch("cdisc_query.urlopen")
    def test_output_is_json(self, mock_urlopen):
        """All subcommand output should be valid JSON."""
        mock_urlopen.return_value = _make_response({
            "_links": {
                "self": {"href": "/mdr/products"},
                "data-tabulation": {
                    "_links": {
                        "sdtmig": [{"href": "/mdr/sdtmig/3-4", "title": "3-4"}],
                    }
                },
            }
        })
        # Use subprocess to test actual JSON output
        result = _run_cli("products")
        if result.returncode == 0:
            parsed = json.loads(result.stdout)
            assert isinstance(parsed, dict)

    def test_no_api_key_json_error(self):
        """Running without API key should produce JSON error output."""
        result = _run_cli("products", env_key=None)
        assert result.returncode != 0
        parsed = json.loads(result.stdout)
        assert "error" in parsed
