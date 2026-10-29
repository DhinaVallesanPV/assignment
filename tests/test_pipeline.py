from __future__ import annotations

from pathlib import Path

from app.services.scrub_pipeline import scrub_folder, write_output


def test_pipeline_headers_statuses_and_cross_file_consistency(tmp_path: Path) -> None:
    (tmp_path / "one.txt").write_text(
        "Email a@example.com\nAddress: 1 Test Street, Testville\n",
        encoding="utf-8",
    )
    (tmp_path / "two.csv").write_text("email,note\na@example.com,ok\n", encoding="utf-8")
    (tmp_path / "three.xyz").write_text("ignored", encoding="utf-8")

    result = scrub_folder(tmp_path)

    assert "---- File: one.txt ----" in result.combined_text
    assert "---- File: two.csv ----" in result.combined_text
    assert "---- File: three.xyz ----" in result.combined_text
    assert "[SKIPPED:" in result.combined_text
    assert result.combined_text.count("<EMAIL_1>") == 2
    assert "Address: <ADDRESS_1>" in result.combined_text
    assert {f.status for f in result.files} == {"processed", "skipped"}


def test_empty_folder_produces_empty_output(tmp_path: Path) -> None:
    result = scrub_folder(tmp_path)
    assert result.combined_text == ""
    assert result.file_count == 0


def test_write_output(tmp_path: Path) -> None:
    (tmp_path / "input").mkdir()
    (tmp_path / "input" / "a.txt").write_text("Email a@example.com", encoding="utf-8")
    result = scrub_folder(tmp_path / "input")
    target = tmp_path / "out" / "scrubbed.txt"
    write_output(result, target)
    assert target.exists()
    assert "<EMAIL_1>" in target.read_text(encoding="utf-8")
