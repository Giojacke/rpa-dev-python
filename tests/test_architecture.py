"""Static checks that enforce the layering rules of AGENTS.md. No browser needed."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXCLUDED_DIRS = {".venv", "venv", ".git", "deploy", "__pycache__"}
BROWSER_LIBRARIES = {"selenium", "playwright"}
LOCATOR_NAME = re.compile(r"^(BTN|TXT|LBL|LNK|CHK|RDO|DDL|TBL|MDL|IFR)_[A-Z0-9_]+$")


def python_files(*folders: str) -> list[Path]:
    roots = [PROJECT_ROOT / folder for folder in folders] if folders else [PROJECT_ROOT]
    return [
        path
        for root in roots
        for path in root.rglob("*.py")
        if not EXCLUDED_DIRS.intersection(path.relative_to(PROJECT_ROOT).parts)
    ]


def imported_modules(path: Path) -> set[str]:
    modules = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def relative(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def test_only_engines_import_browser_libraries():
    offenders = [
        relative(path)
        for path in python_files()
        if not relative(path).startswith("core/engines/")
        and any(module.split(".")[0] in BROWSER_LIBRARIES for module in imported_modules(path))
    ]
    assert offenders == [], "Only core/engines/ may import selenium or playwright"


def test_there_are_no_sleep_calls():
    offenders = []
    for path in python_files():
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            is_time_sleep = isinstance(node, ast.Attribute) and node.attr == "sleep"
            is_sleep_import = isinstance(node, ast.ImportFrom) and node.module == "time" and any(
                alias.name == "sleep" for alias in node.names
            )
            if is_time_sleep or is_sleep_import:
                offenders.append(relative(path))
    assert offenders == [], "Use the engine's explicit waits instead of sleep()"


def test_tasks_contain_no_locators():
    offenders = []
    for path in python_files("tasks"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Assign):
                offenders += [
                    f"{relative(path)}:{target.id}"
                    for target in node.targets
                    if isinstance(target, ast.Name) and LOCATOR_NAME.match(target.id)
                ]
    assert offenders == [], "Locators belong in pages/ or components/"


@pytest.mark.parametrize("folder", ["pages", "components"])
def test_pages_and_components_do_not_depend_on_upper_layers(folder):
    forbidden = ("pages", "tasks", "services", "process", "core.engines")
    offenders = [
        f"{relative(path)} -> {module}"
        for path in python_files(folder)
        for module in imported_modules(path)
        if module.startswith(forbidden) and module != "core.engines.base_engine"
    ]
    assert offenders == [], "Pages/components never import other pages, tasks, services or concrete engines"


def test_tasks_do_not_use_engines_directly():
    offenders = [
        relative(path)
        for path in python_files("tasks")
        if any(module.startswith("core.engines") for module in imported_modules(path))
    ]
    assert offenders == [], "Tasks talk to the browser only through pages/components"


def test_no_absolute_xpath_locators():
    offenders = []
    for path in python_files("pages", "components"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                value = node.value
                if value.startswith("xpath=/") and not value.startswith("xpath=//"):
                    offenders.append(f"{relative(path)}: {value}")
    assert offenders == [], "Never use absolute XPath"
