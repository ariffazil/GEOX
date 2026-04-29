from geox.skills.subsurface.volumes.volumetrics import geox_compute_volume_probabilistic_tool

def geox_compute_volume_probabilistic(
    grv_min: float | None = None,
    grv_ml: float | None = None,
    grv_max: float | None = None,
    ntg_min: float | None = None,
    ntg_ml: float | None = None,
    ntg_max: float | None = None,
    phi_min: float | None = None,
    phi_ml: float | None = None,
    phi_max: float | None = None,
    sw_min: float | None = None,
    sw_ml: float | None = None,
    sw_max: float | None = None,
    fvf: float = 1.0,
    n_draws: int = 10_000,
    **kwargs,
) -> dict:
    if kwargs:
        return geox_compute_volume_probabilistic_tool(**kwargs)
    return geox_compute_volume_probabilistic_tool(
        grv_dist={"min": grv_min, "ml": grv_ml, "max": grv_max},
        ntg_dist={"min": ntg_min, "ml": ntg_ml, "max": ntg_max},
        phi_dist={"min": phi_min, "ml": phi_ml, "max": phi_max},
        sw_dist={"min": sw_min, "ml": sw_ml, "max": sw_max},
        fvf_dist=fvf,
        draws=n_draws,
    )

__all__ = ["geox_compute_volume_probabilistic_tool", "geox_compute_volume_probabilistic"]
