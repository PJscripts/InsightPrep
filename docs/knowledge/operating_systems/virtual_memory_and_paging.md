---
source_key: os_virtual_memory_paging
title: Operating Systems Virtual Memory and Paging
topic: operating_systems
source_origin: InsightPrep Technical Interview Preparation Corpus
source_license: project-authored
---

# Operating Systems Virtual Memory and Paging

## Virtual Memory Overview
Virtual memory is a memory management technique providing an idealized abstraction of the storage resources available on a machine. It provides three primary advantages:
1. **Isolation and Protection**: Each process executes within its own private virtual address space, preventing unauthorized access or corruption of another process's memory.
2. **Simplified Programming**: Programs do not need to manage contiguous physical RAM placement or relocate addresses based on physical load locations.
3. **Overcommitment**: Programs can allocate address spaces larger than available physical RAM by transparently paging inactive memory to secondary storage (swap space).

## Address Translation and Paging Architecture
- **Pages and Frames**:
  - Virtual address space is divided into fixed-size contiguous blocks called **Pages** (commonly 4 KB).
  - Physical memory (RAM) is divided into equal-sized blocks called **Page Frames**.
- **Virtual Address Breakdown**:
  - A virtual address is split by the hardware into: `Virtual Page Number (VPN)` and `Page Offset`.
  - The offset remains unchanged because page boundaries align with frame boundaries.
- **Page Table**:
  - Maintained by the kernel for each process.
  - Maps the VPN to a Physical Frame Number (PFN).
  - Contains status bits:
    - **Valid / Present Bit**: 1 if page is resident in physical RAM; 0 if swapped out or unallocated.
    - **Dirty (Modified) Bit**: 1 if the page was written to, requiring a write-back before eviction.
    - **Reference (Accessed) Bit**: 1 if the page was recently read or written (used by replacement algorithms).
    - **Permission Bits**: Read, Write, Execute flags.

## The Translation Lookaside Buffer (TLB)
Because page tables reside in main memory, translating every address requires an extra memory access. The CPU includes the **TLB (Translation Lookaside Buffer)**:
- A high-speed hardware associative cache located directly on the Memory Management Unit (MMU).
- Caches recently translated VPN-to-PFN mappings.
- **TLB Hit**: Address translation resolves in 1 clock cycle.
- **TLB Miss**: The hardware page table walker or kernel trap fetches the PTE from memory into the TLB (10-100 cycles).
- On process context switch, TLB entries are invalidated or tagged with an Address Space Identifier (ASID).

## Page Fault Handling
When a process references a virtual address whose page table entry has the Present bit set to 0:
1. The MMU raises a hardware interrupt known as a **Page Fault Exception**.
2. The CPU switches to kernel mode and saves the faulting instruction pointer.
3. The OS page fault handler checks if the address is within the process's valid virtual memory regions:
   - If invalid: Raises a Segmentation Fault (`SIGSEGV`) and terminates the process.
   - If valid: The page is valid but currently not in physical RAM (swapped out or demand-paged).
4. The OS finds a free physical frame in RAM (or evicts an existing page using a page replacement algorithm).
5. The OS initiates a blocking disk I/O operation to read the page content from swap or the executable binary.
6. The page table is updated with the new PFN and the Present bit is set to 1.
7. The OS restores the process state and re-executes the faulting instruction transparently.

## Page Replacement Algorithms and Thrashing
When physical memory is full, the OS must choose a victim page to evict:
- **Optimal (OPT)**: Evicts the page that will not be used for the longest time in the future. Theoretical benchmark; impossible to implement in practice.
- **Least Recently Used (LRU)**: Evicts the page unused for the longest duration. Excellent heuristic, but expensive to maintain exact timestamps.
- **Clock (Second Chance)**: Practical approximation of LRU using the Reference bit arranged in a circular buffer.
- **Thrashing**: Occurs when the sum of active working sets of all running processes exceeds available physical memory. The system spends virtually all its CPU time swapping pages in and out of disk rather than executing user code. Resolved by reducing degree of multiprogramming.
