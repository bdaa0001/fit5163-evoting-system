from web3 import Web3
from solcx import compile_source, install_solc, set_solc_version
import config

# Install and set Solidity compiler version
install_solc('0.8.0')
set_solc_version('0.8.0')

# Connect to Ganache
ganache_url = "http://127.0.0.1:7545"
w3 = Web3(Web3.HTTPProvider(ganache_url))

# Verify connection to the Ethereum network
if not w3.is_connected():
    raise ConnectionError("Failed to connect to the Ethereum network.")
print("Successfully connected to the Ethereum network.")

# Set the default account to the first account available in Ganache
default_account = w3.eth.accounts[0]
w3.eth.default_account = default_account

# Retrieve and display the default account's balance in Ether
balance = w3.eth.get_balance(default_account)
print(f"Default account balance: {w3.from_wei(balance, 'ether')} ETH")

# Solidity source code for the e-voting contract
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
        require(msg.sender == owner, "Caller is not the owner.");
        _;
    }

    event VoteCast(address indexed voter, uint indexed candidateId);

    constructor(string memory _electionName) {
        require(bytes(_electionName).length > 0, "Election name cannot be empty.");
        owner = msg.sender;
        electionName = _electionName;
    }

    function addCandidate(string memory _name) public ownerOnly {
        require(bytes(_name).length > 0, "Candidate name cannot be empty.");
        candidates.push(Candidate(candidates.length, _name, 0));
    }

    function authorizeVoter(address _voter) public ownerOnly {
        require(_voter != address(0), "Invalid voter address.");
        voters[_voter].authorized = true;
    }

    function vote(uint _candidateId) public {
        Voter storage sender = voters[msg.sender];
        require(sender.authorized, "Not authorized to vote.");
        require(!sender.voted, "Already voted.");
        require(_candidateId < candidates.length, "Invalid candidate.");

        sender.voted = true;
        sender.vote = _candidateId;
        candidates[_candidateId].voteCount++;
        totalVotes++;

        emit VoteCast(msg.sender, _candidateId);
    }

    function endElection() public view ownerOnly returns (string memory winnerName, uint winnerVoteCount) {
        require(candidates.length > 0, "No candidates available.");
        uint winningVoteCount = 0;
        uint winningCandidateId;

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
}
'''

# Compile the Solidity contract
try:
    compiled_sol = compile_source(solidity_source_code, output_values=['abi', 'bin'])
    contract_interface = compiled_sol['<stdin>:EVoting']
    print("Contract compiled successfully.")
except Exception as e:
    print(f"Compilation failed: {e}")
    exit(1)

# Display the ABI and bytecode of the compiled contract
print(f"ABI: {contract_interface['abi']}")
print(f"Bytecode length: {len(contract_interface['bin'])} characters")

if not contract_interface['bin']:
    print("Compiled bytecode is empty. Check the contract code.")
    exit(1)

# Deploy the contract
EVoting = w3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])

try:
    tx_hash = EVoting.constructor("Sample Election").transact({
        'from': default_account,
        'gas': 3000000,
        'gasPrice': w3.to_wei('20', 'gwei')
    })
    print(f"Transaction hash: {tx_hash.hex()}")

    # Wait for the transaction receipt
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Contract deployed at address: {tx_receipt.contractAddress}")
except Exception as e:
    print(f"Deployment failed: {e}")
    exit(1)

# Create a contract instance
e_voting_contract = w3.eth.contract(address=tx_receipt.contractAddress, abi=contract_interface['abi'])

# Helper functions
def add_candidate(name):
    try:
        tx_hash = e_voting_contract.functions.addCandidate(name).transact({
            'from': default_account,
            'gas': 100000
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
        if(config.PRINT_BACKEND_LOGS): sprint(f"Candidate '{name}' added successfully.")
    except Exception as e:
        print(f"Failed to add candidate '{name}': {e}")

def authorize_voter(voter_address):
    try:
        tx_hash = e_voting_contract.functions.authorizeVoter(voter_address).transact({
            'from': default_account,
            'gas': 100000
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Voter {voter_address} is now authorized.")
    except Exception as e:
        print(f"Failed to authorize voter {voter_address}: {e}")

def cast_vote(voter_address, candidate_id):
    try:
        w3.eth.default_account = voter_address
        tx_hash = e_voting_contract.functions.vote(candidate_id).transact({
            'from': voter_address,
            'gas': 100000
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Vote cast by {voter_address} for candidate ID {candidate_id}.")
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

def get_total_candidates():
    try:
        return e_voting_contract.functions.getTotalCandidates().call()
    except Exception as e:
        print(f"Failed to get total candidates: {e}")
        return 0

def list_candidates():
    try:
        total_candidates = get_total_candidates()
        print("List of candidates:")
        for i in range(total_candidates):
            candidate = e_voting_contract.functions.candidates(i).call()
            print(f"ID: {candidate[0]}, Name: {candidate[1]}, Vote Count: {candidate[2]}")
    except Exception as e:
        print(f"Failed to list candidates: {e}")

# Example usage
add_candidate("Alice")
add_candidate("Bob")

authorize_voter(w3.eth.accounts[1])
authorize_voter(w3.eth.accounts[2])

cast_vote(w3.eth.accounts[1], 1)
cast_vote(w3.eth.accounts[2], 1)

list_candidates()
end_election()
