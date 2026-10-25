"""Small shared glue for the two opt-in P9 advisers, never proof authority."""
from adviser_protocol import (BudgetStop, ProtocolError, read_json, semantic_context)


class P9Advisor:
    def __init__(self, backend, session, runner, *, capabilities, authority_identity):
        if backend not in {"egg", "e"}:
            raise ProtocolError("Unknown P9 adviser.")
        self.backend, self.session, self.runner = backend, session, runner
        self.capabilities, self.authority_identity = capabilities, authority_identity
        self.advice_requests = self.actual_invocations = self.confirmed_backend_executions = 0
        self.accounting_complete = True

    def prepare(self, state, context):
        raise NotImplementedError

    def decode(self, problem, request, execution):
        raise NotImplementedError

    def advise(self, state):
        self.advice_requests += 1
        result = {"status": "unsupported", "suggestions": [], "candidates": (),
                  "kernel_checked": False, "solver": {"backend": self.backend, "invocations": 0,
                  "helper_launches": 0, "backend_execution_confirmed": False}}
        try:
            context = semantic_context(state, self.capabilities, authority_identity=self.authority_identity)
            problem, request = self.prepare(state, context)
            with self.session.lease(request) as lease:
                execution = self.runner(lease)
                record = lease.record_external(execution, quiescent=execution.get("quiescent") is True)
            self.actual_invocations += record["actual_launches"]
            result["context_sha256"] = request.context_sha256
            result["solver"] = {key: execution.get(key) for key in (
                "status", "available", "exit_code", "elapsed_seconds", "input_sha256", "termination",
                "peak_rss_bytes", "rss_samples", "quiescent", "identity", "limits")}
            result["solver"].update(backend=self.backend, invocations=record["actual_launches"],
                helper_launches=record["actual_launches"],
                backend_execution_confirmed=execution.get("backend_execution_confirmed") is True,
                backend_execution_observation=execution.get("backend_execution_observation", "not_observed"))
            confirmed = result["solver"]["backend_execution_confirmed"]
            self.confirmed_backend_executions += int(confirmed)
            # These are helper launches: preflight/exec failures must not be
            # advertised as confirmed work by the actual native backend.
            if execution.get("status") != "completed":
                result.update(status=execution.get("status", "failed"),
                              detail="The bounded helper supplied no usable native advice.")
                return result
            if (execution.get("executed") is not True or execution.get("exit_code") != 0
                    or type(execution.get("exit_code")) is not int or execution.get("quiescent") is not True
                    or execution.get("input_sha256") != request.input_sha256
                    or execution.get("identity") != read_json(request.identity, 4096)):
                raise ProtocolError("The external response does not belong to the completed bound request.")
            status, suggestions, evidence = self.decode(problem, request, execution)
            # A complete source-bound backend format confirms execution; it
            # remains entirely untrusted mathematical evidence.
            self.confirmed_backend_executions += int(not confirmed)
            result["solver"]["backend_execution_confirmed"] = True
            accepted = []
            for suggestion in suggestions[:12]:
                commands = suggestion.get("commands")
                if (type(commands) not in (tuple, list) or not 0 < len(commands) <= 8
                        or any(type(line) is not str or not line or len(line.encode("utf-8")) > 512
                               or "\n" in line or "\r" in line
                               or line.split(maxsplit=1)[0] not in self.capabilities.allowed_commands
                               for line in commands)):
                    continue
                accepted.append({**suggestion, "commands": list(commands), "source": self.backend,
                    "input_sha256": request.input_sha256, "context_sha256": request.context_sha256,
                    "kernel_checked": False})
            result.update(status="advisory_candidate" if accepted else status,
                          suggestions=accepted, candidates=tuple(tuple(row["commands"]) for row in accepted),
                          evidence=evidence)
        except BudgetStop as error:
            result.update(status="budget_stop", detail=str(error)[:400])
        except (ProtocolError, TypeError, ValueError, AttributeError, KeyError, RecursionError) as error:
            result.update(status="unsupported" if result["solver"].get("invocations") == 0 else "unsupported_evidence",
                          detail=str(error)[:400])
            if not self.session.report()["accounting_complete"]:
                self.accounting_complete = False
                result["solver"].update(invocations=None, helper_launches=None)
                result["status"] = "infrastructure_error"
        return result

    def report(self):
        return {"backend": self.backend, "advice_requests": self.advice_requests,
                "actual_invocations": self.actual_invocations if self.accounting_complete else None,
                "known_actual_invocations": self.actual_invocations,
                "confirmed_backend_executions": self.confirmed_backend_executions,
                "confirmation_scope": "Observed backend entry/output; a lower bound, separate from every charged helper launch.",
                "accounting_complete": self.accounting_complete, "kernel_checked": False}
