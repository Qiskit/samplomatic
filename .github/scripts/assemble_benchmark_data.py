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

import json
import shutil
import subprocess
from pathlib import Path


def _git_info(tag: str) -> dict:
    """Return commit metadata for a git tag."""
    fmt = "%H%n%s%n%aI%n%an%n%ae"
    result = subprocess.run(
        ["git", "log", "-1", f"--format={fmt}", tag],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = result.stdout.strip().split("\n")
    sha, message, timestamp, author_name, author_email = lines
    repo_url = subprocess.run(
        ["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=True
    ).stdout.strip()
    # Normalize git@ URLs to https
    if repo_url.startswith("git@"):
        repo_url = repo_url.replace(":", "/").replace("git@", "https://")
    if repo_url.endswith(".git"):
        repo_url = repo_url[:-4]
    return {
        "id": sha,
        "message": message,
        "timestamp": timestamp,
        "url": f"{repo_url}/commit/{sha}",
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


def main():
    results_dir = Path("results")
    output_dir = Path("benchmarks-output")
    output_dir.mkdir(exist_ok=True)

    # Discover tags sorted by creation date (same order used in backfill loop)
    tag_order = (
        subprocess.run(
            ["git", "tag", "--sort=creatordate", "--column=never"],
            capture_output=True,
            text=True,
            check=True,
        )
        .stdout.strip()
        .split("\n")
    )

    # Build ordered list of entries from available result files
    entries = []
    for tag in tag_order:
        result_file = results_dir / f"{tag}.json"
        if not result_file.exists():
            continue
        with open(result_file) as f:
            data = json.load(f)
        commit = _git_info(tag)
        benches = _convert_benchmarks(data)
        if benches:
            entries.append(
                {
                    "commit": commit,
                    "date": commit["timestamp"],
                    "tool": "pytest",
                    "benches": benches,
                }
            )

    # Get repo URL for data.js metadata
    repo_url = subprocess.run(
        ["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=True
    ).stdout.strip()
    if repo_url.startswith("git@"):
        repo_url = repo_url.replace(":", "/").replace("git@", "https://")
    if repo_url.endswith(".git"):
        repo_url = repo_url[:-4]

    data_js = {
        "lastUpdate": 0,
        "repoUrl": repo_url,
        "entries": {"Benchmark": entries},
    }

    with open(output_dir / "data.js", "w") as f:
        f.write("window.BENCHMARK_DATA = ")
        json.dump(data_js, f, indent=2)
        f.write(";\n")

    # Copy the custom index.html
    shutil.copy(".github/benchmark-index.html", output_dir / "index.html")

    print(f"Assembled {len(entries)} benchmark entries into {output_dir / 'data.js'}")


if __name__ == "__main__":
    main()
