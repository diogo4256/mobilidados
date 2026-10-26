"""The command line: what it prints, to which stream, and the exit code, on minimal cases (no network)."""

from mobilidados import cli, sources
from mobilidados.config import Case, MobilidadosError
from mobilidados.provenance import Lock
from mobilidados.sources import raw_path


def locked_case(make_case):
    """A minimal case whose two cached sources are recorded in its lock."""
    case = Case.load(make_case())
    case.raw_dir.mkdir(parents=True)
    lock = Lock(case.lock_path)
    for sid in ("cartography", "street_axes"):
        raw_path(case, sid).write_text(f'{{"source": "{sid}"}}')
        lock.record(sid, [raw_path(case, sid)], case.raw_dir)
    lock.save()
    return case


def test_a_mobilidados_error_is_printed_without_a_traceback_and_exits_2(tmp_path, capsys):
    assert cli.main(["verify", str(tmp_path)]) == 2
    out, err = capsys.readouterr()
    assert err.startswith("error: ")
    assert "case.toml not found" in err
    assert out == ""


def test_lint_exits_1_when_it_finds_issues(tmp_path, capsys):
    draft = tmp_path / "draft.md"
    draft.write_text("A faixa está sempre ocupada.\n", encoding="utf-8")
    assert cli.main(["lint", str(draft)]) == 1
    out = capsys.readouterr().out
    assert "generalisation" in out
    assert out.rstrip().endswith("1 issue(s)")


def test_lint_exits_0_on_a_clean_draft(tmp_path, capsys):
    draft = tmp_path / "draft.md"
    draft.write_text("A faixa livre mede 4,90 m na secção medida.\n", encoding="utf-8")
    assert cli.main(["lint", str(draft)]) == 0
    assert capsys.readouterr().out.strip() == "0 issue(s)"


def test_verify_exits_0_when_every_file_matches_the_lock(make_case, capsys):
    case = locked_case(make_case)
    assert cli.main(["verify", str(case.root)]) == 0
    assert capsys.readouterr().out.strip() == "2/2 files match the lock"


def test_verify_lists_only_the_files_that_differ_and_exits_1(make_case, capsys):
    case = locked_case(make_case)
    raw_path(case, "street_axes").write_text('{"source": "changed"}')
    assert cli.main(["verify", str(case.root)]) == 1
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 2
    assert lines[0].split() == ["changed", "street_axes", "street_axes.json"]
    assert lines[1] == "1/2 files match the lock"


IDENTIFY = """
[sources.identify]
kind = "arcgis_identify"
url = "https://example.org/MapServer/identify"
layers = "all:1"
sr = 3763
licence = "x"
"""


def test_verify_does_not_fail_on_a_routing_network_cache_that_a_run_makes(make_case, capsys):
    case = Case.load(make_case(IDENTIFY))
    case.raw_dir.mkdir(parents=True)
    lock = Lock(case.lock_path)
    for sid in ("cartography", "identify"):
        raw_path(case, sid).write_text("{}")
        lock.record(sid, [raw_path(case, sid)], case.raw_dir)
    lock.save()
    raw_path(case, "identify").unlink()  # a fresh clone: fetch does not make it, the first online run does
    assert cli.main(["verify", str(case.root)]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].split()[:3] == ["later", "identify", "identify.json"]
    assert lines[1] == "1/2 files match the lock"


def test_run_reports_an_unknown_stage_as_an_error(make_case, capsys):
    assert cli.main(["run", str(make_case()), "--stages", "nope"]) == 2
    assert capsys.readouterr().err.startswith("error: unknown stages ['nope']")


def test_snapshot_copies_the_redistributable_sources(make_case, tmp_path):
    case = locked_case(make_case)
    assert cli.main(["snapshot", str(case.root), str(tmp_path / "snap")]) == 0
    assert sorted(p.name for p in (tmp_path / "snap").iterdir()) == ["_snapshot.json", "cartography.json"]  # the axes licence is not stated


def test_verify_live_downloads_again_and_reports_what_differs_leaving_the_cache_and_the_lock(make_case, monkeypatch, capsys):
    case = locked_case(make_case)
    lock, cached = case.lock_path.read_bytes(), raw_path(case, "cartography").read_bytes()

    def download(src, dest):
        if dest.stem == "street_axes":
            raise MobilidadosError("gis.example did not answer as expected")
        dest.write_text('{"source": "cartography, updated"}')
        return {}

    monkeypatch.setattr(sources, "_download", download)
    assert cli.main(["verify", str(case.root), "--live"]) == 1
    lines = [line.split(maxsplit=1) for line in capsys.readouterr().out.splitlines()]
    assert lines == [
        ["cartography", "cartography.json: changed"],
        ["street_axes", "-: error: gis.example did not answer as expected"],
        ["0/2", "files served today match the lock"],
    ]
    assert (case.lock_path.read_bytes(), raw_path(case, "cartography").read_bytes()) == (lock, cached)


def test_verify_live_exits_0_when_every_source_still_serves_the_locked_files(make_case, monkeypatch, capsys):
    case = locked_case(make_case)

    def download(src, dest):
        dest.write_text(f'{{"source": "{dest.stem}"}}')
        return {}

    monkeypatch.setattr(sources, "_download", download)
    assert cli.main(["verify", str(case.root), "--live"]) == 0
    assert capsys.readouterr().out.strip() == "2/2 files served today match the lock"
