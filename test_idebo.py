import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from unittest.mock import Mock

import requests
from idebo_app import ApiRequestError, main, render_departures, with_retries
from idebo_config import ConfigError, load_settings, settings_from_values


class ConfigTests(unittest.TestCase):
    def test_loads_legacy_ini_and_defaults_optional_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.ini"
            path.write_text("[Config]\nHomeStop=53289\nOperator=idol\n", encoding="utf-8")
            settings = load_settings(path)
        self.assertEqual(settings.stop_number, 53289)
        self.assertEqual(settings.limit, 5)

    def test_rejects_missing_stop(self):
        with self.assertRaises(ConfigError):
            settings_from_values(None)


class CliTests(unittest.TestCase):
    def test_rendering(self):
        result = render_departures(
            [{"line": "1", "departure": "12:30", "destination": "Centrum"}],
            5,
            use_color=False,
        )
        self.assertEqual(result, "[Tram 1]\n12:30 Centrum")

    @patch("idebo_app.fetch_departures", return_value=[
        {"line": "1", "departure": "12:30", "destination": "Centrum"},
    ])
    @patch("sys.stdout.isatty", return_value=False)
    def test_json_output(self, _isatty, _fetch):
        with patch("builtins.print") as printer:
            self.assertEqual(main(["--stop", "53289", "--json"]), 0)
        payload = json.loads(printer.call_args.args[0])
        self.assertEqual(payload[0]["destination"], "Centrum")


class RetryTests(unittest.TestCase):
    def test_retry_then_success(self):
        operation = Mock(side_effect=[requests.Timeout(), "ok"])
        with patch("idebo_app.time.sleep"):
            self.assertEqual(with_retries(operation, 1), "ok")

    def test_exhausted_retry_is_explicit(self):
        operation = Mock(side_effect=RuntimeError("bad"))
        with self.assertRaises(ApiRequestError):
            with_retries(operation, 1)


if __name__ == "__main__":
    unittest.main()
