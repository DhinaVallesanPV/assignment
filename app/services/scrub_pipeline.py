from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.services.file_extractor import discover_files, extract_file
from app.services.pii_scrubber import PlaceholderVault, ScrubStats, scrub_text


@dataclass
class FileOutcome:
    display_name: str
    fmt: str
    status: str
    char_count: int
    error: str | None = None


@dataclass
class ScrubResult:
    combined_text: str
    files: list[FileOutcome]
    stats: ScrubStats

    @property
    def file_count(self) -> int:
        return len(self.files)

    @property
    def scrubbed_chars(self) -> int:
        return len(self.combined_text)

    @property
    def placeholder_count(self) -> int:
        return sum(self.stats.occurrences.values())


def _body_for(extracted, vault: PlaceholderVault) -> str:
    if extracted.status == "processed":
        scrubbed = scrub_text(extracted.text, vault)
        return scrubbed if scrubbed.strip() else "[NO TEXT AFTER SCRUBBING]"
    if extracted.status == "empty":
        return "[EMPTY: no extractable text]"
    if extracted.status == "skipped":
        return f"[SKIPPED: {extracted.error or 'unsupported format'}]"
    return f"[FAILED: {extracted.error or 'extraction error'}]"


def scrub_folder(folder: Path, vault: PlaceholderVault | None = None) -> ScrubResult:
    """Scrub every file in *folder* into one combined string with per-file headers."""
    folder = Path(folder)
    vault = vault or PlaceholderVault()
    outcomes: list[FileOutcome] = []
    blocks: list[str] = []

    for path in discover_files(folder):
        extracted = extract_file(path, folder)
        body = _body_for(extracted, vault)
        blocks.append(f"---- File: {extracted.display_name} ----\n{body}")
        outcomes.append(
            FileOutcome(
                display_name=extracted.display_name,
                fmt=extracted.fmt,
                status=extracted.status,
                char_count=extracted.char_count,
                error=extracted.error,
            )
        )

    combined = "\n\n".join(blocks)
    if combined:
        combined += "\n"

    return ScrubResult(combined_text=combined, files=outcomes, stats=vault.stats())


def write_output(result: ScrubResult, output_path: Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.combined_text, encoding="utf-8")
    return output_path
