"""deep_time/ics_chart.py — Embedded ICS Chronostratigraphic Chart v2024/12.

F2 TRUTH: ICS boundary ages are stable, peer-reviewed values. We embed
them directly so the tool is deterministic and offline-capable. The
canonical reference is the International Commission on Stratigraphy
(ICS) International Chronostratigraphic Chart v2024/12.

Coverage: Periods (top of Cenozoic to base of Cambrian) + Eras
(Phanerozoic + Proterozoic + Archean + Hadean) + common epoch names
for the Cenozoic.

DITEMPA BUKAN DIBEI — Forged, Not Given.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ChronostratUnit:
    """A single named chronostratigraphic unit (period, epoch, era, age)."""

    name: str
    rank: str  # 'eon' | 'era' | 'period' | 'epoch' | 'age'
    top_ma: float
    base_ma: float
    ics_id: str = ""
    parent: str = ""

    def contains(self, age_ma: float) -> bool:
        """Whether `age_ma` (in Ma, before present) falls within this unit.

        Note: a younger rock has a smaller top_ma (closer to 0). The
        convention here is top_ma < base_ma throughout.
        """
        return self.base_ma >= age_ma >= self.top_ma

    @property
    def duration_myr(self) -> float:
        return self.base_ma - self.top_ma

    @property
    def midpoint_ma(self) -> float:
        return (self.base_ma + self.top_ma) / 2.0


# ─── Eras (top of Cambrian to Phanerozoic) ────────────────────────────────────
ERAS: tuple[ChronostratUnit, ...] = (
    ChronostratUnit("Cenozoic", "era", 0.0, 66.0, ics_id="era-cenozoic"),
    ChronostratUnit("Mesozoic", "era", 66.0, 251.902, ics_id="era-mesozoic"),
    ChronostratUnit("Paleozoic", "era", 251.902, 538.8, ics_id="era-paleozoic"),
    # Precambrian
    ChronostratUnit("Neoproterozoic", "era", 538.8, 1000.0, ics_id="era-neoproterozoic"),
    ChronostratUnit("Mesoproterozoic", "era", 1000.0, 1600.0, ics_id="era-mesoproterozoic"),
    ChronostratUnit("Paleoproterozoic", "era", 1600.0, 2500.0, ics_id="era-paleoproterozoic"),
    ChronostratUnit("Archean", "era", 2500.0, 4000.0, ics_id="era-archean"),
    ChronostratUnit("Hadean", "era", 4000.0, 4544.0, ics_id="era-hadean"),
)


# ─── Periods (Phanerozoic) ────────────────────────────────────────────────────
PERIODS: tuple[ChronostratUnit, ...] = (
    ChronostratUnit("Quaternary", "period", 0.0, 2.58, ics_id="period-quaternary", parent="Cenozoic"),
    ChronostratUnit("Neogene", "period", 2.58, 23.03, ics_id="period-neogene", parent="Cenozoic"),
    ChronostratUnit("Paleogene", "period", 23.03, 66.0, ics_id="period-paleogene", parent="Cenozoic"),
    ChronostratUnit("Cretaceous", "period", 66.0, 145.0, ics_id="period-cretaceous", parent="Mesozoic"),
    ChronostratUnit("Jurassic", "period", 145.0, 201.4, ics_id="period-jurassic", parent="Mesozoic"),
    ChronostratUnit("Triassic", "period", 201.4, 251.902, ics_id="period-triassic", parent="Mesozoic"),
    ChronostratUnit("Permian", "period", 251.902, 298.9, ics_id="period-permian", parent="Paleozoic"),
    ChronostratUnit("Carboniferous", "period", 298.9, 358.9, ics_id="period-carboniferous", parent="Paleozoic"),
    ChronostratUnit("Devonian", "period", 358.9, 419.2, ics_id="period-devonian", parent="Paleozoic"),
    ChronostratUnit("Silurian", "period", 419.2, 443.8, ics_id="period-silurian", parent="Paleozoic"),
    ChronostratUnit("Ordovician", "period", 443.8, 485.4, ics_id="period-ordovician", parent="Paleozoic"),
    ChronostratUnit("Cambrian", "period", 485.4, 538.8, ics_id="period-cambrian", parent="Paleozoic"),
)


# ─── Common Epochs (Cenozoic + Cretaceous + Jurassic + Triassic + Permian) ───
EPOCHS: tuple[ChronostratUnit, ...] = (
    # Cenozoic epochs
    ChronostratUnit("Holocene", "epoch", 0.0, 0.0117, ics_id="epoch-holocene", parent="Quaternary"),
    ChronostratUnit("Pleistocene", "epoch", 0.0117, 2.58, ics_id="epoch-pleistocene", parent="Quaternary"),
    ChronostratUnit("Pliocene", "epoch", 2.58, 5.333, ics_id="epoch-pliocene", parent="Neogene"),
    ChronostratUnit("Miocene", "epoch", 5.333, 23.03, ics_id="epoch-miocene", parent="Neogene"),
    ChronostratUnit("Oligocene", "epoch", 23.03, 33.9, ics_id="epoch-oligocene", parent="Paleogene"),
    ChronostratUnit("Eocene", "epoch", 33.9, 56.0, ics_id="epoch-eocene", parent="Paleogene"),
    ChronostratUnit("Paleocene", "epoch", 56.0, 66.0, ics_id="epoch-paleocene", parent="Paleogene"),
    # Cretaceous epochs
    ChronostratUnit("Late Cretaceous", "epoch", 66.0, 100.5, ics_id="epoch-late-cretaceous", parent="Cretaceous"),
    ChronostratUnit("Early Cretaceous", "epoch", 100.5, 145.0, ics_id="epoch-early-cretaceous", parent="Cretaceous"),
    # Jurassic epochs
    ChronostratUnit("Late Jurassic", "epoch", 145.0, 163.5, ics_id="epoch-late-jurassic", parent="Jurassic"),
    ChronostratUnit("Middle Jurassic", "epoch", 163.5, 174.7, ics_id="epoch-middle-jurassic", parent="Jurassic"),
    ChronostratUnit("Early Jurassic", "epoch", 174.7, 201.4, ics_id="epoch-early-jurassic", parent="Jurassic"),
    # Triassic epochs
    ChronostratUnit("Late Triassic", "epoch", 201.4, 227.0, ics_id="epoch-late-triassic", parent="Triassic"),
    ChronostratUnit("Middle Triassic", "epoch", 227.0, 242.0, ics_id="epoch-middle-triassic", parent="Triassic"),
    ChronostratUnit("Early Triassic", "epoch", 242.0, 251.902, ics_id="epoch-early-triassic", parent="Triassic"),
    # Permian epochs
    ChronostratUnit("Lopingian", "epoch", 251.902, 259.51, ics_id="epoch-lopingian", parent="Permian"),
    ChronostratUnit("Guadalupian", "epoch", 259.51, 273.01, ics_id="epoch-guadalupian", parent="Permian"),
    ChronostratUnit("Cisuralian", "epoch", 273.01, 298.9, ics_id="epoch-cisuralian", parent="Permian"),
)


# ─── Fuzzy-phrase aliases (informal → formal interval) ───────────────────────
# Lower-case keys; values are (age_ma, "named") where age_ma is the midpoint
# of the canonical interval. The age_resolver maps these to [start, end].
# Short single-word keys enable substring matching for queries like
# "what was Earth like during dinosaurs?".
FUZZY_PHRASES: dict[str, tuple[float, str]] = {
    # Multi-word phrases
    "age of dinosaurs": (160.0, "Mesozoic"),
    "age of mammals": (33.0, "Cenozoic"),
    "age of reptiles": (180.0, "Mesozoic"),
    "age of fish": (400.0, "Devonian"),
    "age of insects": (350.0, "Carboniferous"),
    "age of amphibians": (380.0, "Carboniferous"),
    "age of trilobites": (510.0, "Cambrian"),
    "age of giant dragonflies": (320.0, "Carboniferous"),
    "ice age": (0.5, "Pleistocene"),
    "last glacial maximum": (0.020, "Pleistocene"),
    "snowball earth": (677.0, "Cryogenian"),
    "cambrian explosion": (515.0, "Cambrian"),
    "great ordovician biodiversification event": (465.0, "Ordovician"),
    "when dinosaurs ruled": (160.0, "Mesozoic"),
    "when life exploded": (520.0, "Cambrian"),
    "when pangea existed": (250.0, "Pangaea"),
    "when pangaea existed": (250.0, "Pangaea"),
    "during dinosaurs": (160.0, "Mesozoic"),
    "during the dinosaurs": (160.0, "Mesozoic"),
    "k-pg boundary": (66.043, "K-Pg boundary"),
    "k/t boundary": (66.043, "K-Pg boundary"),
    "cretaceous-paleogene boundary": (66.043, "K-Pg boundary"),
    "cretaceous paleogene boundary": (66.043, "K-Pg boundary"),
    "permian-triassic boundary": (251.902, "P-Tr boundary"),
    "permian triassic boundary": (251.902, "P-Tr boundary"),
    "p-tr boundary": (251.902, "P-Tr boundary"),
    "triassic-jurassic boundary": (201.4, "T-J boundary"),
    "triassic jurassic boundary": (201.4, "T-J boundary"),
    "t-j boundary": (201.4, "T-J boundary"),
    "ordovician-silurian boundary": (443.8, "O-S boundary"),
    "devonian-carboniferous boundary": (358.9, "D-C boundary"),
    "petm": (56.0, "Paleocene-Eocene Thermal Maximum"),
    "paleocene-eocene thermal maximum": (56.0, "Paleocene-Eocene Thermal Maximum"),
    "eocene-oligocene boundary": (33.9, "E-O boundary"),
    "mco": (17.0, "Miocene Climatic Optimum"),
    "miocene climatic optimum": (17.0, "Miocene Climatic Optimum"),
    # Single-word / short keys for substring matching
    "dinosaurs": (160.0, "Mesozoic"),
    "dinosaur": (160.0, "Mesozoic"),
    "mammals": (33.0, "Cenozoic"),
    "mammal": (33.0, "Cenozoic"),
    "trilobites": (510.0, "Cambrian"),
    "trilobite": (510.0, "Cambrian"),
    "pangaea": (250.0, "Pangaea"),
    "pangea": (250.0, "Pangaea"),
    "rodinia": (900.0, "Rodinia"),
    "gondwana": (300.0, "Gondwana"),
    "laurasia": (180.0, "Laurasia"),
    "hadean": (4272.0, "Hadean"),  # midpoint of 4000-4544
    "archean": (3250.0, "Archean"),  # midpoint of 2500-4000
    "proterozoic": (1750.0, "Proterozoic"),  # midpoint of 538.8-2500
}


@dataclass(frozen=True)
class ICSChart:
    """Container for an ICS Chart version."""

    version: str
    eras: tuple[ChronostratUnit, ...] = field(default_factory=tuple)
    periods: tuple[ChronostratUnit, ...] = field(default_factory=tuple)
    epochs: tuple[ChronostratUnit, ...] = field(default_factory=tuple)
    fuzzy_phrases: dict[str, tuple[float, str]] = field(default_factory=dict)

    def unit_containing(self, age_ma: float) -> tuple[ChronostratUnit, ...]:
        """Return (period, epoch, era) that contain `age_ma`.

        Returns (None, None, None) if `age_ma` is outside any unit.
        """
        era = next((e for e in self.eras if e.contains(age_ma)), None)
        period = next((p for p in self.periods if p.contains(age_ma)), None)
        epoch = next((e for e in self.epochs if e.contains(age_ma)), None)
        return (epoch, period, era)


# ─── Canonical chart instance ────────────────────────────────────────────────

ics_chart_v2024_12 = ICSChart(
    version="v2024/12",
    eras=ERAS,
    periods=PERIODS,
    epochs=EPOCHS,
    fuzzy_phrases=FUZZY_PHRASES,
)
