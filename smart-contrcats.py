from web3 import Web3
from solcx import compile_source

# Connect to Ganache
ganache_url = "http://127.0.0.1:7545"
web3 = Web3(Web3.HTTPProvider(ganache_url))

# Check if connected
if not web3.isConnected():
    raise Exception("Failed to connect to the Ethereum network")

# Set the default account for transactions
web3.eth.default_account = web3.eth.accounts[0]

# Solidity source code (from the previous smart contract)
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
        owner = msg.sender;
        electionName = _electionName;
    }

    function addCandidate(string memory _name) public ownerOnly {
        candidates.push(Candidate(candidates.length, _name, 0));
    }

    function authorizeVoter(address _voter) public ownerOnly {
        voters[_voter].authorized = true;
    }

    function vote(uint _candidateId) public {
        require(voters[msg.sender].authorized, "You are not authorized to vote");
        require(!voters[msg.sender].voted, "You have already voted");
        require(_candidateId < candidates.length, "Invalid candidate");

        voters[msg.sender].voted = true;
        voters[msg.sender].vote = _candidateId;

        candidates[_candidateId].voteCount += 1;
        totalVotes += 1;

        emit VoteCast(msg.sender, _candidateId);
    }

    function endElection() public ownerOnly view returns (string memory winnerName, uint winnerVoteCount) {
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
}
'''

# Compile Solidity contract
compiled_sol = compile_source(solidity_source_code)
contract_interface = compiled_sol['<stdin>:EVoting']

# Deploy the contract
EVoting = web3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])
tx_hash = EVoting.constructor("Sample Election").transact()
tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

# Contract instance after deployment
contract_address = tx_receipt.contractAddress
e_voting_contract = web3.eth.contract(address=contract_address, abi=contract_interface['abi'])

print(f"Contract deployed at: {contract_address}")

# Helper functions for the system
def add_candidate(name):
    tx_hash = e_voting_contract.functions.addCandidate(name).transact()
    web3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Candidate '{name}' added successfully.")

def authorize_voter(voter_address):
    tx_hash = e_voting_contract.functions.authorizeVoter(voter_address).transact()
    web3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Voter {voter_address} is now authorized.")

def cast_vote(voter_address, candidate_id):
    web3.eth.default_account = voter_address
    tx_hash = e_voting_contract.functions.vote(candidate_id).transact()
    web3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Vote cast by {voter_address} for candidate ID {candidate_id}.")

def end_election():
    winner_name, winner_vote_count = e_voting_contract.functions.endElection().call()
    print(f"The winner is {winner_name} with {winner_vote_count} votes.")

def get_total_candidates():
    return e_voting_contract.functions.getTotalCandidates().call()

def list_candidates():
    total_candidates = get_total_candidates()
    print("List of candidates:")
    for i in range(total_candidates):
        candidate = e_voting_contract.functions.candidates(i).call()
        print(f"ID: {candidate[0]}, Name: {candidate[1]}, Vote Count: {candidate[2]}")

# Example: Adding candidates
add_candidate("Alice")
add_candidate("Bob")

# Example: Authorizing voters
authorize_voter(web3.eth.accounts[1])
authorize_voter(web3.eth.accounts[2])

# Example: Voting
cast_vote(web3.eth.accounts[1], 0)  # Voter 1 votes for Alice
cast_vote(web3.eth.accounts[2], 1)  # Voter 2 votes for Bob

# List candidates and votes
list_candidates()


# Add a candidate
tx_hash = e_voting_contract.functions.addCandidate("Alice").transact()
web3.eth.wait_for_transaction_receipt(tx_hash)

# Authorize a voter
voter_address = web3.eth.accounts[1]  # Example voter
tx_hash = e_voting_contract.functions.authorizeVoter(voter_address).transact()
web3.eth.wait_for_transaction_receipt(tx_hash)

# Cast a vote
web3.eth.default_account = voter_address  # Set the default account to the voter
tx_hash = e_voting_contract.functions.vote(0).transact()  # Vote for candidate with


# End election and declare the winner
end_election()

