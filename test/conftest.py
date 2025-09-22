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

"""Pytest fixtures"""

import hashlib
import html
import os
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import pytest
from numpy.random import Generator, SeedSequence, default_rng

if TYPE_CHECKING:
    pass


def pytest_addoption(parser):
    """Add pytest options."""
    parser.addoption("--seed", action="store", default=None, help="Set a global random seed")
    parser.addoption(
        "--save-plots",
        action="store_true",
        help="Whether to save plots that are generated during testing to disk.",
    )
    parser.addoption(
        "--performance-light",
        action="store_true",
        default=False,
        help="Use lighter version of the performance tests for smoke test purposes.",
    )


def pytest_configure(config):
    """Add pytest configuration."""
    # suppress beta warning for the entire test session
    os.environ["SAMPLOMATIC_SUPPRESS_BETA_WARNING"] = "1"


@pytest.fixture(scope="session", autouse=True)
def session_seed(request):
    """Return the base seed for all tests, or None for an OS based seed."""
    user_seed = request.config.getoption("--seed")
    seed = SeedSequence().entropy if user_seed is None else int(user_seed)

    # force print: https://github.com/pytest-dev/pytest/issues/2704#issuecomment-603387680
    with request.config.pluginmanager.getplugin("capturemanager").global_and_fixture_disabled():
        print(f"\nRNG seed used in session: {seed}", flush=True)

    return seed


@pytest.fixture
def rng(session_seed, request) -> Generator:
    """Return an RNG whose seed is a combination of the global seed and the particular test.

    This strategy ensures that tests get the same seed state indpendent of execution order.
    """
    test_id = request.node.nodeid.encode()
    test_seed = int(hashlib.sha256(test_id).hexdigest(), 16) % (2**32)
    return default_rng(seed=(session_seed, test_seed) if session_seed else test_seed)


@pytest.fixture(scope="session")
def maybe_clear_assets():
    """Clear the assets folder if it has not been seen yet in this session."""
    cleared_folders = set()

    def _clear_assets(test_dir):
        assets_dir = test_dir / "assets"
        if assets_dir.exists() and test_dir not in cleared_folders:
            for file in assets_dir.iterdir():
                file.unlink()
            cleared_folders.add(test_dir)

    return _clear_assets


# Track plots and test outcomes globally, where the outer dict is by folder
SAVED_PLOTS = defaultdict(lambda: defaultdict(list))
TEST_STATUSES = defaultdict(dict)


@pytest.fixture
def save_plot(request, maybe_clear_assets):
    """Fixture that saves a figure to disk in an assets folder local to the test."""
    if not request.config.getoption("--save-plots"):
        # early exit if the user has not opted into saving plots to disk
        return lambda *_, **__: None

    test_name = request.node.name
    test_class = request.node.cls.__name__ if request.node.cls else None
    test_params = request.node.callspec.id if hasattr(request.node, "callspec") else None
    full_name = "-".join(filter(None, [test_class, test_name, test_params]))

    test_dir = Path(request.fspath).parent
    assets_dir = test_dir / "assets"
    assets_dir.mkdir(exist_ok=True)
    maybe_clear_assets(test_dir)

    def _save_plot(fig, title=None, delayed=False):
        import plotly.io as pio
        from plotly.graph_objects import Figure as PlotlyFigure

        if delayed:
            fig = fig()

        num_existing = len(SAVED_PLOTS[assets_dir][full_name])
        is_plotly = isinstance(fig, PlotlyFigure)
        filename = f"{full_name}_{num_existing}.{'html' if is_plotly else 'png'}"
        file_path = assets_dir / filename

        if is_plotly:
            pio.write_html(fig, file_path)
        else:
            fig.tight_layout()
            fig.savefig(file_path)

        # We render the figure with matplotlib. `close` avoids memory getting jammed
        plt.close()

        SAVED_PLOTS[assets_dir][full_name].append((filename, title, is_plotly))
        return file_path

    return _save_plot


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Update the test status dictionary."""
    outcome = yield
    result = outcome.get_result()

    if result.when == "call":
        test_class = item.cls.__name__ if item.cls else None
        test_params = item.callspec.id if hasattr(item, "callspec") else None
        full_name = "-".join(filter(None, [test_class, item.name, test_params]))
        assets_dir = Path(item.fspath).parent / "assets"
        TEST_STATUSES[assets_dir][full_name] = result.outcome


def pytest_sessionfinish(session, exitstatus):
    """When all tests are done, write index files to each assets folder."""
    for assets_dir, plot_dict in SAVED_PLOTS.items():
        index_file = assets_dir / "index.html"
        with index_file.open("w", encoding="utf-8") as file:
            file.write("<html><body>\n<h1>Test Artifacts</h1>\n")

            for test_name in plot_dict:
                status = TEST_STATUSES[assets_dir].get(test_name, "unknown")
                color = {"passed": "green", "failed": "red"}.get(status, "gray")
                file.write(f'<div><a href="{html.escape(test_name)}.html" style="color:{color}">')
                file.write(f"<span width='10px'></span> ⬤ {html.escape(test_name)}</a></div>\n")

            file.write("</body></html>\n")

        for test_name, figures in plot_dict.items():
            index_file = assets_dir / f"{test_name}.html"
            with index_file.open("w", encoding="utf-8") as file:
                status = TEST_STATUSES[assets_dir].get(test_name, "unknown")
                color = {"passed": "green", "failed": "red"}.get(status, "gray")
                file.write("<a href='index.html'>UP</a><br />")
                file.write(f"<h1 style='color:{color}'>{html.escape(test_name)}</h1>\n")
                for filename, title, is_plotly in figures:
                    file.write(f"<h3>{html.escape(title or '')}</h3>")
                    if is_plotly:
                        file.write(
                            f'<iframe src="{html.escape(filename)}" width="100%" height="500">'
                            "</iframe><br>\n"
                        )
                    else:
                        file.write(
                            f'<img src="{html.escape(filename)}" style="max-width:100%;"><br>\n'
                        )

                file.write("</body></html>\n")
