"""TDD: miner.py must not silently drop .jsonl files.

The project miner (mempalace.miner.scan_project) walks a directory and
keeps only files whose suffix is in READABLE_EXTENSIONS. The whitelist
contains `.json` but NOT `.jsonl`. Every ChatGPT export, Claude Code
transcript, or any other jsonl transcript dumped into a project
directory is silently dropped with no user-visible output.

Two paths to fix this, both tested here:

  1. READABLE_EXTENSIONS must include `.jsonl` so the file is at least
     readable as text (jsonl is line-delimited JSON — each line is
     already valid text for embedding).
  2. OR scan_project must surface skipped .jsonl files to the user so
     they know to use `--mode convos`.

We test (1) — include .jsonl in READABLE_EXTENSIONS. This matches how
`.json` is already handled: the miner doesn't care what the structure
is, it chunks the text.

Written BEFORE the fix.
"""

import tempfile
from pathlib import Path

from mempalace.miner import READABLE_EXTENSIONS, scan_project


class TestJsonlNotSilentlySkipped:
    def test_jsonl_in_readable_extensions(self):
        """`.jsonl` must be in the readable-extensions whitelist.

        `.json` is already there (see mempalace/miner.py:30). `.jsonl`
        is conceptually the same thing — line-delimited JSON — and all
        of Claude Code's transcripts, ChatGPT exports, and similar
        tooling writes `.jsonl`. Excluding it silently drops user data.
        """
        assert ".jsonl" in READABLE_EXTENSIONS, (
            "mempalace/miner.py:READABLE_EXTENSIONS contains `.json` "
            "but NOT `.jsonl`. Every jsonl file in a mined project is "
            "silently skipped at miner.py:722 "
            "(`if filepath.suffix.lower() not in READABLE_EXTENSIONS: "
            "continue`). This causes the 'convos not being saved' bug "
            "reported by users — the hook fires `mempalace mine`, the "
            "miner walks the directory, skips every .jsonl file, exits "
            "cleanly. No warning, no log line, user sees nothing wrong. "
            "Add `.jsonl` to READABLE_EXTENSIONS."
        )

    def test_scan_project_picks_up_jsonl_file(self):
        """scan_project should find .jsonl files in the target dir."""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            jsonl_path = tmpdir / "transcript.jsonl"
            jsonl_path.write_text(
                '{"role": "user", "content": "hello"}\n'
                '{"role": "assistant", "content": "hi there"}\n'
                '{"role": "user", "content": "how do I install this"}\n'
                '{"role": "assistant", "content": "pip install mempalace"}\n'
            )

            found = scan_project(str(tmpdir))
            found_names = [p.name for p in found]
            assert "transcript.jsonl" in found_names, (
                "scan_project silently dropped transcript.jsonl. "
                f"Returned: {found_names}. Users placing transcript "
                "exports in a project directory expect them to be mined."
            )
