#!/usr/bin/env python3
"""
Split compound words like "likethesewords" into individual words
Uses word segmentation algorithms to find the most likely word boundaries
"""

import re
from collections import defaultdict

class WordSplitter:
    def __init__(self):
        # Common English word frequency (simplified)
        # In practice, you'd load this from a real word frequency dictionary
        self.word_freq = {
            'the': 0.06, 'and': 0.04, 'that': 0.03, 'have': 0.025, 'for': 0.022,
            'not': 0.02, 'with': 0.019, 'you': 0.018, 'this': 0.017, 'but': 0.016,
            'his': 0.015, 'from': 0.014, 'they': 0.013, 'know': 0.012, 'want': 0.011,
            'been': 0.01, 'good': 0.009, 'much': 0.008, 'some': 0.007, 'time': 0.006,
            'very': 0.005, 'when': 0.004, 'come': 0.003, 'here': 0.002, 'like': 0.05,
            'words': 0.003, 'word': 0.004, 'split': 0.002, 'into': 0.008,
            'these': 0.006, 'were': 0.005, 'said': 0.004, 'each': 0.003,
            'which': 0.007, 'their': 0.006, 'will': 0.008, 'would': 0.009,
            'about': 0.005, 'could': 0.004, 'other': 0.006, 'than': 0.005,
            'then': 0.004, 'them': 0.006, 'these': 0.006, 'so': 0.003,
            'some': 0.007, 'her': 0.005, 'would': 0.009, 'make': 0.004,
            'like': 0.05, 'the': 0.06, 'se': 0.001, 'words': 0.003
        }
        
    def split_compound_word(self, word):
        """
        Split a compound word using dynamic programming
        Returns the most likely word segmentation
        """
        if len(word) <= 3:  # Too short to split meaningfully
            return word
            
        # Try to find the best split using dynamic programming
        best_split = self._best_segmentation(word)
        
        if best_split and len(best_split.split()) > 1:
            return best_split
        else:
            return word
    
    def _best_segmentation(self, word):
        """
        Find the best segmentation using dynamic programming
        """
        n = len(word)
        dp = [None] * (n + 1)
        dp[0] = ""  # Base case
        
        for i in range(1, n + 1):
            best_score = -float('inf')
            best_segment = None
            
            for j in range(0, i):
                segment = word[j:i]
                score = self._segment_score(segment)
                
                if dp[j] is not None:
                    total_score = score + (0 if j == 0 else -1)  # Small penalty for splits
                    if total_score > best_score:
                        best_score = total_score
                        best_segment = segment if j == 0 else dp[j] + " " + segment
            
            dp[i] = best_segment
        
        return dp[n]
    
    def _segment_score(self, segment):
        """
        Score a segment based on word frequency and length
        """
        # Higher score for common words
        freq_score = self.word_freq.get(segment.lower(), -10)
        
        # Penalty for very short or very long segments
        length_penalty = 0
        if len(segment) == 1:
            length_penalty = -5
        elif len(segment) > 15:
            length_penalty = -3
        
        return freq_score + length_penalty
    
    def split_text(self, text):
        """
        Split compound words in a text string
        """
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        result = []
        
        for word in words:
            if word.isupper() or len(word) <= 3:
                result.append(word)
            else:
                split_word = self.split_compound_word(word.lower())
                result.append(split_word)
        
        # Reconstruct the text with punctuation preserved
        result_text = text
        for original_word in words:
            if len(original_word) > 3 and not original_word.isupper():
                split_word = self.split_compound_word(original_word.lower())
                if split_word != original_word.lower():
                    result_text = result_text.replace(original_word, split_word)
        
        return result_text

def main():
    splitter = WordSplitter()
    
    # Test examples
    test_words = [
        "likethesewords",
        "wordsegmentation", 
        "naturalanguageprocessing",
        "machinelearning",
        "helloworld",
        "thisisatest",
        "splitcompoundwords"
    ]
    
    # print("Word Splitter Test:")
    # print("=" * 50)
    
    # for word in test_words:
    #     split_result = splitter.split_compound_word(word)
    #     print(f"{word:<25} -> {split_result}")
    
    # print("\nText Example:")
    # test_text = "This is a test likethesewords for splitting compoundwords in text."
    # result = splitter.split_text(test_text)
    # print(f"Original: {test_text}")
    # print(f"Fixed:    {result}")

    words = [words.strip() for words in open("conversation.txt").readlines()]
    for line in words:
        res = splitter.split_text(line)
        print(res)

if __name__ == "__main__":
    main()
