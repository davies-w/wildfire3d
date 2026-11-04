"""Offline reference model for the remote rolling scheduler; never runs FDS.

Amounts are integer microdollars. One slot remains occupied through cleanup.
An uncertain submission/outcome retains both its slot and its reservation.
"""
from dataclasses import dataclass, field

@dataclass
class Pool:
    pending: list[str]
    allowance: int
    reserve: int = 525000
    slots: int = 18
    active: dict = field(default_factory=dict)
    settled: set = field(default_factory=set)
    spent: int = 0
    started: int = 0
    evictions: int = 0
    checkpoint_seconds: int = 480
    stopped: bool = False

    def __post_init__(self):
        if len(set(self.pending)) != len(self.pending):
            raise ValueError('Duplicate cases')
        if not 1 <= self.slots <= 18 or self.allowance < 0 or self.reserve <= 0:
            raise ValueError('Invalid limits')

    def admit(self):
        out = []
        while (not self.stopped and self.pending and len(self.active) < self.slots
               and self.spent + (len(self.active)+1)*self.reserve <= self.allowance):
            case = self.pending.pop(0)
            if case in self.active or case in self.settled:
                raise ValueError('Duplicate admission')
            self.active[case] = 'CLAIMED'  # persist BEFORE non-retrying POST
            out.append(case)
        return out

    def submitted(self, case, execution):
        if self.active[case] != 'CLAIMED' or not execution:
            raise ValueError('Invalid submission acknowledgement')
        self.active[case] = execution

    def uncertain(self):
        self.stopped = True  # never release unknown allocation or resubmit

    def finish(self, case, *, charge, cleanup, passed, started, spot=False):
        if case not in self.active or case in self.settled:
            raise ValueError('Duplicate/foreign outcome')
        if not cleanup or not 0 <= charge <= self.reserve or (spot and not started):
            self.stopped = True
            raise ValueError('Outcome needs independent audit; reservation retained')
        del self.active[case]
        self.settled.add(case)
        self.spent += charge
        self.started += int(started)
        self.evictions += int(spot)
        if self.evictions >= 4 and self.evictions * 10 >= self.started:
            self.checkpoint_seconds = min(self.checkpoint_seconds, 180)
        elif self.evictions >= 2 and self.evictions * 20 >= self.started:
            self.checkpoint_seconds = min(self.checkpoint_seconds, 300)
        if not passed and not spot:
            self.stopped = True  # drain running cases; no automatic retry
