from cryptography.hazmat.primitives.asymmetric import rsa, padding 
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from sympy import mod_inverse
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


#----------------------------Vote sign - Encryption/ Decryption---------------------------------------------------

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

#---------------------------Vote Casting with blind signature-------------------------------------------------------------------
# casting a vote
def cast_a_vote(voters, vote_records, candidate_number, candidate_name):
    vote_record = []
    voter_id = input("Enter your voter ID: ")
    hashed_voter_id = hashlib.sha256(voter_id.encode()).hexdigest()
    if hashed_voter_id not in voters:
        print("Voter not registered. Please register first.")
    else:
        voter = voters[hashed_voter_id]
        voter_address= voter['blockchain_address']
        # Cast a vote from voter for a candidate and create a block in Ganache to be added in e-voting contract
        cast_vote_transact(voter_address, candidate_number - 1)  # Candidates are zero-indexed in the contract

        authority_private_key=voter['private_key']
        authority_public_key = voter['public_key']
        # blind the vote
        # Blind the vote using authority's public key
        blinded_vote, blinding_factor = blind_vote(authority_public_key, candidate_number)
        # Send the blinded vote to the authority for signing
        signed_blinded_vote = sign_blinded_vote(authority_private_key, blinded_vote)
        # Unblind the signed vote using the blinding factor
        unblinded_signature = unblind_signature(signed_blinded_vote, blinding_factor, authority_public_key)

        # Add the unblinded signature and encrypted vote to the vote record list
        vote_record.append({
            'voter_id': hashed_voter_id,
            'candidate_number': candidate_number,
            'unblinded_signature': unblinded_signature,
        })
        # Verify the unblinded vote
        if verify_signature(authority_public_key, unblinded_signature,candidate_number):
            print("Vote verified successfully and remains anonymous!")
        else:
            print("Vote verification failed.")
        vote_records.append(vote_record)
        print(f"Your vote cast for candidate {candidate_number} successfully!")


#-- blinding signature functions for realise each vote is anonymous--------------------------------------------------------------------
# Blinding a vote or token (done by voter)
def blind_vote(public_key, vote_number):
    # Get the modulus (n) and exponent (e) from the public key
    n = public_key.public_numbers().n
    e = public_key.public_numbers().e
    # Generate a random blinding factor (r) between 1 and n-1
    blinding_factor = random.randint(1, n-1)
    # Compute blinded vote: v' = (v * r^e) % n
    blinded_vote = (vote_number * pow(blinding_factor, e, n)) % n
    return blinded_vote, blinding_factor

# Function to sign a blinded vote (done by election authority)
def sign_blinded_vote(private_key, blinded_vote):
    # Get the modulus (n) and exponent (d) from the private key
    n = private_key.private_numbers().public_numbers.n
    d = private_key.private_numbers().d
    # Compute the signature: σ' = (v')^d % n
    signature = pow(blinded_vote, d, n)
    
    return signature


# Function to unblind the signature (done by voter)
def unblind_signature(signature, blinding_factor, public_key):
    n = public_key.public_numbers().n
    # Compute the modular inverse of the blinding factor: r^(-1) % n
    blinding_factor_inv = mod_inverse(blinding_factor, n)
    # Compute the unblinded signature: σ = (σ' * r^(-1)) % n
    unblinded_signature = (signature * blinding_factor_inv) % n

    return unblinded_signature

# Function to verify the unblinded signature
def verify_signature(public_key, unblinded_signature,candidate_number):
    n = public_key.public_numbers().n
    e = public_key.public_numbers().e
    # Verify the signature: check if (σ^e) % n == v
    verified = pow(unblinded_signature, e, n) == candidate_number
    return verified

#---------------------------Vote Counting-------------------------------------------------------------------
def count_votes(vote_records, candidates):
    # Initialize the vote count for each candidate to 0
    vote_count = {name: 0 for name in candidates.values()}
    # Iterate over vote records and count votes
    for record in vote_records:
        candidate_number = record[0]['candidate_number'] # Assuming this holds the candidate number
        
        # Retrieve candidate name using the candidate number
        candidate_name = candidates.get(candidate_number)
        
        if candidate_name:
            vote_count[candidate_name] += 1

    return vote_count





# Main function to run the voting application
def main():
    # Define candidates
    candidates = {
        1: "Alice",
        2: "Bob",
        3: "Charlie",
        4: "David",
        5: "Eve"
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
            # Cast a vote
            candidate_number = int(input("Enter the candidate number you want to vote for: "))
            if candidate_number in candidates:
                candidate_name = candidates[candidate_number]
                cast_a_vote(voters, vote_records, candidate_number, candidate_name)
            else:
                print("Invalid candidate number. Please choose a valid candidate.")


        elif choice == '3':
            # Show total votes
            print("\n--- Tallying the votes ---")
            vote_count = count_votes(vote_records, candidates)
            for candidate, count in vote_count.items():
                print(f"{candidate}: {count} votes")

        elif choice == '4':
            print("Exiting the voting system. Goodbye!")
            break

        else:
            print("Invalid choice. Please enter a number between 1 and 4.")

if __name__ == "__main__":
    main()
