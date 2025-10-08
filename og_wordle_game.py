

from collections import Counter
from typing import List

class wordle_game():
    def __init__(self, secret):
        self.secret = secret
        
    def get_wordle_feedback(self, guess: str) -> List[str]:
        
        secret = self.secret.lower()
        guess = guess.lower()
        
        word_len = len(secret)
        
        # Initialize feedback list with 'B' for all positions
        feedback = ['B'] * word_len
        
        # Use a counter to keep track of the letters available in the secret word
        secret_letter_counts = Counter(secret)

        # First pass: Check for 'G' letters (green squares)
        # This pass is crucial to handle duplicate letters correctly.
        for i in range(word_len):
            if guess[i] == secret[i]:
                feedback[i] = 'G'
                # Decrement the count for the matched letter
                secret_letter_counts[guess[i]] -= 1

        # Second pass: Check for 'Y' letters (yellow squares)
        for i in range(word_len):
            # Only check letters that haven't been marked as 'correct'
            if feedback[i] != 'G':
                # Check if the letter is in the secret word and there are still
                # unmatched instances of it available.
                if guess[i] in secret_letter_counts and secret_letter_counts[guess[i]] > 0:
                    feedback[i] = 'Y'
                    # Decrement the count for the used letter
                    secret_letter_counts[guess[i]] -= 1
                    
        return "".join(feedback)