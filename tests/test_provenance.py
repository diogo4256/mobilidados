"""The lock file (what was retrieved, with checksums, and what changed since) and HTTP access: user agent, timeout, atomic writes."""

import pytest

from streetfit import provenance
from streetfit.config import Case
from streetfit.provenance import REQUEST_TIMEOUT_S, Lock, write_atomic
from streetfit.sources import raw_path


def test_lock_detects_changed_and_missing_files(make_case):
    case = Case.load(make_case())
    case.raw_dir.mkdir(parents=True)
    p = raw_path(case, "cartography")
    p.write_text("{}")
    lock = Lock(case.lock_path)
    lock.record("cartography", [p], case.raw_dir)
    lock.save()
    p.write_text('{"changed": true}')
    assert [s for *_, s in Lock(case.lock_path).verify(case.raw_dir)] == ["changed"]
    p.unlink()
    assert [s for *_, s in Lock(case.lock_path).verify(case.raw_dir)] == ["missing"]


def test_the_user_agent_names_the_tool_and_optionally_a_contact(monkeypatch):
    monkeypatch.delenv("STREETFIT_CONTACT", raising=False)
    assert provenance.user_agent() == f"streetfit/{provenance.__version__}"
    monkeypatch.setenv("STREETFIT_CONTACT", "me@example.org")
    assert provenance.user_agent() == f"streetfit/{provenance.__version__} (me@example.org)"


def test_http_get_applies_the_default_timeout_and_raises_on_an_error_status(monkeypatch):
    seen: dict = {}

    class Response:
        def __init__(self, status):
            self.status = status

        def raise_for_status(self):
            if self.status >= 400:
                raise RuntimeError(f"HTTP {self.status}")

    class Session:
        def get(self, url, params, timeout):
            seen.update(url=url, params=params, timeout=timeout)
            return Response(500 if url.endswith("/broken") else 200)

    monkeypatch.setattr(provenance, "session", Session)
    provenance.http_get("https://example.org/ok", {"f": "json"})
    assert seen == {"url": "https://example.org/ok", "params": {"f": "json"}, "timeout": REQUEST_TIMEOUT_S}
    with pytest.raises(RuntimeError, match="HTTP 500"):
        provenance.http_get("https://example.org/broken")


def test_write_atomic_replaces_the_file_and_leaves_no_partial_one(tmp_path):
    target = tmp_path / "data.json"
    write_atomic(target, b"first")
    write_atomic(target, b"second")
    assert target.read_bytes() == b"second"
    assert [p.name for p in tmp_path.iterdir()] == ["data.json"]
