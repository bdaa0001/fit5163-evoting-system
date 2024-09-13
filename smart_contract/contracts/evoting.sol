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