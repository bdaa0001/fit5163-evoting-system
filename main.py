import blockchain_ganache
import voter_authentication

# CLI functions
def register_candidates():
    print("Register candidates")
    while True:
        candidate_name = input("Enter candidate name (or type 'done' to finish): ")
        if candidate_name.lower() == 'done':
            break
        blockchain_ganache.add_candidate(candidate_name)

def register_voters(voters):
    print("Register voters")
    while True:
        voter_id = input("Enter voter ID (or type 'done' to finish): ")
        if voter_id.lower() == 'done':
            break
        voter_authentication.register_voter(voters)

def conduct_voting(voters, vote_records):
    print("Voting begins")
    candidates = blockchain_ganache.list_candidates()  # Display all candidates
    while True:
        voter_id = input("Enter voter ID (or type 'done' to finish): ")
        if voter_id.lower() == 'done':
            break
        try:
            candidate_number = int(input("Enter the number of the candidate you want to vote for: "))
            if candidate_number < 1 or candidate_number > len(candidates):
                print("Invalid candidate number.")
                continue
            
            voter_authentication.cast_vote_and_deserialize_keyPairs(voters, vote_records, candidate_number)  # Candidates are zero-indexed in the contract


        except ValueError:
            print("Invalid input. Please enter a valid number.")




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
        blockchain_ganache.add_candidate(candidate_name)
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
            voter_authentication.register_voter(voters)

        elif choice == '2':
            candidate_number = int(input("Enter the candidate number: "))
            candidate_name = candidates[candidate_number]
            print(f"Voting for candidate: {candidate_name}")
            voter_authentication.cast_vote_and_deserialize_keyPairs(voters, vote_records, candidate_number,candidate_name)

        elif choice == '3':
            print("\nDecrypting and counting votes...")
            for record in vote_records:
                voter_id = record['voter_id']
                private_key = record['stored_private_key']
                encrypted_vote = record['encrypted_vote']
                decrypted_vote = decrypt_vote(private_key, encrypted_vote)
                record['vote_candidate'] = decrypted_vote

            vote_count = voter_authentication.count_votes(vote_records)
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