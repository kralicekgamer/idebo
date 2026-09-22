from __future__ import annotations

import configparser
import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_OPERATOR = "idol"
DEFAULT_LIMIT = 5
DEFAULT_TIMEOUT = 10.0
DEFAULT_RETRIES = 2


class ConfigError(ValueError):
    """Raised when the idebo configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    stop_number: int
    operator: str = DEFAULT_OPERATOR
    limit: int = DEFAULT_LIMIT
    timeout: float = DEFAULT_TIMEOUT
    retries: int = DEFAULT_RETRIES


def default_config_path() -> Path:
    xdg_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_home:
        return Path(xdg_home) / "idebo" / "config.ini"
    return Path.home() / ".config" / "idebo" / "config.ini"


def find_config_path(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser()

    env_path = os.environ.get("IDEBO_CONFIG")
    if env_path:
        return Path(env_path).expanduser()

    user_path = default_config_path()
    if user_path.exists():
        return user_path

    legacy_path = Path.cwd() / "config.ini"
    if legacy_path.exists():
        return legacy_path

    bundled_path = Path(__file__).resolve().parent / "config.ini"
    if bundled_path.exists():
        return bundled_path

    return user_path


def _positive_int(raw: str, field: str) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{field} musí být celé číslo.") from exc
    if value <= 0:
        raise ConfigError(f"{field} musí být větší než nula.")
    return value


def _positive_float(raw: str, field: str) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{field} musí být číslo.") from exc
    if value <= 0:
        raise ConfigError(f"{field} musí být větší než nula.")
    return value


def _nonnegative_int(raw: str, field: str) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{field} musí být celé číslo.") from exc
    if value < 0:
        raise ConfigError(f"{field} nesmí být záporné.")
    return value


def settings_from_values(
    stop_number: str | int | None,
    operator: str = DEFAULT_OPERATOR,
    limit: str | int = DEFAULT_LIMIT,
    timeout: str | float = DEFAULT_TIMEOUT,
    retries: str | int = DEFAULT_RETRIES,
) -> Settings:
    if stop_number is None or str(stop_number).strip() in {"", "0"}:
        raise ConfigError("Číslo zastávky je povinné.")
    stop = _positive_int(str(stop_number), "stop_number")
    operator = str(operator).strip()
    if not operator or "/" in operator or "\\" in operator:
        raise ConfigError("Dopravce musí být neprázdný název bez lomítka.")
    parsed_limit = _positive_int(str(limit), "limit")
    parsed_timeout = _positive_float(str(timeout), "timeout")
    parsed_retries = _nonnegative_int(str(retries), "retries")
    return Settings(stop, operator, parsed_limit, parsed_timeout, parsed_retries)


def load_settings(path: Path) -> Settings:
    if not path.exists():
        raise ConfigError(
            f"Konfigurace neexistuje: {path}. Spusťte `idebo init` nebo použijte argumenty."
        )

    parser = configparser.ConfigParser()
    try:
        with path.open(encoding="utf-8") as config_file:
            parser.read_file(config_file)
        section = parser["Config"]
    except (OSError, configparser.Error, KeyError) as exc:
        raise ConfigError(f"Nelze načíst konfiguraci {path}: {exc}") from exc

    return settings_from_values(
        section.get("HomeStop"),
        section.get("Operator", DEFAULT_OPERATOR),
        section.get("NumberOfConnections", str(DEFAULT_LIMIT)),
        section.get("Timeout", str(DEFAULT_TIMEOUT)),
        section.get("Retries", str(DEFAULT_RETRIES)),
    )


def save_settings(path: Path, settings: Settings) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    parser = configparser.ConfigParser()
    parser["Config"] = {
        "Operator": settings.operator,
        "HomeStop": str(settings.stop_number),
        "NumberOfConnections": str(settings.limit),
        "Timeout": str(settings.timeout),
        "Retries": str(settings.retries),
    }
    try:
        with path.open("w", encoding="utf-8") as config_file:
            parser.write(config_file)
    except OSError as exc:
        raise ConfigError(f"Nelze uložit konfiguraci {path}: {exc}") from exc
