#!/usr/bin/env python3
"""
nav_gen.py - Generate Zensical nav configuration from folder structure.

Usage:
	python nav_gen.py [config_file] [--write]

	Without --write: prints the nav block to stdout.
	With --write:    replaces the nav block directly in zensical_toml
	                 (configured via zensical_toml key, default: zensical.toml).
"""

import json
import re
import sys
from pathlib import Path

try:
	import tomllib
except ImportError:
	try:
		import tomli as tomllib  # type: ignore
	except ImportError:
		tomllib = None


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_config(config_path: Path) -> dict:
	suffix = config_path.suffix.lower()
	text = config_path.read_text(encoding="utf-8")

	if suffix == ".json":
		return json.loads(text)

	if suffix in (".toml", ""):
		if tomllib is None:
			sys.exit(
				"Error: TOML config requires Python 3.11+ or 'pip install tomli'.\n"
				"Use a .json config file instead."
			)
		return tomllib.loads(text)

	sys.exit(f"Error: unsupported config format '{suffix}' (use .toml or .json)")


# ---------------------------------------------------------------------------
# Docs scanning
# ---------------------------------------------------------------------------

def collect_files(directory: Path, rel_base: Path) -> list[str]:
	"""Return .md file paths relative to docs_dir, index.md first."""
	files = []
	for entry in sorted(directory.iterdir()):
		if entry.is_file() and entry.suffix == ".md":
			files.append(str(entry.relative_to(rel_base)))

	def sort_key(p):
		name = Path(p).name.lower()
		return (0 if name in ("index.md", "readme.md") else 1, p)

	return sorted(files, key=sort_key)


def build_nav_entry(folder: Path, display_name: str, docs_dir: Path, depth: int) -> dict | str:
	items = []

	for md in collect_files(folder, docs_dir):
		items.append(md)

	for entry in sorted(folder.iterdir()):
		if entry.is_dir():
			sub_entry = build_nav_entry(entry, entry.name, docs_dir, depth + 1)
			items.append(sub_entry)

	if not items:
		return display_name

	return {display_name: items}


def build_nav(docs_dir: Path, categories: dict[str, str], order: list[str] | None, exclude: set[str] | None = None) -> list:
	nav = []

	root_index = docs_dir / "index.md"
	if root_index.exists():
		nav.append("index.md")

	exclude = exclude or set()

	top_level_dirs = sorted(
		[e for e in docs_dir.iterdir() if e.is_dir() and e.name not in exclude],
		key=lambda e: e.name,
	)

	if order:
		ordered = []
		seen = {d.name for d in top_level_dirs}
		for name in order:
			if name in seen:
				ordered.append(docs_dir / name)
		mentioned = set(order)
		for d in top_level_dirs:
			if d.name not in mentioned:
				ordered.append(d)
		top_level_dirs = ordered

	for folder in top_level_dirs:
		display_name = categories.get(folder.name, folder.name)
		entry = build_nav_entry(folder, display_name, docs_dir, depth=1)
		nav.append(entry)

	return nav


# ---------------------------------------------------------------------------
# TOML rendering
# ---------------------------------------------------------------------------

def toml_string(s: str) -> str:
	s = s.replace("\\", "\\\\").replace('"', '\\"')
	return f'"{s}"'


def render_nav_item(item, indent: int) -> str:
	pad = "\t" * indent

	if isinstance(item, str):
		return f"{pad}{toml_string(item)}"

	if isinstance(item, dict):
		assert len(item) == 1
		key, value = next(iter(item.items()))

		if isinstance(value, list):
			inner = ",\n".join(render_nav_item(v, indent + 1) for v in value)
			return f"{pad}{{{toml_string(key)} = [\n{inner}\n{pad}]}}"

		if isinstance(value, str):
			return f"{pad}{{{toml_string(key)} = {toml_string(value)}}}"

	raise TypeError(f"unexpected nav item type: {type(item)}")


def render_nav(nav: list) -> str:
	lines = ["nav = ["]
	for i, item in enumerate(nav):
		comma = "," if i < len(nav) - 1 else ""
		lines.append(render_nav_item(item, indent=1) + comma)
	lines.append("]")
	return "\n".join(lines)


# ---------------------------------------------------------------------------
# In-place replacement in zensical.toml
# ---------------------------------------------------------------------------

# Matches the start of a nav block, active or commented out.
_NAV_START = re.compile(r"^(\s*#\s*)?nav\s*=\s*\[")


def find_nav_block(lines: list[str]) -> tuple[int, int] | None:
	"""
	Return (start_idx, end_idx) of the nav block in lines (both inclusive),
	or None if no nav block is found.

	Handles:
	  - Single-line:  nav = ["a.md", "b.md"]
	  - Multi-line:   nav = [\n  ...\n]
	  - Commented:    # nav = ["a.md"]
	"""
	for i, line in enumerate(lines):
		if not _NAV_START.match(line):
			continue

		# Count brackets to find where the block ends.
		depth = 0
		for j, scan_line in enumerate(lines[i:], i):
			# Only count unquoted brackets. Since nav values are paths and
			# display names (no brackets expected in them), a simple count works.
			depth += scan_line.count("[") - scan_line.count("]")
			if depth <= 0:
				return (i, j)

	return None


def write_nav_to_toml(toml_path: Path, nav_text: str) -> None:
	lines = toml_path.read_text(encoding="utf-8").splitlines(keepends=True)
	block = find_nav_block(lines)

	if block is None:
		sys.exit(
			f"Error: no nav block found in {toml_path}.\n"
			"Add 'nav = []' (or a commented '# nav = []') to mark the insertion point."
		)

	start, end = block
	replacement = nav_text + "\n"
	new_lines = lines[:start] + [replacement] + lines[end + 1:]
	toml_path.write_text("".join(new_lines), encoding="utf-8")
	print(f"Updated nav in {toml_path}  ({end - start + 1} lines → {nav_text.count(chr(10)) + 1} lines)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
	args = sys.argv[1:]
	write_mode = "--write" in args
	args = [a for a in args if a != "--write"]

	config_path = Path(args[0]) if args else Path("nav_gen.toml")

	if not config_path.exists():
		sys.exit(f"Error: config file not found: {config_path}")

	cfg = load_config(config_path)

	docs_dir = Path(cfg.get("docs_dir", "docs"))
	if not docs_dir.is_absolute():
		docs_dir = config_path.parent / docs_dir

	if not docs_dir.exists():
		sys.exit(f"Error: docs_dir not found: {docs_dir}")

	categories: dict[str, str] = cfg.get("categories", {})
	order: list[str] | None = cfg.get("order", None)
	exclude: set[str] = set(cfg.get("exclude", []))

	nav = build_nav(docs_dir, categories, order, exclude)
	nav_text = render_nav(nav)

	if write_mode:
		toml_path = Path(cfg.get("zensical_toml", "zensical.toml"))
		if not toml_path.is_absolute():
			toml_path = config_path.parent / toml_path
		write_nav_to_toml(toml_path, nav_text)
	else:
		print(nav_text)


if __name__ == "__main__":
	main()
