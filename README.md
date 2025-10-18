# Post-Quantum Secure E-Voting System

A PyQt5-based administrative interface for running and visualizing the [Hyperion voting protocol](https://github.com/hyperion-voting/hyperion) with post-quantum cryptography considerations.

## Overview

This project provides a graphical user interface for:
- **Running the Hyperion Protocol**: Execute the complete receipt-free voting protocol
- **Viewing Results**: Display tallying results in an easy-to-read table
- **Analyzing Logs**: Inspect detailed protocol execution output
- **Understanding PQC Migration**: Reference table mapping classical to post-quantum cryptographic components

## Features

- One-click Hyperion protocol execution
- Real-time protocol log viewing
- Bulletin board visualization
- Post-quantum cryptography mapping reference
- FastAPI backend for protocol coordination

## Prerequisites

- **Operating System**: Linux (tested on Fedora/Ubuntu) or macOS
- **Python**: Python 3.8 or higher
- **Git**: For cloning the Hyperion repository

## Setup

### 1. Run Setup Script

The setup script will automatically:
- Clone the Hyperion voting protocol repository
- Create a Python virtual environment (`.venv/`)
- Install all required dependencies (FastAPI, PyQt5, Hyperion requirements)
- Install the threshold cryptography library

```bash
chmod +x setup.sh
./setup.sh
```
## Running the Admin GUI

### Step 1: Start the Server (Terminal 1)

```bash
./run_server.sh
```

Expected output:
```
[*] Starting Hyperion e-voting server...
INFO:     Started server process
INFO:     Uvicorn running on http://127.0.0.1:8000
```

The server runs a FastAPI application that coordinates the Hyperion protocol execution.

### Step 2: Start the Admin GUI (Terminal 2)

```bash
./run_admin.sh
```

A PyQt5 window will open with four tabs:
1. **Tally Results** - Run the protocol and view voting results
2. **Bulletin Board** - View the final bulletin board
3. **Logs** - View raw Hyperion protocol console output
4. **PQC Mapping** - Reference table for post-quantum alternatives

## Using the Admin GUI

### Running the Hyperion Protocol

1. Click the **"Run Tally"** button in the Tally Results tab
2. The system will execute the full Hyperion protocol:
   - **PoC Setup**: Generate ECDSA keys for voters and tellers
   - **Setup Phase**: Initialize threshold cryptography (3 tellers by default)
   - **Voting Phase**: Simulate 50 voters casting encrypted ballots
   - **Tallying Phase**: Perform threshold decryption and mixnet shuffling
   - **Verification**: Run zero-knowledge proofs for ballot validity
3. The GUI will automatically switch to the **Logs** tab to show progress
4. Once complete, view results in the **Tally Results** table

### Viewing the Bulletin Board

- Click **"Refresh BB"** in the Bulletin Board tab
- Displays the final bulletin board with:
  - Vote data (encrypted EC-ElGamal points)
  - Commitments for each ballot

## Project Structure

```
e-voting-pq-main/
├── client/
│   └── admin_gui.py        # PyQt5 admin interface
├── server/
│   ├── app.py              # FastAPI application
│   ├── hyperion_runner.py  # Hyperion protocol runner
├── hyperion/               # Hyperion protocol (cloned during setup)
├── setup.sh                # Automated setup script
├── run_server.sh           # Server launch script
├── run_admin.sh            # Admin GUI launch script
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## References

- [Hyperion Voting Protocol](https://github.com/hyperion-voting/hyperion) - Original protocol implementation
- [NIST Post-Quantum Cryptography](https://csrc.nist.gov/projects/post-quantum-cryptography) - PQC standardization
- [ML-KEM (Kyber)](https://csrc.nist.gov/pubs/fips/203/final) - NIST FIPS 203
- [ML-DSA (Dilithium)](https://csrc.nist.gov/pubs/fips/204/final) - NIST FIPS 204

## License

This project is for research and educational purposes. Refer to the [Hyperion project license](https://github.com/hyperion-voting/hyperion) for the underlying protocol.

---

**⚠️ Note**: This is a demonstration GUI for the Hyperion protocol. The protocol simulates voters internally. This interface is designed for understanding and analyzing the cryptographic operations involved in receipt-free e-voting systems.

