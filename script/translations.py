"""Generate translations/en.json from strings.json and check the other languages.

Home Assistant core generates en.json at build time; a custom integration must ship it.
Run with: python3 -m script.translations
"""

import json
from pathlib import Path
import re
import sys
from typing import Any

import homeassistant

INTEGRATION = Path(__file__).parent.parent / "custom_components" / "mawaqit"
HA_ROOT = Path(homeassistant.__file__).parent
REFERENCE = re.compile(r"\[%key:([a-z0-9_]+(?:::[a-z0-9_]+)+)%\]")


def _lookup(path: str, strings: dict[str, Any]) -> str:
    """Return the string a [%key:...%] reference points to."""
    parts = path.split("::")
    if parts[0] == "common":
        source = json.loads((HA_ROOT / "strings.json").read_text())
        node: Any = source["common"]
        parts = parts[1:]
    elif parts[0] == "component" and parts[1] == "mawaqit":
        node = strings
        parts = parts[2:]
    elif parts[0] == "component":
        source = json.loads(
            (HA_ROOT / "components" / parts[1] / "strings.json").read_text()
        )
        node = source
        parts = parts[2:]
    else:
        raise ValueError(f"Unsupported reference [%key:{path}%]")
    for part in parts:
        node = node[part]
    return _resolve(node, strings)


def _resolve(value: Any, strings: dict[str, Any]) -> Any:
    if isinstance(value, dict):
        return {key: _resolve(item, strings) for key, item in value.items()}
    if isinstance(value, str):
        return REFERENCE.sub(lambda match: _lookup(match[1], strings), value)
    return value


def _keys(value: Any, prefix: str = "") -> set[str]:
    if not isinstance(value, dict):
        return {prefix}
    return {
        key for name, item in value.items() for key in _keys(item, f"{prefix}{name}.")
    }


def main() -> int:
    """Write en.json, then report keys missing from or unknown to other languages."""
    strings = json.loads((INTEGRATION / "strings.json").read_text())
    english = _resolve(strings, strings)
    (INTEGRATION / "translations" / "en.json").write_text(
        json.dumps(english, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    )

    expected = _keys(english)
    errors = []
    for file in sorted((INTEGRATION / "translations").glob("*.json")):
        found = _keys(json.loads(file.read_text()))
        errors.extend(f"{file.name}: missing {key}" for key in expected - found)
        errors.extend(f"{file.name}: unknown {key}" for key in found - expected)
    for error in sorted(errors):
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
