import sys
import os
from web3 import Web3
# Adding root directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import solcx
from solcx import install_solc, set_solc_version, compile_source
import config

#---------------------------Solidity Compiler Setup---------------------------------------------------------
# Install and set the Solidity compiler to version 0.8.13
install_solc('0.8.13')
set_solc_version('0.8.13')

#---------------------------Blockchain Connection-----------------------------------------------------------

def connect_to_blockchain():
    # Setting up global variables
    global e_voting_contract
    global default_account
    global w3
    # Connect to the Ganache local Ethereum blockchain
    ganache_url = "http://127.0.0.1:7545"
    w3 = Web3(Web3.HTTPProvider(ganache_url))

    # Check if the connection to the blockchain is successful
    if not w3.is_connected():
        raise Exception("Failed to connect to the Ethereum network")
    if(config.PRINT_BACKEND_LOGS): print("Connected to Ethereum network")

    # Set the default account (owner) for transactions
    default_account = w3.eth.accounts[0]
    w3.eth.default_account = default_account

    # Check and display the balance of the default account
    balance = w3.eth.get_balance(default_account)
    if(config.PRINT_BACKEND_LOGS): print(f"Default account balance: {w3.from_wei(balance, 'ether')} ETH")

    #---------------------------Solidity Contract Code----------------------------------------------------------
    # Solidity source code for the e-voting contract
    solidity_source_code = '''
    // SPDX-License-Identifier: MIT
    pragma solidity ^0.8.13;

    contract EVoting {
        struct Candidate {
            uint id;
            string name;
            uint voteCount;
        }

        struct Voter {
            bool authorized;
            bool voted;
            uint vote;
        }

        address public owner;
        string public electionName;

        mapping(address => Voter) public voters;
        Candidate[] public candidates;
        uint public totalVotes;

        modifier ownerOnly() {
            require(msg.sender == owner, "You are not the owner");
            _;
        }

        event VoteCast(address voter, uint candidateId);

        constructor(string memory _electionName) {
            require(bytes(_electionName).length > 0, "Election name cannot be empty");
            owner = msg.sender;
            electionName = _electionName;
        }

        function addCandidate(string memory _name) public ownerOnly {
            require(bytes(_name).length > 0, "Candidate name cannot be empty");
            candidates.push(Candidate(candidates.length, _name, 0));
        }

        function authorizeVoter(address _voter) public ownerOnly {
            require(_voter != address(0), "Invalid voter address");
            voters[_voter].authorized = true;
        }

        function vote(uint _candidateId) public {
            Voter storage sender = voters[msg.sender];
            require(sender.authorized, "You are not authorized to vote");
            require(!sender.voted, "You have already voted");
            require(_candidateId < candidates.length, "Invalid candidate");

            sender.voted = true;
            sender.vote = _candidateId;

            candidates[_candidateId].voteCount += 1;
            totalVotes += 1;

            emit VoteCast(msg.sender, _candidateId);
        }

        function endElection() public ownerOnly view returns (string memory winnerName, uint winnerVoteCount) {
            require(candidates.length > 0, "No candidates in the election");
            uint winningVoteCount = 0;
            uint winningCandidateId = 0;

            for (uint i = 0; i < candidates.length; i++) {
                if (candidates[i].voteCount > winningVoteCount) {
                    winningVoteCount = candidates[i].voteCount;
                    winningCandidateId = i;
                }
            }

            winnerName = candidates[winningCandidateId].name;
            winnerVoteCount = candidates[winningCandidateId].voteCount;
        }

        function getTotalCandidates() public view returns (uint) {
            return candidates.length;
        }

        function getCandidate(uint _candidateId) public view returns (string memory name, uint voteCount) {
            return (candidates[_candidateId].name, candidates[_candidateId].voteCount);
        }
    }
    '''

    #---------------------------Compile and Deploy Contract-----------------------------------------------------
    # Compile the Solidity contract source code
    try:
        compiled_sol = compile_source(solidity_source_code, output_values=['abi', 'bin'])
        contract_interface = compiled_sol['<stdin>:EVoting']
        if(config.PRINT_BACKEND_LOGS): print("Contract compiled successfully")
    except Exception as e:
        print(f"Compilation failed: {e}")
        sys.exit(1)

    # Deploy the compiled contract to the blockchain
    EVoting = w3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])
    try:
        tx_hash = EVoting.constructor("Sample Election").transact({
            'from': default_account,
            'gas': 3000000,
            'gasPrice': w3.to_wei('20', 'gwei')
        })
        if(config.PRINT_BACKEND_LOGS): print(f"Transaction hash: {tx_hash.hex()}")
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if(config.PRINT_BACKEND_LOGS): print(f"Contract deployed at address: {tx_receipt.contractAddress}")
    except Exception as e:
        print(f"Deployment failed: {e}")
        sys.exit(1)

    # Create a contract instance to interact with the deployed contract
    e_voting_contract = w3.eth.contract(address=tx_receipt.contractAddress, abi=contract_interface['abi'])

#---------------------------Helper Functions--------------------------------------------------------------
# Function to add a candidate to the election contract
def add_candidate(name):
    """
    Adds a candidate to the election contract.

    Args:
    name (str): The candidate's name.
    """
    try:
        tx_hash = e_voting_contract.functions.addCandidate(name).transact({
            'from': default_account,
            'gas': 100000
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
        if(config.PRINT_BACKEND_LOGS): print(f"Candidate '{name}' added successfully.")
    except Exception as e:
        print(f"Failed to add candidate '{name}': {e}")

# Function to create a voter account and authorize them in the contract
def create_voter_account(voter_id):
    """
    Assigns a Ganache account to the voter and authorizes them to vote.

    Args:
    voter_id (str): The voter ID (index of Ganache accounts).

    Returns:
    str: The voter's Ethereum address.
    """
    try:
        voter_address = w3.eth.accounts[int(voter_id)]  # Use predefined Ganache accounts
        tx_hash = e_voting_contract.functions.authorizeVoter(voter_address).transact({
            'from': default_account,
            'gas': 100000
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
        if(config.PRINT_BACKEND_LOGS): print(f"Voter index {voter_id} is now authorized.")
        return voter_address
    except Exception as e:
        print(f"Failed to create voter account and authorize voter: {e}")
        return None

# Function to cast a vote for a candidate
def cast_vote_transact(voter_address, candidate_number):
    """
    Casts a vote for a specified candidate.

    Args:
    voter_address (str): The voter's Ethereum address.
    candidate_number (int): The index of the candidate to vote for.
    """
    try:
        w3.eth.default_account = voter_address
        tx_hash = e_voting_contract.functions.vote(candidate_number).transact({
            'from': voter_address,
            'gas': 100000
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
        if(config.PRINT_BACKEND_LOGS): print(f"Vote cast by {voter_address} for candidate number {candidate_number}.")
    except Exception as e:
        print(f"Failed to cast vote by {voter_address}: {e}")

# Function to end the election and display the winner
def end_election():
    """
    Ends the election and announces the winner based on the votes.
    """
    try:
        w3.eth.default_account = default_account
        winner_name, winner_vote_count = e_voting_contract.functions.endElection().call({
            'from': default_account
        })
        print(f"The winner is {winner_name} with {winner_vote_count} votes.")
    except Exception as e:
        print(f"Failed to end election: {e}")

# Function to list all registered candidates
def list_candidates():
    """
    Lists all candidates participating in the election and their vote counts.
    
    Returns:
    list: A list of candidates with their index, name, and vote count.
    """
    try:
        total_candidates = e_voting_contract.functions.getTotalCandidates().call()
        print("List of candidates:")
        candidates = []
        for i in range(total_candidates):
            name, vote_count = e_voting_contract.functions.getCandidate(i).call()
            candidates.append((i, name, vote_count))
            print(f"{i + 1}. {name} - Votes: {vote_count}")
        return candidates
    except Exception as e:
        print(f"Failed to list candidates: {e}")

#---------------------------CLI Functions--------------------------------------------------------------
def register_candidates():
    """
    Allows the user to register candidates interactively.
    """
    print("Register candidates")
    while True:
        candidate_name = input("Enter candidate name (or type 'done' to finish): ")
        if candidate_name.lower() == 'done':
            break
        add_candidate(candidate_name)

def register_voters():
    """
    Allows the user to register voters interactively.
    """
    print("Register voters")
    while True:
        voter_id = input("Enter voter ID (or type 'done' to finish): ")
        if voter_id.lower() == 'done':
            break
        voter_address = create_voter_account(voter_id)

def conduct_voting():
    """
    Conducts the voting process by displaying candidates and allowing voters to cast their votes.
    """
    print("Voting begins")
    candidates = list
