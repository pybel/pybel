[doc("run unit and integration tests")]
test:
    # See the [dependency-groups] entry in pyproject.toml for "tests"
    just coverage erase
    # TODO do something sneaky with installing the PYBEL_TEST_CONNECTOR as a dependency?
    uv run --group tests --all-extras -m coverage run -p -m pytest
    just coverage combine
    just coverage report
    just coverage html

[doc("remove testing coverage artifacts")]
coverage-clean:
    just coverage erase

coverage-report:
    just coverage report

[doc("run `coverage` with a given subcommand")]
@coverage command:
    uvx --from coverage[toml] coverage {{command}}

# Note that the package name is required for discovery
[doc("test that documentation examples run properly")]
doctests:
    uv run --group doctests --all-extras xdoctest -m \
        src/pybel/struct/summary \
        src/pybel/struct/filters \
        src/pybel/struct/mutation \
        src/pybel/struct/graph.py
    # TODO enable on all files

[doc("test that notebooks can be run to completion")]
treon:
    uv run treon

[doc("format code")]
format:
    # Note that ruff check should come before ruff format when using --fix (ref: https://github.com/astral-sh/ruff-pre-commit/blob/main/README.md)
    uvx ruff check --fix
    uvx ruff format

[doc("format documentation")]
format-docs:
    # note that this doesn't work with sphinx-click
    # or any other extension that adds extra directives
    # See the [dependency-groups] entry in pyproject.toml for "rstfmt"
    uv run --group format-docs docstrfmt src/ tests/ docs/ --no-docstring-trailing-line

[doc("format documentation")]
format-markdown:
    npx --yes prettier --write --prose-wrap always "**/*.md"

[doc("check code quality")]
lint:
    uvx ruff check
    uvx ruff format --check

[doc("check markdown is properly formatted")]
lint-markdown:
    # inspired by https://github.com/astral-sh/uv/blob/98523e2014e9a5c69706623344026d76296e178f/.github/workflows/ci.yml#L67C1-L70C61
    npx --yes prettier --check --prose-wrap always "**/*.md"

[doc("check justfile is properly formatted")]
lint-justfile:
    just --fmt --unstable

[doc("run the pyroma tool to check the package friendliness of the project")]
pyroma:
    uv run --group pyroma pyroma --min=10 .

[doc("run static type checking with mypy")]
mypy:
    uv run --group typing --all-extras mypy --ignore-missing-imports --strict src/
    # TODO enable on tests/

[doc("run static type checking with ty")]
ty:
    uv run --group typing --all-extras ty check src/ tests/

[doc("run the doc8 tool to check the style of the RST files in the project docs")]
docs-lint:
    uv run --group docs-lint doc8 docs/source/

[doc("run the docstr-coverage tool to check documentation coverage")]
docstr-coverage:
    uvx docstr-coverage src/ tests/ --skip-private --skip-magic

[doc("build the documentation locally")]
docs:
    uv run --group docs --all-extras -m sphinx -b html -d docs/build/doctrees docs/source docs/build/html

[doc("test building the documentation locally. warnings are considered as errors via -W")]
docs-test:
    #!/usr/bin/env bash
    set -euo pipefail
    tmpdir=$(mktemp -d)
    cp -r docs/source "$tmpdir/source"
    uv run --group docs --all-extras -m sphinx -W -b html -d "$tmpdir/build/doctrees" "$tmpdir/source" "$tmpdir/build/html"
    rm -rf "$tmpdir"

####################
# Deployment tools #
####################

[doc("run `bumpversion` with a given subcommand")]
@bumpversion command:
    uvx bump-my-version bump {{command}}

[doc("make a release")]
bumpversion-release:
    uvx bump-my-version bump release --tag

[doc("build an sdist and wheel")]
build:
    uv build --sdist --wheel --clear

############
# Releases #
############

# In order to make a release to PyPI, you'll need to take the following steps:
#
# 1. Navigate to https://pypi.org/account/register/ to register for Test PyPI
# 2. Navigate to https://pypi.org/manage/account/ and request to re-send a verification email.
#    This is not sent by default, and is required to set up 2-Factor Authentication.
# 3. Get account recovery codes
# 4. Set up 2-Factor Authentication
# 5. Get an API token from https://pypi.org/manage/account/token/
# 6. Install keyring with `uv tool install keyring`
# 7. Add your token to keyring with `keyring set https://upload.pypi.org/legacy/ __token__`

[doc("Release the code to PyPI so users can pip install it, using credentials from keyring")]
release:
    just build
    uv tool install --quiet keyring
    uv publish --username __token__ --keyring-provider subprocess --publish-url https://upload.pypi.org/legacy/

[doc("Release the code to PyPI so users can pip install it, using credentials from the environment.")]
release-via-env:
    just build
    uv publish --publish-url https://upload.pypi.org/legacy/

[doc("Run a workflow that removes -dev from the version, creates a tagged release on GitHub, creates a release on PyPI, and bumps the version again.")]
finish:
    just bumpversion-release
    just release
    git push --tags
    uvx bump-my-version bump patch
    git push

#################
# Test Releases #
#################

# In order to test making a release to Test PyPI, you'll need to take the following steps:
#
# 1. Navigate to https://test.pypi.org/account/register/ to register for Test PyPI
# 2. Navigate to https://test.pypi.org/manage/account/ and request to re-send a verification email.
#    This is not sent by default, and is required to set up 2-Factor Authentication.
# 3. Get account recovery codes
# 4. Set up 2-Factor Authentication
# 5. Get an API token from https://test.pypi.org/manage/account/token/
# 6. Install keyring with `uv tool install keyring`
# 7. Add your token to keyring with `keyring set https://test.pypi.org/legacy/ __token__`

[doc("Release the code to the test PyPI site")]
test-release:
    just build
    uv tool install --quiet keyring
    uv publish --username __token__ --keyring-provider subprocess --publish-url https://test.pypi.org/legacy/

[doc("Run a workflow that removes -dev from the version, creates a tagged release on GitHub, creates a release on Test PyPI, and bumps the version again.")]
test-finish:
    just bumpversion-release
    just test-release
    git push --tags
    uvx bump-my-version bump patch
    git push
