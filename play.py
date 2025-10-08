from wordle_game import wordle_game
from wordle_solver import wordle_solver
import random
import json
import matplotlib.pyplot as plt
import numpy as np

words_file_path = "words.json"
words_list = None

with open(words_file_path, 'r') as f:
    words_list = json.load(f)
    words_list = words_list['words']

total_games = 0
attempt_sum = 0
attempts_list = []  # Store all attempt counts for histogram

for word_of_the_day in words_list:
    game = wordle_game(word_of_the_day)
    solver = wordle_solver(word_list=words_list)

    feedback = "BBBBB"
    next_word = "crane"
    while feedback !="GGGGG":
        feedback = game.get_wordle_feedback(next_word)
        next_words = solver.guess(next_word,feedback, False)
        next_word = next_words[0]

    attempts_list.append(solver.attempts)
    attempt_sum+=solver.attempts
    total_games+=1

print(f"AVG attempts {attempt_sum/total_games}")

# Create histogram
plt.figure(figsize=(10, 6))
plt.hist(attempts_list, bins=range(1, max(attempts_list)+2), alpha=0.7, color='skyblue', edgecolor='black')
plt.xlabel('Number of Attempts')
plt.ylabel('Frequency')
plt.title('Distribution of Attempts to Solve Wordle Puzzles')
plt.grid(True, alpha=0.3)

# Add statistics to the plot
plt.axvline(x=np.mean(attempts_list), color='red', linestyle='--', label=f'Mean: {np.mean(attempts_list):.2f}')
plt.axvline(x=np.median(attempts_list), color='green', linestyle='--', label=f'Median: {np.median(attempts_list):.2f}')
plt.legend()

# Add text with additional statistics
stats_text = f'Total games: {total_games}\nMin attempts: {min(attempts_list)}\nMax attempts: {max(attempts_list)}\nStd dev: {np.std(attempts_list):.2f}'
plt.text(0.7, 0.7, stats_text, transform=plt.gca().transAxes, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()
plt.savefig('wordle_attempts_histogram.png', dpi=300, bbox_inches='tight')
plt.show()
print("Histogram saved as 'wordle_attempts_histogram.png'")

# Print detailed statistics
print(f"\nDetailed Statistics:")
print(f"Total games played: {total_games}")
print(f"Average attempts: {attempt_sum/total_games:.2f}")
print(f"Median attempts: {np.median(attempts_list):.2f}")
print(f"Min attempts: {min(attempts_list)}")
print(f"Max attempts: {max(attempts_list)}")
print(f"Standard deviation: {np.std(attempts_list):.2f}")

# Show attempt distribution
from collections import Counter
attempt_counts = Counter(attempts_list)
print(f"\nAttempt Distribution:")
for attempts in sorted(attempt_counts.keys()):
    percentage = (attempt_counts[attempts] / total_games) * 100
    print(f"{attempts} attempts: {attempt_counts[attempts]} games ({percentage:.1f}%)")

