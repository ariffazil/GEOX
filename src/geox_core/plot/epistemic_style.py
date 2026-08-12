"""
Epistemic Visual Style for GEOX Charts
DITEMPA BUKAN DIBERI — Forged, not given

Visual styling for geopressure charts based on epistemic status.
Ensures confidence levels are visually distinguishable to prevent
misinterpretation of uncalibrated results.
"""

from dataclasses import dataclass
from typing import Any


# Epistemic style configuration
EPISTEMIC_STYLES = {
    "CLAIM": {
        "color": "#1B4F72",  # Dark blue
        "linestyle": "solid",
        "alpha": 1.0,
        "marker": "o",
        "linewidth": 2.5,
        "label": "CALIBRATED CLAIM",
    },
    "ESTIMATE": {
        "color": "#E67E22",  # Amber/orange
        "linestyle": "dashed",
        "alpha": 0.85,
        "marker": "s",
        "linewidth": 2.0,
        "label": "PARTIAL ESTIMATE",
    },
    "HYPOTHESIS": {
        "color": "#C0392B",  # Red
        "linestyle": "dotted",
        "alpha": 0.7,
        "marker": "^",
        "linewidth": 1.5,
        "label": "UNCALIBRATED HYPOTHESIS",
    },
}


@dataclass
class EpistemicStyle:
    """Visual styling for epistemic labels."""

    color: str
    linestyle: str
    alpha: float
    marker: str
    linewidth: float
    label: str


def get_epistemic_style(epistemic_label: str) -> EpistemicStyle:
    """
    Get matplotlib styling based on epistemic label.

    Args:
        epistemic_label: One of "CLAIM", "ESTIMATE", "HYPOTHESIS"

    Returns:
        EpistemicStyle dataclass with matplotlib kwargs

    Example:
        >>> style = get_epistemic_style("ESTIMATE")
        >>> ax.plot(depth, pressure, **style.to_matplotlib())
    """
    label_upper = epistemic_label.upper()

    if label_upper not in EPISTEMIC_STYLES:
        # Default to HYPOTHESIS for unknown labels
        label_upper = "HYPOTHESIS"

    style_dict = EPISTEMIC_STYLES[label_upper]
    return EpistemicStyle(**style_dict)


def add_epistemic_banner(
    ax,
    epistemic_label: str,
    confidence: float,
    position: str = "top",
) -> None:
    """
    Add a colored banner to the axes indicating epistemic status.

    Args:
        ax: Matplotlib axes object
        epistemic_label: One of "CLAIM", "ESTIMATE", "HYPOTHESIS"
        confidence: Confidence value (0-1)
        position: Banner position - "top" or "bottom"

    Example:
        >>> fig, ax = plt.subplots()
        >>> ax.plot(depth, pressure)
        >>> add_epistemic_banner(ax, "ESTIMATE", 0.72)
    """
    style = get_epistemic_style(epistemic_label)

    # Banner colors
    banner_colors = {
        "CLAIM": "#1B4F72",
        "ESTIMATE": "#E67E22",
        "HYPOTHESIS": "#C0392B",
    }

    color = banner_colors.get(epistemic_label.upper(), "#C0392B")

    # Get axes bounds
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    # Banner height as fraction of plot
    banner_height = (ylim[1] - ylim[0]) * 0.05
    banner_height = max(banner_height, 3)  # Minimum 3 units

    if position == "top":
        y_pos = ylim[1]
        ax.axhspan(
            ylim[1],
            ylim[1] + banner_height,
            color=color,
            alpha=0.3,
            zorder=0,
        )
        # Add text
        text_y = ylim[1] + banner_height / 2
        ha = "center"
    else:
        y_pos = ylim[0]
        ax.axhspan(
            ylim[0] - banner_height,
            ylim[0],
            color=color,
            alpha=0.3,
            zorder=0,
        )
        text_y = ylim[0] - banner_height / 2
        ha = "center"

    # Add label
    label_text = f"{style.label} (conf: {confidence:.2f})"
    ax.text(
        (xlim[0] + xlim[1]) / 2,
        text_y,
        label_text,
        ha=ha,
        va="center",
        fontsize=9,
        fontweight="bold",
        color=color,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor=color, alpha=0.8),
    )


def add_provenance_footer(
    fig,
    sources: list[str],
    fontsize: str = "small",
) -> None:
    """
    Add a provenance footer to the figure with literature citations.

    Args:
        fig: Matplotlib figure object
        sources: List of citation strings
        fontsize: Matplotlib fontsize (default: "small")

    Example:
        >>> fig, ax = plt.subplots()
        >>> add_provenance_footer(fig, ["Madon 2006", "USGS OF-99-50T"])
    """
    if not sources:
        return

    # Join sources
    source_text = "Sources: " + "; ".join(sources)

    # Add text at bottom of figure
    fig.text(
        0.5,
        0.01,
        source_text,
        ha="center",
        va="bottom",
        fontsize=fontsize,
        style="italic",
        color="gray",
    )


def style_plot_for_epistemic_status(
    ax,
    epistemic_label: str,
    confidence: float,
    depth: list[float] | None = None,
    pressure: list[float] | None = None,
    label: str = "Pore Pressure",
) -> None:
    """
    Apply complete epistemic styling to a plot.

    Applies line style, adds banner, and sets title with confidence.

    Args:
        ax: Matplotlib axes
        epistemic_label: CLAIM, ESTIMATE, or HYPOTHESIS
        confidence: Confidence value 0-1
        depth: Depth values for plotting
        pressure: Pressure values for plotting
        label: Line label

    Example:
        >>> fig, ax = plt.subplots()
        >>> style_plot_for_epistemic_status(ax, "ESTIMATE", 0.72, depth, pressure)
    """
    style = get_epistemic_style(epistemic_label)

    if depth is not None and pressure is not None:
        ax.plot(
            pressure,
            depth,
            color=style.color,
            linestyle=style.linestyle,
            alpha=style.alpha,
            marker=style.marker,
            linewidth=style.linewidth,
            label=label,
        )

    # Add banner
    add_epistemic_banner(ax, epistemic_label, confidence)

    # Invert y-axis for depth (typical for geopressure)
    ax.invert_yaxis()

    # Add grid
    ax.grid(True, alpha=0.3, linestyle="--")

    # Set labels
    ax.set_xlabel("Pore Pressure (MPa)", fontweight="bold")
    ax.set_ylabel("Depth (m TVDSS)", fontweight="bold")

    # Add legend
    ax.legend(loc="lower right")

    # Title with epistemic status
    status_emoji = {
        "CLAIM": "✓",
        "ESTIMATE": "⚠",
        "HYPOTHESIS": "✗",
    }
    emoji = status_emoji.get(epistemic_label.upper(), "⚠")
    ax.set_title(
        f"{emoji} {style.label} — Confidence: {confidence:.2f}",
        fontweight="bold",
        color=style.color,
    )
