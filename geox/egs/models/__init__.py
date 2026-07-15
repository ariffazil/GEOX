"""EGS models: entities, uncertainty, provenance, claims, sts, translation."""

# Rebuild EarthGraph to resolve forward refs (StateGraph, TranslationLayer)
from geox.egs.models.entities import EarthGraph
from geox.egs.models.sts import StateGraph
from geox.egs.models.translation import TranslationLayer

EarthGraph.model_rebuild()
