"""geox-ugly — run the Ugly Corpus and print a receipt.

Exit codes: 0 all contracts pass · 1 a contract failed · 2 GEOX not importable.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from . import SEED, __version__
from .contracts import budget_result, run_contracts
from .generate import build_corpus, manifest_digest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="geox-ugly",
        description="100% synthetic benchmark for GEOX truth contracts (L5, fail-closed QC, G-1 refusal).",
    )
    parser.add_argument("--json", metavar="PATH", help="write the full JSON receipt to PATH")
    parser.add_argument("--workdir", metavar="DIR", help="keep fixtures in DIR instead of a temp dir")
    parser.add_argument("--budget", type=float, default=60.0, help="seconds (default 60)")
    parser.add_argument("--quiet", action="store_true", help="receipt only, no table")
    args = parser.parse_args(argv)

    started = time.perf_counter()
    workdir = Path(args.workdir) if args.workdir else Path(tempfile.mkdtemp(prefix="ugly-corpus-"))
    fixtures = build_corpus(workdir)
    try:
        results = run_contracts(fixtures)
    except ImportError as exc:
        print(f"geox-ugly: GEOX is not importable: {exc}", file=sys.stderr)
        print("Install the engine or point PYTHONPATH at its src/: pip install geox-mcp", file=sys.stderr)
        return 2
    elapsed = time.perf_counter() - started
    results.append(budget_result(elapsed, args.budget))

    passed = sum(1 for r in results if r.ok)
    total = len(results)
    receipt = {
        "corpus": "geox-ugly-corpus",
        "version": __version__,
        "seed": SEED,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "duration_s": round(elapsed, 3),
        "manifest_digest": manifest_digest(fixtures),
        "fixtures": [
            {
                "name": f.name,
                "sha256": f.sha256,
                "curves": list(f.curves),
                "purpose": f.purpose,
                "synthetic": f.synthetic,
                "seed": f.generator_seed,
            }
            for f in fixtures
        ],
        "contracts": [{"contract": r.contract, "ok": r.ok, "detail": r.detail, "evidence": r.evidence} for r in results],
        "summary": {"passed": passed, "total": total, "verdict": "PASS" if passed == total else "FAIL"},
    }

    if not args.quiet:
        print(f"GEOX UGLY CORPUS v{__version__} — 100% synthetic, seed {SEED}")
        print(f"manifest {receipt['manifest_digest'][:16]}…  fixtures {len(fixtures)}")
        for r in results:
            print(f"[{'PASS' if r.ok else 'FAIL'}] {r.contract}: {r.detail}")
        print(
            f"{passed}/{total} contracts passed in {elapsed:.2f}s (budget {args.budget:.0f}s) → {receipt['summary']['verdict']}"
        )

    if args.json:
        Path(args.json).write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        print(f"receipt → {args.json}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
