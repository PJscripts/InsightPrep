---
source_key: dsa_trees_graphs
title: Trees and Graph Traversals
topic: dsa
source_origin: InsightPrep Technical Interview Preparation Corpus
source_license: project-authored
---

# Trees and Graph Traversals

## Tree Structures and Properties
A tree is a hierarchical, connected, undirected, and acyclic graph with N vertices and N-1 edges. A rooted tree has a designated root node, where every node has zero or more child nodes.

- **Binary Tree**: Every node has at most two children (left and right).
- **Binary Search Tree (BST)**: For every node with key K, all keys in its left subtree are less than K, and all keys in its right subtree are greater than K.
  - Inorder traversal of a BST yields elements in sorted order.
  - Search, insertion, and deletion run in O(h) time, where h is the tree height.
  - In a balanced BST (AVL, Red-Black), h = O(log n). In an unbalanced degenerate BST (linked list), h = O(n).

## Graph Representations
Graphs represent pairs of vertices connected by edges (directed or undirected, weighted or unweighted).
1. **Adjacency Matrix**:
   - 2D array of size V x V where `matrix[u][v]` indicates edge existence/weight.
   - Space Complexity: O(V^2).
   - Edge lookup: O(1). Finding all neighbors of a node: O(V).
   - Best for dense graphs.
2. **Adjacency List**:
   - Array or map of V lists, where `adj[u]` contains all adjacent vertices of u.
   - Space Complexity: O(V + E).
   - Finding neighbors: O(degree(u)).
   - Optimal for sparse graphs typical in interview questions.

## Traversal Algorithms: BFS vs. DFS
- **Breadth-First Search (BFS)**:
  - Explores vertices level-by-level using a FIFO queue.
  - Time Complexity: O(V + E). Space Complexity: O(V) to store the frontier queue.
  - Use cases: Shortest path in unweighted graphs, level-order traversal, finding connected components.
- **Depth-First Search (DFS)**:
  - Explores as deep as possible along each branch before backtracking using a recursion call stack or explicit LIFO stack.
  - Time Complexity: O(V + E). Space Complexity: O(V) recursion stack depth.
  - Use cases: Topological sorting, cycle detection in directed graphs, connected components, path finding.

## Cycle Detection and Topological Sort
- **Cycle Detection**:
  - Undirected Graph: Disjoint Set Union (DSU) or DFS by checking if a neighbor has been visited and is not the immediate parent.
  - Directed Graph: DFS with three-state node coloring (unvisited, currently visiting in current recursion stack, completely visited). A cycle exists if an edge leads to a node currently being visited (back-edge).
- **Topological Sorting**:
  - Linear ordering of vertices in a Directed Acyclic Graph (DAG) such that for every directed edge u -> v, u comes before v.
  - **Kahn's Algorithm (BFS)**: Computes in-degrees for all vertices, enqueues vertices with in-degree 0, and repeatedly decrements neighbor in-degrees upon removal. If processed nodes < V, a cycle exists.
  - **DFS Post-Order**: Performs DFS and pushes finished nodes onto a stack; reversing the stack yields the topological order.
