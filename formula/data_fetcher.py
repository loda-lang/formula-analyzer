"""
Utilities to fetch and regenerate data files used by the formula analyzer.

The helper functions here are intentionally conservative: they only download or
regenerate files when asked or when the target files are missing. Heavy steps
(like ``loda export-formulas``) are isolated so callers can gate them behind
explicit flags or dry runs.
"""
from __future__ import annotations

import gzip
import shutil
import subprocess
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional

# URL hosting the OEIS formulas export
OEIS_FORMULAS_URL = "https://api.loda-lang.org/v2/sequences/data/oeis/formulas.gz"

CommandRunner = Callable[[List[str], Optional[Path]], None]
Downloader = Callable[[Path], None]
Exporter = Callable[[Path], None]


@dataclass
class DataPaths:
    """Container for canonical data file paths."""

    data_dir: Path

    @property
    def names(self) -> Path:
        return self.data_dir / "names"

    @property
    def offsets(self) -> Path:
        return self.data_dir / "offsets"

    @property
    def stripped(self) -> Path:
        return self.data_dir / "stripped"

    @property
    def formulas_loda(self) -> Path:
        # Keep the legacy filename expected by tests and the analyzer.
        return self.data_dir / "formulas-loda.txt"

    @property
    def formulas_oeis(self) -> Path:
        return self.data_dir / "formulas-oeis.txt"


@dataclass
class FetchReport:
    """Summary of actions performed during data preparation."""

    created: List[Path]
    skipped: List[str]
    commands: List[List[str]]


def prepare_data(
    data_dir: Path,
    loda_home: Optional[Path] = None,
    force: bool = False,
    run_if_missing: bool = True,
    dry_run: bool = False,
    runner: Optional[CommandRunner] = None,
    downloader: Optional[Downloader] = None,
    export_formulas: Optional[Exporter] = None,
) -> FetchReport:
    """Ensure required data files exist.

    The function performs the minimum necessary work:
    - ``names``, ``offsets``, ``stripped`` are copied from ``$HOME/loda/seqs/oeis``
      after running ``loda update`` once.
    - ``formulas-loda.txt`` is generated via ``loda export-formulas``.
    - ``formulas-oeis.txt`` is downloaded from the public API and ungzipped.

    Nothing runs unless the corresponding target is missing or ``force`` is
    True. Callers can set ``dry_run`` to see what would happen without doing
    work. A custom ``runner``/``downloader``/``export_formulas`` can be passed
    for testing.
    """

    paths = DataPaths(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    loda_home = loda_home or Path.home() / "loda"
    seqs_dir = loda_home / "seqs" / "oeis"

    run_cmd = runner or _default_runner
    download_fn = downloader or _download_oeis_formulas
    export_fn = export_formulas or (lambda dst: _export_loda_formulas(dst, run_cmd))

    created: List[Path] = []
    skipped: List[str] = []
    commands: List[List[str]] = []

    def _mark_created(path: Path) -> None:
        created.append(path)

    def _mark_skipped(reason: str) -> None:
        skipped.append(reason)

    def _maybe_run_update() -> None:
        cmd = ["loda", "update"]
        commands.append(cmd)
        if not dry_run:
            run_cmd(cmd, None)

    # Copy names/offsets/stripped if needed.
    core_files = {
        "names": paths.names,
        "offsets": paths.offsets,
        "stripped": paths.stripped,
    }
    core_needed = force or any(not p.exists() for p in core_files.values())
    if core_needed and run_if_missing:
        if not seqs_dir.exists():
            raise FileNotFoundError(
                f"Expected OEIS exports under {seqs_dir}; run loda update manually."
            )
        _maybe_run_update()
        for key, dst in core_files.items():
            src = seqs_dir / key
            if not src.exists():
                raise FileNotFoundError(f"Missing source file: {src}")
            if dry_run:
                _mark_skipped(f"would copy {src} -> {dst}")
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            _mark_created(dst)
    else:
        _mark_skipped("core files already present")

    # Export LODA formulas.
    if force or not paths.formulas_loda.exists():
        cmd = ["loda", "export-formulas"]
        commands.append(cmd)
        if dry_run:
            _mark_skipped(f"would run {' '.join(cmd)} > {paths.formulas_loda}")
        else:
            print(f"Running '{' '.join(cmd)}' (this may take a few minutes)...")
            export_fn(paths.formulas_loda)
            _mark_created(paths.formulas_loda)
    else:
        _mark_skipped("formulas-loda.txt already present")

    # Download OEIS formulas.
    if force or not paths.formulas_oeis.exists():
        if dry_run:
            _mark_skipped(f"would download {OEIS_FORMULAS_URL} -> {paths.formulas_oeis}")
        else:
            download_fn(paths.formulas_oeis)
            _mark_created(paths.formulas_oeis)
    else:
        _mark_skipped("formulas-oeis.txt already present")

    return FetchReport(created=created, skipped=skipped, commands=commands)


def _default_runner(cmd: List[str], stdout_path: Optional[Path]) -> None:
    """Run a shell command, optionally piping stdout to a file."""

    if stdout_path:
        with open(stdout_path, "w", encoding="utf-8") as handle:
            subprocess.run(cmd, stdout=handle, check=True)
    else:
        subprocess.run(cmd, check=True)


def _export_loda_formulas(dst: Path, runner: CommandRunner) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    runner(["loda", "export-formulas"], dst)


def _download_oeis_formulas(dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(OEIS_FORMULAS_URL) as response:
        with gzip.GzipFile(fileobj=response) as gz:
            content = gz.read().decode("utf-8")
    dst.write_text(content, encoding="utf-8")


__all__ = [
    "prepare_data",
    "FetchReport",
    "DataPaths",
    "OEIS_FORMULAS_URL",
]
