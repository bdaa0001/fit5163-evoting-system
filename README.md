# Secure Voting Application

* Christian Wu
* Meng-Chin Lee
* Dava Baatar

## Overview

This project is a simple e-voting system that leverages **blind signatures**, **blockchain**, and **smart contracts** to provide a secure and anonymous voting platform. The system ensures voter privacy while maintaining the integrity of the voting process through cryptographic techniques and decentralized technologies.

## Project Structure
The project is organized into several key directories and files, each contributing to different aspects of the e-voting system:

- **core/**: This directory contains the core components of the project, including:
  - `blinding_signature.py`: Handles the implementation of blind signatures, ensuring voter anonymity.
  - `blockchain_ganache.py`: Implements the blockchain logic using Ganache, which serves as the backbone for storing votes and ensuring transparency.
  
- **auth/**: This directory focuses on voter authentication:
  - `voter_authentication.py`: Contains code to manage the voter authentication process, ensuring only eligible voters can cast a vote.

- **main.py**: This is the main entry point of the system. The voting process can be run and managed from here. It orchestrates the interaction between the voter, blind signatures, and the blockchain.

## Features

- **Blind Signatures**: Voters can cast votes without revealing their identity, ensuring privacy.
- **Blockchain Integration**: Votes are stored in a transparent and tamper-resistant manner using blockchain.
- **Smart Contracts**: Utilizes Ethereum-based smart contracts to manage vote transactions and ensure fairness.
- **Voter Authentication**: A secure mechanism to verify voters' identities before they participate in the election.

## Installation
To run this project, you need to have the following installed on your system:
- **Python 3.x**
- **Ganache** (for blockchain simulation)
- **Solidity Compiler (solc)** (for smart contracts)

### Steps
1. Clone the repository:
    ```bash
    git clone https://github.com/bdaa0001/fit5163-evoting-system.git
    cd e-voting-system
    ```

2. Install the required Python dependencies:
    ```bash
    pip install -r <requirements>
    ```

3. Start Ganache for blockchain simulation:
    - Insstall Ganache from https://archive.trufflesuite.com/ganache/
    - Ensure that Ganache is running locally to allow the project to connect to the blockchain network.

4. Compile the smart contracts using the Solidity compiler (`solc`).

5. Run the project from `main.py`:
    ```bash
    python main.py
    ```

## Usage

1. **Voter Registration**: First, the system will authenticate voters to ensure they are eligible to vote.
2. **Voting Process**: Voters cast their votes, which are then anonymized using blind signatures.
3. **Blockchain Storage**: Votes are securely stored on the blockchain, and the results are computed via the smart contract.

## Future Enhancements

- **Scalability**: Improving the system to handle a larger number of voters.
- **Front-end Interface**: Developing a user-friendly front-end to allow voters to interact with the system more easily.
- **Support for Multiple Elections**: Extending the system to support multiple elections simultaneously.
