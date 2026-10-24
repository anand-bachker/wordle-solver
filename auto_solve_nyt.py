import json
import time
import sys
import argparse
from playwright.sync_api import sync_playwright
from wordle_solver import wordle_solver

# Ensure UTF-8 output on Windows terminal
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def solve_nyt_wordle(headless=True, start_word="crane"):
    # Load words list
    words_file_path = "words.json"
    with open(words_file_path, "r") as f:
        data = json.load(f)
        word_list = data["words"]

    solver = wordle_solver(word_list=word_list)

    print("==================================================")
    print("      NYT WORDLE HEADLESS AUTOMATED SOLVER       ")
    print("==================================================")
    print(f"Mode: {'Headless' if headless else 'Headed (visible browser)'}")
    print(f"Starting word: {start_word.upper()}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("\nNavigating to NYT Wordle...")
        page.goto("https://www.nytimes.com/games/wordle/index.html", wait_until="domcontentloaded")
        time.sleep(2)

        # 1. Dismiss cookies banner
        try:
            consent_btn = page.locator("#fides-button-container button, .fides-accept-all-button, .fides-reject-all-button, button:has-text('Accept all')")
            if consent_btn.count() > 0 and consent_btn.first.is_visible():
                consent_btn.first.click(force=True)
                time.sleep(1)
        except Exception:
            pass
        page.evaluate("() => { const el = document.getElementById('fides-overlay'); if (el) el.remove(); }")

        # 2. Click Play button
        play_btn = page.locator("button[data-testid='Play'], button:has-text('Play')")
        if play_btn.count() > 0 and play_btn.first.is_visible():
            play_btn.first.click(force=True)
            time.sleep(2)

        # 3. Handle interstitial ad / subscribe banner
        for _ in range(5):
            skip_btn = page.locator("button:has-text('Continue to Wordle'), button[class*='skipButton'], button:has-text('Skip')")
            if skip_btn.count() > 0 and skip_btn.first.is_visible():
                skip_btn.first.click(force=True)
                time.sleep(2)
            else:
                time.sleep(1)
                if page.locator("div[data-state]").count() >= 30:
                    break

        # 4. Handle "How to play" dialog or modal close
        close_btn = page.locator("button[aria-label='Close'], button[data-testid='modal-close'], button.Modal-module_closeIcon__TcEKb")
        if close_btn.count() > 0 and close_btn.first.is_visible():
            close_btn.first.click(force=True)
            time.sleep(1)
        page.keyboard.press("Escape")
        time.sleep(1)

        # 5. Locate tiles
        tiles = page.locator("div[data-state]")
        if tiles.count() < 30:
            print("Error: Could not locate Wordle grid (less than 30 tiles found).")
            page.screenshot(path="error_screen.png")
            browser.close()
            return

        print("Wordle grid detected! Starting solver loop...\n")

        current_guess = start_word.lower()
        solved = False

        for row in range(6):
            print(f"--- Attempt {row + 1}/6: Trying '{current_guess.upper()}' ---")
            
            # Type the word
            page.keyboard.type(current_guess, delay=60)
            time.sleep(0.5)
            page.keyboard.press("Enter")
            
            # Wait for animation flip to complete
            row_tiles = [tiles.nth(row * 5 + col) for col in range(5)]
            
            # Poll for flip completion or invalid word
            is_valid = True
            for _ in range(20):
                time.sleep(0.2)
                st_last = row_tiles[4].get_attribute("data-state")
                st_first = row_tiles[0].get_attribute("data-state")
                if st_last in ["correct", "present", "absent"]:
                    break
                # Check if toast appeared for invalid word
                if st_first == "tbd":
                    toast = page.locator("[class*='Toast'], [class*='toaster']")
                    if toast.count() > 0 and any("word" in (t.inner_text() or "").lower() for t in toast.all()):
                        is_valid = False
                        break

            if not is_valid or row_tiles[0].get_attribute("data-state") == "tbd":
                print(f"'{current_guess.upper()}' is not in NYT word list. Retracting...")
                for _ in range(5):
                    page.keyboard.press("Backspace")
                    time.sleep(0.1)
                if current_guess in solver.word_list:
                    solver.word_list.remove(current_guess)
                score_map = solver.letter_distribution(solver.word_list)
                if not score_map:
                    print("No more candidate words available!")
                    break
                current_guess = list(score_map.keys())[0]
                continue

            # Read feedback
            feedback_str = ""
            display_emoji = ""
            for col in range(5):
                st = row_tiles[col].get_attribute("data-state")
                if st == "correct":
                    feedback_str += "G"
                    display_emoji += "🟩"
                elif st == "present":
                    feedback_str += "Y"
                    display_emoji += "🟨"
                else:
                    feedback_str += "B"
                    display_emoji += "⬛"

            print(f"Feedback: {feedback_str}  {display_emoji}")

            if feedback_str == "GGGGG":
                solved = True
                print(f"\n🎉 SOLVED in {row + 1} attempts! The word is '{current_guess.upper()}'.")
                page.screenshot(path="wordle_solved.png")
                print("Screenshot saved to 'wordle_solved.png'.")
                break

            # Solver calculates next guess
            next_words = solver.guess(current_guess, feedback_str, print_feedback=False)
            print(f"Remaining candidates: {len(solver.word_list)}")
            if not next_words:
                print("Solver ran out of candidate words!")
                break
            
            current_guess = next_words[0]
            print(f"Next suggestion: '{current_guess.upper()}' (out of {len(next_words)} top scored)")
            time.sleep(1)

        if not solved:
            print("\n❌ Failed to solve Wordle within 6 attempts.")
            page.screenshot(path="wordle_failed.png")

        browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Headless NYT Wordle Auto-Solver")
    parser.add_argument("--headed", action="store_true", help="Run browser in visible (headed) mode")
    parser.add_argument("--start", type=str, default="crane", help="Starting 5-letter word (default: crane)")
    args = parser.parse_args()

    solve_nyt_wordle(headless=not args.headed, start_word=args.start)
