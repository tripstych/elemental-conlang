#!/usr/bin/env python3
"""
Grammar and spelling fixer using LLM API
Reads conversation.txt line by line and fixes inconsistencies
"""

import os
import json
import time
from typing import List, Optional

class GrammarFixer:
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        """
        Initialize the grammar fixer with API configuration
        
        Args:
            api_key: Your LLM API key (not needed for Ollama)
            api_base: Custom API base URL (default: local Ollama)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY', 'ollama')  # Dummy key for Ollama
        self.api_base = api_base or os.getenv('OPENAI_API_BASE', 'http://localhost:11434/v1')
        
        # Try to import requests (install with: pip install requests)
        try:
            import requests
            self.requests = requests
        except ImportError:
            raise ImportError("requests library required. Install with: pip install requests")
    
    def fix_line(self, line: str) -> str:
        """
        Fix grammar and spelling in a single line using LLM
        
        Args:
            line: The input line to fix
            
        Returns:
            Fixed line with proper grammar and spelling
        """
        # Skip empty lines or very short lines
        if not line or len(line.strip()) < 3:
            return line
        
        # Prepare the prompt
        prompt = f"""Please fix the grammar, spelling, and punctuation in the following text. 
Keep the original meaning and style intact. Only fix actual errors.

Text to fix: "{line.strip()}"

Return only the corrected text, nothing else:"""
        
        try:
            response = self._call_api(prompt)
            return response.strip() if response else line
        except Exception as e:
            print(f"Error fixing line: {e}")
            return line
    
    def _call_api(self, prompt: str, model: str = "llama3") -> str:
        """
        Make API call to LLM
        
        Args:
            prompt: The prompt to send
            model: Model to use (default: llama3 for Ollama)
            
        Returns:
            LLM response text
        """
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Ollama API format
        data = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': 'You are a grammar and spelling expert. Fix errors while preserving meaning and style.'},
                {'role': 'user', 'content': prompt}
            ],
            'stream': False
        }
        
        try:
            response = self.requests.post(
                f'{self.api_base}/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                raise Exception(f"API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            # Try alternative Ollama endpoint format
            try:
                alt_data = {
                    'model': model,
                    'prompt': f"You are a grammar and spelling expert. Fix errors while preserving meaning and style.\n\n{prompt}",
                    'stream': False
                }
                
                response = self.requests.post(
                    f'http://localhost:11434/api/generate',
                    headers=headers,
                    json=alt_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.json()['response']
                else:
                    raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
                    
            except Exception as e2:
                raise Exception(f"Both API formats failed. Original: {e}. Ollama fallback: {e2}")
    
    def fix_file(self, input_file: str = 'conversation.txt', output_file: str = 'conversation_fixed.txt') -> int:
        """
        Fix grammar and spelling in entire file
        
        Args:
            input_file: Input file path
            output_file: Output file path
            
        Returns:
            Number of lines processed
        """
        try:
            # Read input file
            with open(input_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            print(f"Processing {len(lines)} lines from {input_file}")
            
            fixed_lines = []
            for i, line in enumerate(lines, 1):
                if i % 10 == 0:
                    print(f"Progress: {i}/{len(lines)} lines processed")
                
                fixed_line = self.fix_line(line)
                fixed_lines.append(fixed_line)
                
                # Add small delay to avoid rate limiting
                time.sleep(0.1)
            
            # Write output file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)
            
            print(f"Fixed text saved to {output_file}")
            return len(lines)
            
        except FileNotFoundError:
            print(f"Error: {input_file} not found")
            return 0
        except Exception as e:
            print(f"Error processing file: {e}")
            return 0
    
    def fix_conversation_interactive(self, input_file: str = 'conversation.txt') -> List[str]:
        """
        Fix conversation interactively, showing changes before applying
        
        Args:
            input_file: Input file path
            
        Returns:
            List of fixed lines
        """
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            fixed_lines = []
            
            for i, line in enumerate(lines, 1):
                if not line.strip():
                    fixed_lines.append(line)
                    continue
                
                print(f"\nLine {i}:")
                print(f"Original: {line.strip()}")
                
                fixed_line = self.fix_line(line)
                print(f"Fixed:    {fixed_line.strip()}")
                
                # Ask for confirmation
                while True:
                    choice = input("Apply fix? (y/n/skip): ").lower().strip()
                    if choice in ['y', 'yes']:
                        fixed_lines.append(fixed_line)
                        break
                    elif choice in ['n', 'no']:
                        fixed_lines.append(line)
                        break
                    elif choice in ['skip', 's']:
                        fixed_lines.append(line)
                        return fixed_lines  # Stop processing
                    else:
                        print("Please enter y, n, or skip")
            
            return fixed_lines
            
        except FileNotFoundError:
            print(f"Error: {input_file} not found")
            return []

def main():
    """
    Main function with command line interface
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix grammar and spelling using local LLM (Ollama + Llama3)')
    parser.add_argument('--input', default='conversation.txt', help='Input file path')
    parser.add_argument('--output', default='conversation_fixed.txt', help='Output file path')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    parser.add_argument('--model', default='llama3', help='Ollama model to use')
    parser.add_argument('--api-base', help='Ollama API base URL (default: http://localhost:11434/v1)')
    
    args = parser.parse_args()
    
    try:
        fixer = GrammarFixer(api_base=args.api_base)
        
        print("Using Ollama with model:", args.model)
        print("Make sure Ollama is running: ollama serve")
        print("And Llama3 is available: ollama run llama3")
        print()
        
        if args.interactive:
            fixed_lines = fixer.fix_conversation_interactive(args.input)
            if fixed_lines:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.writelines(fixed_lines)
                print(f"Interactive fixes saved to {args.output}")
        else:
            lines_processed = fixer.fix_file(args.input, args.output)
            print(f"Processed {lines_processed} lines")
            
    except Exception as e:
        print(f"Error: {e}")
        print("\nSetup instructions:")
        print("1. Install Ollama: https://ollama.ai/")
        print("2. Start Ollama: ollama serve")
        print("3. Pull Llama3: ollama pull llama3")
        print("4. Install requests: pip install requests")
        print("5. Run this script again")

if __name__ == "__main__":
    main()
