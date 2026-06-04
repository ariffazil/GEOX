"""
GEOX Canonical Image Substrate — Forged from paleoscan_python v2.0.0 patterns
═══════════════════════════════════════════════════════════════════════════════
Unifies Image2d, Image3d, BlockSpace, SurveySpace, WorldSpace, and coordinate
transforms into a single physics-governed substrate.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

import numpy as np

logger = logging.getLogger("geox.image")

# ─────────────────── CONSTANTS ───────────────────

NO_VALUE = np.nan  # PaleoScan uses a sentinel; GEOX uses IEEE NaN (industry standard)


# ─────────────────── ENUMS ───────────────────

class ScanOrientation(str, Enum):
    Inline = "inline"
    Crossline = "crossline"
    TimeSlice = "time_slice"
    DepthSlice = "depth_slice"


class AttributeCategory(str, Enum):
    BasicSeismic = "BasicSeismic"
    ComplexSeismic = "ComplexSeismic"
    Frequency = "Frequency"
    General = "General"
    GeoModel = "GeoModel"
    GeoModelSurface = "GeoModelSurface"
    Seismic = "Seismic"
    Stratigraphic = "Stratigraphic"
    Structural = "Structural"
    TruncationSeismic = "TruncationSeismic"


class AttributeType(str, Enum):
    Line = "Line"
    Volume = "Volume"


# ─────────────────── IMAGE2D ───────────────────

class Image2d:
    """
    2-dimensional container for 32-bit floating point data.
    Backed by numpy ndarray for interoperability with scipy, torch, etc.
    """

    def __init__(self, width: int, height: int, name: str = ""):
        if width < 1 or height < 1:
            raise IndexError(f"Invalid Image2d dimensions: ({width}, {height})")
        self.width = width
        self.height = height
        self.name = name
        self._data = np.full((height, width), NO_VALUE, dtype=np.float32)

    # ── Properties ──

    @property
    def size(self) -> int:
        return self.width * self.height

    @property
    def data(self) -> np.ndarray:
        """Direct access to underlying numpy array (shape: height × width)."""
        return self._data

    @property
    def buffer_address(self) -> int:
        """Memory address of the underlying buffer for ctypes interop."""
        return self._data.ctypes.data

    @property
    def min_value(self) -> float:
        valid = self._data[~np.isnan(self._data)]
        return float(valid.min()) if valid.size > 0 else float(NO_VALUE)

    @property
    def max_value(self) -> float:
        valid = self._data[~np.isnan(self._data)]
        return float(valid.max()) if valid.size > 0 else float(NO_VALUE)

    @property
    def average(self) -> float:
        valid = self._data[~np.isnan(self._data)]
        return float(valid.mean()) if valid.size > 0 else float(NO_VALUE)

    @property
    def standard_deviation(self) -> float:
        valid = self._data[~np.isnan(self._data)]
        return float(valid.std()) if valid.size > 0 else float(NO_VALUE)

    # ── Methods ──

    def clear(self) -> None:
        """Fill image with NO_VALUE (np.nan)."""
        self._data.fill(NO_VALUE)

    def fill(self, values: float | list[float] | np.ndarray) -> None:
        """Fill image with a scalar, list, or numpy array."""
        if isinstance(values, (int, float)):
            self._data.fill(float(values))
        elif isinstance(values, np.ndarray):
            if values.size != self.size:
                raise RuntimeError(
                    f"Fill array size {values.size} != image size {self.size}"
                )
            self._data = values.reshape(self.height, self.width).astype(np.float32)
        elif isinstance(values, list):
            if len(values) != self.size:
                raise RuntimeError(
                    f"Fill list length {len(values)} != image size {self.size}"
                )
            self._data = np.array(values, dtype=np.float32).reshape(self.height, self.width)
        else:
            raise TypeError(f"Unsupported fill type: {type(values)}")

    def get_value(self, x: int, y: int) -> float:
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise IndexError(f"Coordinate ({x}, {y}) out of range [0..{self.width-1}, 0..{self.height-1}]")
        return float(self._data[y, x])

    def set_value(self, x: int, y: int, value: float) -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise IndexError(f"Coordinate ({x}, {y}) out of range [0..{self.width-1}, 0..{self.height-1}]")
        self._data[y, x] = float(value)

    def __getitem__(self, key: tuple[int, int]) -> float:
        x, y = key
        return self.get_value(x, y)

    def __setitem__(self, key: tuple[int, int], value: float) -> None:
        x, y = key
        self.set_value(x, y, value)

    def resize(self, new_width: int, new_height: int) -> None:
        if new_width < 1 or new_height < 1:
            raise RuntimeError(f"Invalid resize dimensions: ({new_width}, {new_height})")
        if new_width == self.width and new_height == self.height:
            import warnings
            warnings.warn("Resize to same size — no operation performed", RuntimeWarning)
            return
        self.width = new_width
        self.height = new_height
        self._data = np.full((new_height, new_width), NO_VALUE, dtype=np.float32)

    def transpose(self) -> "Image2d":
        """Return a transposed copy (width ↔ height)."""
        t = Image2d(self.height, self.width, name=f"{self.name}_T")
        t._data = self._data.T.copy()
        return t

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "Image2d",
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "size": self.size,
            "min_value": self.min_value if not np.isnan(self.min_value) else None,
            "max_value": self.max_value if not np.isnan(self.max_value) else None,
            "average": self.average if not np.isnan(self.average) else None,
            "standard_deviation": self.standard_deviation if not np.isnan(self.standard_deviation) else None,
        }

    def __repr__(self) -> str:
        return f"geox.Image2d: name = '{self.name}', width = {self.width}, height = {self.height}"


# ─────────────────── BLOCKSPACE ───────────────────

@dataclass
class BlockSpace:
    """
    Represents the discrete block dimensions of a volume or image.
    PaleoScan equivalent: paleoscan_python.BlockSpace
    """

    width: int = 1   # crossline count (X)
    height: int = 1  # sample count   (Z)
    length: int = 1  # inline count   (Y)

    def __post_init__(self):
        if self.width < 1 or self.height < 1 or self.length < 1:
            raise RuntimeError(f"Invalid BlockSpace: ({self.width}, {self.height}, {self.length})")

    @property
    def inline_resolution(self) -> float:
        """Resolution along inline axis (samples per inline)."""
        return 1.0  # Default; overridden by survey space linkage

    @property
    def crossline_resolution(self) -> float:
        """Resolution along crossline axis (samples per crossline)."""
        return 1.0

    @property
    def vertical_resolution(self) -> float:
        """Resolution along vertical axis (samples per depth/time unit)."""
        return 1.0

    def set_block_space(self, width: int, height: int, length: int) -> None:
        if width < 1 or height < 1 or length < 1:
            raise RuntimeError(f"Invalid BlockSpace: ({width}, {height}, {length})")
        self.width = width
        self.height = height
        self.length = length

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "BlockSpace",
            "width": self.width,
            "height": self.height,
            "length": self.length,
        }


# ─────────────────── SURVEYSPACE ───────────────────

@dataclass
class SurveySpace:
    """
    Represents the survey-coordinate bounds of a volume.
    PaleoScan mapping:
      xMin/xMax → crossline range
      zMin/zMax → time/depth range
      yMin/yMax → inline range
    """

    x_min: float = 0.0   # crossline min
    x_max: float = 1.0   # crossline max
    z_min: float = 0.0   # time/depth min
    z_max: float = 1.0   # time/depth max
    y_min: float = 0.0   # inline min
    y_max: float = 1.0   # inline max

    def set_survey_space(
        self,
        x_min: float,
        x_max: float,
        z_min: float,
        z_max: float,
        y_min: float,
        y_max: float,
    ) -> None:
        self.x_min = x_min
        self.x_max = x_max
        self.z_min = z_min
        self.z_max = z_max
        self.y_min = y_min
        self.y_max = y_max

    @property
    def inline_range(self) -> tuple[float, float]:
        return (self.y_min, self.y_max)

    @property
    def crossline_range(self) -> tuple[float, float]:
        return (self.x_min, self.x_max)

    @property
    def vertical_range(self) -> tuple[float, float]:
        return (self.z_min, self.z_max)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "SurveySpace",
            "x_range": [self.x_min, self.x_max],
            "z_range": [self.z_min, self.z_max],
            "y_range": [self.y_min, self.y_max],
        }


# ─────────────────── WORLDSPACE ───────────────────

@dataclass
class WorldSpace:
    """
    Represents the world-coordinate corners of a volume.
    PaleoScan defines 4 corner points P0–P3.
    """

    p0: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float64))  # [first IL, first XL, min Z]
    p1: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float64))  # [first IL, last XL, min Z]
    p2: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float64))  # [first IL, first XL, max Z]
    p3: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float64))  # [last IL, first XL, min Z]

    def set_world_space(
        self,
        p0: np.ndarray,
        p1: np.ndarray,
        p2: np.ndarray,
        p3: np.ndarray,
    ) -> None:
        self.p0 = np.asarray(p0, dtype=np.float64)
        self.p1 = np.asarray(p1, dtype=np.float64)
        self.p2 = np.asarray(p2, dtype=np.float64)
        self.p3 = np.asarray(p3, dtype=np.float64)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "WorldSpace",
            "p0": self.p0.tolist(),
            "p1": self.p1.tolist(),
            "p2": self.p2.tolist(),
            "p3": self.p3.tolist(),
        }


# ─────────────────── IMAGE3D ───────────────────

class Image3d(BlockSpace):
    """
    3-dimensional container for 32-bit floating point data.
    Extends BlockSpace. PaleoScan equivalent: paleoscan_python.Image3d
    """

    def __init__(self, width: int = 1, height: int = 1, length: int = 1, name: str = ""):
        super().__init__(width=width, height=height, length=length)
        self.name = name
        self._data = np.full((length, height, width), NO_VALUE, dtype=np.float32)

    @property
    def data(self) -> np.ndarray:
        """Direct access to underlying numpy array (shape: length × height × width)."""
        return self._data

    def clear(self) -> None:
        self._data.fill(NO_VALUE)

    def get_value(self, x: int, y: int, z: int) -> float:
        if not (0 <= x < self.width and 0 <= y < self.length and 0 <= z < self.height):
            raise IndexError(
                f"Coordinate ({x}, {y}, {z}) out of range "
                f"[0..{self.width-1}, 0..{self.length-1}, 0..{self.height-1}]"
            )
        return float(self._data[y, z, x])

    def set_value(self, x: int, y: int, z: int, value: float) -> None:
        if not (0 <= x < self.width and 0 <= y < self.length and 0 <= z < self.height):
            raise IndexError(
                f"Coordinate ({x}, {y}, {z}) out of range "
                f"[0..{self.width-1}, 0..{self.length-1}, 0..{self.height-1}]"
            )
        self._data[y, z, x] = float(value)

    def __getitem__(self, key: tuple[int, int, int]) -> float:
        x, y, z = key
        return self.get_value(x, y, z)

    def __setitem__(self, key: tuple[int, int, int], value: float) -> None:
        x, y, z = key
        self.set_value(x, y, z, value)

    def resize(self, new_width: int, new_height: int, new_length: int) -> None:
        if new_width < 1 or new_height < 1 or new_length < 1:
            raise RuntimeError(f"Invalid resize: ({new_width}, {new_height}, {new_length})")
        if new_width == self.width and new_height == self.height and new_length == self.length:
            import warnings
            warnings.warn("Resize to same size — no operation performed", RuntimeWarning)
            return
        self.width = new_width
        self.height = new_height
        self.length = new_length
        self._data = np.full((new_length, new_height, new_width), NO_VALUE, dtype=np.float32)

    def set_block_space(self, width: int, height: int, length: int) -> None:
        """Overloaded: changes block space AND resizes buffer."""
        super().set_block_space(width, height, length)
        self._data = np.full((length, height, width), NO_VALUE, dtype=np.float32)

    def get_image(self, orientation: ScanOrientation, index: int) -> Image2d:
        """Extract a 2D frame from the 3D volume by orientation and index."""
        if orientation == ScanOrientation.Inline:
            if not (0 <= index < self.length):
                raise IndexError(f"Inline index {index} out of range [0..{self.length-1}]")
            img = Image2d(self.width, self.height, name=f"{self.name}_inline_{index}")
            img._data = self._data[index, :, :].copy()
            return img
        elif orientation == ScanOrientation.Crossline:
            if not (0 <= index < self.width):
                raise IndexError(f"Crossline index {index} out of range [0..{self.width-1}]")
            img = Image2d(self.height, self.length, name=f"{self.name}_crossline_{index}")
            img._data = self._data[:, :, index].copy().T
            return img
        elif orientation in (ScanOrientation.TimeSlice, ScanOrientation.DepthSlice):
            if not (0 <= index < self.height):
                raise IndexError(f"Time/depth index {index} out of range [0..{self.height-1}]")
            img = Image2d(self.width, self.length, name=f"{self.name}_slice_{index}")
            img._data = self._data[:, index, :].copy()
            return img
        else:
            raise ValueError(f"Unknown orientation: {orientation}")

    def set_image(self, orientation: ScanOrientation, index: int, image: Image2d) -> None:
        """Write a 2D frame into the 3D volume at orientation and index."""
        if orientation == ScanOrientation.Inline:
            if not (0 <= index < self.length):
                raise IndexError(f"Inline index {index} out of range [0..{self.length-1}]")
            if image.width != self.width or image.height != self.height:
                raise IndexError(
                    f"Image size ({image.width}, {image.height}) != expected ({self.width}, {self.height})"
                )
            self._data[index, :, :] = image._data.copy()
        elif orientation == ScanOrientation.Crossline:
            if not (0 <= index < self.width):
                raise IndexError(f"Crossline index {index} out of range [0..{self.width-1}]")
            if image.width != self.height or image.height != self.length:
                raise IndexError(
                    f"Image size ({image.width}, {image.height}) != expected ({self.height}, {self.length})"
                )
            self._data[:, :, index] = image._data.T.copy()
        elif orientation in (ScanOrientation.TimeSlice, ScanOrientation.DepthSlice):
            if not (0 <= index < self.height):
                raise IndexError(f"Time/depth index {index} out of range [0..{self.height-1}]")
            if image.width != self.width or image.height != self.length:
                raise IndexError(
                    f"Image size ({image.width}, {image.height}) != expected ({self.width}, {self.length})"
                )
            self._data[:, index, :] = image._data.copy()
        else:
            raise ValueError(f"Unknown orientation: {orientation}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "Image3d",
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "length": self.length,
            "size": self.width * self.height * self.length,
        }

    def __repr__(self) -> str:
        return f"geox.Image3d: name = '{self.name}', width = {self.width}, height = {self.height}, length = {self.length}"
