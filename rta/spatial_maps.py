"""
rta.spatial_maps — Publication-quality spatial trend maps.

Top-level convenience module; delegates to rta.figures.spatial_maps.
Also exposes fig8_spatial_summary for callers that import from here.

Usage
-----
    from rta.spatial_maps import fig8_spatial_summary, fig14_spatial_maps
"""

from .figures.spatial      import fig8_spatial_summary        # v3 Fig 8
from .figures.spatial_maps import fig14_spatial_maps           # v4 Fig 14

__all__ = ["fig8_spatial_summary", "fig14_spatial_maps"]
