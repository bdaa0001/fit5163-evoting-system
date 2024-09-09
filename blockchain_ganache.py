import sys
from web3 import Web3
from solcx import compile_source, install_solc, set_solc_version

# Install and set Solidity compiler
install_solc('0.8.0')
set_solc_version('0.8.0')

# Connect to Ganache
ganache_url = "http://127.0.0.1:7545"
w3 = Web3(Web3.HTTPProvider(ganache_url))

# Check connection
if not w3.is_connected():
    raise Exception("Failed to connect to the Ethereum network")
print("Connected to Ethereum network")

# Set the default account (owner)
default_account = w3.eth.accounts[0]
w3.eth.default_account = default_account

# Check the balance of the default account
balance = w3.eth.get_balance(default_account)
print(f"Default account balance: {w3.from_wei(balance, 'ether')} ETH")

# Solidity source code
solidity_source_code = '''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

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

try:
    compiled_sol = compile_source(solidity_source_code, output_values=['abi', 'bin'])
    contract_interface = compiled_sol['<stdin>:EVoting']
    print("Contract compiled successfully")
except Exception as e:
    print(f"Compilation failed: {e}")
    sys.exit(1)

# Deploy the contract
EVoting = w3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])
try:
    tx_hash = EVoting.constructor("Sample Election").transact({
        'from': default_account,
        'gas': 3000000,
        'gasPrice': w3.to_wei('20', 'gwei')
    })
    print(f"Transaction hash: {tx_hash.hex()}")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Contract deployed at address: {tx_receipt.contractAddress}")
except Exception as e:
    print(f"Deployment failed: {e}")
    sys.exit(1)

# Create a contract instance
e_voting_contract = w3.eth.contract(address=tx_receipt.contractAddress, abi=contract_interface['abi'])

# Store voter accounts with their IDs
voter_accounts = {}

# Functions to interact with the contract
# create a block in Ganache for candidate to be added in e-voting contract
def add_candidate(name):
    try:
        tx_hash = e_voting_contract.functions.addCandidate(name).transact({
            'from': default_account,
            'gas': 100000
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Candidate '{name}' added successfully.")
    except Exception as e:
        print(f"Failed to add candidate '{name}': {e}")

# Assign an existing Ganache accountfor a voter and create a block in Ganache to be authorized in e-voting contract
def create_voter_account(voter_id):
    """Assign an existing Ganache account to the voter ID and authorize the voter."""
    try:
        voter_address = w3.eth.accounts[int(voter_id)]  # Use predefined Ganache accounts
        # voter_accounts[voter_id] = voter_address
        tx_hash = e_voting_contract.functions.authorizeVoter(voter_address).transact({
            'from': default_account,
            'gas': 100000
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Voter index {voter_id} is now authorized.")
        return voter_address
    except Exception as e:
        print(f"Failed to create voter account and authorize voter: {e}")
        return None

# Cast a vote from voter for a candidate and create a block in Ganache to be added in e-voting contract
def cast_vote_transact(voter_address, candidate_number):
    try:
        w3.eth.default_account = voter_address
        tx_hash = e_voting_contract.functions.vote(candidate_number).transact({
            'from': voter_address,
            'gas': 100000
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Vote cast by {voter_address} for candidate number {candidate_number}.")
    except Exception as e:
        print(f"Failed to cast vote by {voter_address}: {e}")

def end_election():
    try:
        w3.eth.default_account = default_account
        winner_name, winner_vote_count = e_voting_contract.functions.endElection().call({
            'from': default_account
        })
        print(f"The winner is {winner_name} with {winner_vote_count} votes.")
    except Exception as e:
        print(f"Failed to end election: {e}")

def list_candidates():
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

# CLI functions
def register_candidates():
    print("Register candidates")
    while True:
        candidate_name = input("Enter candidate name (or type 'done' to finish): ")
        if candidate_name.lower() == 'done':
            break
        add_candidate(candidate_name)

def register_voters():
    print("Register voters")
    while True:
        voter_id = input("Enter voter ID (or type 'done' to finish): ")
        if voter_id.lower() == 'done':
            break
        voter_address = create_voter_account(voter_id)
        authorize_voter_transact(voter_id)

def conduct_voting():
    print("Voting begins")
    candidates = list_candidates()  # Display all candidates
    while True:
        voter_id = input("Enter voter ID (or type 'done' to finish): ")
        if voter_id.lower() == 'done':
            break
        try:
            candidate_number = int(input("Enter the number of the candidate you want to vote for: "))
            if candidate_number < 1 or candidate_number > len(candidates):
                print("Invalid candidate number.")
                continue
            cast_vote_transact(voter_id, candidate_number - 1)  # Candidates are zero-indexed in the contract
        except ValueError:
            print("Invalid input. Please enter a valid number.")

def main():
    print("Election System CLI")
    while True:
        print("\nOptions:")
        print("1. Register Candidates")
        print("2. Register Voters")
        print("3. Start Voting")
        print("4. End Election and Show Results")
        print("5. Exit")
        option = input("Select an option: ")

        if option == "1":
            register_candidates()
        elif option == "2":
            register_voters()
        elif option == "3":
            conduct_voting()
        elif option == "4":
            list_candidates()
            end_election()
        elif option == "5":
            print("Exiting election system.")
            break
        else:
            print("Invalid option, please try again.")

if __name__ == "__main__":
    main()
