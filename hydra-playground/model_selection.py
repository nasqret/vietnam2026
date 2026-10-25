"""Explicit reversible model selection. No model imports during selection.

The historical model remains the default until a reviewed fresh comparison
justifies changing DEFAULT_MODEL_ID. A failed explicit choice never falls back.
"""
OLD_MODEL_ID = "hydra-mixed"
WMI_MODEL_ID = "wmi-c6-vanilla47"
DEFAULT_MODEL_ID = OLD_MODEL_ID
MODEL_IDS = (OLD_MODEL_ID, WMI_MODEL_ID)


def resolve_model_id(requested=None):
    selected = DEFAULT_MODEL_ID if requested is None else requested
    if type(selected) is not str or selected not in MODEL_IDS:
        raise ValueError("Model must be hydra-mixed or wmi-c6-vanilla47.")
    return selected


def metadata_status(requested=None):
    selected = resolve_model_id(requested)
    if selected == OLD_MODEL_ID:
        import model_runtime
        result = model_runtime.metadata_status()
    else:
        import wmi_model_runtime
        result = wmi_model_runtime.metadata_status()
    return {**result, "selection_id": selected, "default_selection_id": DEFAULT_MODEL_ID,
            "is_default": selected == DEFAULT_MODEL_ID, "automatic_fallback": False,
            "selectable_models": list(MODEL_IDS)}


def create_policy(model_id, capabilities, emit_progress, **case_limits):
    """Policy for the new sequential route; historical prompt/mask are retained.

    This route uses matched greedy decoding. Existing model_runtime and
    hybrid_runtime entrypoints still own their unchanged legacy beam decoder.
    """
    selected = resolve_model_id(model_id)
    from wmi_model_runtime import HistoricalGreedyPolicy, WMIModelPolicy
    cls = HistoricalGreedyPolicy if selected == OLD_MODEL_ID else WMIModelPolicy
    return cls(capabilities, emit_progress, **case_limits)


def create_sequential_policy(model_id, capabilities, emit_progress, **case_limits):
    """Matched greedy path; does not change the historical beam4 implementation."""
    return create_policy(model_id, capabilities, emit_progress, **case_limits)
