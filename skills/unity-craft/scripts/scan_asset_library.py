#!/usr/bin/env python3
"""
scan_asset_library.py — Scan local Unity Asset Store cache for inventory.

Purpose:
  Builds a structured JSON inventory of all .unitypackage files in the user's
  Unity Asset Store-5.x cache directory. Parses concatenated category strings
  (e.g., "3D ModelsEnvironmentsFantasy") into {category, subcategory} pairs.
  Used by Assets_ScanLibrary tool to power asset recommendation pipelines.

Usage:
  scan_asset_library.py [--output-json PATH] [--refresh]

Output (stdout or file):
  {
    "scanned_at": "2026-04-18T14:30:22Z",
    "cache_root": "/Users/username/Library/Unity/Asset Store-5.x/",
    "publisher_count": 62,
    "package_count": 1847,
    "publishers": [...]
  }

Cache: .unity-craft/asset-cache.json
Dependencies: stdlib only (os, json, argparse, pathlib, datetime)
"""

import argparse
import datetime
import json
import os
import sys
from pathlib import Path

# Known category prefixes (longest match wins)
CATEGORY_TAXONOMY = [
    "3D Models",
    "2D",
    "Animation",
    "Audio",
    "Complete Projects",
    "Editor Extensions",
    "Essentials",
    "GUI Skins",
    "Particle Systems",
    "Props",
    "Scripting",
    "Services",
    "Shaders",
    "Templates",
    "Textures Materials",
    "Tools",
    "VFX",
    "Add-Ons",
    "Environments",
    "Characters",
]


def find_cache_root():
    """Locate Asset Store cache directory (macOS or Windows)."""
    home = Path.home()

    # macOS
    macos_path = home / "Library" / "Unity" / "Asset Store-5.x"
    if macos_path.exists():
        return macos_path

    # Windows
    appdata = os.getenv("APPDATA")
    if appdata:
        win_path = Path(appdata) / "Unity" / "Asset Store-5.x"
        if win_path.exists():
            return win_path

    return None


def parse_category_subcategory(category_dir):
    """
    Parse concatenated category string from directory name.
    Longest taxonomy prefix wins; rest becomes subcategory.
    Returns (category, subcategory) or (None, None) if no match.
    """
    category_dir_str = str(category_dir)

    # Match longest prefix
    matched_category = None
    for prefix in sorted(CATEGORY_TAXONOMY, key=len, reverse=True):
        if category_dir_str.startswith(prefix):
            matched_category = prefix
            break

    if not matched_category:
        return None, None

    # Rest becomes subcategory
    subcategory = category_dir_str[len(matched_category):]
    if not subcategory:
        subcategory = None

    return matched_category, subcategory


def scan_library(refresh=False, cache_path=None):
    """
    Scan Asset Store cache and return inventory dict.
    If refresh=False and cache_path is <24h old, return cached result.
    """
    cache_root = find_cache_root()
    if not cache_root or not cache_root.exists():
        return {"error": "cache_not_found", "message": "Asset Store cache directory not found"}

    # Check cache
    if not refresh and cache_path:
        try:
            cache_path = Path(cache_path)
            if cache_path.exists():
                file_mtime = datetime.datetime.fromtimestamp(cache_path.stat().st_mtime, tz=datetime.timezone.utc)
                age = datetime.datetime.now(datetime.timezone.utc) - file_mtime
                if age < datetime.timedelta(hours=24):
                    with open(cache_path) as f:
                        return json.load(f)
        except Exception:
            pass  # Fall through to scan

    # Scan
    scanned_at = datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z"
    publishers = {}
    package_count = 0

    # Iterate publisher dirs
    for publisher_dir in sorted(cache_root.iterdir()):
        if not publisher_dir.is_dir():
            continue

        publisher_name = publisher_dir.name
        publisher_packages = []

        # Iterate category subdirs (concatenated category+subcategory)
        for category_dir in publisher_dir.iterdir():
            if not category_dir.is_dir():
                continue

            category_name, subcategory_name = parse_category_subcategory(category_dir.name)
            if category_name is None:
                continue

            # List .unitypackage files
            for pkg_file in category_dir.glob("*.unitypackage"):
                size_bytes = pkg_file.stat().st_size
                last_modified = datetime.datetime.fromtimestamp(
                    pkg_file.stat().st_mtime, tz=datetime.timezone.utc
                ).isoformat() + "Z"

                pkg_name = pkg_file.stem  # filename without .unitypackage

                publisher_packages.append({
                    "publisher": publisher_name,
                    "category": category_name,
                    "subcategory": subcategory_name,
                    "name": pkg_name,
                    "path": str(pkg_file.absolute()),
                    "sizeBytes": size_bytes,
                    "lastModified": last_modified,
                })
                package_count += 1

        # Sort packages by lastModified descending
        publisher_packages.sort(key=lambda p: p["lastModified"], reverse=True)

        if publisher_packages:
            publishers[publisher_name] = publisher_packages

    # Sort publishers alphabetically
    sorted_publishers = []
    for pub_name in sorted(publishers.keys()):
        sorted_publishers.append({
            "publisher": pub_name,
            "packages": publishers[pub_name],
        })

    return {
        "scanned_at": scanned_at,
        "cache_root": str(cache_root.absolute()),
        "publisher_count": len(publishers),
        "package_count": package_count,
        "publishers": sorted_publishers,
    }


def main():
    parser = argparse.ArgumentParser(description="Scan Unity Asset Store local cache")
    parser.add_argument("--output-json", type=str, default=None,
                        help="Output file path (default: stdout)")
    parser.add_argument("--refresh", "--force", action="store_true",
                        help="Force refresh — bypass 24h cache (also accepted as --force)")

    args = parser.parse_args()

    # Determine cache file path
    cache_file = None
    if not args.refresh:
        home = Path.home()
        unity_craft_dir = home / ".unity-craft"
        unity_craft_dir.mkdir(exist_ok=True)
        cache_file = unity_craft_dir / "asset-cache.json"

    result = scan_library(refresh=args.refresh, cache_path=cache_file)

    # Write result
    result_json = json.dumps(result, indent=2)

    if args.output_json:
        with open(args.output_json, "w") as f:
            f.write(result_json)
        print(f"Cache written to {args.output_json}", file=sys.stderr)
    else:
        print(result_json)


if __name__ == "__main__":
    main()
