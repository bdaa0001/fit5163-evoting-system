import blockchain_ganache
import voter_authentication
import blinding_signature

# CLI functions
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
            # Cast a vote
            candidate_number = int(input("Enter the candidate number you want to vote for: "))
            if candidate_number in candidates:
                candidate_name = candidates[candidate_number]
                blinding_signature.cast_a_vote(voters, vote_records, candidate_number, candidate_name)
            else:
                print("Invalid candidate number. Please choose a valid candidate.")


        elif choice == '3':
            # Show total votes
            print("\n--- Tallying the votes ---")
            vote_count = blinding_signature.count_votes(vote_records, candidates)
            for candidate, count in vote_count.items():
                print(f"{candidate}: {count} votes")

        elif choice == '4':
            print("Exiting the voting system. Goodbye!")
            break

        else:
            print("Invalid choice. Please enter a number between 1 and 4.")

if __name__ == "__main__":
    main()