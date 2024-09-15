import core.blockchain_ganache as blockchain_ganache
import auth.voter_authentication as voter_authentication
import core.blinding_signature as blinding_signature
import config
import hashlib
import re

# Function to select log type
def select_log_type():
    """
    Outputs console messages differently based on the intended audience:
    - Back-end (developer) output: detailed messages for developers' debugging and monitoring purposes.
    - Front-end (user) output: clear and concise messages meant for user interaction.

    Parameters:
    message (str): The message to be output.
    is_backend (bool): Set to True for developer-facing messages (default).
                       Set to False for user-facing messages.

    Behavior:
    - For back-end (developer) output, more technical and detailed information is provided for troubleshooting.
    - For front-end (user) output, the message is simplified for user understanding without technical jargon.
    """
    while True:
        log_choice = input("Do you want to print back-end logs (Yes/Y / [No])? : ").lower()
        if log_choice in ['yes', 'y']:
            config.PRINT_BACKEND_LOGS = True
            print("Back-end logs will be printed.")
            break
        elif log_choice == '' or log_choice not in ['yes', 'y']:
            config.PRINT_BACKEND_LOGS = False
            print("Only Front-end logs will be printed.")
            break

# Function to add candidates to the blockchain
def add_candidates(candidates):
    """
    Add each candidate to the blockchain and display the candidate list.
    
    Args:
    candidates (dict): A dictionary of candidate numbers and names.
    """
    print("Voting candidates:")
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

# Wlcome message
def welcome_message():
    print("Welcome to the E-Voting System!\n")
    print("Your vote matters, and we’re here to make sure it counts.")
    print("Rest assured, your vote will remain completely anonymous and secure.")
    print("Our system is designed to protect your privacy while ensuring fairness.")
    print("Please follow the instructions to cast your vote confidently.\n")

# Main CLI function
def main():
    """
    Main function to run the voting system. Provides options to register voters, cast votes,
    show vote totals, and exit the system.
    """
    select_log_type()
    
    blockchain_ganache.connect_to_blockchain()
    
    welcome_message()
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
                    
                hashed_voter_id = hashlib.sha256(voter_id.encode()).hexdigest()
                
                 # Check if the voter has registered
                if voter_id not in voters and hashed_voter_id not in voters:
                    print("Voter ID not registered or ineligible. Please register first.")
                    continue
                
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
                        # Cast a valid vote using the blinding_signature module
                        blinding_signature.cast_a_vote(voter_id, voters, vote_records, candidate_number)
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
