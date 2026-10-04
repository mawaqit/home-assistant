"""Tests for the dashboard examples of docs/dashboards*.md."""

import json
from pathlib import Path
import re

import pytest
import yaml

from homeassistant.core import HomeAssistant

from .conftest import build_prayer_data

ROOT = Path(__file__).parent.parent
PAGES = sorted((ROOT / "docs").glob("dashboards*.md"))
TRANSLATIONS = json.loads(
    (ROOT / "custom_components/mawaqit/translations/en.json").read_text()
)
TRANSLATION_KEYS = {
    key for platform in TRANSLATIONS["entity"].values() for key in platform
}


def _yaml_blocks(page: Path) -> list[str]:
    """Return the YAML code blocks of a page."""
    return re.findall(r"```yaml\n(.*?)```", page.read_text(), re.DOTALL)


def _mosque_display(page: Path) -> str:
    """Return the YAML of the mosque display."""
    return next(block for block in _yaml_blocks(page) if "button-card" in block)


def test_pages_found() -> None:
    """Test the four languages are tested."""
    assert [page.name for page in PAGES] == [
        "dashboards.de.md",
        "dashboards.fr.md",
        "dashboards.md",
        "dashboards.nl.md",
    ]


@pytest.mark.parametrize("page", PAGES, ids=lambda page: page.name)
def test_examples_are_valid_yaml(page: Path) -> None:
    """Test every example is a card configuration."""
    blocks = _yaml_blocks(page)
    assert len(blocks) == 3
    for block in blocks:
        assert "type" in yaml.safe_load(block)


@pytest.mark.parametrize("page", PAGES, ids=lambda page: page.name)
async def test_example_entity_ids_exist(
    hass: HomeAssistant, setup_mawaqit_integration, page: Path
) -> None:
    """Test the entity IDs of the examples are the ones of an English install."""
    await setup_mawaqit_integration(
        prayer_data={
            **build_prayer_data(fill_all_months=False),
            "name": "My Mosque",
            "image": "https://mawaqit.net/upload/picture.jpg",
        }
    )

    entity_ids = set(re.findall(r"\b(?:sensor|image)\.my_mosque_\w+", page.read_text()))
    assert entity_ids
    assert {
        entity_id for entity_id in entity_ids if not hass.states.get(entity_id)
    } == set()


@pytest.mark.parametrize("page", PAGES, ids=lambda page: page.name)
def test_mosque_display_translation_keys_exist(page: Path) -> None:
    """Test the mosque display finds the entities by existing translation keys."""
    display = _mosque_display(page)
    keys = set(re.findall(r'time\("(\w+)"\)', display))
    keys |= set(re.findall(r"(?:ids|entities\?)\.(\w+)", display)) - {"name"}
    for prefix in re.findall(r"(\w+_)\$\{key\}", display):
        keys |= {
            prefix + key
            # The prayers, listed with their Arabic name.
            for key in re.findall(r'\["(\w+)", "[\u0600-\u06ff]', display)
            if prefix + key != "iqama_shuruq"
        }

    assert "prayer_fajr" in keys
    assert keys <= TRANSLATION_KEYS


def test_mosque_display_is_the_same_in_every_language() -> None:
    """Test the pages share the mosque display, which has no text to translate."""
    assert len({_mosque_display(page) for page in PAGES}) == 1
