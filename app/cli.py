from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.scrub_pipeline import scrub_folder, write_output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scrub every supported statement in a folder into one combined string.",
    )
    parser.add_argument("--input", "-i", type=Path, default=Path("data"), help="input folder")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("output/scrubbed_output.txt"),
        help="combined output file",
    )
    args = parser.parse_args(argv)

    result = scrub_folder(args.input)
    write_output(result, args.output)

    summary = {
        "output": str(args.output),
        "file_count": result.file_count,
        "files": [
            {
                "name": f.display_name,
                "format": f.fmt,
                "status": f.status,
                "chars": f.char_count,
                "error": f.error,
            }
            for f in result.files
        ],
        "placeholder_occurrences": result.stats.occurrences,
        "placeholder_types": result.stats.unique_by_type,
        "total_placeholder_occurrences": result.placeholder_count,
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
