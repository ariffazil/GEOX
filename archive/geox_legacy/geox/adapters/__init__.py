"""
GEOX Adapters — Domain bridges for arifOS ecosystem
DITEMPA BUKAN DIBERI
"""

from .wealth_bridge import geox_to_wealth, AdmissibilityError, WealthInput

__all__ = ["geox_to_wealth", "AdmissibilityError", "WealthInput"]