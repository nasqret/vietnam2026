"""One request's actual native import ledger, including independent replay."""
from contextlib import contextmanager


class ImportBudget:
    MAX_ATTEMPTS = 32
    MAX_PER_PROOF = 8

    def __init__(self):
        self.attempts = 0
        self.accepted = 0
        self.rejected = 0
        self._phase = "search"
        self._counts = {"search":0,"independent_replay":0,"manual":0}
        self._records = []

    @contextmanager
    def phase(self, value):
        if value not in self._counts:
            raise ValueError("Unknown import phase.")
        previous, self._phase = self._phase, value
        try:
            yield
        finally:
            self._phase = previous

    def run(self, name, operation):
        if self.attempts >= self.MAX_ATTEMPTS:
            raise ValueError("The complete request reached 32 native import attempts, including replay.")
        self.attempts += 1
        self._counts[self._phase] += 1
        row = {"name":name,"phase":self._phase,"status":"attempted"}
        self._records.append(row)
        try:
            result = operation()
        except BaseException:
            self.rejected += 1
            row["status"] = "rejected_or_interrupted"
            raise
        self.accepted += 1
        row["status"] = "native_accepted"
        return result

    def report(self):
        return {"policy":"hydra-checked-import-budget-v1", "attempts":self.attempts,
            "accepted":self.accepted,"rejected":self.rejected,"phases":dict(self._counts),
            "max_attempts":self.MAX_ATTEMPTS,"max_imports_per_proof":self.MAX_PER_PROOF,
            "records":[dict(row) for row in self._records],
            "scope":"Actual use_checked calls, including failed calls and final replay; library preload checks are separate."}
