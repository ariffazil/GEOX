from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

ARTEFACT_DIR = Path("/root/geox/ops/reports")


class ArtefactEmitter:
    """
    WAJIB #5: Excel / Artefact Emission.
    Intelligence not exportable = not institutional.
    """

    def __init__(self, output_dir: Path = ARTEFACT_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def emit_well_ingestion_report(self, well_result: dict) -> str:
        """Produces a human-readable CSV report for management/TAC slides."""
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"TAC_IngestReport_{well_result.get('well_id', 'UNKNOWN')}_{timestamp}.csv"
        filepath = self.output_dir / filename

        # Flatten data for management consumption
        data = {
            "Parameter": [
                "Well ID",
                "UWI",
                "Source Type",
                "Claim State",
                "Suitability",
                "Total Curves",
                "Depth Range",
                "QC Fail Count",
            ],
            "Value": [
                well_result.get("well_id"),
                well_result.get("uwi"),
                well_result.get("source_type"),
                well_result.get("claim_state"),
                well_result.get("suitability"),
                well_result.get("n_curves"),
                str(well_result.get("depth_range")),
                well_result.get("qcfail_count"),
            ],
        }

        # Add curve specifics
        for curve in well_result.get("curves", []):
            data["Parameter"].append(f"Curve Loaded: {curve.get('mnemonic')}")
            data["Value"].append("OK")

        for limit in well_result.get("limitations", []):
            data["Parameter"].append("LIMITATION / WARNING")
            data["Value"].append(limit)

        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        return str(filepath)
