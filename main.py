import blockchain_ganache
import voter_authentication
import blinding_signature
import re


def add_candidates(candidates):
    print("Candidates:")
    for candidate_number, candidate_name in candidates.items():
        blockchain_ganache.add_candidate(candidate_name)
        print(f"{candidate_number}: {candidate_name}") 

def display_candidates(candidates):
    print("Candidates:")
    for candidate_number, candidate_name in candidates.items():
        print(f"{candidate_number}: {candidate_name}")

# CLI functions
def main():
    # Define candidates
    candidates = {
        1: "Alice",
        2: "Bob",
        3: "Charlie",
        4: "David",
        5: "Eve"
    }
    
    add_candidates(candidates)

    # Voter data storage
    voters = {}  # Store registered voters
    vote_records = []  # Store valid vote records
    voted_voters = set()  # Store voters who have already voted to prevent double voting

    while True:
        print("\n--- Voting Menu ---")
        print("1. Register voter")
        print("2. Cast a vote")
        print("3. Show total votes")
        print("4. Exit")

        choice = input("Enter your choice (1-4): ")

        if choice == '1':
            try:
                # Register a voter
                voter_id = voter_authentication.register_voter(voters)
            except Exception as e:
                print(f"Error registering voter: {e}")

        elif choice == '2':
            try:
                voter_id = input("Enter your voter ID: ")

                # Check if the voter has already voted
                if voter_id in voted_voters:
                    print("You have already cast your vote. You cannot vote again.")
                    continue

                # Display candidates
                display_candidates(candidates)

                # Cast a vote
                candidate_number = int(input("Enter the candidate number you want to vote for: "))
                if candidate_number in candidates:
                    confirmation = input(f"Are you sure you want to vote for {candidates[candidate_number]}? (yes/no): ").lower()
                    if confirmation == "yes":
                        candidate_name = candidates.get(candidate_number, "Invalid candidate number")
                        blinding_signature.cast_a_vote(voters, vote_records, candidate_number, candidate_name)
                    else:
                        print("Vote cancelled.")
                else:
                    print("Invalid candidate number. Please enter a valid candidate number.")
            except ValueError:
                print("Invalid input. Please enter a valid candidate number.")
            except Exception as e:
                print(f"Error casting vote: {e}")

        elif choice == '3':
            try:
                # Show total votes
                print("\n--- Tallying the votes ---")
                vote_count = blinding_signature.count_votes(vote_records, candidates)
                for candidate, count in vote_count.items():
                    print(f"{candidate}: {count} votes")
            except Exception as e:
                print(f"Error tallying votes: {e}")

        elif choice == '4':
            print("Exiting the voting system. Goodbye!")
            break

        else:
            print("Invalid choice. Please enter a number between 1 and 4.")


if __name__ == "__main__":
    main()
