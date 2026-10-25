"""Explicit Deep-only wiring of bounded advisers; no proof authority."""
from collections import Counter
import hashlib
from pathlib import Path
import time

from adviser_protocol import (AdviserSession,BudgetStop,ProtocolError,RequestLease,canonical_json,
    external_request,semantic_context)


EXTRA_BACKENDS = ("sympy","cvc5")


def available_advisers():
    from adviser_process import metadata_status
    return {name:metadata_status(name) for name in EXTRA_BACKENDS}


def authority_identity(native_identity,library_identity):
    return hashlib.sha256(canonical_json({"native":native_identity,
        "checked_library":library_identity})).hexdigest()


class _CapturedVampireRunner:
    """Keep the existing exact supervisor and record its real return value."""
    def __init__(self,runner):
        self.runner=runner
        self.profile=runner.profile
        self.lease=None
        self.execution=None

    def __call__(self,text):
        lease=self.lease
        if type(lease) is not RequestLease or lease.completed or text.encode("utf-8")!=lease.request.data:
            raise ProtocolError("Vampire dispatch is not bound to its live exact-input lease.")
        if lease._owner.cancelled() or time.monotonic()>=lease.deadline:
            raise BudgetStop("Vampire lease expired before its one launch.")
        lease.claim_dispatch()
        self.execution=self.runner(text)
        return self.execution


class _SharedVampire:
    def __init__(self,session,runner,capabilities,identity):
        from vampire_process import VERSION,RUNTIME_POLICY,metadata_status
        self.session,self.runner,self.capabilities,self.identity=session,runner,capabilities,identity
        self.capture=_CapturedVampireRunner(runner)
        self.requests=0
        self.advisors={}
        status=metadata_status("deep")
        if runner.profile!="deep" or not status["available"]:
            raise ProtocolError("Shared Vampire requires its installed fixed Deep supervisor.")
        app=Path(__file__).resolve().parent
        pins={name:hashlib.sha256((app/name).read_bytes()).hexdigest() for name in
              ("vampire_bridge.py","vampire_process.py","vampire_worker.py","vampire_limits.py")}
        self.backend_identity={"backend":"vampire","version":VERSION,"profile":"deep",
            "policy":RUNTIME_POLICY,"binary_sha256":status["binary_sha256"],
            "helper_sources_sha256":hashlib.sha256(canonical_json(pins)).hexdigest()}

    def advise(self,state):
        from vampire_bridge import VampireAdvisor,export_state,UnsupportedFragment
        self.requests+=1
        try:
            context=semantic_context(state,self.capabilities,authority_identity=self.identity)
            problem=export_state(state)
            raw=problem.text.encode("utf-8")
            request=external_request("vampire",raw,context,self.backend_identity)
            # An old focused-FOF cache cannot cross a changed sibling goal,
            # substitution, original theorem or checked-library edition.
            key=(context,raw)
            with self.session.lease(request) as lease:
                advisor=self.advisors.get(key)
                if advisor is None:
                    advisor=VampireAdvisor(self.capture)
                    self.advisors[key]=advisor
                self.capture.lease,self.capture.execution=lease,None
                try:
                    result=advisor.advise(state)
                    cached=result.get("cache",{}).get("hit") is True
                    if cached:
                        execution={"executed":False,"status":"cached_unsuccessful","exit_code":None,
                            "problem_sha256":problem.sha256,"elapsed_seconds":time.monotonic()-lease.started}
                        quiescent=True
                    else:
                        execution=self.capture.execution
                        if type(execution) is not dict:
                            raise ProtocolError("Vampire supplied no actual execution receipt.")
                        execution=dict(execution)
                        execution.setdefault("elapsed_seconds",time.monotonic()-lease.started)
                        # This fixed supervisor returns after wait(); an
                        # unconfirmed reap raises, leaving this lease blocked.
                        quiescent=execution.get("executed") is False or type(execution.get("exit_code")) is int
                    lease.record_external(execution,cache_hit=cached,quiescent=quiescent)
                finally:
                    self.capture.lease=None
            return result
        except (ProtocolError,UnsupportedFragment,TypeError,KeyError,RecursionError) as error:
            report=self.session.report()
            complete=report["accounting_complete"]
            return {"status":"unsupported_fragment" if complete else "infrastructure_error",
                "detail":str(error)[:400],"suggestions":[],"kernel_checked":False,
                "solver":{"available":True,"invocations":0 if complete else None}}

    def report(self):
        reports=[item.report() for item in self.advisors.values()]
        return {"policy":"hydra-shared-full-context-vampire-cache-v1",
            "scope":"one search, exact full native context, exact FOF and fixed backend identity",
            "requests":self.requests,"actual_invocations":self.runner.calls,
            "cache_hits":sum(row["cache_hits"] for row in reports),
            "stores":sum(row["stores"] for row in reports),
            "entries":sum(row["entries"] for row in reports),
            "retained_input_bytes":sum(row["retained_input_bytes"] for row in reports),
            "max_semantic_contexts":self.session.max_requests,"kernel_checked":False}


class _SelectedAdviser:
    def __init__(self,pool,backend):
        self.pool,self.backend=pool,backend

    @property
    def can_request(self):
        return self.pool.can_request

    @property
    def calls(self):
        return self.pool.runners[self.backend].calls

    def advise(self,state):
        return self.pool.request(self.backend,state)

    def report(self):
        return self.pool.advisors[self.backend].report()


class AdviserPool:
    """A fixed set of five possible backends, never a dynamic plugin loader."""
    def __init__(self,selected,*,capabilities,native_identity,library_identity,
                 deadline,vampire_runner=None,should_stop=None):
        if type(selected) not in (tuple,list) or len(selected)>len(EXTRA_BACKENDS) \
                or len(set(selected))!=len(selected) or any(name not in EXTRA_BACKENDS for name in selected):
            raise ProtocolError("Unknown or repeated experimental adviser selection.")
        self.session=AdviserSession(deadline=deadline,should_stop=should_stop)
        self.identity=authority_identity(native_identity,library_identity)
        self.requests=0
        self.by_backend=Counter()
        self.advisors,self.runners={},{}
        from adviser_process import AdviserRunner
        for name in EXTRA_BACKENDS:
            if name not in selected:
                continue
            runner=AdviserRunner(name)
            if name=="sympy":
                from sympy_bridge import SympyAdvisor
                advisor=SympyAdvisor(self.session,runner,capabilities=capabilities,authority_identity=self.identity)
            else:
                from smt_bridge import SmtAdvisor
                advisor=SmtAdvisor(self.session,runner,capabilities=capabilities,authority_identity=self.identity)
            self.runners[name],self.advisors[name]=runner,advisor
        if vampire_runner is not None:
            self.runners["vampire"]=vampire_runner
            self.advisors["vampire"]=_SharedVampire(self.session,vampire_runner,capabilities,self.identity)
        self.extra=tuple(_SelectedAdviser(self,name) for name in EXTRA_BACKENDS if name in self.advisors)
        self.vampire=None if vampire_runner is None else _SelectedAdviser(self,"vampire")

    @property
    def can_request(self):
        report=self.session.report()
        return self.requests<12 and report["blocked_reason"] is None and not self.session.cancelled()

    def request(self,backend,state):
        if backend not in self.advisors:
            raise ProtocolError("Backend was not selected for this search.")
        if not self.can_request:
            return {"status":"shared_budget_stop","suggestions":[],"kernel_checked":False,
                    "solver":{"available":True,"invocations":0,"backend":backend}}
        # Even syntactically unsupported requests spend the controller cap.
        self.requests+=1
        self.by_backend[backend]+=1
        return self.advisors[backend].advise(state)

    def report(self):
        shared=self.session.report()
        actual={name:runner.calls for name,runner in self.runners.items()}
        if shared["accounting_complete"] and sum(actual.values())!=shared["actual_launches"]:
            raise ProtocolError("Shared adviser ledger and actual supervisors disagree.")
        return {"policy":"hydra-explicit-shared-advisers-v1","controller_requests":self.requests,
            "requests_by_backend":dict(self.by_backend),"actual_launches_by_backend":actual,
            "shared":shared,"authority_identity":self.identity,"kernel_checked":False,
            "runners":{name:runner.records for name,runner in self.runners.items() if name!="vampire"}}
