import hashlib
import os

# Function to hash a voter ID
def hash_voter_id(voter_id):
    return hashlib.sha256(voter_id.encode()).hexdigest()

# Function to test the hashed voter ID
def test_hashed_voter_id():
    random_id = os.urandom(4).hex()
    print(f"Random voter ID: {random_id}")
    hashed_voter_id = hash_voter_id(random_id)

    print(f"Computed hashed voter ID: {hashed_voter_id}")

    comfirm_id = input("Enter the comfirm voter ID: ")
    hashed_comfirm_id = hash_voter_id(comfirm_id)
    expected_hashed_voter_id = input("Enter the expected hashed voter ID (or press Enter to skip): ")

    if expected_hashed_voter_id:
        if hashed_comfirm_id == expected_hashed_voter_id:
            print("Success! The hashed voter ID matches the expected value.")
        else:
            print("Error: The hashed voter ID does not match the expected value.")
    else:
        print("No expected hashed voter ID provided, only showing computed hash.")

# Run the test function
if __name__ == "__main__":
    test_hashed_voter_id()
