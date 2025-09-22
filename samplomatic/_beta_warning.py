# This code is a Qiskit project.
#
# (C) Copyright IBM 2025.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


from __future__ import annotations

import json
import os
import warnings
from pathlib import Path
from typing import Any

ENV_VAR_SUPPRESS = "SAMPLOMATIC_SUPPRESS_BETA_WARNING"
WARNED_VERSIONS_KEY = "warned_versions"


def warn_once_per_version(message: str, *, version_str: str, suppress_for_devs: bool):
    """Emit a warning once per installed version of the package.

    Persistence is tracked via a small JSON file under the user's state/home directory.
    Best-effort I/O: failures reading/writing the file will not break import.

    Args:
        message: The message to warn with.
        version_str: The version at hand.
        suppress_for_devs: Whether to supress the warning when the version is a dev version.
    """
    try:
        if _is_suppressed_by_env_variable():
            return
        if suppress_for_devs and version_str.split(".")[-1].startswith("dev"):
            return

        config_path = _get_config_path()
        config_data = _read_config(config_path)

        if version_str in (warned_versions := set(config_data.get(WARNED_VERSIONS_KEY, []))):
            return

        # use stacklevel=2 so the import site appears in the traceback, not this helper.
        warnings.warn(message, category=UserWarning, stacklevel=2)

        # record that we've warned for this version
        warned_versions.add(version_str)
        config_data[WARNED_VERSIONS_KEY] = sorted(warned_versions)
        _update_config(config_path, config_data)

    except Exception:
        # never block import due to warning machinery
        pass


def _get_config_path() -> Path:
    """Determine the path of the config file."""
    try:
        if os.name != "nt":
            # Posix: XDG then .home()
            xdg = os.environ.get("XDG_STATE_HOME")
            base = Path(xdg) if xdg else Path.home() / ".local" / "state"
            path = base / "samplomatic" / "config.json"
        else:
            # Windows: LOCALAPPDATA preferred, then APPDATA, then .home()
            app_data = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
            base = Path(app_data or str(Path.home()))
        path = base / "samplomatic" / "config.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    except Exception:
        # last-resort fallback directly in home directory (hidden-ish file)
        return Path.home() / ".samplomatic-config.json"


def _read_config(path: Path) -> dict[str, Any]:
    """Read and return the content of the config file."""
    try:
        if not path.exists():
            return {}
        raw = path.read_text(encoding="utf-8")
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def _update_config(path: Path, data: dict[str, Any]) -> None:
    """Update the config with a new value."""
    try:
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        # on POSIX, this is atomic; on Windows it's best-effort, may require removing first.
        try:
            tmp_path.replace(path)
        except Exception:
            # Windows fallback
            if path.exists():
                try:
                    path.unlink()
                except Exception:
                    pass
            tmp_path.replace(path)
    except Exception:
        # swallow errors to avoid breaking import
        pass


def _is_suppressed_by_env_variable() -> bool:
    """Whether warning emission is supressed by an env var."""
    if (val := os.environ.get(ENV_VAR_SUPPRESS)) is None:
        return False
    return val.strip().lower() in {"1", "true", "yes", "on"}
