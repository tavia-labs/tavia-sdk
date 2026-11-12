"""Tool helpers: templates, the checker on them, and function_tool."""

import pytest

from tavia import TOOL_TEMPLATES, check_tools, function_tool, template_tool
from tavia.generated.spec import LIMITS


def test_every_template_passes_alone():
    for template in TOOL_TEMPLATES:
        assert check_tools([template_tool(template["id"])]) == {"errors": [], "warnings": []}, template["id"]


def test_location_templates_ship():
    ids = {t["id"] for t in TOOL_TEMPLATES}
    assert {"geocode", "find_nearest_branch", "get_directions", "check_service_area"} <= ids


def test_reserved_prefix_is_refused():
    prefix = LIMITS["realtime.builtinTools.prefix"]
    tool = {**template_tool("geocode"), "name": f"{prefix}geocode"}
    assert [e["code"] for e in check_tools([tool])["errors"]] == ["name_reserved"]
    assert check_tools([{**tool, "name": f"my_{prefix}geocode"}])["errors"] == []


def test_tools_must_be_a_list():
    with pytest.raises(TypeError):
        check_tools({"type": "function"})


def test_function_tool_states_its_effect_and_passes_the_checker():
    tool = function_tool(
        "get_hours",
        effect="read",
        description="Opening hours for a day.",
        parameters={"type": "object", "properties": {"day": {"type": "string"}}},
    )
    assert tool["x-effect"] == "read" and tool["type"] == "function"
    assert check_tools([tool])["errors"] == []
    assert function_tool("book", effect="write", action="create")["x-action"] == "create"
    with pytest.raises(ValueError):
        function_tool("x", effect="maybe")
