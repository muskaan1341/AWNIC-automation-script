"""
Reads the settings file.

WHICH FILE? That depends on where you are pointing the tests:
    pytest                    -> config/config.properties           (your own laptop)
    pytest --env=deployed     -> config/config.deployed.properties  (the AWS test site)

WHY IS THIS ITS OWN MODULE? So that "where do settings come from" is one small file you
can read in a minute, instead of being mixed into the browser setup. Tests get values
through BaseTest.get("..."), which just calls Config.get("...").

ORDER OF PRECEDENCE, highest first:
  1. a -D key=value on the pytest command line
  2. the value in whichever settings file was chosen above
That is why "pytest -D headless=true" works without editing any file.

The settings files are the SAME .properties files the Java suite used, copied across
unchanged. They carry a lot of hard-won knowledge about the environments in their
comments, and rewriting them into .ini would have thrown that away for no gain. The
format is trivial - "key = value", "#" or "!" starts a comment - so it is parsed here
in a dozen lines rather than pulling in a dependency.
"""

from __future__ import annotations

from pathlib import Path

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

_TRUE_VALUES = {"true", "yes", "on", "1"}


class ConfigError(RuntimeError):
    """A setting was asked for that nothing can answer."""


class Config:
    """A holder for the loaded settings. Never instantiated."""

    #: Which settings file was loaded - printed once at the start of a run.
    file_name: str = ""

    _values: dict[str, str] = {}
    _overrides: dict[str, str] = {}

    def __init__(self) -> None:  # pragma: no cover - defensive
        raise TypeError("Config is a holder for class methods, not a thing to create.")

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, env: str | None = None, overrides: dict[str, str] | None = None) -> None:
        """Called once by conftest.py before any test runs."""
        cls.file_name = (
            "config.deployed.properties" if env == "deployed" else "config.properties"
        )
        cls._values = _read_properties(_CONFIG_DIR / cls.file_name)
        cls._overrides = dict(overrides or {})

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    @classmethod
    def get(cls, key: str) -> str:
        """A value from the settings file, e.g. get("agentEmail")."""
        if key in cls._overrides:
            return cls._overrides[key]
        if key in cls._values:
            return cls._values[key]
        raise ConfigError(
            f"No setting called '{key}' in {cls.file_name}. "
            f"Add it there, or pass it on the command line with -D {key}=value."
        )

    @classmethod
    def get_or(cls, key: str, fallback: str) -> str:
        """The same, but for settings that are allowed to be absent."""
        try:
            return cls.get(key)
        except ConfigError:
            return fallback

    @classmethod
    def get_bool(cls, key: str) -> bool:
        return cls.get(key).strip().lower() in _TRUE_VALUES

    @classmethod
    def get_int(cls, key: str) -> int:
        return int(cls.get(key).strip())


def _read_properties(path: Path) -> dict[str, str]:
    """Parses a Java .properties file: 'key = value', '#' or '!' comments, blanks ignored."""
    if not path.exists():
        raise ConfigError(
            f"Settings file not found: {path}. The suite ships two of them in QA/selenium-py/config/."
        )
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values
