"""
GEOX Spatial Transforms — 4x4 Affine Matrix Operations
═══════════════════════════════════════════════════════
Forged from paleoscan_python coordinate system patterns.

Provides deterministic math for converting between:
  • Block space  (discrete voxel indices)
  • Survey space (inline/crossline/time or depth)
  • World space  (real-world XY coordinates + elevation)

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from geox_core.core.geox_image import BlockSpace, SurveySpace, WorldSpace

logger = logging.getLogger("geox.spatial.transforms")

# ─────────────────── MATRIX CONSTRUCTION ───────────────────


def build_block_to_survey_matrix(block: BlockSpace, survey: SurveySpace) -> np.ndarray:
    """
    Build 4×4 affine matrix that maps block indices → survey coordinates.

    Mapping:
      x_block → x_survey (crossline)
      y_block → y_survey (inline)
      z_block → z_survey (time/depth)
    """
    sx = (survey.x_max - survey.x_min) / max(block.width - 1, 1)
    sy = (survey.y_max - survey.y_min) / max(block.length - 1, 1)
    sz = (survey.z_max - survey.z_min) / max(block.height - 1, 1)

    matrix = np.eye(4, dtype=np.float64)
    matrix[0, 0] = sx
    matrix[1, 1] = sy
    matrix[2, 2] = sz
    matrix[0, 3] = survey.x_min
    matrix[1, 3] = survey.y_min
    matrix[2, 3] = survey.z_min
    return matrix


def build_survey_to_block_matrix(block: BlockSpace, survey: SurveySpace) -> np.ndarray:
    """Inverse of block→survey. Maps survey coordinates → block indices."""
    forward = build_block_to_survey_matrix(block, survey)
    return np.linalg.inv(forward)


def build_block_to_world_matrix(block: BlockSpace, world: WorldSpace) -> np.ndarray:
    """
    Build 4×4 affine matrix that maps block indices → world coordinates.

    Uses the 4 corner points P0–P3 to solve for the affine transform.
    P0 = (0, 0, 0) block → worldP0
    P1 = (width, 0, 0) block → worldP1
    P2 = (0, 0, height) block → worldP2  (vertical)
    P3 = (0, length, 0) block → worldP3  (inline)
    """
    # Build system: M @ block_corners = world_corners
    # We'll solve for M (4×4) using least squares on the 4 known correspondences
    block_corners = np.array(
        [
            [0, 0, 0, 1],
            [block.width, 0, 0, 1],
            [0, 0, block.height, 1],
            [0, block.length, 0, 1],
        ],
        dtype=np.float64,
    )

    world_corners = np.array(
        [
            np.append(world.p0, 1),
            np.append(world.p1, 1),
            np.append(world.p2, 1),
            np.append(world.p3, 1),
        ],
        dtype=np.float64,
    )

    # Solve M^T using least squares: block_corners @ M^T = world_corners
    M_t, _, _, _ = np.linalg.lstsq(block_corners, world_corners, rcond=None)
    M = M_t.T
    return M


def build_world_to_block_matrix(block: BlockSpace, world: WorldSpace) -> np.ndarray:
    """Inverse of block→world. Maps world coordinates → block indices."""
    forward = build_block_to_world_matrix(block, world)
    return np.linalg.inv(forward)


def build_survey_to_world_matrix(survey: SurveySpace, world: WorldSpace) -> np.ndarray:
    """
    Compose survey→block→world to get direct survey→world matrix.
    Requires a dummy BlockSpace with unit dimensions since survey→world
    is independent of block resolution.
    """
    dummy_block = BlockSpace(width=2, height=2, length=2)
    s2b = build_survey_to_block_matrix(dummy_block, survey)
    b2w = build_block_to_world_matrix(dummy_block, world)
    return b2w @ s2b


def build_world_to_survey_matrix(survey: SurveySpace, world: WorldSpace) -> np.ndarray:
    """Inverse of survey→world."""
    forward = build_survey_to_world_matrix(survey, world)
    return np.linalg.inv(forward)


# ─────────────────── COORDINATE SYSTEM BUNDLE ───────────────────


class CoordinateSystem:
    """
    Holds BlockSpace, SurveySpace, WorldSpace, and precomputed 4×4 transforms.
    PaleoScan equivalent: paleoscan_python.Volume coordinate spaces.
    """

    def __init__(
        self,
        block: BlockSpace | None = None,
        survey: SurveySpace | None = None,
        world: WorldSpace | None = None,
    ):
        self.block = block or BlockSpace()
        self.survey = survey or SurveySpace()
        self.world = world or WorldSpace()
        self._matrices: dict[str, np.ndarray] = {}
        self._rebuild()

    def _rebuild(self) -> None:
        """Recompute all transformation matrices."""
        try:
            self._matrices["block_to_survey"] = build_block_to_survey_matrix(self.block, self.survey)
            self._matrices["survey_to_block"] = build_survey_to_block_matrix(self.block, self.survey)
        except Exception as e:
            logger.debug(f"block↔survey matrix build failed: {e}")
            self._matrices["block_to_survey"] = np.eye(4)
            self._matrices["survey_to_block"] = np.eye(4)

        try:
            self._matrices["block_to_world"] = build_block_to_world_matrix(self.block, self.world)
            self._matrices["world_to_block"] = build_world_to_block_matrix(self.block, self.world)
        except Exception as e:
            logger.debug(f"block↔world matrix build failed: {e}")
            self._matrices["block_to_world"] = np.eye(4)
            self._matrices["world_to_block"] = np.eye(4)

        try:
            self._matrices["survey_to_world"] = build_survey_to_world_matrix(self.survey, self.world)
            self._matrices["world_to_survey"] = build_world_to_survey_matrix(self.survey, self.world)
        except Exception as e:
            logger.debug(f"survey↔world matrix build failed: {e}")
            self._matrices["survey_to_world"] = np.eye(4)
            self._matrices["world_to_survey"] = np.eye(4)

    def set_block_space(self, width: int, height: int, length: int) -> None:
        self.block.set_block_space(width, height, length)
        self._rebuild()

    def set_survey_space(
        self,
        x_min: float,
        x_max: float,
        z_min: float,
        z_max: float,
        y_min: float,
        y_max: float,
    ) -> None:
        self.survey.set_survey_space(x_min, x_max, z_min, z_max, y_min, y_max)
        self._rebuild()

    def set_world_space(
        self,
        p0: np.ndarray,
        p1: np.ndarray,
        p2: np.ndarray,
        p3: np.ndarray,
    ) -> None:
        self.world.set_world_space(p0, p1, p2, p3)
        self._rebuild()

    def get_matrix(self, from_space: str, to_space: str) -> np.ndarray:
        key = f"{from_space}_to_{to_space}"
        if key not in self._matrices:
            raise KeyError(f"Transform matrix not available: {from_space} → {to_space}")
        return self._matrices[key]

    @property
    def inline_resolution(self) -> float:
        """Inline resolution: survey inline range / block length."""
        return (self.survey.y_max - self.survey.y_min) / max(self.block.length - 1, 1)

    @property
    def crossline_resolution(self) -> float:
        """Crossline resolution: survey crossline range / block width."""
        return (self.survey.x_max - self.survey.x_min) / max(self.block.width - 1, 1)

    @property
    def vertical_resolution(self) -> float:
        """Vertical resolution: survey vertical range / block height."""
        return (self.survey.z_max - self.survey.z_min) / max(self.block.height - 1, 1)

    def transform_points(
        self,
        points: np.ndarray,
        from_space: str,
        to_space: str,
    ) -> np.ndarray:
        """
        Transform an array of points between coordinate spaces.

        Args:
            points: Array of shape (N, 3) or (3,) with coordinates.
            from_space: "block", "survey", or "world"
            to_space: "block", "survey", or "world"

        Returns:
            Transformed points with same shape as input.
        """
        points = np.asarray(points, dtype=np.float64)
        single = points.ndim == 1
        if single:
            points = points.reshape(1, -1)

        if points.shape[1] != 3:
            raise ValueError(f"Points must have 3 columns, got {points.shape[1]}")

        matrix = self.get_matrix(from_space, to_space)
        homogeneous = np.hstack([points, np.ones((points.shape[0], 1))])
        transformed = (matrix @ homogeneous.T).T
        result = transformed[:, :3]

        return result[0] if single else result

    def to_dict(self) -> dict[str, Any]:
        return {
            "block_space": self.block.to_dict(),
            "survey_space": self.survey.to_dict(),
            "world_space": self.world.to_dict(),
            "inline_resolution": self.inline_resolution,
            "crossline_resolution": self.crossline_resolution,
            "vertical_resolution": self.vertical_resolution,
            "matrices": {k: v.tolist() for k, v in self._matrices.items()},
        }


# ─────────────────── POINT UTILITIES ───────────────────


def block_to_survey(
    points: np.ndarray,
    block: BlockSpace,
    survey: SurveySpace,
) -> np.ndarray:
    """Utility: transform points from block space to survey space."""
    cs = CoordinateSystem(block=block, survey=survey)
    return cs.transform_points(points, "block", "survey")


def survey_to_block(
    points: np.ndarray,
    block: BlockSpace,
    survey: SurveySpace,
) -> np.ndarray:
    """Utility: transform points from survey space to block space."""
    cs = CoordinateSystem(block=block, survey=survey)
    return cs.transform_points(points, "survey", "block")


def block_to_world(
    points: np.ndarray,
    block: BlockSpace,
    world: WorldSpace,
) -> np.ndarray:
    """Utility: transform points from block space to world space."""
    cs = CoordinateSystem(block=block, world=world)
    return cs.transform_points(points, "block", "world")


def world_to_block(
    points: np.ndarray,
    block: BlockSpace,
    world: WorldSpace,
) -> np.ndarray:
    """Utility: transform points from world space to block space."""
    cs = CoordinateSystem(block=block, world=world)
    return cs.transform_points(points, "world", "block")


def survey_to_world(
    points: np.ndarray,
    survey: SurveySpace,
    world: WorldSpace,
) -> np.ndarray:
    """Utility: transform points from survey space to world space."""
    cs = CoordinateSystem(survey=survey, world=world)
    return cs.transform_points(points, "survey", "world")


def world_to_survey(
    points: np.ndarray,
    survey: SurveySpace,
    world: WorldSpace,
) -> np.ndarray:
    """Utility: transform points from world space to survey space."""
    cs = CoordinateSystem(survey=survey, world=world)
    return cs.transform_points(points, "world", "survey")
