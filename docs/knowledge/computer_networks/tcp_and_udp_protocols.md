---
source_key: cn_tcp_udp_reliable_transport
title: Computer Networks TCP and UDP Protocols
topic: computer_networks
source_origin: InsightPrep Technical Interview Preparation Corpus
source_license: project-authored
---

# Computer Networks TCP and UDP Protocols

## TCP vs. UDP Core Distinction
The Transport Layer provides logical communication between process endpoints using 16-bit port numbers. The two primary protocols represent opposite ends of the trade-off spectrum between reliability and latency:

- **TCP (Transmission Control Protocol - RFC 793)**:
  - Connection-oriented (requires three-way handshake before data transfer).
  - Byte-stream oriented (no application message boundary preservation).
  - Guarantees in-order, error-free, duplicate-free delivery.
  - Features flow control, congestion control, and connection teardown.
  - Header size: 20 bytes minimum (up to 60 bytes with options).
  - Typical use cases: HTTP/1.1, HTTP/2, SSH, database drivers, email protocols.
- **UDP (User Datagram Protocol - RFC 768)**:
  - Connectionless (no handshake, stateless).
  - Message/Datagram oriented (preserves discrete packet boundaries).
  - Best-effort delivery: packets can be dropped, delayed, duplicated, or reordered without notification.
  - No flow control or congestion control.
  - Lightweight header: fixed 8 bytes (Source Port, Destination Port, Length, Checksum).
  - Typical use cases: Real-time gaming, live audio/video streaming (VoIP, WebRTC), DNS queries, DHCP, HTTP/3 (QUIC over UDP).

## TCP Connection Lifecycle
1. **Three-Way Handshake (Connection Establishment)**:
   - **Step 1 (SYN)**: Client sends `SYN=1`, random initial sequence number `seq = x`. Client enters `SYN-SENT` state.
   - **Step 2 (SYN-ACK)**: Server receives SYN, allocates buffers, responds with `SYN=1, ACK=1`, `seq = y`, `ack = x + 1`. Server enters `SYN-RECEIVED` state.
   - **Step 3 (ACK)**: Client sends `ACK=1`, `seq = x + 1`, `ack = y + 1`. Both enter `ESTABLISHED` state. Data payload can accompany this third packet.
2. **Four-Way Handshake (Connection Teardown)**:
   - Either side can initiate closure (e.g., Client sends `FIN`).
   - Server responds with `ACK`, entering `CLOSE-WAIT` state; Client enters `FIN-WAIT-2`.
   - Server finishes sending remaining pending data and sends its own `FIN`.
   - Client sends final `ACK` and enters `TIME-WAIT` state (lasting 2 * Maximum Segment Lifetime, or 2MSL, typically 60-120 seconds).
   - **Why TIME-WAIT exists**:
     - Ensures the final ACK is reliably received by the server (if lost, the server retransmits FIN).
     - Allows lingering duplicate segments from the connection to expire in network transit before reusing the same 4-tuple socket `(source_ip, source_port, dest_ip, dest_port)`.

## Reliability, Flow Control, and Congestion Control
- **Sequence Numbers and Cumulative ACKs**:
  - Every transmitted byte has a sequence number. The receiver acknowledges bytes using cumulative ACKs indicating the next expected byte.
  - Unacknowledged segments are retransmitted upon Retransmission Timeout (RTO) or upon receiving 3 duplicate ACKs (Fast Retransmit).
- **Flow Control (Sliding Window)**:
  - Prevents the sender from overwhelming the receiver's available buffer space.
  - Receiver advertises its available buffer capacity in the TCP header as `Receive Window (rwnd)`.
  - Sender limits outstanding unacknowledged bytes to `<= rwnd`.
- **Congestion Control**:
  - Prevents the network infrastructure (routers/switches) from buffer bloat and packet drops.
  - Maintains a Congestion Window (`cwnd`).
  - Four phases:
    1. **Slow Start**: `cwnd` starts small (e.g., 10 MSS) and doubles every Round Trip Time (RTT) exponentially until reaching `ssthresh` (slow start threshold).
    2. **Congestion Avoidance**: Once `cwnd >= ssthresh`, `cwnd` grows linearly by 1 MSS per RTT (Additive Increase).
    3. **Fast Retransmit**: Triggered by 3 duplicate ACKs; retransmits missing segment immediately before timer expires.
    4. **Fast Recovery**: Halves `ssthresh`, drops `cwnd` to the new threshold (Multiplicative Decrease), and resumes linear increase without resetting `cwnd` to 1.
