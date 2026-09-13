# ADR-001 Shared Backtracking Fallback

## Status

Accepted

## Context

`logical_solver.py` previously stopped when the implemented logic techniques
could not continue. That made it impossible to distinguish between:

- a valid puzzle that simply needs search
- an invalid puzzle with no solution

`solver.py` already had a separate backtracking implementation, but it was not
shared.

## Decision

Introduce a shared module `sudoku_backtracking.py` with these responsibilities:

- validate the input board
- solve with MRV backtracking
- accelerate the core search with `numba.njit`
- return structured results to callers

`logical_solver.py` now uses this shared solver as a fallback when logic stalls.
If the fallback finds no solution, it prints an error indicating the input may
be wrong.

`solver.py` now reuses the same shared module instead of keeping a separate
backtracking path.

## Consequences

- backtracking behavior is centralized and easier to regression-test
- invalid boards now produce an explicit error path
- logical solving remains the primary path, with search only as a fallback
