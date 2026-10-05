---
source_key: dbms_indexing_b_trees
title: Database Indexing, B-Trees, and Query Optimization
topic: dbms
source_origin: InsightPrep Technical Interview Preparation Corpus
source_license: project-authored
---

# Database Indexing, B-Trees, and Query Optimization

## Why Indexes Matter
Without an index, a relational database must execute a Full Table Scan (Sequential Scan), reading every disk block allocated to the table to filter matching rows (O(n) I/O cost). Indexes are auxiliary search structures that map indexed column values directly to physical tuple identifiers (TIDs or RowIDs), reducing lookups to O(log n) I/O operations.

## B-Tree and B+ Tree Architecture
Most relational database management systems use B+ Trees as their default general-purpose indexing structure.
- **B-Tree Structure**:
  - Balanced, multi-way search tree where all leaf nodes reside at the exact same depth.
  - High branching factor (fan-out): A node typically corresponds to a disk page (e.g., 8 KB) and holds hundreds of keys, keeping the tree depth low (often 3 to 4 levels for millions of rows).
- **B+ Tree Enhancements over Standard B-Trees**:
  - Data records / Row pointers are stored exclusively in leaf nodes.
  - Internal nodes store only navigation routing keys and child page pointers, maximizing the branching factor.
  - Leaf nodes are linked sequentially as a doubly linked list, enabling highly efficient range scans (e.g., `BETWEEN`, `>`, `<`) by following leaf pointers without re-traversing parent nodes.

## Clustered vs. Non-Clustered Indexes
1. **Clustered Index**:
   - Determines the physical storage order of rows on disk.
   - Because physical storage can have only one ordering, a table can possess at most one clustered index (often the primary key in engines like MySQL InnoDB).
   - In PostgreSQL, heap tables are unordered by default, but the `CLUSTER` command can physically sort a table based on an index once.
2. **Non-Clustered (Secondary) Index**:
   - A separate search structure whose leaf nodes contain the indexed key value and a pointer (tuple ID or primary key) pointing to the corresponding row in the heap.
   - Requires a secondary heap lookup unless the query is a "Covering Index" query where all requested columns reside inside the index itself.

## Composite Indexes and the Leftmost Prefix Rule
- A composite index covers multiple columns: `CREATE INDEX idx_emp_dept_salary ON employee(dept_id, salary)`.
- **Leftmost Prefix Rule**: The query optimizer can utilize this index if the `WHERE` clause filters by:
  - `dept_id` alone.
  - `dept_id` AND `salary`.
- The index cannot be used efficiently for lookups on `salary` alone because the tree is sorted first by `dept_id`.

## Index Types and Specializations
- **B-Tree**: Default choice for equality (`=`), range (`<`, `<=`, `>`, `>=`, `BETWEEN`), and sorting (`ORDER BY`).
- **Hash Index**: Supports O(1) exact equality lookups (`=`); does not support range scans.
- **GiST / GIN (Generalized Inverted Index)**: Suited for full-text search, JSONB documents, and array containment.
- **Vector Indexes (HNSW / IVFFlat)**: Used with extensions like pgvector for high-dimensional approximate nearest neighbor (ANN) vector similarity searches.
