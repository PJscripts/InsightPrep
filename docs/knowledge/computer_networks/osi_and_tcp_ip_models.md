---
source_key: cn_osi_tcp_ip_models
title: Computer Networks OSI Model and TCP/IP Architecture
topic: computer_networks
source_origin: InsightPrep Technical Interview Preparation Corpus
source_license: project-authored
---

# Computer Networks OSI Model and TCP/IP Architecture

## Architectural Comparison: OSI vs. TCP/IP
Network communication architectures standardize multi-system interoperability through layered abstraction models:

1. **OSI 7-Layer Reference Model**:
   - **Layer 7 - Application**: Network processes directly serving user applications (HTTP, SMTP, DNS, FTP).
   - **Layer 6 - Presentation**: Data representation, serialization, compression, and encryption (TLS/SSL).
   - **Layer 5 - Session**: Manages dialogue control, connection establishment, and session checkpoints.
   - **Layer 4 - Transport**: End-to-end communication, reliability, multiplexing via port numbers (TCP, UDP).
   - **Layer 3 - Network**: Logical addressing, host-to-host routing across autonomous systems (IP, ICMP, BGP).
   - **Layer 2 - Data Link**: Physical frame addressing, hop-to-hop transit across single link (Ethernet, MAC, ARP).
   - **Layer 1 - Physical**: Raw electrical, optical, or radio bitstream transmission across physical media.

2. **TCP/IP 4-Layer Implementation Model**:
   - **Application Layer**: Combines OSI layers 7, 6, and 5 (HTTP, DNS, SSH, TLS).
   - **Transport Layer**: Matches OSI layer 4 (TCP, UDP).
   - **Internet Layer**: Matches OSI layer 3 (IPv4, IPv6, ICMP).
   - **Network Access / Link Layer**: Combines OSI layers 2 and 1 (Ethernet, Wi-Fi, MAC).

## Data Encapsulation and Protocol Data Units (PDUs)
When data traverses down the protocol stack at the sender, each layer prepends a protocol header (and sometimes a trailer):
- Application Layer: **Data / Message / Payload**.
- Transport Layer: **Segment** (TCP) or **Datagram** (UDP) adding source and destination port numbers.
- Network Layer: **Packet** adding source and destination IP addresses.
- Data Link Layer: **Frame** adding source and destination MAC addresses and CRC checksum trailer.
- Physical Layer: **Bits** transmitted across physical medium.
Upon arrival at the destination host, the reverse process (Decapsulation) strips each layer's header before handing the payload to the appropriate higher-layer protocol.

## Core Protocol Roles
- **IP (Internet Protocol - RFC 791 / RFC 8200)**:
  - Connectionless, best-effort packet delivery service.
  - Does not guarantee packet ordering, delivery, or duplicate prevention.
- **ARP (Address Resolution Protocol)**:
  - Resolves a known 32-bit IPv4 address to a 48-bit physical MAC address on a local area network (LAN) via broadcast request and unicast reply.
- **DNS (Domain Name System)**:
  - Distributed hierarchical naming system translating human-readable domain names (e.g., `api.example.com`) to numeric IP addresses.
  - Primarily utilizes UDP port 53 for low latency; falls back to TCP when response payload exceeds 512 bytes or for zone transfers.
- **ICMP (Internet Control Message Protocol)**:
  - Network-layer diagnostic and reporting tool (e.g., `ping` Echo Request/Reply, `traceroute` Time-to-Live expired messages).
