"""Tests for volume manifest contracts (VolumeManifest, DerivedVolumeManifest)."""
from __future__ import annotations

import pytest

from geox.seismic.contracts import (
    DerivedVolumeManifest,
    DomainSpec,
    GridSpec,
    ImplementationRef,
    ParentRef,
    SignalSpec,
    StorageSpec,
    ValiditySpec,
    VolumeManifest,
)


def _valid_volume_kwargs() -> dict:
    return {
        "artifact_id": "geox://volume/f3/raw",
        "sha256": "a" * 64,
        "created_by": "kimi-code/FI-008",
        "domain": DomainSpec(
            vertical="TWT",
            unit="ms",
            crs="EPSG:4326",
        ),
        "grid": GridSpec(
            shape=(651, 951, 463),
            spacing=(25.0, 25.0, 4.0),
            axis_order=("iline", "xline", "twt"),
        ),
        "signal": SignalSpec(
            polarity="SEG_NORMAL",
            phase_deg=0.0,
            amplitude_status="relative",
            sample_interval_ms=4.0,
        ),
        "storage": StorageSpec(
            uri="s3://geox-data/f3/raw.zarr",
            chunks=(32, 32, 256),
            dtype="float32",
        ),
        "source_uri": "file:///data/f3.sgy",
        "source_format": "SEGY_REV2",
        "classification": "PUBLIC",
    }


class TestGridSpec:
    def test_valid_grid(self):
        g = GridSpec(shape=(100, 200, 300), spacing=(25.0, 25.0, 4.0))
        assert g.shape == (100, 200, 300)
        assert g.axis_order == ("iline", "xline", "twt")

    def test_wrong_length(self):
        with pytest.raises(ValueError):
            GridSpec(shape=(100, 200), spacing=(25.0, 25.0, 4.0))

    def test_negative_shape_rejected(self):
        with pytest.raises(ValueError):
            GridSpec(shape=(100, 200, 0), spacing=(25.0, 25.0, 4.0))


class TestVolumeManifest:
    def test_valid_volume(self):
        v = VolumeManifest(**_valid_volume_kwargs())
        assert v.schema_uri == "geox.seismic.volume-manifest.v1"
        assert v.signal.polarity == "SEG_NORMAL"

    def test_sha256_lowercase(self):
        kw = _valid_volume_kwargs()
        kw["sha256"] = "A" * 64
        v = VolumeManifest(**kw)
        assert v.sha256 == "a" * 64

    def test_sha256_length_validated(self):
        kw = _valid_volume_kwargs()
        kw["sha256"] = "abcdef"
        with pytest.raises(ValueError):
            VolumeManifest(**kw)

    def test_extra_field_rejected(self):
        kw = _valid_volume_kwargs()
        kw["unknown_field"] = "bad"
        with pytest.raises(ValueError):
            VolumeManifest(**kw)

    def test_content_hash_stable(self):
        v1 = VolumeManifest(**_valid_volume_kwargs())
        v2 = VolumeManifest(**_valid_volume_kwargs())
        # created_at may differ; content_hash excludes it
        assert v1.content_hash() == v2.content_hash()
        assert len(v1.content_hash()) == 64


class TestDerivedVolumeManifest:
    def _derived_kwargs(self):
        kw = _valid_volume_kwargs()
        kw.update(
            {
                "artifact_id": "geox://derived/coherence/test",
                "capability_id": "geox.seismic.attr.coherence.v1",
                "implementation": ImplementationRef(
                    name="gst_energy_ratio",
                    version="1.0.0",
                    code_hash="b" * 64,
                    library="numpy_scipy_v1",
                ),
                "parents": [
                    ParentRef(
                        artifact_id="geox://volume/f3/raw",
                        sha256="a" * 64,
                        role="input",
                    )
                ],
                "validity": ValiditySpec(
                    qc_ref="geox://qc/test",
                ),
                "parameters": {"window": [5, 5, 9]},
            }
        )
        return kw

    def test_valid_derived(self):
        d = DerivedVolumeManifest(**self._derived_kwargs())
        assert d.capability_id == "geox.seismic.attr.coherence.v1"
        assert d.schema_uri == "geox.seismic.derived-volume-manifest.v1"
        assert len(d.parents) == 1

    def test_capability_id_pattern(self):
        kw = self._derived_kwargs()
        kw["capability_id"] = "geox.seismic.attr.coherence"  # missing .vN
        with pytest.raises(ValueError):
            DerivedVolumeManifest(**kw)

    def test_duplicate_parents_rejected(self):
        kw = self._derived_kwargs()
        kw["parents"] = [
            ParentRef(artifact_id="geox://volume/f3/raw", sha256="a" * 64, role="input"),
            ParentRef(artifact_id="geox://volume/f3/raw", sha256="a" * 64, role="reference"),
        ]
        with pytest.raises(ValueError):
            DerivedVolumeManifest(**kw)

    def test_empty_parents_rejected(self):
        kw = self._derived_kwargs()
        kw["parents"] = []
        with pytest.raises(ValueError):
            DerivedVolumeManifest(**kw)

    def test_human_edits_recorded(self):
        kw = self._derived_kwargs()
        kw["human_edits"] = [
            {
                "actor": "arif",
                "timestamp": "2026-09-29T00:00:00Z",
                "operation": "polygon_reshape",
                "parent_version": "geox://derived/coherence/test@v0",
            }
        ]
        d = DerivedVolumeManifest(**kw)
        assert len(d.human_edits) == 1
        assert d.human_edits[0]["operation"] == "polygon_reshape"
