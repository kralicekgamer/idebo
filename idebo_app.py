from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Callable, Sequence
from typing import Any

import requests
from mpvnet_cz_api import Api, Stop

from idebo_config import (
    DEFAULT_OPERATOR,
    DEFAULT_RETRIES,
    DEFAULT_TIMEOUT,
    ConfigError,
    Settings,
    default_config_path,
    find_config_path,
    load_settings,
    save_settings,
    settings_from_values,
)

RESET = "\033[0m"
RED = "\033[31m"
BLUE = "\033[34m"
BOLD = "\033[1m"
TRAM_LINES = {"1", "2", "3", "5", "11", "X2", "X3", "X5", "X11"}


class ApiRequestError(RuntimeError):
    pass


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, (requests.ConnectionError, requests.Timeout)):
        return True
    return isinstance(exc, requests.HTTPError) and (
        exc.response is not None and exc.response.status_code >= 500
    )


def with_retries(operation: Callable[[], Any], retries: int) -> Any:
    attempts = retries + 1
    for attempt in range(attempts):
        try:
            return operation()
        except Exception as exc:
            if not _is_retryable(exc) or attempt == retries:
                raise ApiRequestError(str(exc) or exc.__class__.__name__) from exc
            time.sleep(0.25 * (2**attempt))
    raise AssertionError("unreachable")


def fetch_departures(settings: Settings) -> list[dict[str, Any]]:
    api = Api(settings.stop_number, settings.operator, timeout=settings.timeout)
    result = with_retries(api.sync, settings.retries)
    if not isinstance(result, list):
        raise ApiRequestError("API vrátilo neočekávaný formát odjezdů.")
    return result


def search_stops(name: str, operator: str, timeout: float, retries: int) -> list[dict[str, Any]]:
    result = with_retries(
        lambda: Stop.search(name, operator, timeout=timeout),
        retries,
    )
    if not isinstance(result, list):
        raise ApiRequestError("API vrátilo neočekávaný formát zastávek.")
    return result


def render_departures(
    departures: list[dict[str, Any]],
    limit: int,
    *,
    use_color: bool = True,
) -> str:
    lines: list[str] = []
    for connection in departures[:limit]:
        line = str(connection.get("line", "?"))
        departure = str(connection.get("departure", ""))
        destination = str(connection.get("destination", ""))
        kind = "Tram" if line in TRAM_LINES else "Bus"
        color = RED if kind == "Tram" else BLUE
        if use_color:
            header = f"[{color}{kind} {line}{RESET}]"
            time_text = f"{BOLD}{departure}{RESET}"
        else:
            header = f"[{kind} {line}]"
            time_text = departure
        lines.append(f"{header}\n{time_text} {destination}")
    return "\n\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="idebo",
        description="Odjezdy ze zastávek MPVNET.CZ v terminálu.",
    )
    parser.add_argument("--config", help="cesta k INI konfiguraci")
    parser.add_argument("--operator", help="dopravce (pid, idol, odis, zlin, jikord)")
    parser.add_argument("--stop", dest="stop_number", help="číslo zastávky")
    parser.add_argument("--limit", type=int, help="počet zobrazených spojů")
    parser.add_argument("--timeout", type=float, help="HTTP timeout v sekundách")
    parser.add_argument("--retries", type=int, help="počet opakování dočasných chyb")
    parser.add_argument("--json", action="store_true", help="výstup ve formátu JSON")
    parser.add_argument("--no-color", action="store_true", help="vypnout ANSI barvy")

    subparsers = parser.add_subparsers(dest="command")
    search_parser = subparsers.add_parser("search", help="vyhledat zastávku")
    search_parser.add_argument("name", help="název nebo část názvu zastávky")
    search_parser.add_argument("--operator", default=DEFAULT_OPERATOR)
    search_parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    search_parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES)
    search_parser.add_argument("--json", action="store_true")
    init_parser = subparsers.add_parser("init", help="vytvořit nebo přepsat konfiguraci")
    init_parser.add_argument("--config", help="cesta k INI konfiguraci")
    return parser


def _settings_from_args(args: argparse.Namespace) -> Settings:
    path = find_config_path(args.config)
    try:
        base = load_settings(path)
    except ConfigError:
        if args.stop_number is None:
            raise
        base = None
    return settings_from_values(
        args.stop_number if args.stop_number is not None else base.stop_number,
        args.operator or (base.operator if base else DEFAULT_OPERATOR),
        args.limit if args.limit is not None else (base.limit if base else 5),
        args.timeout if args.timeout is not None else (base.timeout if base else DEFAULT_TIMEOUT),
        args.retries if args.retries is not None else (base.retries if base else DEFAULT_RETRIES),
    )


def run_init(path: str | None) -> int:
    target = find_config_path(path)
    print(f"Konfigurace: {target}")
    stop = input("Číslo zastávky: ").strip()
    operator = input(f"Dopravce [{DEFAULT_OPERATOR}]: ").strip() or DEFAULT_OPERATOR
    limit = input("Počet spojů [5]: ").strip() or "5"
    timeout = input("Timeout v sekundách [10]: ").strip() or "10"
    retries = input("Počet opakování [2]: ").strip() or "2"
    settings = settings_from_values(stop, operator, limit, timeout, retries)
    save_settings(target, settings)
    print(f"Konfigurace uložena do {target}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "init":
        return run_init(args.config)
    if args.command == "search":
        results = search_stops(args.name, args.operator, args.timeout, args.retries)
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            for item in results:
                label = item.get("label", item)
                value = item.get("value", {}) if isinstance(item, dict) else {}
                number = value.get("stopNum", "?") if isinstance(value, dict) else "?"
                print(f"{label} [{number}]")
        return 0

    settings = _settings_from_args(args)
    departures = fetch_departures(settings)
    if args.json:
        print(json.dumps(departures[: settings.limit], ensure_ascii=False, indent=2))
    else:
        use_color = not args.no_color and sys.stdout.isatty()
        output = render_departures(departures, settings.limit, use_color=use_color)
        if output:
            print(output)
    return 0


def cli_entrypoint() -> int:
    try:
        return main()
    except (ConfigError, ApiRequestError, requests.RequestException) as exc:
        print(f"idebo: chyba: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(cli_entrypoint())
