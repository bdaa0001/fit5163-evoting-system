from cryptography.hazmat.primitives.asymmetric import rsa, padding 
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from sympy import mod_inverse
import hashlib
import sys
import os
import random
import re
from core.blockchain_ganache import add_candidate,create_voter_account, create_voter_account, cast_vote_transact
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config


#----------------------------Voter Registration-with Storing Key Pair----------------------------------------

# Function to generate a random voter ID and hash it
def generate_voter_id():
    random_id = os.urandom(4).hex()  # Generates a random ID
    hashed_id = hashlib.sha256(random_id.encode()).hexdigest()  # Hashes the ID
    return hashed_id, random_id  # Return both hashed ID for storage and plain ID to show to voter

# Function to check if an email is already registered
def is_email_registered(voters, email):
    return any(voter['email'] == email for voter in voters.values())

def is_valid_email(email):
    
    email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    return re.match(email_regex, email) is not None

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
    """
    Registers a voter by generating an ID, creating a blockchain address, and storing their details.
    """
    name = input("Enter your name: ")

    while True:
        email = input("Enter your email address: ")
        if is_valid_email(email):
            break
        else:
            print("Invalid email format. Please enter a valid email address.")

    if is_email_registered(voters, email):
        print("Email already registered. One email can be used for one registration.")
        return

    # Generate both hashed and plain voter IDs
    hashed_voter_id, plain_voter_id = generate_voter_id()
    
    # Blockchain: Create voter account and authorize on the blockchain index 0-9
    ganache_index = random.randint(1, 9)
    voter_address = create_voter_account(ganache_index)

    if config.PRINT_BACKEND_LOGS:
        print(f"Block is mined for a voter and stored on this address")
        print(f"Voter '{plain_voter_id}' assigned to existing address: {voter_address}")

    # Generate RSA keys
    private_key, public_key = generate_rsa_keys()

    # Store voter info with blockchain address (hashed_voter_id used as key)
    voters[hashed_voter_id] = {
        'name': name,
        'email': email,
        'id': plain_voter_id,  # Plain voter ID for reference
        'private_key': private_key,
        'public_key': public_key,
        'ganache_index': ganache_index,
        'blockchain_address': voter_address  # Store their blockchain address
    }

    # Print plain voter ID for the voter to remember
    print(f"You have registered successfully with ID: {plain_voter_id}")
    print(f"IMPORTANT! Please keep this ID in a safe place, You will need this ID to cast a vote!")

    # After registration process, print the voters dictionary for debugging
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

