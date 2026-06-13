"""
rta.spatial_maps — Publication-quality spatial trend maps.

Top-level convenience module; delegates to rta.figures.spatial_maps.

Usage
-----
    from rta.spatial_maps import (
        fig8_spatial_summary,
        fig14_spatial_maps,
        fig_station_distribution,
        fig_spatial_methods,
        fig_spatial_field_sig,
        fig_spatial_full,
    )
"""

from .figures.spatial      import fig8_spatial_summary        # v3 Fig 8
from .figures.spatial_maps import (                            # v4 spatial
    fig14_spatial_maps,
    fig_station_distribution,
    fig_spatial_methods,
    fig_spatial_field_sig,
    fig_spatial_full,
)

__all__ = [
    "fig8_spatial_summary",
    "fig14_spatial_maps",
    "fig_station_distribution",
    "fig_spatial_methods",
    "fig_spatial_field_sig",
    "fig_spatial_full",
]
