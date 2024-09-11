# Description: This file contains the functions for blinding a vote, signing a blinded vote, unblinding the signature, and verifying the unblinded signature.
from sympy import mod_inverse
import hashlib
import random
from blockchain_ganache import cast_vote_transact
from voter_authentication import generate_rsa_keys
#---------------------------create election authority-------------------------------------------------------------------
def create_election_authority():
    authority_private_key, authority_public_key = generate_rsa_keys()
    return authority_private_key, authority_public_key

#---------------------------Vote Casting with blind signature-------------------------------------------------------------------
# casting a vote
def cast_a_vote(voters, candidate_number, vote_records):
    vote_record = {}
    voter_id = input("Enter your voter ID: ")
    hashed_voter_id = hashlib.sha256(voter_id.encode()).hexdigest()
    if hashed_voter_id not in voters:
        print("Voter not registered. Please register first.")
    else:
        voter = voters[hashed_voter_id]
        voter_address= voter['blockchain_address']
        # Cast a vote from voter for a candidate and create a block in Ganache to be added in e-voting contract
        double_voting_check=cast_vote_transact(voter_address, candidate_number - 1)  # Candidates are zero-indexed in the contract
        if double_voting_check==False:
            print("You have already cast your vote!")
            return
        else:
            # Generate RSA keys for the election authority, and get voter's private and public keys
            authority_private_key, authority_public_key = create_election_authority()
            # voter_private_key=voter['private_key']
            # voter_public_key = voter['public_key']
            #---------------------------------------------------- blind the vote
            # voter Blind the vote using authority's public key
            blinded_vote, blinding_factor = blind_vote(authority_public_key, candidate_number)
            # Send the blinded vote to the authority for signing
            signed_blinded_vote = sign_blinded_vote(authority_private_key, blinded_vote)
            # voter Unblind the signed vote using the blinding factor
            voter_unblinded_signature = unblind_signature(signed_blinded_vote, blinding_factor, authority_public_key)

            # Add the unblinded signature and encrypted vote to the voter record dictionary and store it
            vote_record[voter_id]={
                'candidate_number': candidate_number,
                'unblinded_signature': voter_unblinded_signature,
            }
            print(f"Your vote cast for candidate {candidate_number} successfully!")
            verify_signature(authority_public_key, voter_unblinded_signature, candidate_number,vote_records)



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
def verify_signature(authority_public_key, unblinded_signature, candidate_number,vote_records):
    n = authority_public_key.public_numbers().n
    e = authority_public_key.public_numbers().e
    # Verify the signature: check if (σ^e) % n == v
    verified = pow(unblinded_signature, e, n) == candidate_number
    # Verify the unblinded vote
    if verified:
        print("Vote verified successfully and remains anonymous!")
        vote_records.append(candidate_number)
        print(vote_records)
    else:
        print("Vote verification failed.")

#---------------------------Vote Counting-------------------------------------------------------------------
def count_votes(vote_records, candidates):
    # Initialize the vote count for each candidate to 0
    vote_count = {name: 0 for name in candidates.values()}
    # Iterate over vote records and count votes
    for count_candidate_number in vote_records:     
        # Retrieve candidate name using the candidate number
        candidate_name = candidates.get(count_candidate_number)
        
        if candidate_name:
            vote_count[candidate_name] += 1

    return vote_count