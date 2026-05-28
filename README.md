# PyHealthChain - Blockchain-based Electronic Health Record System

A decentralized blockchain network for managing electronic health records (EHR) with peer-to-peer consensus, cryptographic security, and gRPC-based block synchronization.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   Node List Server                        │
│              (port 9009, Twisted UDP)                     │
│              Registers & discovers peers                  │
└────┬──────────────────────────────────┬───────────────────┘
     │                                  │
     ▼                                  ▼
┌──────────┐                     ┌──────────┐
│  Node 1  │◄──────────────────►│  Node 2  │
│          │    gRPC (50051)     │          │
│  ┌──────┐│    Twisted (5000)   │┌──────┐  │
│  │Chain ││    JSON-RPC (client)││Chain │  │
│  └──────┘│                     │└──────┘  │
└──────────┘                     └──────────┘
     │                                  │
     ▼                                  ▼
┌──────────┐                     ┌──────────┐
│ MongoDB  │                     │ MongoDB  │
└──────────┘                     └──────────┘
```

### Components

- **Node List Server** (`node_list_server.py`): Central registry running on port 9009. New nodes register here and receive a list of active peers.
- **Blockchain Node** (`server.py`): Each node runs a full blockchain node with:
  - Twisted UDP protocol for peer discovery and light messaging
  - gRPC server for block synchronization between nodes
  - JSON-RPC interface for client communication
- **Blockchain Core** (`blockchain/`): Block/chain data structures, transaction model, peer management, cryptographic identity
- **Security** (`blockchain/security/`): RSA-based signing, encryption, and verification
- **Storage** (`blockchain/storage/`): MongoDB persistence layer

### Communication Protocols

| Protocol | Port | Purpose |
|----------|------|---------|
| Twisted UDP | 5000 | Peer-to-peer messages, leader election |
| gRPC | 50051 | Block/chain download between nodes |
| JSON-RPC | (default) | Client-to-node API |
| UDP | 9009 | Node list server (central registry) |

## Setup

### Prerequisites

- Python 3.10+
- MongoDB (running on default port 27017)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Generate gRPC Code (if proto changes)

```bash
python -m grpc_tools.protoc -I proto --python_out=. --grpc_python_out=. proto/block.proto
```

## Running

### 1. Start Node List Server (central registry)

```bash
python node_list_server.py
```

This must be running first so nodes can discover each other.

### 2. Start Blockchain Node(s)

```bash
python server.py <mongo_host> <node_name>
```

Example:
```bash
python server.py localhost node-alpha
```

The `<mongo_host>` is the hostname/IP of the MongoDB server. If omitted, you'll be prompted. The `<node_name>` is a unique name for this node.

### 3. Client API

The JSON-RPC server starts automatically with each node. Clients can connect and call methods like:
- `create_account` - Register a new user
- `insert_record` - Add health records
- `view_records` - View patient records
- `update_permissions` - Manage doctor access

## Data Model

- **Blocks**: Each block contains a header (hash, prev_hash, data_hash) and a list of transactions
- **Transactions**: Typed data entries (record, permission update, account init, appointment)
- **Records**: Clinical data types including notes, test results, prescriptions, and allergies

## Security

- RSA 2048-bit keys for node identity
- SHA-256 hashing for block linking and data integrity
- Digital signatures on all peer-to-peer messages
- Encrypted communication for sensitive data

## Project Structure

```
├── server.py                  # Main blockchain node server
├── node_list_server.py        # Central peer registry
├── _server_helper.py          # Server utility functions
├── _grpc_server_helper.py     # gRPC server for block sync
├── _grpc_client_helper.py     # gRPC client for block download
├── blockchain/
│   ├── block.py               # Block data structure
│   ├── blockchain.py          # Chain data structure
│   ├── transaction.py         # Transaction data model
│   ├── peer.py                # Peer management
│   ├── errors.py              # Custom exceptions
│   ├── security/
│   │   ├── Identity.py        # RSA key management & crypto
│   │   └── __init__.py        # Verify/encrypt helpers
│   └── storage/
│       ├── database.py        # MongoDB interface
│       ├── onchain.py         # On-chain data persistence
│       └── object/            # Data models (Person, Patient, etc.)
├── clients/
│   ├── rpc.py                 # Client RPC methods
│   ├── transact.py            # Client call wrappers
│   └── decorators.py          # Auth decorators
├── proto/block.proto          # gRPC protocol definition
├── block_pb2.py               # Generated protobuf code
├── block_pb2_grpc.py          # Generated gRPC code
├── requirements.txt           # Python dependencies
└── Dockerfile                 # Container setup
```
