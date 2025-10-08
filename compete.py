import json
import time
import os
import csv
from concurrent.futures import ProcessPoolExecutor, as_completed
from threading import Lock
from og_wordle_solver import wordle_solver
from og_wordle_game import wordle_game

# Global lock for file writes
file_lock = Lock()
RESULTS_FILE = "compete_results.csv"

def load_existing_results():
    """Load already processed results from CSV file"""
    existing_results = {}
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_results[row['first_word']] = {
                    'avg_attempts': float(row['avg_attempts']),
                    'successful_games': int(row['successful_games']),
                    'total_games': int(row['total_games'])
                }
    return existing_results

def save_result_to_file(first_word, avg_attempts, successful_games, total_games):
    """Save a single result to CSV file (thread-safe)"""
    with file_lock:
        file_exists = os.path.exists(RESULTS_FILE)
        with open(RESULTS_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                # Write header if file doesn't exist
                writer.writerow(['first_word', 'avg_attempts', 'successful_games', 'total_games'])
            writer.writerow([first_word, avg_attempts, successful_games, total_games])

def test_first_word(first_word, words_list):
    """Test a single first word against all secret words"""
    # Note: print statements in processes may not appear in real-time
    attempts_list = []
    successful_games = 0
    
    for i, secret in enumerate(words_list):
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
            # Error info will be handled by main process
            pass
    
    return first_word, attempts_list, successful_games

if __name__ == "__main__":
    words_file_path = "words.json"
    words_list = None

    with open(words_file_path, 'r') as f:
        words_list = json.load(f)
        words_list = words_list['words']

    # Load existing results
    print(f"Loading existing results from {RESULTS_FILE}...")
    existing_results = load_existing_results()
    print(f"Found {len(existing_results)} already processed first words.")

    # Filter out already processed words
    remaining_words = [word for word in words_list if word not in existing_results]
    
    print(f"Total first words: {len(words_list)}")
    print(f"Already processed: {len(existing_results)}")
    print(f"Remaining to process: {len(remaining_words)}")
    
    if not remaining_words:
        print("All first words have already been processed!")
        print(f"Results are saved in {RESULTS_FILE}")
        exit(0)
    
    print(f"\nTesting {len(remaining_words)} remaining first words against {len(words_list)} secret words...")
    print("Results will appear as each first word completes testing:\n")

    # Use ProcessPoolExecutor to test first words in parallel for better CPU utilization
    completed_count = 0
    start_time = time.time()
    with ProcessPoolExecutor(max_workers=64) as executor:
        # Submit tasks only for remaining words  
        future_to_word = {executor.submit(test_first_word, first_word, words_list): first_word 
                          for first_word in remaining_words}
        
        # Process completed tasks as they finish
        for future in as_completed(future_to_word):
            try:
                first_word, attempts_list, successful_games = future.result()
                completed_count += 1
                elapsed = time.time() - start_time
                
                # Calculate and print average attempts for this first word immediately
                if attempts_list:
                    avg_attempts = sum(attempts_list) / len(attempts_list)
                    # Save to file
                    save_result_to_file(first_word, avg_attempts, successful_games, len(words_list))
                    print(f"[{completed_count}/{len(remaining_words)}] ({elapsed:.1f}s) First word: {first_word} | Avg attempts: {avg_attempts:.2f} | Successful games: {successful_games}/{len(words_list)}")
                else:
                    # Save failed result to file
                    save_result_to_file(first_word, 0.0, 0, len(words_list))
                    print(f"[{completed_count}/{len(remaining_words)}] ({elapsed:.1f}s) First word: {first_word} | No successful games completed")
            except Exception as error:
                first_word = future_to_word[future]
                completed_count += 1
                elapsed = time.time() - start_time
                # Save error result to file
                save_result_to_file(first_word, 0.0, 0, len(words_list))
                print(f"[{completed_count}/{len(remaining_words)}] ({elapsed:.1f}s) Error processing first word '{first_word}': {error}")

    print(f"\nCompleted testing all {len(remaining_words)} remaining first words!")
    print(f"Results saved to {RESULTS_FILE}")