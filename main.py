# Imports
import core.blockchain_ganache as blockchain_ganache
import auth.voter_authentication as voter_authentication
import core.blinding_signature as blinding_signature
import config
import hashlib

# ------------------------------ Utility Functions ------------------------------

# Function to select log type (back-end or front-end)
def select_log_type():
    """
    Prompt the user to select whether they want to print back-end logs.
    """
    while True:
        log_choice = input("Do you want to print back-end logs (Yes / [No])? : ").lower()
        print()
        if log_choice in ['yes', 'y']:
            config.PRINT_BACKEND_LOGS = True
            print("Back-end logs will be printed.")
            break
        else:
            config.PRINT_BACKEND_LOGS = False
            print("Only Front-end logs will be printed.")
            break

# Function to add candidates to the blockchain
def add_candidates(candidates):
    """
    Add each candidate to the blockchain and print the list of candidates.
    """
    print("Voting candidates:")
    for candidate_number, candidate_name in candidates.items():
        blockchain_ganache.add_candidate(candidate_name)
        print(f"{candidate_number}: {candidate_name}")

# Function to display available candidates
def display_candidates(candidates):
    """
    Print the list of candidates available for voting.
    """
    print("Candidates:")
    for candidate_number, candidate_name in candidates.items():
        print(f"{candidate_number}: {candidate_name}")

# Function to show total votes or total voters based on a secret code
def show_total_votes(vote_records, candidates, voters):
    """
    Display either the total number of voters or detailed vote counts for each candidate
    if the secret code is provided.
    """
    secret_code = "secure123"  # Hardcoded secret for authorized access
    user_input = input("Enter the secret code to view detailed vote counts or press Enter to view total voters: ")

    if user_input == secret_code:
        print("\n--- Vote counts for each candidate ---")
        vote_count = blinding_signature.count_votes(vote_records, candidates)
        for candidate, count in vote_count.items():
            print(f"🗳️  {candidate}: {count} votes")
    else:
        print(f"\nTotal number of voters so far: {len(vote_records)}")
        print("The total votes for each candidate will be announced at the end of the voting.")

# Function to pass the system to the next voter
def pass_to_next_voter(voter_id, voted_voters):
    """
    Check if the voter has already voted. If yes, pass the system to the next voter.
    If not, prompt them to vote.
    """
    if voter_id in voted_voters:
        print("\n✅ Thank you for voting!")
        print("\n--- Please pass the system to the next voter ---\n")
        welcome_message()  # Display welcome message again for the next voter
        input("Press any key to proceed to the voting menu")
        return True
    else:
        print("\n⚠️ You have not voted yet. Please register and cast your vote first.\n")
        return False

# Function to display the final exit poll results
def exit_poll(vote_records, candidates):
    """
    Display the final vote counts and declare the winner(s) or handle ties.
    """
    try:
        print("\n--- Final vote counts ---")
        vote_count = blinding_signature.count_votes(vote_records, candidates)

        # Display total number of voters
        print(f"\nTotal number of voters: {len(vote_records)}")

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
        print(f"\n❌ Error tallying votes: {e}")

# ------------------------------ Core Functions ------------------------------

# Welcome message displayed to the user
def welcome_message():
    """
    Print the welcome message with information about the voting system.
    """
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

# ------------------------------ Main Program Logic ------------------------------

def main():
    """
    Main CLI function for interacting with the voting system.
    Handles voter registration, voting, and vote tallying.
    """
    select_log_type()  # Prompt for log settings
    blockchain_ganache.connect_to_blockchain()  # Connect to blockchain

    welcome_message()  # Display welcome message

    # Define candidates with their assigned numbers
    candidates = {
        1: "Alice",
        2: "Bob",
        3: "Charlie",
        4: "David",
        5: "Eve"
    }

    add_candidates(candidates)  # Add candidates to blockchain

    # Data structures to manage voters and votes
    voters = {}  # Dictionary to store registered voters
    vote_records = []  # List to store valid vote records
    voted_voters = set()  # Set to store voters who have already voted, preventing double voting

    # Main voting loop
    while True:
        # Display menu options
        print("\n" + "="*30)
        print("          Voting Menu")
        print("="*30)
        print("1. Register as a voter")
        print("2. Cast a vote")
        print("3. Show total votes")
        print("4. Pass to next voter")
        print("5. Exit/Finish voting")
        print("="*30)

        # User input for menu selection
        choice = input("Enter your choice (1-5): ")

        # Handle each menu option
        if choice == '1':
            # Register a new voter
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

                # Ensure voter is registered
                if voter_id not in voters and hashed_voter_id not in voters:
                    print("\n❌ Your Voter ID has not been registered or is ineligible. Please register first.\n")
                    continue

                # Ensure voter hasn't already voted
                if voter_id in voted_voters:
                    print("\n⚠️ You have already cast your vote. You cannot vote again.\n")
                    continue

                display_candidates(candidates)  # Display available candidates
                candidate_number = int(input("\nEnter the candidate number you want to vote for: "))
                
                # Validate candidate selection
                if candidate_number in candidates:
                    confirmation = input(f"\nAre you sure you want to vote for {candidates[candidate_number]}? (yes/[no]): ").lower()
                    if confirmation in ['yes', 'y']:
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
            # Show total votes or total voters
            show_total_votes(vote_records, candidates, voters)

        elif choice == '4':
            # Pass the system to the next voter
            voter_id = input("\nEnter your voter ID: ")
            if pass_to_next_voter(voter_id, voted_voters):
                continue

        elif choice == '5':
            # Exit voting process and show final results
            exit_poll(vote_records, candidates)
            print("\n👋 Thank you for using our secure voting system. Goodbye!\n")
            break

        else:
            # Handle invalid menu option
            print("\n❌ Invalid choice. Please enter a number between 1 and 5.\n")


if __name__ == "__main__":
    main()
