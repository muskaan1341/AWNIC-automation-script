"""
Reads the settings file.

    pytest                  -> config/config.properties           (your laptop)
    pytest --env=deployed   -> config/config.deployed.properties  (the AWS test site)

A "-D key=value" on the command line wins over the value in the file.
"""

from pathlib import Path

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

_TRUE_VALUES = {"true", "yes", "on", "1"}


class ConfigError(RuntimeError):
    """A setting was asked for that does not exist."""


class Config:
    """Holds the loaded settings. Only class methods - never create one."""

    # Which settings file was loaded.
    file_name: str = ""

    _values: dict = {}
    _overrides: dict = {}

    def __init__(self):  # pragma: no cover - defensive
        raise TypeError("Config is a holder for class methods, not a thing to create.")

    @classmethod
    def load(cls, env=None, overrides=None):
        """Called once by conftest.py before any test runs."""
        if env == "deployed":
            cls.file_name = "config.deployed.properties"
        else:
            cls.file_name = "config.properties"
        cls._values = _read_properties(_CONFIG_DIR / cls.file_name)
        cls._overrides = dict(overrides or {})

    @classmethod
    def get(cls, key):
        """A value from the settings, e.g. get("agentEmail")."""
        if key in cls._overrides:
            return cls._overrides[key]
        if key in cls._values:
            return cls._values[key]
        raise ConfigError(
            f"No setting called '{key}' in {cls.file_name}. "
            f"Add it there, or pass it on the command line with -D {key}=value."
        )

    @classmethod
    def get_or(cls, key, fallback):
        """Same as get(), but returns fallback when the setting is missing."""
        try:
            return cls.get(key)
        except ConfigError:
            return fallback

    @classmethod
    def get_bool(cls, key):
        return cls.get(key).strip().lower() in _TRUE_VALUES

    @classmethod
    def get_int(cls, key):
        return int(cls.get(key).strip())


def _read_properties(path):
    """Reads a .properties file: 'key = value' lines; '#' or '!' lines are comments."""
    if not path.exists():
        raise ConfigError(
            f"Settings file not found: {path}. The suite ships two of them in QA/selenium-py/config/."
        )
    values = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values
