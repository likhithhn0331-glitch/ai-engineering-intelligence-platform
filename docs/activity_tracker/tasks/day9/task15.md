# Day 9 / Task 15 — System design requirements

## Objective

Design APIs conceptually for a hierarchy-aware document service without implementing it.

This is a system design exercise, not a coding task.

## Core domain

The service should support engineering artifacts with parent-child relationships:

- Project
- Requirement
- Design
- Code Change
- Test

This means the system must model both the artifact itself and its place in the hierarchy.

## Conceptual APIs

### 1. Create node

Purpose:

- create a new artifact node
- optionally attach it under a parent

Example conceptual request:

- POST /nodes
- body includes:
  - type
  - title
  - parent_id (optional)
  - metadata

Design considerations:

- is parent_id required for some node types?
- can a node be created without a parent?
- should there be validation for allowed node types?
- should the API reject cyclic parent relationships?

### 2. Get node

Purpose:

- return a single node by id

Example conceptual request:

- GET /nodes/{id}

Returned data may include:

- id
- type
- title
- parent_id
- created_at
- updated_at
- optional metadata

### 3. List children

Purpose:

- return the immediate direct children of a node

Example conceptual request:

- GET /nodes/{id}/children

This is the simplest hierarchical read pattern.

### 4. Get descendants

Purpose:

- return the full subtree below a node

Example conceptual request:

- GET /nodes/{id}/descendants

This is more expensive than listing direct children and requires careful design.

## Design concerns beyond the API

The system design should reason through:

- Requirements
- Scale
- API shape
- Data model
- Hierarchy representation
- Traversal strategy
- Indexes
- Consistency
- Reliability
- Monitoring
- Cost

These topics are all connected. A poor hierarchy design can make simple reads unexpectedly expensive.

## Data model thinking

A node record likely needs:

- id
- type
- parent_id (if using adjacency list)
- title
- content or metadata
- timestamps
- status

The design must decide whether more than one relationship type is allowed or whether the system is a pure tree.

## Hierarchy representation decisions

The system should reason about tradeoffs such as:

- adjacency list
- closure table
- nested set

For early design, adjacency list is usually easier to reason about and implement.

For larger graph-like traceability systems, closure tables or explicit relationship models may eventually be necessary.

## Traversal strategy

When reading descendants, the service may need to:

- recursively fetch children
- perform a SQL recursive CTE
- limit traversal depth
- paginate results

The design must be explicit about performance and operational limits.

## Indexes and performance

The system needs to consider:

- child lookup by parent_id
- node lookup by id
- ancestry queries
- ordering of siblings

Index design is part of the system design, not an implementation detail.

## Consistency and data integrity

Important questions:

- can a node become its own ancestor?
- what happens when a parent is deleted?
- should orphaned children be prevented?
- do we need to enforce a strict tree model?

The service should define and enforce the hierarchy’s invariants.

## Reliability and operational concerns

The system should consider:

- database failures
- slow descendant queries
- partial writes
- retries
- auditability

This connects back to the reliability concepts already covered in Day 9.

## Cost model

A hierarchy service can become expensive quickly if the product allows large descendant fetches or deeply nested trees.

Design questions:

- what is the maximum depth?
- what is the maximum subtree size?
- should descendant queries be paginated?
- how much monitoring signal do we need?

## Key takeaway

This is not an implementation task. It is a design exercise to reason how structured artifacts can be represented, traversed, and made reliable at scale.
