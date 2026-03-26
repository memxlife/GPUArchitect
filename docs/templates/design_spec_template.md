# Design Specification (Current)

## Version
v0.X

## 1. Current Objective

What is the system trying to achieve *at this stage*?

---

## 2. Current System Architecture

Describe the actual working system (not ideal system):

- benchmark layer
- execution layer
- parsing layer
- model layer
- LLM layer

---

## 3. Current Assumptions

What assumptions are currently being made?

Example:
- compute kernel approximates arithmetic intensity scaling
- parser assumes key=value format
- LLM is used only for interpretation

---

## 4. Experimental Evidence

Summarize key findings so far.

Example:
- inner_iters sweep shows two regimes
- transition between 64 and 256
- overflow occurs at 16384

---

## 5. Current Knowledge (Causal Form)

For each major finding:

### Claim
### Evidence
### Why (cause)
### How (mechanism)
### So What (implication)
### Uncertainty

---

## 6. Known Issues / Failure Modes

List real problems:

- compute kernel overflow
- sweep output not structured
- no uncertainty tracking
- no experiment selection logic

---

## 7. Design Gaps

What is missing from the system?

- no knowledge base structure
- no planner
- no uncertainty modeling
- no causal graph

---

## 8. Design Decisions (This Iteration)

What decisions were made and why?

Example:
- not using LangGraph yet
- LLM limited to interpretation
- start with compute benchmark

---

## 9. Next Iteration Plan

Define **exact next step**

Example:
- implement structured experiment registry
- redesign compute kernel for stability
- refine transition boundary sweep

---

## 10. Open Questions

What we do not understand yet:

- exact transition point
- role of memory vs compute in early regime
- scheduler sensitivity

---
