<!--
SPDX-FileCopyrightText: 2021 - 2023  StorPool <support@storpool.com>
SPDX-License-Identifier: BSD-2-Clause
-->

# Changelog

All notable changes to the sp-variant project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.5.3] - 2025-02-06

### Additions

- all:
    - add support for Oracle 9

## [3.5.2] - 2024-06-03

### Additions

- all:
    - fix Oracle 8 support

## [3.5.1] - 2024-05-28

### Additions

- all:
    - add support for Oracle 8

## [3.5.0] - 2024-04-03

### Semi-incompatible changes

- use Python 3.x as `min_sys_python` everywhere
- drop the definitions for CentOS 6, Debian 9, Ubuntu 16.04, and Ubuntu 23.04;
  they will no longer even be recognized

### Fixes

- mark Debian 10 as unsupported
- documentation:
    - correct the changelog link for version 3.4.2
- python:
    - library:
        - re-sort the `sp_variant.variant.__all__` list
    - test suite:
        - do not expect Debian 9 and CentOS 6 to be present in the variant data
        - update the `test-stages` requirements file to use Tox 4.x

### Additions

- all:
    - add support for Ubuntu 24.04 (Noble Numbat)
- documentation:
    - add `publync` configuration to the `pyproject.toml` file
- python:
    - tentatively declare Python 3.13 as supported

### Other changes

- documentation:
    - use `mkdocstrings` 0.24 with no changes
- python:
    - test suite:
        - run the unit tests with pytest 6, 7, and 8, separately
        - test with Ruff 0.3.4:
            - simplify the Ruff configuration files layout
            - override some more checks
            - push the linter configuration into the `lint.*` TOML hierarchy
            - use the concise output format even in preview mode
            - let Ruff insist on trailing commas
        - add the "docs" environment to the second Tox stage
        - vendor-import `vetox` version 0.1.3
- rust:
    - use the `clap_derive` and `serde_derive` crates instead of features for
      the respective `clap` and `serde` ones
    - minor fixes and improvements suggested by Clippy
- nix:
    - remove an explanation for not running the Tox tests with Python 3.8;
      it was dropped from nixpkgs/unstable anyway
    - also run the Tox tests with Python 3.12
    - add an expression and a shell helper to run `vetox` with Python 3.9 through 3.13

## [3.4.2] - 2023-12-19

### Other changes

- python:
    - use Ruff 0.1.8 for testing with no changes
    - use Ruff instead of Black for source code formatting
    - drop the Tox `requires` specification for `test-stages`: recent
      versions of the `tox-stages` tool autodetect the need for that
    - consistently pass `--` before positional arguments in commands
      invoked by Tox
    - move the "reuse" test to the first Tox stage
- rust:
    - refresh the `Cargo.lock` file

## [3.4.1] - 2023-10-18

### Fixes

- all:
    - remove the duplicate builder definition for `centos/9`; switching to
      CentOS Stream 9 means that the AlmaLinux 9 one must be dropped
- docs:
    - use a more descriptive heading for the Python API reference

### Additions

- python:
    - add some unit tests for the `builder` attribute of the variants data
    - use Ruff 0.1.0 for testing with minor adaptations of the configuration
    - sync some docstrings with the ones used in the Rust implementation
    - add some more docstrings

## [3.4.0] - 2023-10-03

### Additions

- all:
    - add CentOS Stream 9 as an unsupported distribution

### Other changes

- rust:
    - specify the features of the `nix` crate that we use ("fs" and "user")

## [3.3.0] - 2023-10-02

### Fixes

- python:
    - do not pass the `python_version` parameter to mypy, we have other ways of
      testing with different Python versions
- rust:
    - output a newline character in `storpool_variant show all`

### Additions

- add a Nix expression for running the Python Tox tests
- add a Nix expression for building the Rust implementation
- python:
    - add 3.12 to the list of supported Python versions
- rust:
    - expose `Variant.supported.repo` as a public struct member

### Other changes

- python:
    - drop the `cfg-diag` dependency for the `sp_build_repo` and
      `test_docker` utilities, use Python's `logging` library directly
    - also run the "format" environment in the first Tox stage
    - use reuse 2.x for testing with no changes
    - bump the black version dependency to 23.7 for "py312" support
    - convert the `tox.ini` file to the Tox 4.x format:
        - add backslashes for line continuation in multiline variables
        - add a `minversion` specification and set it to 4.1
        - add a `requires` specification and list `test-stages` so that
          it may be installed within the bootstrapped Tox environment to
          make it possible to be run from the outside
- rust:
    - bump MSRV to 1.64 to unbreak the compilation now that we may pull
      clap >= 4.3 in as a dependency
    - use the clippy tool from Rust 1.72:
        - note the clippy version in a code comment in the `run-clippy.sh` file
        - allow the use of raw strings for the detection regular expressions,
          those are almost free-form and they may contain special characters
        - rename a single-character variable to a more descriptive name
        - allow single-call functions, we break some of those out for clarity

## [3.2.3] - 2023-08-24

### Fixes

- data:
    - look for "almalinux" instead of "alma" in the `ID` field of the `os-release` file
    - catch up with the renaming of the powertools repository to CodeReadyBuilder in
      AlmaLinux 9.x and the like

### Other changes

- python:
    - use Ruff 0.0.285 in the test suite:
        - override a warning related to the `Config.diag_to_stderr` weirdness
    - use MyPy 1.5 in the test suite:
        - override an "arguments too generic" check for a `NamedTuple` initialization
- rust:
    - let clippy know that we do use the `ref` keyword

## [3.2.2] - 2023-07-06

### Fixes

- docs:
    - fix the 3.2.1 GitHub commit log URL

### Additions

- docs:
    - add a navigational bar-like list of URLs at the top of the index page
    - use a link reference for the StorPool support team e-mail address
- python:
    - add the repo.storpool.com URL as the project homepage, keep the GitHub one as
      "Source Code"

## [3.2.1] - 2023-07-06

### Fixes

- python:
    - drop the unneeded `hatch-requirements-txt` PEP 517 build dependency

## [3.2.0] - 2023-07-06

### Fixes

- data:
    - drop the `Architectures` line from the Debian sources list file so that
      `add-storpool-repo` can also be used on arm64 hosts
    - mark Debian 9.x (stretch) as no longer supported
    - drop the `mcelog` package definition for Debian, it was only ever
      present in the unsupported Debian 9.x and Ubuntu 16.04
    - refer to the OpenSSL 3.x package for Debian unstable and Ubuntu 22.04
    - reflect the removal of the `libcgroup-tools` and `python2-simplejson`
      packages in CentOS 9.x
    - add a 0644 default to the `--mode` argument of `sp_build_repo.subst`
- python:
    - add a no-op `_diag_to_stderr` property setter to avoid mypy errors on
      (wrong, deprecated) attempts to set that field. Those attempts are
      ignored anyway since the changes in version 3.1.2, but let mypy know
      that they are still not completely forbidden.

### Additions

- data:
    - add Debian 12.x (bookworm), mark Debian unstable as Debian 13.x (trixie)
    - add Ubuntu 23.04 (Lunar Lobster) as an unsupported variant
- docs:
    - add a raw Python API reference
- python:
    - install the OS packages defined for each variant during the Docker test
- rust:
    - add the `get_all_variants()` and `get_all_variants_in_order()`
      functions that return all known StorPool build variants
    - derive `Copy` for some structs and enums
    - derive `PartialEq` and `Eq` for most structs
    - allow the Makefile Rust build infrastructure to not pass the `--offline`
      option to Cargo if the `NO_CARGO_OFFLINE` environment variable is set
    - run the Cargo tests in the Makefile `test` target

### Other changes

- data:
    - drop the definitions for the temporary, intermediate, non-LTS
      Ubuntu 21.10 version
- docs:
    - point to version 1.1.0 of the "Keep a Changelog" specification
- python:
    - switch from `setuptools` to `hatchling` for the PEP 517 build
    - use Ruff 0.0.277 in the test suite:
        - override some checks related to the use of the `subprocess` library
        - override a "too many parameters" check for the click-decorated main
          function of `sp_build_repo`
        - globally disable the "performance penalty for try/except in loops" check;
          we want our exceptions to provide as much context as possible, including
          the values of the loop variables
    - pin the Ruff version to avoid failures due to newly-added future checks
    - use Ruff's isort implementation to format the source files and
      rename the `black` and `black-reformat` Tox testing environments to
      `format` and `reformat` respectively
    - hide some imports behind `TYPE_CHECKING` checks
    - use `ClassVar` as needed for singleton data holder classes
    - narrow down the "run Ruff" stage specification in the `test-stages` definition
    - drop the `flake8` and `pylint` Tox test environments, rely on Ruff
    - use `click.Path` in `sp_build_repo` and `test_docker`
- rust:
    - import the `VariantError` struct directly in the test suite

## [3.1.2] - 2023-03-17

### Semi-incompatible changes

- python:
    - deprecate the `defs.Config._diag_to_stderr` member variable;
      replace it with a read-only property that always returns true and
      a `__setattr__()` override that detects and ignores attempts to
      modify it. Both will be removed in a future version of sp-variant.

### Additions

- python:
    - add some more PyPI trove classifiers to the setuptools metadata
    - break out the Tox environments' dependencies into separate files so
      that they may be reused by external tools
    - `test_docker`: allow multiple `-i imagepattern` options to be
      specified so that several unrelated Docker images may be tested in
      a single run
- Start some MkDocs-based documentation with a copy of the README file and
  the changelog moved there

### Other changes

- python:
    - move the setuptools metadata to the `pyproject.toml` file
    - test with ruff 0.0.256, drop a couple of overrides for false
      positives emitted by earlier versions of Ruff
    - invoke the `tox-stages` tool from the directory where the Python 3.x
      interpreter lives, so that it is virtually certain that `tox-stages`
      (and consequenty Tox) will use the same Python interpreter
    - drop the `types-dataclasses` dependency for the `mypy` Tox test
      environment; dataclasses are included with Python 3.8
    - clean up some more Python-related files in the `clean` Makefile target

## [3.1.1] - 2023-02-28

### Fixes

- python:
    - do not build a universal wheel

### Other changes

- python:
    - test with ruff 0.0.253 with no changes

## [3.1.0] - 2023-02-28

### Semi-incompatible changes

- python:
    - drop Python 2.x compatibility
    - drop Python 3.6 and 3.7 compatibility; 3.8 and 3.9 will probably also be
      dropped in an upcoming release
- rust:
    - use named arguments for `format!()`, `println!()`, etc, and declare
      a minimum Rust supported version of 1.58

### Fixes

- use the `en_US.UTF-8` locale for CentOS 7.x and the related variants;
  we should really specify a UTF-8-capable locale, and `en_US.UTF-8` is
  installed by default on most minimal container setups
- use the `C.UTF-8` locale for CentOS 8.x/9.x and the related variants;
  this is the preferred POSIX name of the locale, `C.utf8` is merely
  an implementation detail
- use the `appstream` DNF/Yum repository for CentOS 8.x/9.x and the related
  variants; it should be enabled by default at this point in time, and some of
  the software that the various StorPool packages need has moved there
- python:
    - fix the way the `_fields` member of various named tuples is accessed
    - fix the format of several module and function docstrings
    - `sp_build_repo`: obtain the current date in a better timezone-aware way
    - mark the `setup.py` file as executable

### Additions

- all:
    - add the `supported` variant member with a single boolean field, `repo`,
      that declares whether StorPool provides a third-party OS packages
      repository for that variant
    - bump the variant description format version to 1.4 for the added
      `supported` member

### Other changes

- use the "Keep a Changelog" format for the changelog file
- python:
    - use the StorPool Python 2.x interpreter for the Tox tests
    - use the `tox-stages` utility instead of the `tox-delay` one
    - drop the Python 2.x, 3.6, and 3.7 compatibility, use some Python 3.x
      language features and modules that are in the standard library now
    - use black 23.x and flake8 6.x with no changes
    - use pylint 2.16.x, fix some of the issues it reported
    - start using ruff, fix some of the issues it reported
- rust:
    - bump the minor versions of the `anyhow`, `once_cell`, and `thiserror`
      dependencies to sync them with the StorPool `sp-rust-crates-io` package
    - let clippy know that we do mean to request a blanket `clippy::restriction`
      set of checks
- test-docker: test the `builder.utf8_locale` setting

## [3.0.0] - 2022-11-09

### Incompatible changes

- all:
    - Yum/DNF: when installing packages (both via the `package.install` and
      `pkgfile.install` commands), disable all the configured repositories,
      only enable some base system ones and the StorPool ones
- python:
    - drop Python 2.6 support, use dict comprehensions
- rust:
    - all the functions now return our own error enum instead of
      `Box<dyn error::Error>`

### Fixes

- all:
    - correctly treat Linux Mint 21.x as a Ubuntu 22.04 equivalent
    - make AlmaLinux the principal RPM-based distribution instead of CentOS
- python:
    - `sp_build_repo`:
        - correctly use the `name` and `slug` fields when generating the repository
          definitions files

### Additions

- all:
    - add some initial support for AlmaLinux 9 and Rocky Linux 9
- python:
    - `sp_build_repo`:
        - allow repository URLs to be overridden using a TOML configuration file;
          provide a sample as `examples/build-repo-overrides.toml`
- rust:
    - use a separate tool, `run-clippy.sh`, to invoke clippy;
      remove the `#![warn(...)]` directives from the individual source files
    - keep the `Cargo.lock` file under version control

### Other changes

- all:
    - allow repository definitions to be built using a different `storpool_variant`
      interpretation, mostly for testing the correctness of the Rust one
    - use the simpler container names for AlmaLinux and Rocky Linux
- python:
    - use the `cfg-diag` 0.4 `Config` class API
    - declare Python 3.10 and 3.11 as supported versions
    - drop the Rust and POSIX shell implementations from the sdist tarball
    - `sp_variant`:
        - now that `sp_build_repo` and `test_docker` use the `click` library,
          drop the `base_parser()` method
    - `sp_build_repo`:
        - mark the `-r` option as required, rename its long form to `--runtime`
        - override a "duplicate code" warning from pylint
        - use the `typedload` library for validating and loading configuration data
        - use the `click` library for command-line argument parsing
        - use f-strings
        - use the Text type instead of str; long overdue
    - `test_docker`:
        - install the StorPool Python packages to make sure the repository is
          indeed accessible and configured correctly
        - only use `asyncio.run()` for the parts that need to run asynchronously
          (e.g. not for command-line parsing or trivial queries)
        - use the `click` library for command-line argument parsing
        - run `docker swap` for the CentOS 8 container to switch to the CentOS Stream
          repositories; maybe we need to start using the quay.io containers instead
    - test suite:
        - specify version constraints for the library dependencies
        - use `pytest.mark.parametrize()` instead of the `ddt` library
        - drop the Python 2.x mypy and the `flake8` + `hacking` test environments,
          they do not provide much value nowadays
        - drop the outdated `pytest.pyi` typing stub
        - move the configuration for the check tools out of the `tox.ini` file,
          mostly into `pyproject.toml`, but still `setup.cfg` for `flake8`
- rust:
    - minor refactoring following some suggestions from clippy
    - override several clippy lints, mostly for good reasons
    - use the `clap` library for command-line parsing
    - use the `thiserror` library instead of the `quick-error` one, it is cleaner
    - use the `once_cell` library instead of the `lazy_static` one
    - use the `anyhow` library instead of `expect-exit` in the command-line tool

## [2.3.3] - 2022-04-28

### Fixes

- all:
    - make the quoting style in the Debian/Ubuntu `pkgfile.dep_query` command
      consistent with that of the others
- sh:
    - fix the quoting for the Debian/Ubuntu `pkgfile.dep_query` command
    - complete the exiting-on-errors fix: two missed invocations

### Other changes

- sh:
    - minor changes to implement some shellcheck suggestions
    - add a shellcheck test unless `NO_SHELLCHECK` is specified

## [2.3.2] - 2022-04-27

### Fixes

- sh:
    - fix exiting on errors in some situations; local variable declarations
      and error-checked assignments do not mix

## [2.3.1] - 2022-04-27

### Fixes

- sh:
    - fix matching the `VERSION_ID` variable in the `/etc/os-release` file:
      use a POSIX extended regular expression with `grep -E`, not
      a Perl-compatible one!

## [2.3.0] - 2022-04-26

### Incompatible changes

- rust:
    - the structs and enums exported by the `sp_variant` crate are now
      marked as non-exhaustive
    - some functions are now marked as "must use"

### Other changes

- python:
    - now that there is a working POSIX shell implementation that is better
      suited for bootstrapping, split the Python library into several modules
    - always require the "typing" module to be installed
- rust:
    - import struct names directory for a more idiomatic Rust style
    - many small improvements, mostly suggested by Clippy lints

## [2.2.0] - 2022-02-05

### Fixes

- python:
    - fix two bugs in the `list_all_packages()` convenience function:
        - do not modify the variant structure's command list in place!
        - correctly recognize installed packages on Debian/Ubuntu systems

### Additions

- all:
    - recognize Ubuntu 22.04 (Jammy Jellyfish)

### Other changes

- python:
    - reformat with 100 characters per line
    - make the ArgumentParser-related type annotations a bit more precise to
      pass some checks in recent versions of Mypy
- rust:
    - change the dependency on nix to a >= relation, hoping they do not
      break backwards compatibility

## [2.1.1] - 2021-12-18

### Fixes

- all:
    - Make sure all the implementations output the same thing for
      `command run package.list_all`.
- rust:
    - Fix a command.run bug: do not output the command to run, the tools
      that invoke `storpool_variant` may use its output!

### Other changes

- all:
    - Add two-clause BSD licenses to all the source files.
- python:
    - Drop a "type: ignore" comment and bump the mypy version used for
      the test suite to 0.920.
- rust:
    - Code clean-up:
        - drop an unused internal "url" field
        - simplify a double match
        - use `.find_map()` instead of reimplementing it
        - streamline `yai::parse()`

## [2.1.0] - 2021-11-15

### Fixes

- all:
    - On RedHat-derived distributions, the `package.list_all` command now
      displays the full epoch:version-release (EVR) string instead of
      only the version component.

### Additions

- all:
    - Add support for Ubuntu 21.10 (Impish Indri).

## [2.0.0] - 2021-10-24

### Incompatible changes

- rust:
    - change the return type of `get_program_version()` and
      `get_program_version_from()` from `String` to `&str`.

### Fixes

- all:
    - Install (or update as necessary) the ca-certificates package on
      RedHat-derived distributions, too, to take care of the Let's Encrypt
      certificate expiration debacle.
- python:
    - Fix the program name in the usage message of the `sp_variant` and
      `sp_build_repo` tools.
- build-repo:
    - Use trivver to sort DEBIAN9 before DEBIAN10.
- test-docker:
    - Run `apt-get update` if necessary.

### Additions

- all:
    - Add a "descr" field to the variant containing a brief
      human-readable name/description.
- sh:
    - Install ourselves as `/usr/sbin/sp_variant` in `repo add` so that
      other programs may use this helper.
- rust:
    - Use the new Variant.descr field in the documentation.

### Other changes

- rust:
    - Autogenerate the VariantKind enum.
    - Make the `sp_variant::data` module private.
    - Create the variants' data structure directly, do not decode a JSON
      document.
- test-docker:
    - Add the "-i" option to limit the images to run on.
    - Show the containers' output continually.

## [1.3.0] - 2021-09-15

### Started

- First public release.

[Unreleased]: https://github.com/storpool/sp-variant/compare/release/3.5.3...main
[3.5.3]: https://github.com/storpool/sp-variant/compare/release/3.5.2...release/3.5.3
[3.5.2]: https://github.com/storpool/sp-variant/compare/release/3.5.1...release/3.5.2
[3.5.1]: https://github.com/storpool/sp-variant/compare/release/3.5.0...release/3.5.1
[3.5.0]: https://github.com/storpool/sp-variant/compare/release/3.4.2...release/3.5.0
[3.4.2]: https://github.com/storpool/sp-variant/compare/release/3.4.1...release/3.4.2
[3.4.1]: https://github.com/storpool/sp-variant/compare/release/3.4.0...release/3.4.1
[3.4.0]: https://github.com/storpool/sp-variant/compare/release/3.3.0...release/3.4.0
[3.3.0]: https://github.com/storpool/sp-variant/compare/release/3.2.3...release/3.3.0
[3.2.3]: https://github.com/storpool/sp-variant/compare/release/3.2.2...release/3.2.3
[3.2.2]: https://github.com/storpool/sp-variant/compare/release/3.2.1...release/3.2.2
[3.2.1]: https://github.com/storpool/sp-variant/compare/release/3.2.0...release/3.2.1
[3.2.0]: https://github.com/storpool/sp-variant/compare/release/3.1.2...release/3.2.0
[3.1.2]: https://github.com/storpool/sp-variant/compare/release/3.1.1...release/3.1.2
[3.1.1]: https://github.com/storpool/sp-variant/compare/release/3.1.0...release/3.1.1
[3.1.0]: https://github.com/storpool/sp-variant/compare/release/3.0.0...release/3.1.0
[3.0.0]: https://github.com/storpool/sp-variant/compare/release/2.3.3...release/3.0.0
[2.3.3]: https://github.com/storpool/sp-variant/compare/release/2.3.2...release/2.3.3
[2.3.2]: https://github.com/storpool/sp-variant/compare/release/2.3.1...release/2.3.2
[2.3.1]: https://github.com/storpool/sp-variant/compare/release/2.3.0...release/2.3.1
[2.3.0]: https://github.com/storpool/sp-variant/compare/release/2.2.0...release/2.3.0
[2.2.0]: https://github.com/storpool/sp-variant/compare/release/2.1.1...release/2.2.0
[2.1.1]: https://github.com/storpool/sp-variant/compare/release/2.1.0...release/2.1.1
[2.1.0]: https://github.com/storpool/sp-variant/compare/release/2.0.0...release/2.1.0
[2.0.0]: https://github.com/storpool/sp-variant/compare/release/1.3.0...release/2.0.0
[1.3.0]: https://github.com/storpool/sp-variant/releases/tag/release%2F1.3.0
