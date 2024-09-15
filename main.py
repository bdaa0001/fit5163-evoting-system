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
        log_choice = input("Do you want to print back-end logs (Yes / [No])? : ").lower()
        print()
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

# Wecome message
def welcome_message():
    print("="*50)
    print("        Welcome to the E-Voting System!")
    print("="*50)
    print("\nYour vote is anonymous, secure, and fully protected.")
    print("We use advanced technologies such as:")
    print("  - Blinding Signatures")
    print("  - Blockchain")
    print("  - Smart Contracts")
    print("\nThese ensure confidentiality, authentication, and integrity.")
    print("Rest assured, your vote is handled with the highest standards of privacy and security.")
    print("\nPlease follow the instructions to cast your vote confidently.")
    print("="*50)

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
        print("\n" + "="*30)
        print("          Voting Menu")
        print("="*30)
        print("1. Register voter")
        print("2. Cast a vote")
        print("3. Show total votes")
        print("4. Exit")
        print("="*30)

        # User input to select an option from the menu
        choice = input("Enter your choice (1-4): ")

        if choice == '1':
            # Register a voter
            try:
                voter_id = voter_authentication.register_voter(voters)
                print(f"\n✅ You have been successfully registered!\n")
            except Exception as e:
                print(f"\n❌ Error registering voter: {e}\n")

        elif choice == '2':
            # Cast a vote
            try:
                voter_id = input("\nEnter your voter ID: ")
                    
                hashed_voter_id = hashlib.sha256(voter_id.encode()).hexdigest()
                
                # Check if the voter has registered
                if voter_id not in voters and hashed_voter_id not in voters:
                    print("\n❌ Your Voter ID has not been registered or is ineligible. Please register first.\n")
                    continue
                
                # Check if the voter has already voted
                if voter_id in voted_voters:
                    print("\n⚠️ You have already cast your vote. You cannot vote again.\n")
                    continue

                # Display candidates for voting
                display_candidates(candidates)

                # Collect and validate candidate selection
                candidate_number = int(input("\nEnter the candidate number you want to vote for: "))
                if candidate_number in candidates:
                    confirmation = input(f"\nAre you sure you want to vote for {candidates[candidate_number]}? (yes/[no]): ").lower()
                    if confirmation in ['yes', 'y']:
                        # Cast a valid vote using the blinding_signature module
                        blinding_signature.cast_a_vote(voter_id, voters, vote_records, candidate_number)
                        voted_voters.add(voter_id)  # Mark voter as having voted
                        print(f"\n✅ Your vote for {candidates[candidate_number]} has been successfully cast!\n")
                    else:
                        print("\n⚠️ Vote cancelled.\n")
                else:
                    print("\n❌ Invalid candidate number. Please enter a valid candidate number.\n")
            except ValueError:
                print("\n❌ Invalid input. Please enter a valid candidate number.\n")
            except Exception as e:
                print(f"\n❌ Error casting vote: {e}\n")

        elif choice == '3':
            # Show total votes for each candidate
            try:
                print("\n--- Tallying the votes ---\n")
                vote_count = blinding_signature.count_votes(vote_records, candidates)
                for candidate, count in vote_count.items():
                    print(f"🗳️  {candidate}: {count} votes")
            except Exception as e:
                print(f"\n❌ Error tallying votes: {e}\n")

        elif choice == '4':
            # Exit the voting system
            try:
                print("\n--- Final votes ---\n")
                vote_count = blinding_signature.count_votes(vote_records, candidates)

                # Print the vote count for each candidate
                for candidate, count in vote_count.items():
                    print(f"🗳️  {candidate}: {count} votes")

                # Check if all votes are zero
                if all(count == 0 for count in vote_count.values()):
                    print("\n🚫 No winner: All candidates received 0 votes.")
                else:
                    # Find the maximum vote count
                    max_votes = max(vote_count.values())
                    
                    # Find all candidates with the maximum votes
                    winners = [candidate for candidate, count in vote_count.items() if count == max_votes]

                    if len(winners) == 1:
                        # If there is only one winner
                        print(f"\n🏆 The winner is: {winners[0]} with {max_votes} votes!")
                    else:
                        # If there are multiple winners
                        print(f"\n🤝 It's a tie! The winners are: {', '.join(winners)} with {max_votes} votes each!")
                
            except Exception as e:
                print(f"\n❌ Error tallying votes: {e}\n")

            print("\n👋 Exiting the voting system. Goodbye!\n")
            break

        else:
            # Invalid menu selection
            print("\n❌ Invalid choice. Please enter a number between 1 and 4.\n")


# Run the main function when the script is executed
if __name__ == "__main__":
    main()
