import rsa
import random
import hashlib

class VotingSystem:
    def __init__(self):
        # Initialize dictionaries to store group information, votes, and voter tokens
        self.groups = {}  # Stores group details
        self.group_votes = {}  # Stores votes: {group_name: [(group_token, vote)]}
        self.voter_tokens = {}  # Stores voter tokens to anonymize: {voter_id: group_token}
        self.voter_group = {}  # Tracks which group a voter is assigned to
        self.voter_casted_votes = {}  # Tracks whether a voter has voted
        self.signature_type = None  # To store signature type (group or ring)

    # Admin class for group signature (not used in ring signature)
    class Admin:
        def __init__(self, name):
            # Generate RSA key pair (public and private keys) for this admin
            (self.public_key, self.private_key) = rsa.newkeys(512)
            self.name = name  # Name of the admin

        # Decrypt the vote using the admin's private key
        def decrypt_vote(self, encrypted_vote):
            try:
                return rsa.decrypt(encrypted_vote, self.private_key).decode('utf-8')
            except:
                return "Decryption failed."

    # Create a new group for group signature
    def create_group_signature_group(self, group_name, admin_name=None):
        admin = self.Admin(admin_name)  # Create an admin for group signature
        (group_public_key, group_private_key) = rsa.newkeys(512)
        self.groups[group_name] = {
            "admin": admin, 
            "voters": set(),
            "group_key": group_public_key,
            "group_private_key": group_private_key
        }
        self.group_votes[group_name] = []
        print(f"Group '{group_name}' created with group signature by admin '{admin_name}'.")

    # Create a new group for ring signature
    def create_ring_signature_group(self, group_name):
        self.groups[group_name] = {
            "admin": None,  # No admin in ring signature
            "voters": set()
        }
        self.group_votes[group_name] = []
        print(f"Group '{group_name}' created with ring signature.")

    # Generate a random anonymous group token for voters
    def generate_group_token(self):
        return ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=16))

    # Add a voter to a group
    def add_voter_to_group(self, group_name, voter_id):
        if group_name in self.groups:
            group_token = self.generate_group_token()
            self.groups[group_name]["voters"].add(group_token)
            self.voter_tokens[voter_id] = group_token
            self.voter_group[voter_id] = group_name  # Assign the voter to the group
            self.voter_casted_votes[voter_id] = False  # Track whether this voter has voted
            print(f"Voter {voter_id} added to group '{group_name}'.")
        else:
            print(f"Group '{group_name}' does not exist.")

    # Method for voters to cast a vote
    def cast_vote(self, voter_id, candidate):
        if voter_id in self.voter_tokens and voter_id in self.voter_group:
            group_name = self.voter_group[voter_id]  # Get the group the voter belongs to

            # Check if the voter has already voted
            if self.voter_casted_votes[voter_id]:
                print(f"Voter {voter_id} has already cast their vote in group '{group_name}'. You cannot vote twice.")
                return

            group_token = self.voter_tokens[voter_id]

            if self.signature_type == 'group':
                if group_token in self.groups[group_name]["voters"]:
                    encrypted_vote = rsa.encrypt(candidate.encode('utf-8'), self.groups[group_name]["admin"].public_key)
                    self.group_votes[group_name].append((group_token, encrypted_vote))
                    print(f"Voter {voter_id} successfully cast a vote in group '{group_name}' using group signature.")
                else:
                    print("Invalid group token.")
            elif self.signature_type == 'ring':
                # For ring signature, the vote is hashed for anonymity
                hashed_vote = hashlib.sha256(candidate.encode('utf-8')).hexdigest()
                self.group_votes[group_name].append((None, hashed_vote))  # No token tracking for anonymity
                print(f"Voter {voter_id} successfully cast a vote in group '{group_name}' using ring signature.")
            
            # Mark the voter as having voted
            self.voter_casted_votes[voter_id] = True
        else:
            print(f"Voter ID {voter_id} is not authorized to vote.")

    # Reveal the vote counts (no admin required for ring signature)
    def reveal_vote_counts(self, group_name):
        if group_name in self.groups:
            print(f"\nRevealing vote counts for group '{group_name}'...")
            vote_counts = {}

            if self.signature_type == 'group':
                # In group signature, decrypt the votes using admin
                admin = self.groups[group_name]["admin"]
                for group_token, encrypted_vote in self.group_votes[group_name]:
                    decrypted_vote = admin.decrypt_vote(encrypted_vote)
                    if decrypted_vote != "Decryption failed.":
                        vote_counts[decrypted_vote] = vote_counts.get(decrypted_vote, 0) + 1
            elif self.signature_type == 'ring':
                # In ring signature, count hashed votes without decryption
                for _, hashed_vote in self.group_votes[group_name]:
                    vote_counts[hashed_vote] = vote_counts.get(hashed_vote, 0) + 1

            for candidate, count in vote_counts.items():
                print(f"{candidate}: {count} votes")
        else:
            print(f"Group '{group_name}' does not exist.")

    # Main menu to log in as either voter or admin
    def main_menu(self):
        print("\n--- Welcome to the Voting System ---")
        self.signature_type = input("Choose voting system type (group/ring): ").lower()
        
        if self.signature_type not in ['group', 'ring']:
            print("Invalid signature type. Defaulting to group signature.")
            self.signature_type = 'group'

        while True:
            print("\n--- Main Menu ---")
            print("1. Log in as Voter")
            if self.signature_type == 'group':
                print("2. Log in as Group Administrator")
            print("3. Exit")
            
            option = input("Select an option: ")
            
            if option == '1':
                voter_id = input("Enter your Voter name: ")
                self.voter_menu(voter_id)  # Voter menu
            elif option == '2' and self.signature_type == 'group':
                admin_name = input("Enter admin name (your name): ")
                self.admin_menu(admin_name)  # Admin menu
            elif option == '3':
                print("Exiting...")  # Exit program
                break
            else:
                print("Invalid option.")  # Invalid input

    # Voter menu for casting votes
    def voter_menu(self, voter_id):
        # Ensure the voter is registered (has a token)
        if voter_id not in self.voter_tokens:
            # If voter doesn't exist, create a new voter
            group_name = input(f"Enter the group you want to vote in: ")
            if group_name in self.groups:
                self.add_voter_to_group(group_name, voter_id)
            else:
                print(f"Group '{group_name}' does not exist.")
                return

        candidate = input(f"Enter the candidate you want to vote for in your group '{self.voter_group[voter_id]}': ")
        self.cast_vote(voter_id, candidate)  # Voter casts their vote

    # Admin menu for managing votes and verifying tokens (only available for group signature)
    def admin_menu(self, admin_name):
        # Admins can create groups
        group_name = input("Enter the name of the group to create: ")
        self.create_group_signature_group(group_name, admin_name)

        # Admin functionality after creating a group
        while True:
            print(f"\n--- Admin Menu for group '{group_name}' ---")
            print("1. Reveal vote counts")
            print("2. Exit")
                
            option = input("Select an option: ")
                
            if option == '1':
                self.reveal_vote_counts(group_name)  # Admin can reveal total vote counts
            elif option == '2':
                print("Exiting admin menu...")
                break
            else:
                print("Invalid option.")  # Invalid input

# Example Usage
voting_system = VotingSystem()

# Main menu
voting_system.main_menu()
