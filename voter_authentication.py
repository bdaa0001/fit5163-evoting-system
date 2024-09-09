from cryptography.hazmat.primitives.asymmetric import rsa, padding 
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import json
import hashlib
import os
import random
from blockchain_ganache import add_candidate,create_voter_account, create_voter_account, cast_vote_transact

#----------------------------Voter Registration-with Storing Key Pair----------------------------------------

# Function to generate a random voter ID and hash it
def generate_voter_id():
    random_id = os.urandom(4).hex()  # Generates a random ID
    hashed_id = hashlib.sha256(random_id.encode()).hexdigest()  # Hashes the ID
    return hashed_id, random_id  # Return both hashed ID for storage and plain ID to show to voter

# Function to check if an email is already registered
def is_email_registered(voters, email):
    return any(voter['email'] == email for voter in voters.values())


# Function to generate RSA key pair
def generate_rsa_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key


# Function to register a voter with blockchain and store their keys and info
def register_voter(voters):
    name = input("Enter your name: ")
    email = input("Enter your email: ")

    if is_email_registered(voters, email):
        print("Email already registered. One email can be used for one registration.")
        return

    hashed_voter_id, plain_voter_id = generate_voter_id()
    
    # Blockchain: Create voter account and authorize on the blockchain index 0-9
    ganache_index= random.randint(0, 9)
    voter_address=create_voter_account(ganache_index)
    print(f"Voter '{plain_voter_id}' assigned to existing address: {voter_address}")

    # Generate RSA keys
    private_key, public_key = generate_rsa_keys()

    # Store voter info with blockchain address
    voters[hashed_voter_id] = {
        'name': name,
        'email': email,
        'id': plain_voter_id,
        'private_key': private_key,
        'public_key': public_key,
        'ganache_index': ganache_index,
        'blockchain_address': voter_address  # Store their blockchain address
    }
    print(f"Voter registered successfully with ID: {plain_voter_id}")

# def register_voter(voters):
#     name = input("Enter your name: ")
#     email = input("Enter your email: ")

#     if is_email_registered(voters, email):
#         print("Email already registered. One email can be used for one registration.")
#         return

#     hashed_voter_id, plain_voter_id = generate_voter_id()
#     private_key, public_key = generate_rsa_keys()
#     # Serialize the keys before storing
#     serialized_private_key = serialize_private_key(private_key)
#     serialized_public_key = serialize_public_key(public_key)

#     voters[hashed_voter_id] = {
#         'name': name,
#         'email': email,
#         'id': plain_voter_id,
#         'private_key': serialized_private_key,
#         'public_key': serialized_public_key
#     }
#     print(f"You registered successfully with Voting_ID: {plain_voter_id}")

# Function to serialize private key
def serialize_private_key(private_key):
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

# Function to serialize public key
def serialize_public_key(public_key):
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )


#----------------------------Vote Encryption/ Decryption---------------------------------------------------

# Function to sign a vote using private key
def sign_vote(private_key, vote):
    signature = private_key.sign(
        vote.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature

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

# Function to deserialize a private key
def deserialize_private_key(serialized_private_key):
    return serialization.load_pem_private_key(
        serialized_private_key,
        password=None,
        backend=default_backend()
    )

# Function to deserialize a public key
def deserialize_public_key(serialized_public_key):
    return serialization.load_pem_public_key(
        serialized_public_key,
        backend=default_backend()
    )
# casting a vote
def cast_vote_and_deserialize_keyPairs(voters, vote_records, candidate_number, candidate_name):
    voter_id = input("Enter your voter ID: ")
    hashed_voter_id = hashlib.sha256(voter_id.encode()).hexdigest()
    if hashed_voter_id not in voters:
        print("Voter not registered. Please register first.")
    else:
        voter = voters[hashed_voter_id]
        voter_address= voter['blockchain_address']
        # Cast a vote from voter for a candidate and create a block in Ganache to be added in e-voting contract
        cast_vote_transact(voter_address, candidate_number - 1)  # Candidates are zero-indexed in the contract
        # Deserialize the private key for signing
        private_key=voter['private_key']
        # Deserialize the public key for encryption
        public_key = voter['public_key']
        # Sign and encrypt the vote with private key
        signature = sign_vote(private_key, candidate_name)
        # Encrypt the vote with public key
        encrypted_vote = encrypt_vote(public_key, candidate_name)

        vote_records.append({
            'voter_id': hashed_voter_id,
            'encrypted_vote': encrypted_vote,
            'stored_private_key': private_key,
            'stored': public_key,
            'signature': signature
        })
        print(f"Vote cast for candidate {candidate_number} successfully!")


#--Add blinding function for preventing double voting--------------------------------------------------------------------
# Blinding a vote or token (done by voter)
def blind_vote(public_key, vote):
    blinding_factor = os.urandom(16)
    blind_vote = public_key.encrypt(
        vote.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return blind_vote, blinding_factor

# Signing a blinded vote (done by election authority)
def sign_blinded_vote(private_key, blinded_vote):
    signature = private_key.sign(
        blinded_vote,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature

# Unblinding the signature
def unblind_signature(public_key, signature, blinding_factor):
    # For simplicity, assuming unblinding is handled outside for now (pseudo code)
    return signature

# Verify the unblinded signature when the vote is cast
def verify_signature(public_key, signature, original_vote):
    try:
        public_key.verify(
            signature,
            original_vote.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False

#-------------------------------------------------------------------------
# Function to count votes
def count_votes(vote_records):
    vote_count = {}
    for record in vote_records:
        candidate = record['vote_candidate']
        if candidate not in vote_count:
            vote_count[candidate] = 0
        vote_count[candidate] += 1
    return vote_count




# Main function to run the voting application
def main():
    # Define candidates
    candidates = {
        1: "Alice",
        2: "Bob",
        3: "Charlie"
    }
    

    print("Welcome to the RSA Secure Voting System!")
    print("Candidates:")
    for candidate_number, candidate_name in candidates.items():
        add_candidate(candidate_name)
        print(f"{candidate_number}: {candidate_name}")

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
            register_voter(voters)

        elif choice == '2':
            candidate_number = int(input("Enter the candidate number: "))
            candidate_name = candidates[candidate_number]
            print(f"Voting for candidate: {candidate_name}")
            cast_vote_and_deserialize_keyPairs(voters, vote_records, candidate_number,candidate_name)

        elif choice == '3':
            print("\nDecrypting and counting votes...")
            for record in vote_records:
                voter_id = record['voter_id']
                private_key = record['stored_private_key']
                encrypted_vote = record['encrypted_vote']
                decrypted_vote = decrypt_vote(private_key, encrypted_vote)
                record['vote_candidate'] = decrypted_vote

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
