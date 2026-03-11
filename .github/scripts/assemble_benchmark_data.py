# This code is a Qiskit project.
#
# (C) Copyright IBM 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Assemble backfilled pytest-benchmark results into ``data.js`` for github-action-benchmark."""

import argparse
import json
import shutil
import subprocess
from pathlib import Path

PREFIX = "window.BENCHMARK_DATA = "


def _git_info(ref: str) -> dict:
    """Return commit metadata for a git ref (tag or SHA)."""
    fmt = "%H%n%s%n%aI%n%an%n%ae"
    result = subprocess.run(
        ["git", "log", "-1", f"--format={fmt}", ref],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = result.stdout.strip().split("\n")
    sha, message, timestamp, author_name, author_email = lines
    return {
        "id": sha,
        "message": message,
        "timestamp": timestamp,
        "url": f"{_get_repo_url()}/commit/{sha}",
        "author": {"name": author_name, "email": author_email, "username": ""},
        "committer": {"name": author_name, "email": author_email, "username": ""},
    }


def _convert_benchmarks(data: dict) -> list[dict]:
    """Convert pytest-benchmark entries to github-action-benchmark format."""
    results = []
    for bench in data.get("benchmarks", []):
        stats = bench["stats"]
        mean_sec = stats["mean"]
        # Convert mean to human-readable units
        if mean_sec < 1e-6:
            mean_str = f"{mean_sec * 1e9:.2f} nsec"
        elif mean_sec < 1e-3:
            mean_str = f"{mean_sec * 1e6:.2f} usec"
        elif mean_sec < 1:
            mean_str = f"{mean_sec * 1e3:.2f} msec"
        else:
            mean_str = f"{mean_sec:.2f} sec"

        results.append(
            {
                "name": bench["fullname"],
                "value": stats["ops"],
                "unit": "iter/sec",
                "range": f"stddev: {stats['stddev']}",
                "extra": f"mean: {mean_str}\nrounds: {stats['rounds']}",
            }
        )
    return results


def _get_repo_url() -> str:
    """Return the normalized HTTPS repo URL."""
    repo_url = subprocess.run(
        ["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=True
    ).stdout.strip()
    if repo_url.startswith("git@"):
        repo_url = repo_url.replace(":", "/").replace("git@", "https://")
    if repo_url.endswith(".git"):
        repo_url = repo_url[:-4]
    return repo_url


def _load_existing_data() -> list[dict]:
    """Fetch existing benchmark entries from gh-pages, if any."""
    result = subprocess.run(
        ["git", "show", "origin/gh-pages:benchmarks/data.js"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    text = result.stdout.strip()
    if not text.startswith(PREFIX):
        return []
    json_str = text[len(PREFIX) :]
    if json_str.endswith(";"):
        json_str = json_str[:-1]
    try:
        data = json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        return []
    return data.get("entries", {}).get("Benchmark", [])


def _discover_refs(mode: str) -> list[str]:
    """Return ordered list of refs to look for in results/."""
    if mode == "commits":
        results_dir = Path("results")
        shas = [p.stem for p in results_dir.glob("*.json")]
        return shas  # ordering doesn't matter; entries are sorted by timestamp after assembly
    else:
        return (
            subprocess.run(
                ["git", "tag", "--sort=creatordate", "--column=never"],
                capture_output=True,
                text=True,
                check=True,
            )
            .stdout.strip()
            .split("\n")
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["tags", "commits"], default="tags")
    args = parser.parse_args()

    results_dir = Path("results")
    output_dir = Path("benchmarks-output")
    output_dir.mkdir(exist_ok=True)

    refs = _discover_refs(args.mode)

    # Build new entries from result files
    new_entries = []
    for ref in refs:
        result_file = results_dir / f"{ref}.json"
        if not result_file.exists():
            continue
        try:
            with open(result_file) as f:
                data = json.load(f)
        except (json.JSONDecodeError, ValueError):
            print(f"Skipping {ref} (invalid JSON)")
            continue
        commit = _git_info(ref)
        benches = _convert_benchmarks(data)
        if benches:
            new_entries.append(
                {
                    "commit": commit,
                    "date": commit["timestamp"],
                    "tool": "pytest",
                    "benches": benches,
                }
            )

    # Merge with existing data from gh-pages, deduplicating by commit SHA
    existing_entries = _load_existing_data()
    existing_shas = {e["commit"]["id"] for e in existing_entries}
    new_shas = {e["commit"]["id"] for e in new_entries}

    merged = [e for e in existing_entries if e["commit"]["id"] not in new_shas] + new_entries
    # Sort by timestamp
    merged.sort(key=lambda e: e.get("date", ""))

    print(
        f"Existing: {len(existing_entries)}, "
        f"new: {len(new_entries)}, "
        f"replaced: {len(existing_shas & new_shas)}, "
        f"merged total: {len(merged)}"
    )

    data_js = {
        "lastUpdate": 0,
        "repoUrl": _get_repo_url(),
        "entries": {"Benchmark": merged},
    }

    with open(output_dir / "data.js", "w") as f:
        f.write(PREFIX)
        json.dump(data_js, f, indent=2)
        f.write(";\n")

    # Copy the custom index.html
    shutil.copy(".github/benchmark-index.html", output_dir / "index.html")

    print(f"Wrote {len(merged)} benchmark entries to {output_dir / 'data.js'}")


if __name__ == "__main__":
    main()
