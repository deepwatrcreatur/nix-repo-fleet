# 07 Claims Leases And Heartbeat Surface

Status: ready

## Goal

Define a small machine-readable state surface for branch/worktree claims,
leases, and heartbeats so wrapper/control-plane tools can distinguish active
ownership from stale residue.

## Deliverables

- choose a minimal local state format for claims/leases/heartbeats
- define how a worktree or branch is identified
- capture enough data to answer:
  - who claims this worktree or task
  - when it was last touched
  - whether the claim is still plausibly alive
- document expiration / stale-claim semantics
- emit or read the state in a way other tools can consume later

## Notes

- keep the first slice local and simple
- this item is about the **state contract**, not a full scheduler or daemon
