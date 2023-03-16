# SPDX-FileCopyrightText: 2021 - 2023  StorPool <support@storpool.com>
# SPDX-License-Identifier: BSD-2-Clause
"""Test the functions in the sp.variant module."""

from __future__ import annotations

import dataclasses
import pathlib
import sys

from unittest import mock

from typing import Final, IO

import pytest

from sp_variant import defs
from sp_variant import variant
from sp_variant import vbuild


_MSG_NOT_SEEN = "This should not be seen"
_MSG_SEEN = "This should be seen"


def test_get() -> None:
    """Test the operation of get_variant()."""
    assert variant.get_variant("CENTOS7").name == "CENTOS7"
    assert variant.get_variant("CENTOS6").name == "CENTOS6"

    repo = variant.get_variant("UBUNTU1804").repo
    assert isinstance(repo, defs.DebRepo)
    assert repo.vendor == "ubuntu"
    assert repo.codename == "bionic"

    repo = variant.get_variant("DEBIAN9").repo
    assert isinstance(repo, defs.DebRepo)
    assert repo.vendor == "debian"
    assert repo.codename == "stretch"

    with pytest.raises(variant.VariantKeyError):
        variant.get_variant("whee")


def test_roundtrip() -> None:
    """Run through the variants with some minimal sanity checks."""
    vbuild.build_variants(variant.Config(verbose=False))
    assert vbuild.VARIANTS
    for name in vbuild.VARIANTS:
        var = variant.get_variant(name)
        assert var.name == name
        avar = variant.get_by_alias(var.builder.alias)
        assert avar == var


def test_detect() -> None:
    """Make sure that detect_variant() returns a reasonably valid result."""
    var: Final = variant.detect_variant()
    assert var is not None
    assert pathlib.Path(var.detect.filename).is_file()


def test_list_all() -> None:
    """Make sure that the package.list_all command does not go amok."""
    print("")

    var: Final = variant.detect_variant()
    assert var is not None
    det_cmd: Final = list(var.commands.package.list_all)
    print(f"list_all command: {det_cmd!r}")

    pkgs_a: Final = variant.list_all_packages(var, patterns=["a*"])
    print(f"{len(pkgs_a)} packages with names starting with 'a'")
    assert det_cmd == var.commands.package.list_all

    pkgs_b: Final = variant.list_all_packages(var, patterns=["b*"])
    print(f"{len(pkgs_b)} packages with names starting with 'b'")
    assert det_cmd == var.commands.package.list_all

    pkgs_a_again: Final = variant.list_all_packages(var, patterns=["a*"])
    print(f"now {len(pkgs_a_again)} packages with names starting with 'a'")
    assert det_cmd == var.commands.package.list_all
    assert set(pkgs_a) == set(pkgs_a_again)

    # There should be at least one package installed on the system... right?
    pkgs_all: Final = variant.list_all_packages(var, patterns=["*"])
    print(f"{len(pkgs_all)} total packages on the system")
    assert pkgs_all


def test_config_diag() -> None:
    """Test the `cfg_diag`-like functionality of the `Config` class."""
    output: list[tuple[str, IO[str]]] = []

    def check(*, seen: bool, to_stderr: bool = True) -> None:
        """Make sure the output is exactly as expected."""
        if not seen:
            assert not output
            return

        assert output == [(_MSG_SEEN, sys.stderr if to_stderr else sys.stdout)]
        output.clear()

    def init_cfg(
        *, verbose: bool, diag_to_stderr: bool = True, use_setattr: bool = False
    ) -> defs.Config:
        """Initialize a defs.Config object in the specified way."""
        # pylint: disable=protected-access
        cfg = defs.Config(verbose=verbose)
        assert cfg._diag_to_stderr  # noqa: SLF001
        if diag_to_stderr:
            return cfg

        if use_setattr:
            object.__setattr__(cfg, "_diag_to_stderr", False)  # noqa: FBT003
        else:
            cfg._diag_to_stderr = False  # type: ignore[misc]  # noqa: SLF001
        assert not cfg._diag_to_stderr  # noqa: SLF001
        return cfg

    def mock_print(msg: str, *, file: IO[str]) -> None:
        """Mock a print() invocation."""
        output.append((msg, file))

    check(seen=False)

    cfg = init_cfg(verbose=False)
    with mock.patch("builtins.print", new=mock_print):
        cfg.diag(_MSG_NOT_SEEN)

    check(seen=False)

    cfg = init_cfg(verbose=True)
    with mock.patch("builtins.print", new=mock_print):
        cfg.diag(_MSG_SEEN)

    check(seen=True)

    # We can't set _diag_to_stderr directly, right?
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg = init_cfg(verbose=True, diag_to_stderr=False)

    check(seen=False)

    # OK, can we do stdout now?
    cfg = init_cfg(verbose=True, diag_to_stderr=False, use_setattr=True)
    with mock.patch("builtins.print", new=mock_print):
        cfg.diag(_MSG_SEEN)

    check(seen=True, to_stderr=False)
