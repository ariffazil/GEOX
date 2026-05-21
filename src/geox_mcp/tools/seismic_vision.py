import logging
from typing import Any
from geox_core.engines.seismic.vision_bridge import GEOXVisionDepthEngine

logger = logging.getLogger("geox.canonical.seismic_vision")

def enforce_anti_hantu_protocol(input_type: str, execution_mode: str) -> None:
    """
    [ANTI-HANTU LAW]
    Directly breaks the execution loop if the system attempts to 
    generate or hallucinate seismic data transformations.
    """
    if input_type in ["user_image", "screenshot", "seismic_image"] and execution_mode == "generative":
        # JITU Circuit Breaker Keyword Triggered
        raise PermissionError(
            "CRITICAL HOLD [JITU]: Generative pixel alteration detected. "
            "GEOX is barred from hallucinating seismic data profiles. "
            "Execution terminated to protect W_scar. Human validation required."
        )

async def geox_vision_time_to_depth(
    image_path: str, 
    max_time_ms: float, 
    max_cmp: float, 
    v_rms_anchor: list,
    execution_mode: str = "deterministic"
) -> dict[str, Any]:
    """
    Executes the AAA process on an uploaded seismic image profile 
    to output a calibrated true depth structural diagram.
    """
    # 0. JITU CIRCUIT BREAKER
    enforce_anti_hantu_protocol("seismic_image", execution_mode)
    
    engine = GEOXVisionDepthEngine()
    output_target = "/root/geox/output/depth_migrated_section.png"
    
    result = engine.generate_calibrated_depth_section(
        image_path=image_path,
        max_time_ms=max_time_ms,
        max_cmp=max_cmp,
        v_rms_anchor=v_rms_anchor,
        output_path=output_target
    )
    
    # Wrap in standard envelope
    if result["status"] == "HOLD":
        return {
            "execution_status": "HOLD",
            "tool_class": "vision_depth",
            "claim_state": "VOID",
            "reason": result.get("error") or result.get("reason", "Unknown error")
        }
    
    return {
        "execution_status": "SUCCESS",
        "tool_class": "vision_depth",
        "claim_state": result["f2_claim_state"],
        "derived": {
            "max_calculated_depth_m": result["max_calculated_depth_m"],
            "min_calculated_depth_m": result["min_calculated_depth_m"],
            "total_unphysical_drift": result["total_unphysical_drift"]
        },
        "artifact_refs": {
            "depth_image": output_target
        },
        "audit_receipt": {
            "structural_entropy_delta": result["structural_entropy_delta"],
            "authority": "F2_PHYSICS_GUARD"
        }
    }
