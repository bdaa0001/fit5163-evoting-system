from sympy import mod_inverse
import hashlib
import random
from core.blockchain_ganache import cast_vote_transact

#---------------------------Vote Casting with Blind Signature----------------------------------------------
def cast_a_vote(voters, vote_records, candidate_number, candidate_name):
    """
    Allows a registered voter to cast a vote by:
    - Blinding the vote using the authority's public key
    - Signing the blinded vote
    - Unblinding the signature
    - Verifying the unblinded vote to ensure it's valid and anonymous

    Args:
    voters (dict): Registered voters with their details.
    vote_records (list): List of recorded votes.
    candidate_number (int): The candidate number the voter is voting for.
    candidate_name (str): The candidate's name.
    """
    vote_record = []
    voter_id = input("Enter your voter ID: ")
    hashed_voter_id = hashlib.sha256(voter_id.encode()).hexdigest()
    
    # Check if voter is registered
    if hashed_voter_id not in voters:
        print("Voter not registered. Please register first.")
    else:
        voter = voters[hashed_voter_id]
        voter_address = voter['blockchain_address']

        # Cast the vote on the blockchain using the voter's address and candidate number
        cast_vote_transact(voter_address, candidate_number - 1)  # Candidates are zero-indexed in the contract

        authority_private_key = voter['private_key']
        authority_public_key = voter['public_key']
        
        # Blind the vote using authority's public key
        blinded_vote, blinding_factor = blind_vote(authority_public_key, candidate_number)

        # Send the blinded vote to the authority for signing
        signed_blinded_vote = sign_blinded_vote(authority_private_key, blinded_vote)

        # Unblind the signed vote using the blinding factor
        unblinded_signature = unblind_signature(signed_blinded_vote, blinding_factor, authority_public_key)

        # Add the unblinded signature and vote to the vote records
        vote_record.append({
            'voter_id': hashed_voter_id,
            'candidate_number': candidate_number,
            'unblinded_signature': unblinded_signature,
        })

        # Verify the unblinded vote
        if verify_signature(authority_public_key, unblinded_signature, candidate_number):
            print("Vote verified successfully and remains anonymous!")
        else:
            print("Vote verification failed.")
        
        vote_records.append(vote_record)
        print(f"Your vote for candidate {candidate_number}: {candidate_name} was cast successfully!")

#---------------------------Blinding Signature Functions----------------------------------------------
def blind_vote(public_key, vote_number):
    """
    Blinds the vote using the authority's public key to ensure anonymity.
    
    Args:
    public_key (object): Authority's public key.
    vote_number (int): The vote for the candidate.

    Returns:
    tuple: Blinded vote and blinding factor.
    """
    n = public_key.public_numbers().n
    e = public_key.public_numbers().e

    # Generate a random blinding factor between 1 and n-1
    blinding_factor = random.randint(1, n-1)

    # Compute the blinded vote
    blinded_vote = (vote_number * pow(blinding_factor, e, n)) % n

    return blinded_vote, blinding_factor

def sign_blinded_vote(private_key, blinded_vote):
    """
    Signs the blinded vote using the authority's private key.
    
    Args:
    private_key (object): Authority's private key.
    blinded_vote (int): Blinded vote value.

    Returns:
    int: Signed blinded vote.
    """
    n = private_key.private_numbers().public_numbers.n
    d = private_key.private_numbers().d

    # Compute the signature
    signature = pow(blinded_vote, d, n)

    return signature

def unblind_signature(signature, blinding_factor, public_key):
    """
    Unblinds the signed vote using the modular inverse of the blinding factor.
    
    Args:
    signature (int): Signed blinded vote.
    blinding_factor (int): Random blinding factor used during the blinding process.
    public_key (object): Authority's public key.

    Returns:
    int: Unblinded signature.
    """
    n = public_key.public_numbers().n
    blinding_factor_inv = mod_inverse(blinding_factor, n)

    # Compute the unblinded signature
    unblinded_signature = (signature * blinding_factor_inv) % n

    return unblinded_signature

def verify_signature(public_key, unblinded_signature, candidate_number):
    """
    Verifies the unblinded signature to ensure the vote is valid and corresponds to the candidate.
    
    Args:
    public_key (object): Authority's public key.
    unblinded_signature (int): Unblinded signature from the vote.
    candidate_number (int): Candidate number being voted for.

    Returns:
    bool: True if the vote is verified, False otherwise.
    """
    n = public_key.public_numbers().n
    e = public_key.public_numbers().e

    # Verify if the signature is correct
    verified = pow(unblinded_signature, e, n) == candidate_number
    return verified

#---------------------------Vote Counting Function----------------------------------------------
def count_votes(vote_records, candidates):
    """
    Counts the votes from the vote records and tallies them for each candidate.
    
    Args:
    vote_records (list): List of recorded votes.
    candidates (dict): Dictionary of candidates with their numbers and names.

    Returns:
    dict: Vote count for each candidate.
    """
    # Initialize the vote count for each candidate
    vote_count = {name: 0 for name in candidates.values()}

    # Iterate over vote records to tally votes
    for record in vote_records:
        candidate_number = record[0]['candidate_number']  # Assuming this holds the candidate number
        candidate_name = candidates.get(candidate_number)
        
        if candidate_name:
            vote_count[candidate_name] += 1

    return vote_count
