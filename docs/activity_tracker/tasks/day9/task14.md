# Day 9 / Task 14 — Design: Document Hierarchy Service

## Objective

Connect the Tree/Hierarchy reasoning to the eventual Project 1 architecture.

The central idea is that engineering artifacts are not isolated records. They are connected in a hierarchy of traceability.

Example:

Project
└── Requirement
    └── Design
        └── Code Change
            └── Test

This is a natural tree-like structure.

## Why this matters

In a real engineering system, artifacts are linked as a chain of evidence and implementation:

- a requirement motivates a design
- a design leads to code changes
- code changes are validated by tests
- test evidence connects back to the original requirement

This is the conceptual foundation for traceability.

## Design thinking

A hierarchy service should model the relationship between nodes, not just independent documents.

Possible conceptual node model:

- id
- type
- title
- parent_id (nullable)
- created_at
- updated_at
- metadata

This allows a document to live in a tree while still being represented as a first-class record.

## Core operations

The design exercise is meant to reason about these APIs conceptually:

1. Create node
2. Get node
3. List children
4. Get descendants

## API examples

### Create node

Conceptually:

- POST /nodes
- body contains type, title, parent_id, optional metadata

Questions to reason about:

- should parent_id be required for all nodes?
- does the API allow cross-type relationships?
- should the API reject cycles?

### Get node

Conceptually:

- GET /nodes/{id}

Should return:

- node metadata
- parent information
- perhaps type and ancestry summary

### List children

Conceptually:

- GET /nodes/{id}/children

This is a straightforward hierarchical traversal query.

It should return the immediate children of a node.

### Get descendants

Conceptually:

- GET /nodes/{id}/descendants

This returns the full subtree under a node, not just the immediate children.

This is more expensive and is where traversal strategy, recursion depth, and pagination become important.

## Design dimensions

The notes from earlier in Day 9 still apply:

- Requirements
- Scale
- API
- Data Model
- Hierarchy representation
- Traversal
- Indexes
- Consistency
- Reliability
- Monitoring
- Cost

These are the factors a real system must evaluate, not just the happy path.

## Hierarchy representation

The project can choose between a few patterns:

- adjacency list
  - each node stores parent_id
  - simple and easy to build
  - good for immediate parent/child queries
- closure table
  - stores ancestor/descendant relationships explicitly
  - good for efficient descendant queries
  - more write overhead
- nested sets
  - efficient read-heavy hierarchical queries
  - more complex updates

For an early service, adjacency lists are often the simplest design, but the right choice depends on the workload.

## Traversal

When retrieving descendants, the system must decide:

- recursive queries in SQL or application code
- depth-limited traversal
- cycle protection
- maximum subtree size

The engineer should reason about how deep the tree can become and how expensive descendants requests can be.

## Indexes

A hierarchy service needs indexes to keep reads fast:

- index on parent_id for child lookup
- possibly index on id for direct retrieval
- additional index for ancestry queries if closure tables are used

Without proper indexing, tree traversal becomes expensive even for moderate data volume.

## Consistency

A hierarchical service must make choices around consistency:

- reject orphans
- reject cycles
- guard against moving a node under its own descendant
- handle parent-child updates atomically

A hierarchy is not just data; it is a relationship graph with rules.

## Reliability

Questions to ask:

- what happens if the database is unavailable?
- what happens if a parent is deleted?
- what happens if a move creates a cycle?
- do descendant queries timeout?

The project should treat hierarchy operations as real transactional operations when necessary.

## Monitoring and cost

A hierarchy API may create expensive workloads:

- deep descendants requests
- large tree traversals
- high concurrency on shared ancestors

This means monitoring is necessary for:

- query latency
- slow descendant traversals
- deadlocks or lock contention
- write amplification

## Connection to Project 1

The key connection is traceability.

Project 1’s long-term goal is conceptually:

Requirement
    ↓
Code
    ↓
Test
    ↓
Result

This is not a relational table problem only. It is a linkage problem.

The hierarchy service introduces the idea that artifacts can be connected and traversed systematically.

## Day 9 scope

This task is design-only. No implementation is required.

The purpose is to build intuition for:

- hierarchical relationships
- layered API design
- data modeling tradeoffs
- traversal cost and indexing
- future traceability architecture

## Key takeaway

A document hierarchy service is a conceptual bridge between today’s document/query work and Project 1’s eventual traceability model.
