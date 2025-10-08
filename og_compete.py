import json
from og_wordle_solver import wordle_solver
from og_wordle_game import wordle_game
from tqdm import tqdm

words_file_path = "words.json"
words_list = None

with open(words_file_path, 'r') as f:
    words_list = json.load(f)
    words_list = words_list['words']

for first_word in tqdm(words_list, desc="Testing first words"):
    attempts_list = []
    successful_games = 0
    
    for secret in tqdm(words_list, desc=f"Testing '{first_word}' as first word", leave=False):
        try:
            # print(f"Stating with {first_word} for secret {secret}")
            trace = []
            solver  = wordle_solver(words_list)
            game    = wordle_game(secret)
            next_word = first_word
            max_attempts = 10  # Safety limit
            attempts = 0
            while attempts < max_attempts:
                attempts += 1
                trace.append(next_word)
                feed_back = game.get_wordle_feedback(next_word)
                if feed_back == "GGGGG":
                    # trace_string = "->".join(trace)
                    # print(f"Answer is {next_word} with {solver.attempts} attempts | {trace_string}")
                    attempts_list.append(attempts)
                    successful_games += 1
                    break
                top_words = solver.guess(next_word, feed_back, False)
                if not top_words:  # No more possible words
                    print(f"No solution found for secret '{secret}' starting with '{first_word}'")
                    break
                next_word = top_words[0]
            # else:
                # print(f"Reached maximum attempts ({max_attempts}) for secret '{secret}'")
        except Exception as error:
            print()
            print("ERROR",error)
            trace_string = "->".join(trace)
            print(f"First word: {first_word}, Secret: {secret}, Trace: {trace_string}")
            print()
    
    # Calculate and print average attempts for this first word
    if attempts_list:
        avg_attempts = sum(attempts_list) / len(attempts_list)
        print(f"First word: {first_word} | Avg attempts: {avg_attempts:.2f} | Successful games: {successful_games}/{len(words_list)}")
    else:
        print(f"First word: {first_word} | No successful games completed")