![Samplomatic](assets/samplomatic.svg)

_Serving all of your circuit sampling needs since 2025._

> [!NOTE]
> This library is in an early stage of development where things are changing fast and in breaking ways. You probably don't want to depend on it yet, but we hope you stick around and check it out.

Samplomatic is a library that helps you sample randomizations of your quantum circuits in exactly the way that you specify.
Pauli twirling a static circuit will be the first milestone, but the possible types of sampling will be extensible by design—we hope that you will contribute your own weird groups!
This library will also not be specific to twirling, though a primary use-case, it will also support ideas like sample-based noise injection, like used in PEC.

## Installation

You can install Samplomatic via pip:

```bash
pip install .
```

For visualization support, include the visualization dependencies:

```bash
pip install ".[vis]"
```

Developers should install in editable mode with the development requirements:

```bash
pip install -e ".[dev,vis]"
```

## Development

### Testing

Testing is done with `pytest` and tests are located in the `test` folder:

```bash
pytest
```

### Performance tests

The performance tests in `test/performance` are implemented using the `pytest-benchmark` plugin and its `benchmark` fixture ([User Guide](https://pytest-benchmark.readthedocs.io/en/latest/index.html)). To run the performance test, use the command:
``` bash
pytest test/benchmarks
```
Upon successful completion, they provide exaustive statistics about the runtime of the benchmarked lines of code.

`pytest-benchmark` provides useful flags, such as:

* `benchmark-time-unit=COLUMN`: Unit to scale the results to. Available units: `ns`, `us`, `ms`, `s`.

* `benchmark-json=PATH`: Dump a JSON report into `PATH`.

* `--benchmark-compare=PATH`: Compare the current run against the json results stored in `PATH`. Fail test if the performance has regressed.

* `benchmark-compare-fail=EXPR`: Fail test if performance regresses according to given `EXPR`, e.g. `min:5% `or `mean:0.001`. To be used in conjunction with `--benchmark-compare`.

Additionally, `pytest-benchmark` supports a CLI to list and compare past runs.

``` bash
# List the saved benchmarks
pytest-benchmark list

# Generate SVG files to compare past plots saved in `PATH`.
# Note: `pip install pygal pygaljs` is required for plotting.
pytest-benchmark compare PATH --histogram --group-by=name
```

### Linting and Formatting

`ruff` is used for linting and formatting. Run the following to manually apply checks:

```bash
ruff check .
```

More conveniently, set up ruff in your IDE to run-on-save.

### Pre-commit Hooks

It is recommended that contributers install and use `pre-commit` to ensure code quality and consistency in this library.
It automatically runs linters and formatters on staged files during `git commit`.

1. Install the hooks defined in the .pre-commit-config.yaml file:

```bash
pre-commit install
```

2. Test the hooks on all files (optional):

```bash
pre-commit run --all-files
```

3. To update the pre-commit hooks to their latest versions, run:

```bash
pre-commit autoupdate
```

### VSCode Setup

Optionally, paste these into your `.vscode/settings.json` to set up ruff (you also need to install the ruff VSCode extension) and the test suite:

```json
{
    "python.testing.pytestArgs": [
        "test"
    ],
    "python.testing.unittestEnabled": false,
    "python.testing.pytestEnabled": true,
    "[python]": {
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
        "source.fixAll": "explicit",
        "source.organizeImports": "explicit"
        },
        "editor.defaultFormatter": "charliermarsh.ruff"
    }
}
```

### Generating `sphinx` documentation

`samplomatic` documentation can be rendered via `sphinx`. In order to produce the rendered
documentation:

1. Install samplomatic with the [development requirements](#installation)
2. Regenerate the API stubs:
    ```bash
    $ cd docs/
    docs$ make apidocstubs
    ```
3. Update the API documentation index at `docs/index.rst` if you added a new module (the contents
   of the toc tree should match the listing of the `docs/apidocs` directory).
4. Build the documentation:
    ```bash
    docs$ make html
    ```

The `.html` documentation will be rendered at `docs/_build` (with the index being available at
`docs/_build/html/index.html`).

### Adding to the changelog

We use [Towncrier](https://towncrier.readthedocs.io/) for changelog management.
All PRs that make a changelog-worthy change should add a changelog entry.
To do this, supposing your PR is `#42`, create a [new fragment](https://towncrier.readthedocs.io/en/stable/tutorial.html#creating-news-fragments) file in the `changelog.d/` directory:

```bash
towncrier create -c "Added a cool feature!" 42.added.md
```

### Releasing a version

To release a new version `1.2.3`:

```bash
./assets/release.sh 1.2.3  # use the new version as an argument. this:
                           #  - checks out a new branch release-1.2.3
                           #  - calls towncrier to prepend to CHANGELOG
                           #  - commits this change in a new commit

git push origin release-1.2.3
```

Merge the PR into `main` and then use the GitHub UI to create a new release, copying the new changelog section into the body.
This will trigger a job to publish to PyPI.
