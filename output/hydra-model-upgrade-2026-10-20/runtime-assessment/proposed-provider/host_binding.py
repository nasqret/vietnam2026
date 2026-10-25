"""Host integration example; no checkpoint load, model execution, or CLI side effects.

The driver must independently authenticate all supplied modules, tokenizer,
base weights and adapter, then construct a fresh provider for each case. Frozen
C5/C6 imports belong in separate child processes to prevent source collisions.
"""
from hydra_torch_candidate import CandidatePolicy, Limits, TorchGreedyBackend


def bind_policy(*, loaded_model, tokenizer, kind, execution_environment,
                current_prompt_module, current_authority_module,
                frozen_latent_data_module, frozen_latent_eval_module,
                provenance, case_deadline_monotonic, should_stop):
    """Return a CandidateProvider for the existing Hydra hybrid search.

    Baseline loaded_model is the authenticated old PEFT causal LM.
    Candidate loaded_model is the authenticated vanilla QwenRecurrentLM wrapper
    from that checkpoint's frozen source, loaded with the exact selected policy.
    All model parameters must already have requires_grad=False, CUDA placement,
    and eval mode. This bridge does not mutate or repair a loaded model.
    """
    latent = kind == "latent_compact_v3"
    return CandidatePolicy(
        backend=TorchGreedyBackend(loaded_model, kind=kind),
        tokenizer=tokenizer,
        kind=kind,
        environment=execution_environment,
        provenance=provenance,
        render_prompt=(frozen_latent_data_module.compact_prompt if latent
                       else current_prompt_module.render_prompt),
        strict_generation=frozen_latent_eval_module.strict_generation,
        check_prompt_binding=frozen_latent_eval_module.check_prompt_binding,
        validate_tactic=current_authority_module.validate_authority_tactic,
        constraint_factory=None if latent else current_authority_module.AuthorityTokenConstraint,
        limits=Limits(max_calls=16, max_new_tokens=128, max_total_decision_tokens=4096,
                      max_context_tokens=6144, provider_seconds=30.0),
        should_stop=should_stop,
        deadline_monotonic=case_deadline_monotonic,
    )
