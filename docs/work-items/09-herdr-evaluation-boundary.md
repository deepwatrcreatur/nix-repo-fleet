# 09 Herdr Evaluation Boundary

Status: ready

## Goal

Record a bounded evaluation of `herdr` as the stronger future control-plane
reference without prematurely displacing the current `dmux`-first direction.

## Deliverables

- define the exact questions the evaluation should answer, such as:
  - what lifecycle/control semantics `herdr` appears to provide
  - which missing `dmux` follow-ups it could plausibly subsume
  - which gaps still require local wrapper/state work
- compare `herdr` against the current first-slice `dmux` guard and the new
  fleet-state work
- produce a decision artifact that classifies `herdr` as:
  - watch item only
  - bounded spike candidate
  - or ready for adoption work

## Notes

- this is intentionally an **evaluation boundary** item, not an adoption item
- the point is to keep parallel research possible without splitting primary
  implementation too early
