from pathlib import Path

from formula.data_fetcher import prepare_data, OEIS_FORMULAS_URL


def test_prepare_data_runs_needed_steps(tmp_path):
    data_dir = tmp_path / "data"
    loda_home = tmp_path / "loda"
    seq_dir = loda_home / "seqs" / "oeis"
    seq_dir.mkdir(parents=True)

    # Seed source files that would normally come from loda update
    for name in ["names", "offsets", "stripped"]:
        (seq_dir / name).write_text(f"{name}\n", encoding="utf-8")

    commands = []

    def runner(cmd, stdout_path=None):
        commands.append((cmd, stdout_path))
        if stdout_path:
            Path(stdout_path).write_text("generated\n", encoding="utf-8")

    def downloader(dst: Path) -> None:
        dst.write_text("oeis formulas\n", encoding="utf-8")

    def exporter(dst: Path) -> None:
        dst.write_text("loda formulas\n", encoding="utf-8")

    report = prepare_data(
        data_dir=data_dir,
        loda_home=loda_home,
        force=False,
        run_if_missing=True,
        dry_run=False,
        runner=runner,
        downloader=downloader,
        export_formulas=exporter,
    )

    assert (data_dir / "names").exists()
    assert (data_dir / "offsets").exists()
    assert (data_dir / "stripped").exists()
    assert (data_dir / "formulas-loda.txt").exists()
    assert (data_dir / "formulas-oeis.txt").exists()
    assert any(cmd == ["loda", "update"] for cmd, _ in commands)
    assert any(cmd == ["loda", "export-formulas"] for cmd, _ in commands)
    assert OEIS_FORMULAS_URL in str(report.skipped) or report.created


def test_prepare_data_skips_when_present(tmp_path):
    data_dir = tmp_path / "data"
    loda_home = tmp_path / "loda"
    seq_dir = loda_home / "seqs" / "oeis"
    seq_dir.mkdir(parents=True)

    for name in ["names", "offsets", "stripped"]:
        (data_dir / name).parent.mkdir(parents=True, exist_ok=True)
        (data_dir / name).write_text("existing\n", encoding="utf-8")
    (data_dir / "formulas-loda.txt").write_text("existing\n", encoding="utf-8")
    (data_dir / "formulas-oeis.txt").write_text("existing\n", encoding="utf-8")

    commands = []

    def runner(cmd, stdout_path=None):
        commands.append((cmd, stdout_path))

    report = prepare_data(
        data_dir=data_dir,
        loda_home=loda_home,
        force=False,
        run_if_missing=True,
        dry_run=False,
        runner=runner,
        downloader=lambda dst: dst.write_text("", encoding="utf-8"),
        export_formulas=lambda dst: dst.write_text("", encoding="utf-8"),
    )

    # No commands should run because everything already exists
    assert not commands
    assert not report.created
    assert report.skipped
