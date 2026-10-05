---
source_key: dbms_acid_transactions
title: DBMS ACID Properties and Transaction Isolation
topic: dbms
source_origin: InsightPrep Technical Interview Preparation Corpus
source_license: project-authored
---

# DBMS ACID Properties and Transaction Isolation

## The ACID Model
A database transaction is a logical unit of work consisting of one or more database operations that must be executed reliably. The ACID model guarantees database integrity:

1. **Atomicity**:
   - The "all or nothing" principle. Either all operations of the transaction commit successfully to durable storage, or all changes are rolled back on failure.
   - Implemented using Write-Ahead Logging (WAL) and undo logs.
2. **Consistency**:
   - A transaction transforms the database from one valid state to another valid state, preserving all defined schema constraints (foreign keys, uniqueness, check constraints).
3. **Isolation**:
   - Concurrent execution of transactions yields the same database state as if they were executed serially (one after another).
   - Prevents intermediate uncommitted changes from being observed by other concurrent transactions.
4. **Durability**:
   - Once a transaction commits, its updates persist permanently even in the event of an immediate system crash or power outage.
   - Ensured via WAL flush to non-volatile disk before acknowledging commit to the client.

## Concurrency Anomalies
When transactions run concurrently without full serializability, specific read phenomena can occur:
- **Dirty Read**: Transaction T1 modifies a row without committing; Transaction T2 reads this uncommitted row. If T1 rolls back, T2 has read invalid data.
- **Non-Repeatable Read (Fuzzy Read)**: Transaction T1 reads a row; Transaction T2 updates or deletes that row and commits. When T1 reads the same row again, it sees modified or deleted data.
- **Phantom Read**: Transaction T1 executes a query with a range condition (e.g., `WHERE age > 30`); Transaction T2 inserts a new row satisfying the condition and commits. When T1 repeats the range query, it observes extra "phantom" rows.

## Standard SQL Isolation Levels
ANSI SQL defines four isolation levels offering varying trade-offs between performance and concurrency safety:

| Isolation Level | Dirty Read | Non-Repeatable Read | Phantom Read |
|---|---|---|---|
| **Read Uncommitted** | Possible | Possible | Possible |
| **Read Committed** | Prevented | Possible | Possible |
| **Repeatable Read** | Prevented | Prevented | Possible (in strict ANSI SQL; prevented in PostgreSQL via snapshot isolation) |
| **Serializable** | Prevented | Prevented | Prevented |

## Concurrency Control Mechanisms
- **Two-Phase Locking (2PL)**:
  - Growing Phase: Locks (shared/read or exclusive/write) are acquired; no locks can be released.
  - Shrinking Phase: Locks are released; no new locks can be acquired.
  - Strict 2PL holds exclusive locks until transaction commit/abort to prevent cascading rollbacks.
- **Multi-Version Concurrency Control (MVCC)**:
  - Writes do not block reads, and reads do not block writes.
  - Instead of overwriting data in-place, the database maintains multiple versions of each tuple with visibility timestamps (transaction IDs).
  - Used by modern relational engines including PostgreSQL. Old versions are reclaimed later through vacuuming.
