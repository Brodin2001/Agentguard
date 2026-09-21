from pathlib import Path
import runpy


_FIXTURE = runpy.run_path(
    str(Path(__file__).parents[1] / "examples" / "hass_mcp_conformance_fixture.py")
)
run_fixture = _FIXTURE["run_fixture"]


def test_hass_mcp_style_conformance_fixture():
    result = run_fixture()

    assert result["raw_mutated_effect"] == {
        "entity_id": "light.kitchen",
        "action": "off",
    }
    assert result["negative_control"]["allowed"] is False
    assert result["negative_control"]["executed"] is False
    assert result["positive_control"]["allowed"] is True
    assert result["positive_control"]["executed"] is True
