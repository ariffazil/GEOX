"""CLI: receipt <fixture.json> | benchmark [--out path]."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from geox_core.engines.structural_reconstruction.ledger import evaluate, run_benchmark


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        return 2
    if args[0] == "receipt" and len(args) == 2:
        payload = json.loads(Path(args[1]).read_text(encoding="utf-8"))
        receipt = evaluate(payload)
        sys.stdout.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        return 0 if receipt.get("schema") else 1
    if args[0] == "benchmark" and len(args) in {1, 3}:
        out = None
        if len(args) == 3:
            if args[1] != "--out":
                return 2
            out = Path(args[2])
        receipt = run_benchmark(out_path=out, write=True)
        sys.stdout.write(json.dumps({"reality_discipline_pass": receipt["reality_discipline_pass"], "failures": receipt["failures"]}) + "\n")
        return 0 if receipt["reality_discipline_pass"] else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
