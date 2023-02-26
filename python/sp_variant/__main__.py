# SPDX-FileCopyrightText: 2021 - 2023  StorPool <support@storpool.com>
# SPDX-License-Identifier: BSD-2-Clause
"""Support for different OS distributions and StorPool build variants."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys

from typing import Any, Callable, Final, TYPE_CHECKING

from . import defs
from . import variant
from . import vbuild


if TYPE_CHECKING:
    # pylint: disable-next=protected-access,invalid-name
    SubPAction: Final = argparse._SubParsersAction[argparse.ArgumentParser]  # noqa: SLF001


CMD_LIST_BRIEF: Final = [
    ("pkgfile", "install"),
]


def cmd_detect(cfg: defs.Config) -> None:
    """Detect and output the build variant for the current host."""
    try:
        print(variant.detect_variant(cfg=cfg).name)
    except variant.VariantError as err:
        print(str(err), file=sys.stderr)
        sys.exit(1)


def copy_file(cfg: defs.Config, src: str, dstdir: str) -> None:
    """Use `install(8)` to install a configuration file."""
    dst: Final = os.path.join(dstdir, os.path.basename(src))
    mode: Final = "0644"
    cfg.diag(f"{src} -> {dst} [{mode}]")
    try:
        subprocess.check_call(
            [
                "install",
                "-o",
                "root",
                "-g",
                "root",
                "-m",
                mode,
                "--",
                src,
                dst,
            ],
            shell=False,
        )
    except subprocess.CalledProcessError as err:
        raise variant.VariantFileError(f"Could not copy {src} over to {dst}: {err}")


def repo_add_extension(cfg: defs.Config, name: str) -> str:
    """Add the extension for the specified repository type."""
    parts: Final = name.rsplit(".")
    if len(parts) != 2:
        raise variant.VariantFileError(
            f"Unexpected repository file name without an extension: {name}"
        )
    return f"{parts[0]}{cfg.repotype.extension}.{parts[1]}"


def repo_add_deb(cfg: defs.Config, var: defs.Variant, vardir: str) -> None:
    """Install the StorPool Debian-like repo configuration."""
    assert isinstance(var.repo, defs.DebRepo)  # noqa: S101  # mypy needs this

    try:
        subprocess.check_call(var.commands.package.install + var.repo.req_packages, shell=False)
    except subprocess.CalledProcessError as err:
        raise variant.VariantFileError(
            f"Could not install the required packages {' '.join(var.repo.req_packages)}: {err}"
        )

    copy_file(
        cfg,
        os.path.join(vardir, repo_add_extension(cfg, os.path.basename(var.repo.sources))),
        "/etc/apt/sources.list.d",
    )
    copy_file(
        cfg,
        os.path.join(vardir, os.path.basename(var.repo.keyring)),
        "/usr/share/keyrings",
    )

    try:
        subprocess.check_call(["apt-get", "update"], shell=False)
    except subprocess.CalledProcessError as err:
        raise variant.VariantFileError(f"Could not update the APT database: {err}")


def repo_add_yum(cfg: defs.Config, var: defs.Variant, vardir: str) -> None:
    """Install the StorPool RedHat/CentOS-like repo configuration."""
    assert isinstance(var.repo, defs.YumRepo)  # noqa: S101  # mypy needs this

    try:
        subprocess.check_call(
            [
                "yum",
                "--disablerepo=storpool-*'",
                "install",
                "-q",
                "-y",
                "ca-certificates",
            ],
            shell=False,
        )
    except subprocess.CalledProcessError as err:
        raise variant.VariantFileError(
            f"Could not install the required ca-certificates package: {err}"
        )

    copy_file(
        cfg,
        os.path.join(vardir, repo_add_extension(cfg, os.path.basename(var.repo.yumdef))),
        "/etc/yum.repos.d",
    )
    copy_file(
        cfg,
        os.path.join(vardir, os.path.basename(var.repo.keyring)),
        "/etc/pki/rpm-gpg",
    )

    if os.path.isfile("/usr/bin/rpmkeys"):
        try:
            subprocess.check_call(
                [
                    "rpmkeys",
                    "--import",
                    os.path.join("/etc/pki/rpm-gpg", os.path.basename(var.repo.keyring)),
                ],
                shell=False,
            )
        except subprocess.CalledProcessError as err:
            raise variant.VariantFileError(f"Could not import the RPM PGP keys: {err}")

    try:
        subprocess.check_call(
            [
                "yum",
                "--disablerepo=*",
                f"--enablerepo=storpool-{cfg.repotype.name}",
                "clean",
                "metadata",
            ],
            shell=False,
        )
    except subprocess.CalledProcessError as err:
        raise variant.VariantFileError(f"Could not clean the Yum repository metadata: {err}")


def repo_add(cfg: defs.Config) -> None:
    """Install the StorPool repository configuration."""
    assert cfg.repodir is not None  # noqa: S101  # mypy needs this
    var: Final = variant.detect_variant(cfg)
    vardir: Final = os.path.join(cfg.repodir, var.name)
    if not os.path.isdir(vardir):
        raise defs.VariantConfigError(f"No {vardir} directory")

    if isinstance(var.repo, defs.DebRepo):
        repo_add_deb(cfg, var, vardir)
    elif isinstance(var.repo, defs.YumRepo):
        repo_add_yum(cfg, var, vardir)


def cmd_repo_add(cfg: defs.Config) -> None:
    """Install the StorPool repository configuration, display errors."""
    try:
        repo_add(cfg)
    except variant.VariantError as err:
        print(str(err), file=sys.stderr)
        sys.exit(1)


def command_find(cfg: defs.Config, var: defs.Variant) -> list[str]:
    """Get a distribution-specific command from the variant definition."""
    assert cfg.command is not None  # noqa: S101  # mypy needs this

    current = var.commands
    for comp in cfg.command.split("."):
        if not isinstance(current, tuple):
            raise defs.VariantConfigError("Too many command components")

        fields: list[str] = getattr(current, "_fields")
        if comp not in fields:
            raise defs.VariantConfigError(
                f"Invalid command component '{comp}', should be one of {' '.join(fields)}"
            )
        current = getattr(current, comp)

    if not isinstance(current, list):
        fields = getattr(current, "_fields")
        raise defs.VariantConfigError(
            f"Incomplete command specification, should continue with one of {' '.join(fields)}"
        )

    return current


def command_run(cfg: defs.Config) -> None:
    """Run a distribution-specific command."""
    assert cfg.args is not None  # noqa: S101  # mypy needs this

    cmd: Final = command_find(cfg, variant.detect_variant(cfg=cfg)) + cfg.args
    cmdstr: Final = shlex.join(cmd)
    cfg.diag(f"About to run `{cmdstr}`")
    if cfg.noop:
        print(cmdstr)
        return

    try:
        subprocess.check_call(cmd, shell=False)
    except subprocess.CalledProcessError as err:
        raise variant.VariantFileError(f"Could not run `{cmdstr}`: {err}")


def cmd_command_list(cfg: defs.Config) -> None:
    """List the distribution-specific commands."""
    var: Final = variant.detect_variant(cfg=cfg)

    # We only have two levels, right?
    for cat_name, category in (
        (name, getattr(var.commands, name)) for name in sorted(var.commands._fields)
    ):
        for cmd_name, command in (
            (name, getattr(category, name)) for name in sorted(category._fields)
        ):
            result = ["..."] if (cat_name, cmd_name) in CMD_LIST_BRIEF else command
            print(f"{cat_name}.{cmd_name}: {shlex.join(result)}")


def cmd_command_run(cfg: defs.Config) -> None:
    """Run a distribution-specific command."""
    try:
        command_run(cfg)
    except variant.VariantError as err:
        print(str(err), file=sys.stderr)
        sys.exit(1)


def cmd_features(_cfg: defs.Config) -> None:
    """Display the features supported by storpool_variant."""
    print(
        f"Features: repo=0.2 variant={defs.VERSION} "
        f"format={defs.FORMAT_VERSION[0]}.{defs.FORMAT_VERSION[1]}"
    )


def cmd_show(cfg: defs.Config) -> None:
    """Display information about a single build variant."""
    vbuild.build_variants(cfg)

    def get_data() -> Any:  # noqa: ANN401  # well, we know it's a dict...
        """Build up the variant description."""
        if cfg.command == "all":
            return defs.jsonify(
                {
                    "format": {
                        "version": {
                            "major": defs.FORMAT_VERSION[0],
                            "minor": defs.FORMAT_VERSION[1],
                        }
                    },
                    "version": defs.VERSION,
                    "variants": vbuild.VARIANTS,
                    "order": [var.name for var in vbuild.DETECT_ORDER],
                }
            )

        assert cfg.command is not None  # noqa: S101  # mypy needs this
        var: Final[defs.Variant | None] = (
            variant.detect_variant(cfg)
            if cfg.command == "current"
            else vbuild.VARIANTS.get(cfg.command)
        )
        if var is None:
            sys.exit(f"Invalid build variant '{cfg.command}'")

        return defs.jsonify(
            {
                "format": {
                    "version": {
                        "major": defs.FORMAT_VERSION[0],
                        "minor": defs.FORMAT_VERSION[1],
                    }
                },
                "version": defs.VERSION,
                "variant": var,
            }
        )

    print(json.dumps(get_data(), sort_keys=True, indent=2))


def parse_arguments() -> tuple[defs.Config, Callable[[defs.Config], None]]:
    """Parse the command-line arguments."""
    parser: Final = argparse.ArgumentParser(prog="storpool_variant")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="verbose operation; display diagnostic output",
    )
    subp = parser.add_subparsers()

    p_cmd = subp.add_parser("command", help="Distribition-specific commands")
    subp_cmd = p_cmd.add_subparsers()

    p_subcmd = subp_cmd.add_parser("list", help="List the distribution-specific commands")
    p_subcmd.set_defaults(func=cmd_command_list)

    p_subcmd = subp_cmd.add_parser("run", help="Run a distribution-specific command")
    p_subcmd.add_argument(
        "-N",
        "--noop",
        action="store_true",
        help="display the command instead of executing it",
    )
    p_subcmd.add_argument("command", type=str, help="The identifier of the command to run")
    p_subcmd.add_argument("args", type=str, nargs="*", help="Arguments to pass to the command")
    p_subcmd.set_defaults(func=cmd_command_run)

    p_cmd = subp.add_parser("detect", help="Detect the build variant for the current host")
    p_cmd.set_defaults(func=cmd_detect)

    p_cmd = subp.add_parser("features", help="Display the features supported by storpool_variant")
    p_cmd.set_defaults(func=cmd_features)

    p_cmd = subp.add_parser("repo", help="StorPool repository-related commands")
    subp_cmd = p_cmd.add_subparsers()

    p_subcmd = subp_cmd.add_parser("add", help="Install the StorPool repository configuration")
    p_subcmd.add_argument(
        "-d",
        "--repodir",
        type=str,
        required=True,
        help="The path to the directory with the repository configuration",
    )
    p_subcmd.add_argument(
        "-t",
        "--repotype",
        type=str,
        default=defs.REPO_TYPES[0].name,
        choices=[item.name for item in defs.REPO_TYPES],
        help="The type of repository to add (default: contrib)",
    )
    p_subcmd.set_defaults(func=cmd_repo_add)

    p_cmd = subp.add_parser("show", help="Display information about a build variant")
    p_cmd.add_argument(
        "name",
        type=str,
        help=(
            "the name of the build variant to query, 'all' for all, or "
            "'current' for the one detected"
        ),
    )
    p_cmd.set_defaults(func=cmd_show)

    args: Final = parser.parse_args()
    if getattr(args, "func", None) is None:
        sys.exit("No command specified")

    return (
        defs.Config(
            args=getattr(args, "args", None),
            command=getattr(args, "command", getattr(args, "name", None)),
            noop=bool(getattr(args, "noop", False)),
            repodir=getattr(args, "repodir", None),
            repotype=next(rtype for rtype in defs.REPO_TYPES if rtype.name == args.repotype)
            if hasattr(args, "repotype")
            else defs.REPO_TYPES[0],
            verbose=args.verbose,
        ),
        args.func,
    )


def main() -> None:
    """Main routine: parse options, detect the variant."""
    cfg, func = parse_arguments()
    func(cfg)


if __name__ == "__main__":
    main()
