from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
import json

# Function to generate RSA key pair
def generate_rsa_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key

# Function to encrypt a vote using public key
def encrypt_vote(public_key, vote):
    encrypted_vote = public_key.encrypt(
        vote.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted_vote

# Function to decrypt a vote using private key
def decrypt_vote(private_key, encrypted_vote):
    decrypted_vote = private_key.decrypt(
        encrypted_vote,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return decrypted_vote.decode()

# Function to count votes
def count_votes(vote_records):
    vote_count = {}
    for record in vote_records:
        candidate = record['candidate']
        if candidate not in vote_count:
            vote_count[candidate] = 0
        vote_count[candidate] += 1
    return vote_count

# Main function to run the voting application
def main():
    # Define candidates
    candidates = ["Alice", "Bob", "Charlie"]

    print("Welcome to the RSA Secure Voting System!")
    print("Candidates:", ", ".join(candidates))

    # Voter data storage
    voters = {}
    vote_records = []

    while True:
        print("\n--- Voting Menu ---")
        print("1. Register voter")
        print("2. Cast a vote")
        print("3. Show total votes")
        print("4. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            voter_id = input("Enter new voter ID: ")
            if voter_id in voters:
                print("Voter already registered.")
            else:
                private_key, public_key = generate_rsa_keys()
                voters[voter_id] = {'private_key': private_key, 'public_key': public_key}
                print(f"Voter {voter_id} registered successfully with RSA keys.")

        elif choice == '2':
            voter_id = input("Enter your voter ID: ")
            if voter_id not in voters:
                print("Voter not registered. Please register first.")
            else:
                candidate = input("Enter your vote (choose a candidate's name): ")
                if candidate not in candidates:
                    print("Invalid vote. Please choose a valid candidate.")
                else:
                    public_key = voters[voter_id]['public_key']
                    encrypted_vote = encrypt_vote(public_key, candidate)
                    vote_records.append({'voter_id': voter_id, 'encrypted_vote': encrypted_vote})
                    print(f"Vote cast for {candidate} successfully!")

        elif choice == '3':
            print("\nDecrypting and counting votes...")
            for record in vote_records:
                voter_id = record['voter_id']
                private_key = voters[voter_id]['private_key']
                encrypted_vote = record['encrypted_vote']
                decrypted_vote = decrypt_vote(private_key, encrypted_vote)
                record['candidate'] = decrypted_vote

            vote_count = count_votes(vote_records)
            print("\n--- Total Votes ---")
            for candidate, count in vote_count.items():
                print(f"{candidate}: {count} votes")

        elif choice == '4':
            print("Exiting the voting system. Goodbye!")
            break

        else:
            print("Invalid choice. Please enter a number between 1 and 4.")

if __name__ == "__main__":
    main()
