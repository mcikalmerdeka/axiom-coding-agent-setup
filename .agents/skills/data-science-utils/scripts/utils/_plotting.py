"""Shared figure finalization helpers for ML plotting utilities."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt


def finalize_figure(fig, *, show: bool):
    """Lay out a figure, optionally show it, and return the figure."""
    fig.tight_layout()
    if show:
        plt.show()
    return fig


def save_figure(fig, path):
    """Save a figure to ``path`` and return the path as a ``Path``."""
    path = Path(path)
    fig.savefig(path, bbox_inches="tight")
    return path
