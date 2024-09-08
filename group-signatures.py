import rsa
import random
import hashlib

class VotingSystem:
    def __init__(self):
        # Initialize dictionaries to store group information, votes, and voter tokens
        self.groups = {}  # Stores group details:
        self.group_votes = {}  # Stores encrypted votes: {group_name: [(group_token, encrypted_vote)]}
        self.voter_tokens = {}  # Stores voter tokens to anonymize: {voter_id: group_token}

    # Admin class represents a group admin who can decrypt votes and verify group tokens
    class Admin:
        def __init__(self, name):
            # Generate RSA key pair (public and private keys) for this admin
            (self.public_key, self.private_key) = rsa.newkeys(512)
            self.name = name  # Name of the admin

        # Decrypt the vote using the admin's private key
        def decrypt_vote(self, encrypted_vote):
            try:
                # Decrypts the vote to reveal the candidate choice
                return rsa.decrypt(encrypted_vote, self.private_key).decode('utf-8')
            except:
                return "Decryption failed."

        # Simulated verification of group token to check if it is valid (not full cryptographic signature)
        def verify_group_token(self, token, public_key):
            # Hash the group token for verification
            hashed_token = hashlib.sha256(token.encode()).hexdigest()
            try:
                # Verify the hashed token (simulating group token verification)
                rsa.verify(hashed_token.encode(), public_key)
                return True
            except:
                return False

    # Create a new voting group (e.g., State A or State B)
    def create_group(self, group_name, admin_name):
        admin = self.Admin(admin_name)  # Create an admin for the group
        # Generate a new key pair for the group itself
        (group_public_key, group_private_key) = rsa.newkeys(512)
        # Store the group information: admin, voter set, and the group's key pair
        self.groups[group_name] = {
            "admin": admin, 
            "voters": set(),  # Empty set of voters initially
            "group_key": group_public_key,  # Public key for the group (could be used for token verification)
            "group_private_key": group_private_key  # Private key for signing tokens (not fully implemented here)
        }
        self.group_votes[group_name] = []  # Initialize an empty list to store votes
        print(f"Group '{group_name}' created with admin '{admin_name}'.")

    # Generate a random anonymous group token for voters to use when casting votes
    def generate_group_token(self):
        # Generate a 16-character long random token for anonymous voting
        return ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=16))

    # Add a voter to a specific group and assign them a group token
    def add_voter_to_group(self, group_name, voter_id):
        if group_name in self.groups:
            group_token = self.generate_group_token()  # Generate an anonymous token for the voter
            self.groups[group_name]["voters"].add(group_token)  # Add the token to the set of voters in the group
            self.voter_tokens[voter_id] = group_token  # Link the voter ID to the token (but admin won't know the link)
            print(f"Voter {voter_id} added to group '{group_name}' with token {group_token}.")
        else:
            print(f"Group '{group_name}' does not exist.")

    # Method for voters to cast a vote
    def cast_vote(self, voter_id, group_name, candidate):
        # Check if the group exists and the voter has a valid token
        if group_name in self.groups and voter_id in self.voter_tokens:
            group_token = self.voter_tokens[voter_id]  # Retrieve the voter's group token

            # Ensure the token belongs to the group (voter authorization)
            if group_token in self.groups[group_name]["voters"]:
                # Encrypt the vote (candidate choice) with the admin's public key
                encrypted_vote = rsa.encrypt(candidate.encode('utf-8'), self.groups[group_name]["admin"].public_key)

                # Store the encrypted vote along with the voter's anonymous token
                self.group_votes[group_name].append((group_token, encrypted_vote))
                print(f"Voter {voter_id} successfully cast a vote in group '{group_name}'.")
            else:
                print("Invalid group token.")  # Token mismatch (voter is not authorized)
        else:
            print(f"Voter {voter_id} is not authorized to vote in group '{group_name}'.")

    # Reveal the vote counts (admin function) without revealing who voted
    def reveal_vote_counts(self, group_name):
        if group_name in self.groups:
            print(f"\nRevealing vote counts for group '{group_name}'...")
            vote_counts = {}  # Dictionary to count votes for each candidate
            admin = self.groups[group_name]["admin"]  # Retrieve the admin for the group

            # Loop through all votes (each vote is encrypted and linked to a token)
            for group_token, encrypted_vote in self.group_votes[group_name]:
                decrypted_vote = admin.decrypt_vote(encrypted_vote)  # Admin decrypts the vote
                if decrypted_vote != "Decryption failed.":
                    # Count the votes for each candidate
                    if decrypted_vote in vote_counts:
                        vote_counts[decrypted_vote] += 1
                    else:
                        vote_counts[decrypted_vote] = 1
            
            # Display the vote counts for each candidate
            for candidate, count in vote_counts.items():
                print(f"{candidate}: {count} votes")
        else:
            print(f"Group '{group_name}' does not exist.")

    # Verify a specific vote using its group token (admin function)
    def verify_vote(self, group_name, group_token):
        if group_name in self.groups:
            # Check if the group token is valid and belongs to the group
            if group_token in self.groups[group_name]["voters"]:
                print(f"Vote from token {group_token} is valid.")
            else:
                print(f"Invalid token: {group_token}")
        else:
            print(f"Group '{group_name}' does not exist.")

    # Admin menu for managing votes and verifying tokens
    def admin_menu(self, admin_name):
        for group_name, group_info in self.groups.items():
            if group_info["admin"].name == admin_name:
                print(f"\n--- Admin Menu for group '{group_name}' ---")
                print("1. Reveal vote counts")
                print("2. Verify vote by group token")
                print("3. Exit")
                
                option = input("Select an option: ")
                
                if option == '1':
                    self.reveal_vote_counts(group_name)  # Admin can reveal total vote counts
                elif option == '2':
                    group_token = input("Enter group token to verify: ")
                    self.verify_vote(group_name, group_token)  # Admin can verify if a vote is from a valid token
                elif option == '3':
                    print("Exiting...")
                else:
                    print("Invalid option.")  # Invalid input

    # Voter menu for casting votes
    def voter_menu(self, voter_id):
        # Ensure the voter is registered (has a token)
        if voter_id in self.voter_tokens:
            group_name = input("Enter your group (e.g., state): ")
            candidate = input("Enter the candidate you want to vote for: ")
            self.cast_vote(voter_id, group_name, candidate)  # Voter casts their vote
        else:
            print(f"Voter ID {voter_id} not found.")  # Voter is not registered

    # Main menu to log in as either voter or admin
    def main_menu(self):
        while True:
            print("\n--- Main Menu ---")
            print("1. Log in as Voter")
            print("2. Log in as Group Administrator")
            print("3. Exit")
            
            option = input("Select an option: ")
            
            if option == '1':
                voter_id = input("Enter your Voter ID: ")
                self.voter_menu(voter_id)  # Voter menu
            elif option == '2':
                admin_name = input("Enter admin name: ")
                self.admin_menu(admin_name)  # Admin menu
            elif option == '3':
                print("Exiting...")  # Exit program
                break
            else:
                print("Invalid option.")  # Invalid input

# Example Usage
voting_system = VotingSystem()

# Create two groups (e.g., two states)
voting_system.create_group("State A", "Admin A")
voting_system.create_group("State B", "Admin B")

# Add voters to the groups
voting_system.add_voter_to_group("State A", "Voter1")
voting_system.add_voter_to_group("State A", "Voter2")
voting_system.add_voter_to_group("State B", "Voter3")

# Main menu
voting_system.main_menu()
