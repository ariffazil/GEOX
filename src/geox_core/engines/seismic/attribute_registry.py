"""
GEOX Dynamic Seismic Attribute Registry
════════════════════════════════════════
Forged from paleoscan_python attribute system patterns.

Provides an extensible registry of seismic attribute compute functions.
Attributes are self-describing classes with category/type metadata and a
compute() hook that takes an Image3d and returns an Image3d.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy.ndimage import generic_filter
from scipy.signal import hilbert, welch

from geox_core.core.geox_image import (
    Image2d,
    Image3d,
    AttributeCategory,
    AttributeType,
)

logger = logging.getLogger("geox.seismic.attribute_registry")

# ─────────────────── ABSTRACT BASE ───────────────────


class SeismicAttribute(ABC):
    """
    Abstract base for a seismic attribute compute engine.
    PaleoScan equivalent: paleoscan_python.Attribute (compute layer only)
    """

    name: str = ""
    categories: set[str] = field(default_factory=set)
    types: set[str] = field(default_factory=set)
    properties: dict[str, Any] = field(default_factory=dict)

    @abstractmethod
    def compute(self, input_image: Image3d, **kwargs: Any) -> Image3d:
        """
        Compute the attribute on the input volume/frame.

        Args:
            input_image: Input Image3d (or Image2d for Line attributes)
            **kwargs: Attribute-specific parameters

        Returns:
            Output Image3d with computed attribute values.
        """
        ...

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "categories": sorted(self.categories),
            "types": sorted(self.types),
            "properties": self.properties,
        }


# ─────────────────── BUILT-IN ATTRIBUTES ───────────────────


class AmplitudeAttribute(SeismicAttribute):
    name = "Amplitude"
    categories = {AttributeCategory.BasicSeismic.value, AttributeCategory.Seismic.value}
    types = {AttributeType.Volume.value, AttributeType.Line.value}
    properties = {"window_ms": 40, "units": "normalized"}

    def compute(self, input_image: Image3d, **kwargs: Any) -> Image3d:
        out = Image3d(input_image.width, input_image.height, input_image.length, name="Amplitude")
        out._data = input_image._data.copy()
        return out


class VarianceAttribute(SeismicAttribute):
    name = "Variance"
    categories = {AttributeCategory.Structural.value, AttributeCategory.Seismic.value}
    types = {AttributeType.Volume.value, AttributeType.Line.value}
    properties = {"window_ms": 60, "units": "normalized", "window_size": 11}

    def compute(self, input_image: Image3d, **kwargs: Any) -> Image3d:
        window = kwargs.get("window_size", self.properties["window_size"])
        out = Image3d(input_image.width, input_image.height, input_image.length, name="Variance")
        for i in range(input_image.length):
            slice_2d = input_image._data[i, :, :]
            var_slice = generic_filter(slice_2d, np.var, size=window)
            out._data[i, :, :] = var_slice.astype(np.float32)
        return out


class SweetnessAttribute(SeismicAttribute):
    name = "Sweetness"
    categories = {AttributeCategory.BasicSeismic.value, AttributeCategory.Seismic.value}
    types = {AttributeType.Volume.value, AttributeType.Line.value}
    properties = {"window_ms": 40, "units": "ratio"}

    def compute(self, input_image: Image3d, **kwargs: Any) -> Image3d:
        out = Image3d(input_image.width, input_image.height, input_image.length, name="Sweetness")
        for i in range(input_image.length):
            slice_2d = input_image._data[i, :, :]
            analytic = hilbert(slice_2d, axis=-1)
            env = np.abs(analytic)
            peak = np.max(env, axis=-1, keepdims=True)
            total = np.sum(np.abs(analytic) ** 2, axis=-1, keepdims=True) + 1e-10
            sweetness_raw = (peak / np.sqrt(total / slice_2d.shape[-1])).squeeze()
            out._data[i, :, :] = np.clip(sweetness_raw, 0, 10).astype(np.float32)
        return out


class CoherenceAttribute(SeismicAttribute):
    name = "Coherence"
    categories = {AttributeCategory.Structural.value, AttributeCategory.Seismic.value}
    types = {AttributeType.Volume.value, AttributeType.Line.value}
    properties = {"window_ms": 80, "units": "normalized", "half_window": 3}

    def compute(self, input_image: Image3d, **kwargs: Any) -> Image3d:
        hw = kwargs.get("half_window", self.properties["half_window"])
        out = Image3d(input_image.width, input_image.height, input_image.length, name="Coherence")
        for i in range(input_image.length):
            arr = input_image._data[i, :, :]
            m, n = arr.shape
            C = np.zeros((m, n))
            for y in range(hw, m - hw):
                for x in range(hw, n - hw):
                    window = arr[y - hw : y + hw + 1, x - hw : x + hw + 1]
                    if window.size >= 4:
                        C[y, x] = np.mean(window) / (np.std(window) + 1e-10)
            out._data[i, :, :] = np.clip(C, 0, 1).astype(np.float32)
        return out


class EnvelopeAttribute(SeismicAttribute):
    name = "Envelope"
    categories = {AttributeCategory.ComplexSeismic.value, AttributeCategory.Seismic.value}
    types = {AttributeType.Volume.value, AttributeType.Line.value}
    properties = {"window_ms": 40, "units": "normalized"}

    def compute(self, input_image: Image3d, **kwargs: Any) -> Image3d:
        out = Image3d(input_image.width, input_image.height, input_image.length, name="Envelope")
        for i in range(input_image.length):
            slice_2d = input_image._data[i, :, :]
            analytic = hilbert(slice_2d, axis=-1)
            out._data[i, :, :] = np.abs(analytic).astype(np.float32)
        return out


class FrequencyAvgAttribute(SeismicAttribute):
    name = "Frequency Average"
    categories = {AttributeCategory.Frequency.value, AttributeCategory.Seismic.value}
    types = {AttributeType.Volume.value, AttributeType.Line.value}
    properties = {"window_ms": 60, "units": "Hz", "nperseg": 64}

    def compute(self, input_image: Image3d, **kwargs: Any) -> Image3d:
        nperseg = kwargs.get("nperseg", self.properties["nperseg"])
        out = Image3d(input_image.width, input_image.height, input_image.length, name="FreqAvg")
        for i in range(input_image.length):
            arr = input_image._data[i, :, :]
            freqs = np.zeros(arr.shape[:2])
            ns = min(nperseg, arr.shape[-1])
            if ns >= 2:
                for y in range(arr.shape[0]):
                    f, p = welch(arr[y], nperseg=ns)
                    freqs[y] = np.sum(f * p) / (np.sum(p) + 1e-10)
            out._data[i, :, :] = freqs.astype(np.float32)
        return out


# ─────────────────── REGISTRY ───────────────────


class AttributeRegistry:
    """
    Dynamic registry for seismic attributes.
    PaleoScan equivalent: paleoscan_python attribute registry (compute layer)
    """

    def __init__(self):
        self._attributes: dict[str, SeismicAttribute] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        defaults = [
            AmplitudeAttribute(),
            VarianceAttribute(),
            SweetnessAttribute(),
            CoherenceAttribute(),
            EnvelopeAttribute(),
            FrequencyAvgAttribute(),
        ]
        for attr in defaults:
            self.register(attr)

    def register(self, attribute: SeismicAttribute) -> bool:
        if not attribute.name:
            logger.warning("Cannot register attribute with empty name")
            return False
        if attribute.name in self._attributes:
            logger.debug(f"Attribute '{attribute.name}' already registered — overwriting")
        self._attributes[attribute.name] = attribute
        logger.info(f"Registered attribute: {attribute.name}")
        return True

    def unregister(self, attribute_name: str) -> bool:
        if attribute_name not in self._attributes:
            return False
        del self._attributes[attribute_name]
        logger.info(f"Unregistered attribute: {attribute_name}")
        return True

    def list_attributes(self) -> list[str]:
        return sorted(self._attributes.keys())

    def get(self, name: str) -> SeismicAttribute | None:
        return self._attributes.get(name)

    def compute(
        self,
        attribute_name: str,
        input_image: Image3d,
        **kwargs: Any,
    ) -> Image3d | None:
        attr = self.get(attribute_name)
        if attr is None:
            logger.error(f"Attribute '{attribute_name}' not found in registry")
            return None
        return attr.compute(input_image, **kwargs)

    def filter_by_category(self, category: str) -> list[SeismicAttribute]:
        return [a for a in self._attributes.values() if category in a.categories]

    def filter_by_type(self, type_: str) -> list[SeismicAttribute]:
        return [a for a in self._attributes.values() if type_ in a.types]

    def to_dict(self) -> dict[str, Any]:
        return {
            "attributes": {name: attr.to_dict() for name, attr in self._attributes.items()},
            "count": len(self._attributes),
        }


# ─────────────────── GLOBAL INSTANCE ───────────────────

DEFAULT_REGISTRY = AttributeRegistry()
