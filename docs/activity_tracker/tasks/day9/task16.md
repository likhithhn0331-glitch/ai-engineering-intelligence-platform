# Day 9 / Task 16 — Connect it to Project 1

## Objective

Connect the idea of hierarchical artifacts to the project’s eventual traceability system.

## Long-term traceability goal

The flagship project aims for a conceptual chain like:

Requirement
    ↓
Code
    ↓
Test
    ↓
Result

This means the system must eventually connect artifacts across implementation and verification stages.

## Why this matters

Without traceability, the engineering system can only answer isolated questions:

- what document exists?
- what code was changed?
- what tests were run?

It cannot answer the most important product question:

- how does this requirement connect to the implemented code and the resulting verification evidence?

That is where hierarchy and graph-like relationships become important.

## Hierarchy vs graph

A tree is a useful first concept because the artifact relationships are often parent-child.

But as the system matures, many real-world relationships are graph-like, for example:

- one requirement may influence several design documents
- one code change may support multiple requirements
- a test may validate several changed components

This suggests the eventual system may need more than a simple tree. But for Day 9, the purpose is to reason about the concept, not to build a graph database.

## What Day 9 is not doing

Day 9 is not introducing a graph database.

It is not building a full traceability engine.

It is simply teaching the architectural reasoning required to think about:

- relationships between artifacts
- parent-child structure
- lifecycle traceability
- future system design

## The conceptual bridge

The project has already covered:

- document storage
- querying
- filtering
- ordering
- pagination
- service/repository boundaries

Now the next step is to ask:

- how do these documents relate to one another?
- how do we traverse those relationships?
- how do we design for scale and correctness?

This is the conceptual bridge from CRUD/querying to traceability-aware system design.

## Key takeaway

The hierarchy design exercise is not an implementation requirement for Day 9. It is a future-oriented reasoning exercise that prepares the project for Project 1’s traceability needs.

The real lesson is:

- artifacts are connected
- relationships matter
- the system must support traversal and validation
- the architecture should evolve with those needs, without jumping prematurely into a graph database solution
