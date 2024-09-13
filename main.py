import blockchain_ganache
import voter_authentication
import blinding_signature
import re

# Function to add candidates to the blockchain
def add_candidates(candidates):
    """
    Add each candidate to the blockchain and display the candidate list.
    
    Args:
    candidates (dict): A dictionary of candidate numbers and names.
    """
    print("Candidates:")
    for candidate_number, candidate_name in candidates.items():
        blockchain_ganache.add_candidate(candidate_name)
        print(f"{candidate_number}: {candidate_name}")

# Function to display candidates
def display_candidates(candidates):
    """
    Display the list of candidates in the election.
    
    Args:
    candidates (dict): A dictionary of candidate numbers and names.
    """
    print("Candidates:")
    for candidate_number, candidate_name in candidates.items():
        print(f"{candidate_number}: {candidate_name}")

# Main CLI function
def main():
    """
    Main function to run the voting system. Provides options to register voters, cast votes,
    show vote totals, and exit the system.
    """
    
    # Define candidates with their assigned numbers
    candidates = {
        1: "Alice",
        2: "Bob",
        3: "Charlie",
        4: "David",
        5: "Eve"
    }
    
    # Add candidates to the blockchain
    add_candidates(candidates)

    # Voter data storage
    voters = {}  # Dictionary to store registered voters
    vote_records = []  # List to store valid vote records
    voted_voters = set()  # Set to store voters who have already voted, preventing double voting

    while True:
        # Display menu options for the voting system
        print("\n--- Voting Menu ---")
        print("1. Register voter")
        print("2. Cast a vote")
        print("3. Show total votes")
        print("4. Exit")

        # User input to select an option from the menu
        choice = input("Enter your choice (1-4): ")

        if choice == '1':
            # Register a voter
            try:
                voter_id = voter_authentication.register_voter(voters)
            except Exception as e:
                print(f"Error registering voter: {e}")

        elif choice == '2':
            # Cast a vote
            try:
                voter_id = input("Enter your voter ID: ")

                # Check if the voter has already voted
                if voter_id in voted_voters:
                    print("You have already cast your vote. You cannot vote again.")
                    continue

                # Display candidates for voting
                display_candidates(candidates)

                # Collect and validate candidate selection
                candidate_number = int(input("Enter the candidate number you want to vote for: "))
                if candidate_number in candidates:
                    confirmation = input(f"Are you sure you want to vote for {candidates[candidate_number]}? (yes/no): ").lower()
                    if confirmation == "yes":
                        candidate_name = candidates.get(candidate_number, "Invalid candidate number")
                        # Cast a valid vote using blinding_signature module
                        blinding_signature.cast_a_vote(voters, vote_records, candidate_number, candidate_name)
                        voted_voters.add(voter_id)  # Mark voter as having voted
                    else:
                        print("Vote cancelled.")
                else:
                    print("Invalid candidate number. Please enter a valid candidate number.")
            except ValueError:
                print("Invalid input. Please enter a valid candidate number.")
            except Exception as e:
                print(f"Error casting vote: {e}")

        elif choice == '3':
            # Show total votes for each candidate
            try:
                print("\n--- Tallying the votes ---")
                vote_count = blinding_signature.count_votes(vote_records, candidates)
                for candidate, count in vote_count.items():
                    print(f"{candidate}: {count} votes")
            except Exception as e:
                print(f"Error tallying votes: {e}")

        elif choice == '4':
            # Exit the voting system
            print("Exiting the voting system. Goodbye!")
            break

        else:
            # Invalid menu selection
            print("Invalid choice. Please enter a number between 1 and 4.")

# Run the main function when the script is executed
if __name__ == "__main__":
    main()
