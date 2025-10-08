
# Every word is 5 letters
# A word may contain repeating character
# Feedback loop telling whether guessed letter is either part of word or letter at exact location

class wordle_solver():
    def __init__(self, word_list):

        self.word_list = word_list
        self.letters_with_index = {
            # 'letter':[idx1,idx2]
        }
        self.letters_that_should_exist_without_index = {
            # 'letter':[idx1,idx2]
        }
        self.letters_that_should_not_exist = set()
        self.attempts = 0
        self.original_word_list = word_list.copy()  # Keep original for reset

    def reset(self):
        """Reset the solver state for a new game"""
        self.word_list = self.original_word_list.copy()
        self.letters_with_index = {}
        self.letters_that_should_exist_without_index = {}
        self.letters_that_should_not_exist = set()
        self.attempts = 0

    def update_filter(self, word_feed_back):
        # First pass: collect all Green and Yellow letters to know which letters should exist
        letters_that_should_exist = set()
        for i in range(5):
            letter = word_feed_back['word'][i]
            letter_feed_back = word_feed_back['feed_back'][i]
            if letter_feed_back in ['G', 'Y']:
                letters_that_should_exist.add(letter)
        
        # Second pass: process feedback
        for i in range(5):
            letter = word_feed_back['word'][i]
            letter_feed_back = word_feed_back['feed_back'][i]
            if(letter_feed_back == 'G'):
                if letter in self.letters_with_index:
                    if i not in self.letters_with_index[letter]:
                        self.letters_with_index[letter].append(i)
                else:
                    self.letters_with_index[letter] = [i]
                    
                if letter in self.letters_that_should_exist_without_index and i in self.letters_that_should_exist_without_index[letter]:
                    self.letters_that_should_exist_without_index[letter].remove(i)
            elif (letter_feed_back == "Y"):
                if letter in self.letters_that_should_exist_without_index:
                    if i not in self.letters_that_should_exist_without_index[letter]:
                        self.letters_that_should_exist_without_index[letter].append(i)
                else:
                    self.letters_that_should_exist_without_index[letter] = [i]
            else:
                if letter not in letters_that_should_exist:
                    self.letters_that_should_not_exist.add(letter)


    def letter_distribution(self, new_word_list):
        letter_count = {chr(i):0 for i in range(97,97+26)}
        total_count = 0
        for word in new_word_list:
            letter_already_added = []
            for letter in word:
                if letter not in letter_already_added and letter not in self.letters_that_should_exist_without_index.keys():
                    letter_count[letter]+=1
                    letter_already_added.append(letter)
                    total_count+=1
        word_score_map = {}
        for word in new_word_list:
            letter_already_added = []
            current_score = 0
            for letter in word:
                if letter not in letter_already_added:
                    if total_count > 0:  # Avoid division by zero
                        current_score+=((total_count-letter_count[letter])/total_count)
                    letter_already_added.append(letter)
            word_score_map[word]=current_score
        letter_count = {k:v for k,v in letter_count.items() if v>0}
        word_score_map = dict(sorted(word_score_map.items(), key=lambda item: item[1], reverse=True))
        return word_score_map



    def filter_words(self, words_list):
        filterd_list = []
        for word in words_list:
            should_exist = True
            for l in self.letters_that_should_exist_without_index.keys():
                if l in word:
                    indices = set([i for i, x in enumerate(word) if x == l])
                    indexs_where_it_should_not_exists = self.letters_that_should_exist_without_index[l]
                    if len(indices.intersection(indexs_where_it_should_not_exists))!=0:
                        should_exist = False
                else:
                    should_exist = False
            for key in self.letters_with_index.keys():
                for index in self.letters_with_index[key]:
                    if word[index] != key:
                        should_exist = False
            for banned_letter in self.letters_that_should_not_exist:
                if banned_letter in word:
                    should_exist = False
            if should_exist:
                filterd_list.append(word)
        return filterd_list


    def guess(self, word, feedback, print_feedback=True):
        """
        Process a guess with its feedback
        word: the guessed word (5 letters)
        feedback: string of 5 characters (G=Green/correct position, Y=Yellow/wrong position, B=Black/not in word)
        print_feedback: whether to print the results
        """
        word_feed_back = {
            "word": word,
            "feed_back": list(feedback)
        }
        self.attempts+=1
        
        self.update_filter(word_feed_back)
        self.word_list = self.filter_words(self.word_list)
        
        # Check if any words remain after filtering
        if not self.word_list:
            if print_feedback:
                print(f"After guess '{word}' with feedback '{feedback}':")
                print("No possible words remain. The feedback might be inconsistent.")
                print("-" * 50)
            return []
        
        word_score_map = self.letter_distribution(self.word_list)
        top_score = list(word_score_map.values())[0]
        top_words = [word for word, score in word_score_map.items() if score == top_score]

        if print_feedback:
            print(f"After guess '{word}' with feedback '{feedback}':")
            print(f"Remaining possible words: {len(self.word_list)}")
            
            print("Top words are ", top_words)
            print("-" * 50)
        return top_words
    
if __name__ == "__main__":
    import json
    words_file_path = "words.json"
    words_list = None

    with open(words_file_path, 'r') as f:
        words_list = json.load(f)
        words_list = words_list['words']
   
    solver = wordle_solver(word_list=words_list)
    solver.guess("which","BBBBB")
