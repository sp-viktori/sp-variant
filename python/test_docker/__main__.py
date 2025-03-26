# SPDX-FileCopyrightText: 2021 - 2024  StorPool <support@storpool.com>
# SPDX-License-Identifier: BSD-2-Clause
"""Run some sp_variant tests using Docker containers."""

from __future__ import annotations

import asyncio
import asyncio.subprocess as aprocess
import dataclasses
import json
import logging
import pathlib
import subprocess
import sys
import tempfile
from typing import TYPE_CHECKING, NamedTuple

import click
import utf8_locale

from sp_build_repo import diag


if TYPE_CHECKING:
    from typing import Final


@dataclasses.dataclass(frozen=True)
class Config:
    """Runtime configuration for the Docker test runner."""

    images_filter: tuple[str, ...]
    repo_file: pathlib.Path
    utf8_env: dict[str, str]
    verbose: bool


class SimpleBuilder(NamedTuple):
    """A part of a variant's builder data."""

    alias: str
    base_image: str
    utf8_locale: str


class SimpleVariant(NamedTuple):
    """A part of the variants representation."""

    name: str
    builder: SimpleBuilder


def extract_variants_data(
    cfg: Config,
    tempd: pathlib.Path,
) -> tuple[pathlib.Path, dict[str, SimpleVariant]]:
    """Extract the variants data into the specified directory."""
    logging.debug("Making sure the %(tempd)s directory is empty", {"tempd": tempd})
    if found := list(tempd.iterdir()):
        sys.exit(f"Unexpected stuff found in {tempd}: {found!r}")

    logging.debug(
        "Extracting %(repo_file)s into %(tempd)s",
        {"repo_file": cfg.repo_file, "tempd": tempd},
    )
    subprocess.check_call(["tar", "-xaf", cfg.repo_file, "-C", tempd], env=cfg.utf8_env)
    logging.debug("Looking for a single directory")
    found = list(tempd.iterdir())
    if len(found) != 1 or not found[0].is_dir() or found[0].name != "add-storpool-repo":
        sys.exit(f"Expected a single add-storpool-repo directory in {tempd}: {found!r}")
    spdir: Final = found[0]

    spvar: Final = spdir / "storpool_variant"
    if not spvar.is_file() or (spvar.stat().st_mode & 0o555) != 0o555:
        sys.exit(f"Expected an executable {spvar} file")

    output: Final = subprocess.check_output(
        [spvar, "show", "all"],
        encoding="UTF-8",
        env=cfg.utf8_env,
    )
    try:
        data: Final = json.loads(output)
    except ValueError as err:
        sys.exit(f"Failed to decode the output of `{spvar} show all`: {err}")

    if (
        not isinstance(data, dict)
        or not isinstance(data.get("format"), dict)
        or not isinstance(data["format"].get("version"), dict)
        or data["format"]["version"].get("major") != 1
        or data["format"]["version"]["minor"] < 2
    ):
        sys.exit(f"Missing or unsupported `{spvar} show all` format version")

    res: Final = {}
    for var in data["variants"].values():
        res[var["name"]] = SimpleVariant(
            name=var["name"],
            builder=SimpleBuilder(
                alias=var["builder"]["alias"],
                base_image=var["builder"]["base_image"],
                utf8_locale=var["builder"]["utf8_locale"],
            ),
        )

    return spdir, res


def filter_docker_images(cfg: Config, var_data: dict[str, SimpleVariant]) -> dict[str, str]:
    """Find the Docker images present on this system."""
    logging.debug("Querying Docker for the available images")
    all_images: Final = set(
        subprocess.check_output(
            ["docker", "image", "ls", "--format", "{{.Repository}}:{{.Tag}}"],
            encoding="UTF-8",
            env=cfg.utf8_env,
        ).splitlines(),
    )
    images: Final = (
        all_images
        if not cfg.images_filter
        else {name for name in all_images if any(word in name for word in cfg.images_filter)}
    )

    res: Final = {}
    ignored: Final = {"IGNORE", "centos:6", "debian:buster"}
    for var in var_data.values():
        for image in (var.builder.base_image, "builder:" + var.builder.alias):
            if image in ignored:
                continue
            if image in images:
                res[image] = var.name

    return res


async def process_detect_lines(
    image: str,
    proc: aprocess.Process,
) -> tuple[bytes | None, list[str]]:
    """Read the lines output by `storpool_variant detect`, see if they look okay."""
    assert proc.stdout is not None  # noqa: S101  # mypy needs this

    first_line = None
    rest = b""
    errors: Final = []
    try:
        try:
            first_line = await proc.stdout.readline()
        except Exception as err:  # noqa: BLE001
            errors.append(f"Could not read the first line: {err}")
        logging.debug(
            "%(image)s: first line %(first_line)r",
            {"image": image, "first_line": first_line},
        )

        if first_line:
            first_line = first_line.rstrip(b"\n")
            while True:
                try:
                    more = await proc.stdout.readline()
                except Exception as err:  # noqa: BLE001
                    errors.append(f"Could not read a further line: {err}")
                    break
                logging.debug("%(image)s: more %(more)r", {"image": image, "more": more})

                if not more:
                    break
                rest += b"\n" + more.rstrip(b"\n")

        if rest:
            assert first_line is not None  # noqa: S101  # mypy needs this
            errors.append(f"More than one line of output: {(first_line + rest)!r}")
    finally:
        res: Final = await proc.wait()
        logging.debug("%(image)s: exit code %(res)r", {"image": image, "res": res})
        if res:
            errors.append(f"Non-zero exit code {res}")

    return first_line, errors


async def run_detect_for_image(
    cfg: Config,
    spdir: pathlib.Path,
    image: str,
) -> tuple[str | None, str | None]:
    """Run `storpool_variant detect` in a single new Docker container."""
    logging.debug("%(image)s: starting a container", {"image": image})
    proc: Final = await aprocess.create_subprocess_exec(
        "docker",
        "run",
        "--rm",
        "-v",
        f"{spdir}:/sp:ro",
        "--",
        image,
        "/sp/storpool_variant",
        "detect",
        env=cfg.utf8_env,
        stdout=aprocess.PIPE,
    )
    logging.debug("%(image)s: created process %(pid)d", {"image": image, "pid": proc.pid})

    first_line, errors = await process_detect_lines(image, proc)
    first_line_dec: Final = None if first_line is None else first_line.decode("ISO-8859-15")
    logging.debug(
        "%(image)s: first_line_dec %(first_line_dec)r errors %(errors)r",
        {"image": image, "first_line_dec": first_line_dec, "errors": errors},
    )
    if errors:
        return (first_line_dec, "\n".join(errors))
    return (first_line_dec, None)


def analyze_detect_single(
    image: str,
    expected: str,
    received: BaseException | tuple[str | None, str | None],
) -> list[str]:
    """Analyze a single container result."""
    if isinstance(received, BaseException):
        return [f"{image}: {received}"]
    if not isinstance(received, tuple) or len(received) != 2:
        return [f"{image}: unexpected result {received!r}"]

    r_first, r_err = received
    if r_err is not None:
        return [f"{image}: first line {r_first!r} stderr output {r_err!r}"]

    if r_first != expected:
        return [f"{image}: expected {expected!r}, got {r_first!r}"]

    logging.debug("%(image)s: OK: %(r_first)r", {"image": image, "r_first": r_first})
    return []


async def test_detect(
    cfg: Config,
    spdir: pathlib.Path,
    ordered: list[tuple[str, str]],
) -> list[str]:
    """Run `storpool_variant detect` for all the images."""
    logging.debug("Spawning the detect containers")
    gathering: Final = asyncio.gather(
        *(run_detect_for_image(cfg, spdir, image) for image, _ in ordered),
        return_exceptions=True,
    )
    logging.debug("Waiting for the detect containers")
    res: Final = await gathering

    logging.debug("Analyzing %(count)d detect results", {"count": len(res)})
    errors: Final = []
    for (image, expected), received in zip(ordered, res):
        errors.extend(analyze_detect_single(image, expected, received))

    if len(res) != len(ordered):
        errors.append(
            f"Internal error: expected {len(ordered)} detect results, got {len(res)} ones",
        )

    return errors


async def run_add_repo_for_image(
    cfg: Config,
    spdir: pathlib.Path,
    addsh: pathlib.Path,
    image: str,
    variant: SimpleVariant,
) -> tuple[bytes, bytes, int]:
    """Run `add-storpool-repo` in a single new Docker container."""
    logging.debug("%(image)s: starting a container", {"image": image})
    proc: Final = await aprocess.create_subprocess_exec(
        "docker",
        "run",
        "--rm",
        "-v",
        f"{spdir}:/sp:ro",
        "--",
        image,
        "env",
        "LC_ALL=" + variant.builder.utf8_locale,
        "/sp/" + str(addsh.relative_to(spdir)),
        env=cfg.utf8_env,
        stdout=aprocess.PIPE,
        stderr=aprocess.PIPE,
    )
    logging.debug("%(image)s: created process %(pid)d", {"image": image, "pid": proc.pid})
    assert proc.stdout is not None  # noqa: S101  # mypy needs this
    assert proc.stderr is not None  # noqa: S101  # mypy needs this

    async def read_stream(stype: str, stream: asyncio.StreamReader) -> bytes:
        """Read lines from a stream, output them, gather them."""
        logging.debug("%(image)s: waiting for %(stype)s lines", {"image": image, "stype": stype})
        res = b""
        while True:
            if not (line := await stream.readline()):
                logging.debug("%(image)s: no more %(stype)s", {"image": image, "stype": stype})
                break

            logging.debug(
                "%(image)s: read a %(stype)s line: %(line)r",
                {"image": image, "stype": stype, "line": line},
            )
            res += line

        return res

    r_out, r_err = await asyncio.gather(
        read_stream("stdout", proc.stdout),
        read_stream("stderr", proc.stderr),
    )
    res: Final = await proc.wait()
    return (r_out, r_err, res)


def analyze_add_repo_single(
    image: str,
    received: BaseException | tuple[bytes, bytes, int],
) -> list[str]:
    """Analyze a single add-storpool-repo result."""
    if isinstance(received, BaseException):
        return [f"{image}: {received}"]
    if not isinstance(received, tuple) or len(received) != 3:
        return [f"{image}: unexpected result {received!r}"]

    r_out, r_err, r_res = received
    if r_res:
        return [
            f"{image}: the script failed with exit code {r_res}; "
            f"stdout: {r_out!r} stderr {r_err!r}",
        ]

    logging.debug("%(image)s: OK", {"image": image})
    return []


async def test_add_repo(
    cfg: Config,
    spdir: pathlib.Path,
    ordered: list[tuple[str, str]],
    var_data: dict[str, SimpleVariant],
) -> list[str]:
    """Run `storpool_variant detect` for all the images."""
    logging.debug("Preparing the add-repo script")
    addsh: Final = spdir / "run-add-repo.sh"
    if addsh.exists() or addsh.is_symlink():
        return [f"Did not expect {addsh} to exist"]
    try:
        addsh.write_text(
            """#!/bin/sh

set -e
set -x

check_locale()
{
    local var="$1" value="$2"

    if [ -z "$value" ]; then
        echo "$var is not set" 1>&2
        exit 1
    fi
    if [ -n "$(env LC_ALL="$value" locale -k -c LC_CTYPE 2>&1 > /dev/null)" ]; then
        echo "$var specifies a '$value' locale that is not configured" 1>&2
        exit 1
    fi
    if ! env LC_ALL="$value" locale -k -c LC_CTYPE | grep -Eqe '^charmap=.*UTF-8'; then
        echo "$var specifies a '$value' locale with a non-UTF-8 charmap" 1>&2
        exit 1
    fi
}

fix_centos_eol_repos()
{
    # Fix EOL CentOS repos and mirrorlist usage
    if /sp/storpool_variant detect | grep -q 'CENTOS[78]'; then
        echo 'Fixing CentOS EOL repos'
        for repo in /etc/yum.repos.d/CentOS-*; do
            sed -r -i'' -e 's,^mirrorlist=,#mirrorlist=,' \
                -e 's,^#baseurl=https?://mirror,baseurl=http://vault,' "$repo"
        done
    fi
}

# Make sure LC_ALL is set to a valid UTF-8-capable locale
echo 'Checking whether LC_ALL specifies a valid UTF-8-capable locale'
check_locale 'The LC_ALL environment variable' "$LC_ALL"

tempf="$(mktemp -t current-variant.json.XXXXXX)"
trap "rm -f -- '$tempf'" HUP INT TERM EXIT
echo "Stashing the `sp_variant show current` output into $tempf"
/sp/storpool_variant show current > "$tempf"

fix_centos_eol_repos

# Parsing JSON without jq? Yeah, sure, why not...
echo 'Checking for a Debian-like variant'
unset is_debian
if tr "\n" ' ' < "$tempf" | grep -Eqe '"family"[[:space:]]*:[[:space:]]*"debian"'; then
    is_debian=1
    echo 'Running apt-get update'
    apt-get update
elif [ "$(/sp/storpool_variant detect)" = 'CENTOS8' ]; then
    echo 'Installing CentOS GPG keys'
    yum install -y centos-gpg-keys
    echo 'Running dnf swap centos-linux-repos centos-stream-repos'
    dnf --disablerepo '*' --enablerepo extras -y swap centos-linux-repos centos-stream-repos
    fix_centos_eol_repos
else
    echo 'No apt-get update or dnf swap necessary'
fi

echo 'Running add-storpool-repo'
/sp/add-storpool-repo.sh

echo 'Installing jq'
/sp/storpool_variant command run -- package.install jq

echo 'Checking whether builder.utf8_locale specifies a valid UTF-8-capable locale'
u8loc="$(jq -r '.variant.builder.utf8_locale' < "$tempf")"
check_locale 'The builder.utf8_locale setting' "$u8loc"

echo 'Checking whether StorPool has a package repository for this variant'
supp_repo="$(jq -r '.variant.supported.repo' < "$tempf")"
case "$supp_repo" in
    true)
        supp_repo='1'
        ;;

    false)
        supp_repo=''
        ;;

    *)
        echo "storpool_variant output an unexpected value for supported.repo: '$supp_repo'" 1>&2
        exit 1
        ;;
esac

echo 'Installing some programs'
if ! /sp/storpool_variant command run -- package.install sp-python3 sp-python3-modules; then
    if [ -z "$supp_repo" ]; then
        echo 'Ignoring the package.install failure for an unsupported repository'
    else
        echo 'Installing the StorPool packages failed' 1>&2
        exit 1
    fi
fi

echo 'Running add-storpool-repo -t staging'
/sp/add-storpool-repo.sh -t staging

echo 'Running the "update the repository metadata" command'
/sp/storpool_variant.sh command run package.update_db

echo 'Obtaining information about the sp-python3 package'
res=0
if [ -n "$is_debian" ]; then
    if ! apt-cache policy sp-python3; then
        res="$?"
    fi
else
    if ! yum info sp-python3; then
        res="$?"
    fi
fi
if [ "$res" -ne 0 ]; then
    if [ -z "$supp_repo" ]; then
        echo 'Ignoring the package query failure for an unsupported repository'
    else
        echo 'Querying for the sp-python3 package failed' 1>&2
        exit 1
    fi
fi

pkg_count="$(jq '.variant.package | length' < "$tempf")"
echo "Trying to install $pkg_count packages"

failed=''
for pkg in $(jq -r '.variant.package | to_entries[] | .value' < "$tempf"); do
    if ! /sp/storpool_variant command run -- package.install "$pkg"; then
        failed="$failed $pkg"
    fi
done
if [ -n "$failed" ]; then
    echo "Could not install some packages:$failed" 1>&2
    exit 1
fi

echo 'Done, it seems'
""",
            encoding="UTF-8",
        )
    except Exception as err:  # noqa: BLE001
        return [f"Could not create {addsh}: {err}"]
    try:
        addsh.chmod(0o755)
    except OSError as err:
        return [f"Could not set the permissions mode on {addsh}: {err}"]

    logging.debug("Spawning the add-repo containers")
    gathering: Final = asyncio.gather(
        *(
            run_add_repo_for_image(cfg, spdir, addsh, image, var_data[variant])
            for image, variant in ordered
        ),
        return_exceptions=True,
    )
    logging.debug("Waiting for the add-repo containers")
    res: Final = await gathering

    logging.debug("Analyzing %(count)d add-repo results", {"count": len(res)})
    errors: Final = []
    for (image, _), received in zip(ordered, res):
        errors.extend(analyze_add_repo_single(image, received))

    if len(res) != len(ordered):
        errors.append(
            f"Internal error: expected {len(ordered)} add-repo results, got {len(res)} ones",
        )

    return errors


async def run_tests(
    cfg: Config,
    spdir: pathlib.Path,
    ordered: list[tuple[str, str]],
    var_data: dict[str, SimpleVariant],
) -> None:
    """Run the tests themselves."""
    if errors := await test_detect(cfg, spdir, ordered):
        sys.exit("`storpool_variant detect` errors: " + "\n".join(errors))

    if errors := await test_add_repo(cfg, spdir, ordered, var_data):
        sys.exit("`add-storpool-repo.sh` errors: " + "\n".join(errors))

    logging.debug("Everything seems fine!")


@click.command()
@click.option(
    "-i",
    "--images-filter",
    type=str,
    multiple=True,
    help="Only process images with names containing this string; may be specified multiple times",
)
@click.option(
    "-r",
    "--repo-file",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        path_type=pathlib.Path,
    ),
    required=True,
    help="The add-storpool-repo archive to test",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Verbose operation; display diagnostic output",
)
def main(*, images_filter: tuple[str, ...], repo_file: pathlib.Path, verbose: bool) -> None:
    """Parse command-line options, run tests."""
    diag.setup_logger(verbose=verbose)
    cfg: Final = Config(
        images_filter=images_filter,
        repo_file=repo_file,
        utf8_env=utf8_locale.get_utf8_env(),
        verbose=verbose,
    )
    with tempfile.TemporaryDirectory() as tempd_path:
        tempd: Final = pathlib.Path(tempd_path)
        logging.debug("Using %(tempd)s as a temporary directory", {"tempd": tempd})
        spdir, var_data = extract_variants_data(cfg, tempd)

        images: Final = filter_docker_images(cfg, var_data)
        logging.debug(
            "About to test %(count)d containers: %(images)s",
            {"count": len(images), "images": sorted(images.keys())},
        )
        ordered: Final = sorted(images.items())

        asyncio.run(run_tests(cfg, spdir, ordered, var_data))


if __name__ == "__main__":
    main()
