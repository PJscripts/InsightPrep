---
source_key: os_process_threads_synchronization
title: Operating Systems Processes, Threads, and Synchronization
topic: operating_systems
source_origin: InsightPrep Technical Interview Preparation Corpus
source_license: project-authored
---

# Operating Systems Processes, Threads, and Synchronization

## Process vs. Thread
- **Process**:
  - An executing instance of a computer program.
  - Represents the fundamental unit of resource allocation by the operating system.
  - Possesses an isolated address space containing Text (code), Data (globals), BSS, Heap (dynamic memory), and Stack.
  - Managed by the OS kernel using a Process Control Block (PCB) storing PID, registers, program counter, and open file descriptors.
  - Inter-Process Communication (IPC) requires explicit mechanisms: pipes, sockets, shared memory, or message queues.
- **Thread**:
  - The smallest unit of CPU scheduling and execution within a process.
  - Often referred to as a "lightweight process".
  - Multiple threads within the same process share the text section, data section, heap, and open file handles.
  - Each thread maintains its own private Thread Control Block (TCB), Program Counter (PC), CPU register state, and private call stack.
  - Context switching between threads of the same process is significantly faster than process context switching because the virtual memory address space (page tables / TLB) does not need to be flushed or replaced.

## CPU Scheduling Concepts
The operating system CPU scheduler selects runnable processes from the ready queue:
- **Preemptive vs. Non-preemptive**:
  - Non-preemptive: Once a process gets the CPU, it holds it until termination or voluntary I/O wait.
  - Preemptive: The kernel can interrupt an executing process when a timer interrupt fires or a higher-priority task arrives.
- **Common Algorithms**:
  - **First-Come, First-Served (FCFS)**: Non-preemptive; susceptible to the "convoy effect" where short jobs wait behind long jobs.
  - **Shortest Job First (SJF) / Shortest Remaining Time First (SRTF)**: Minimizes average waiting time; risks starvation of long jobs.
  - **Round Robin (RR)**: Preemptive scheduling allocating fixed time quantum slices. Balances responsiveness.
  - **Multi-Level Feedback Queue (MLFQ)**: Dynamically adjusts process priorities based on observed CPU-burst vs. I/O-burst behavior.

## Synchronization Primitives and Critical Sections
When concurrent threads access shared mutable data, a Race Condition occurs if the outcome depends on the timing or interleaving of thread execution. A Critical Section is the block of code accessing shared resources.
- **Mutual Exclusion (Mutex)**:
  - A binary locking mechanism with ownership semantics (the thread that locks the mutex must unlock it).
  - Threads attempting to acquire a locked mutex are blocked and put to sleep by the kernel.
- **Spinlock**:
  - Repeatedly polls a memory flag using atomic hardware instructions (e.g., Test-and-Set, Compare-and-Swap).
  - Avoids context switch overhead; useful for very short waits on multi-core systems, but wastes CPU cycles if held long.
- **Counting Semaphore**:
  - Maintains an integer counter representing available resource units.
  - `wait()` / `P()`: Decrements counter; blocks if counter <= 0.
  - `signal()` / `V()`: Increments counter; awakens a waiting thread.

## Deadlock: Conditions and Strategies
A deadlock occurs when a set of concurrent processes are permanently blocked because each is holding a resource and waiting for another resource held by another process.
- **The Four Coffman Conditions** (All four must hold simultaneously for a deadlock to exist):
  1. **Mutual Exclusion**: At least one resource is held in a non-shareable mode.
  2. **Hold and Wait**: A process holds at least one resource while waiting to acquire additional resources.
  3. **No Preemption**: Resources cannot be forcibly taken from a process holding them.
  4. **Circular Wait**: A closed chain of processes exists where each process waits for a resource held by the next process in the chain.
- **Deadlock Handling**:
  - **Prevention**: Invalidate at least one Coffman condition (e.g., impose strict global resource ordering to eliminate circular wait).
  - **Avoidance**: Dynamically evaluate resource requests using algorithms like the Banker's Algorithm to ensure the system remains in a safe state.
  - **Detection and Recovery**: Periodically build and inspect resource allocation wait-for graphs; terminate deadlocked processes or preempt resources.
