import hashlib
import json
from time import time

class Blockchain:
    def __init__(self):
        self.chain = []  # List to store the chain of blocks
        self.current_votes = []  # List to store the current votes

        # Create the genesis block (the first block in the blockchain)
        self.create_block(previous_hash='1')

    def create_block(self, previous_hash):
        # Create a new block and add it to the chain
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'votes': self.current_votes,
            'previous_hash': previous_hash,
        }

        # Calculate the hash of the new block
        block['hash'] = self.hash(block)

        # Reset the list of current votes and add the new block to the chain
        self.current_votes = []
        self.chain.append(block)
        return block

    @staticmethod
    def hash(block):
        # Create a SHA-256 hash of the block
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def add_vote(self, voter_id, candidate):
        # Add a new vote to the list of current votes
        vote = {
            'voter_id': voter_id,
            'candidate': candidate,
        }
        self.current_votes.append(vote)
        return self.last_block['index'] + 1

    @property
    def last_block(self):
        # Return the last block in the chain
        return self.chain[-1]

    def is_chain_valid(self):
        # Check if the blockchain is valid by ensuring the hashes match
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # Check if the hash of the current block is correct
            if current_block['hash'] != self.hash(current_block):
                return False

            # Check if the current block points to the correct previous block
            if current_block['previous_hash'] != previous_block['hash']:
                return False

        return True

    def count_votes(self):
        # Count votes from all blocks in the chain
        vote_count = {}
        for block in self.chain:
            for vote in block['votes']:
                candidate = vote['candidate']
                if candidate not in vote_count:
                    vote_count[candidate] = 0
                vote_count[candidate] += 1
        return vote_count


# Main function to run the voting application
def main():
    blockchain = Blockchain()

    # Define candidates
    candidates = ["Alice", "Bob", "Charlie"]

    print("Welcome to the Blockchain Voting System!")
    print("Candidates:", ", ".join(candidates))

    while True:
        print("\n--- Voting Menu ---")
        print("1. Cast a vote")
        print("2. Show total votes")
        print("3. Validate blockchain integrity")
        print("4. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            voter_id = input("Enter your voter ID: ")
            candidate = input("Enter your vote (choose a candidate's name): ")

            if candidate not in candidates:
                print("Invalid vote. Please choose a valid candidate.")
            else:
                blockchain.add_vote(voter_id, candidate)
                previous_hash = blockchain.last_block['hash']
                blockchain.create_block(previous_hash)
                print(f"Vote cast for {candidate} successfully!")

        elif choice == '2':
            vote_count = blockchain.count_votes()
            print("\n--- Total Votes ---")
            for candidate, count in vote_count.items():
                print(f"{candidate}: {count} votes")

        elif choice == '3':
            if blockchain.is_chain_valid():
                print("Blockchain is valid. All votes are secure.")
            else:
                print("Blockchain integrity check failed. There may be tampering.")

        elif choice == '4':
            print("Exiting the voting system. Goodbye!")
            break

        else:
            print("Invalid choice. Please enter a number between 1 and 4.")

if __name__ == "__main__":
    main()
