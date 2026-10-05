---
source_key: dsa_arrays_hashing
title: Arrays and Hashing Fundamentals
topic: dsa
source_origin: InsightPrep Technical Interview Preparation Corpus
source_license: project-authored
---

# Arrays and Hashing Fundamentals

## Overview and Memory Layout
An array is a contiguous block of memory storing elements of the same data type. Because memory is contiguous, element addresses can be calculated directly using an offset calculation: `address = base_address + index * element_size`. This layout gives arrays an O(1) random-access read and write time complexity.

A hash table (or hash map) builds on array indexing to provide associative key-value mapping. Keys are converted into integer array indices using a deterministic hash function followed by a modulo operation with the bucket array capacity.

## Core Time and Space Complexities
- **Static Array**:
  - Access / Update by Index: O(1) time.
  - Search (Unsorted): O(n) time.
  - Search (Sorted): O(log n) time using binary search.
  - Insert / Delete: O(n) time due to element shifting.
- **Dynamic Array (Vector / ArrayList)**:
  - Amortized Append: O(1) time. Resizing doubles capacity when full, copying n elements in O(n) time occasionally.
  - Space Overhead: O(n) storage, potentially holding unused allocated capacity.
- **Hash Table**:
  - Insert, Lookup, Delete (Average): O(1) time.
  - Worst Case (All keys collide): O(n) time.
  - Space Complexity: O(n) storage with load factor tuning (typically 0.7 to 0.75).

## Collision Resolution Strategies
1. **Separate Chaining**:
   - Each bucket points to a linked list (or balanced BST when chain length exceeds a threshold like 8 in modern runtimes).
   - Gracefully handles high load factors without table corruption.
   - Requires pointer overhead and suffers from lower cache locality.
2. **Open Addressing**:
   - All entries live directly inside the bucket array.
   - **Linear Probing**: Inspects bucket `(hash + i) % capacity`. Simple and cache-friendly, but prone to primary clustering.
   - **Quadratic Probing**: Inspects `(hash + c1*i + c2*i^2) % capacity` to reduce clustering.
   - **Double Hashing**: Uses a secondary hash function `(hash1 + i * hash2) % capacity` to disperse probes uniformly.

## Common Interview Patterns and Trade-offs
- **Two Pointers & Sliding Window**: Efficient on contiguous arrays for subarray sums, palindromes, or pair searches without auxiliary memory.
- **Prefix Sums**: Precomputes cumulative sums in O(n) time to answer range-sum queries in O(1) time.
- **Frequency Maps / Anagrams**: Storing element frequencies in an array of size 26 or a hash map allows O(n) identification of duplicates, common elements, or anagrams.
