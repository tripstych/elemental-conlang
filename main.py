#!/usr/bin/env python3
"""
Main Application - Tkinter version for conlang development tools
Provides interface for editing elements, phonetics, and building dictionaries
"""
import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import queue
import random



class MainTkApp:
    """Main application for conlang development tools"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Conlang Development Studio")
        self.root.geometry("600x800")
        
        # Initialize queue for thread-safe GUI updates
        self.queue = queue.Queue()
        
        self.root.after(100, self.check_queue)
        # Create main interface
        self._create_main_interface()
    
    def start_monitoring_thread(self):
        """Create and start a new thread for monitoring the counter file"""
        threading.Thread(target=self.monitor_counter_file, daemon=True).start()
    
    def monitor_counter_file(self):
        """This function runs in the separate thread to monitor .tmp.counter file"""
        import time
        # Wait a moment for the file to be created
        time.sleep(2)
        while True:
            try:
                if os.path.exists('.tmp.counter'):
                    with open('.tmp.counter', 'r') as f:
                        content = f.read().strip()
                    lines = content.split('\n')
                    if lines:
                        last_line = lines[-1].strip()
                        if last_line == "done":
                            # Put completion message in queue
                            self.queue.put("Completed!")
                            break
                        else:
                            # Put progress update (latest line number) in queue
                            self.queue.put(f"Processing: {last_line}")
                time.sleep(1)  # Check every second
            except:
                time.sleep(1)
    
    def check_queue(self):
        """This function runs in the main GUI thread to check for queue messages"""
        try:
            while True:
                # Try to get all new messages from the queue without blocking
                message = self.queue.get_nowait()
                # Update the status label
                self.status_label.config(text=message)
        except queue.Empty:
            pass  # Ignore if the queue is empty
        finally:
            # Reschedule this check for after 100ms
            self.root.after(100, self.check_queue)
    
    def _create_main_interface(self):
        """Create the main application interface"""
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="Conlang Development Studio",
            font=('Arial', 24, 'bold'),
            foreground='#3377CC'
        )
        title_label.pack(pady=(0, 20))
        
        # Language Name input section
        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill='x', pady=10)
        
        name_label = ttk.Label(
            name_frame,
            text="Language Name:",
            font=('Arial', 16, 'bold')
        )
        name_label.pack(side='left', padx=(0, 10))
        
        self.language_name_var = tk.StringVar(value="MyConlang")
        self.language_name_input = ttk.Entry(
            name_frame,
            textvariable=self.language_name_var,
            font=('Arial', 16),
            width=30
        )
        self.language_name_input.pack(side='left', fill='x', expand=True)
        
        # Button grid layout
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='both', expand=True, pady=20)
        
        # Configure grid weights
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_rowconfigure(0, weight=1)
        button_frame.grid_rowconfigure(1, weight=1)

        style = ttk.Style()
        style.configure('BlueButton.TButton', background='#4D99FF', foreground='white')

        
        # Row 1: Edit Elements and Edit Phonetics
        edit_elements_btn = tk.Button(
            button_frame,
            text="Edit Elements",
            command=lambda: self.launch_edit_elements(None),
            bg='black',
            fg='white',
            font=('Arial', 16, 'bold')
        )
        edit_elements_btn.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        
        edit_phonetics_btn = tk.Button(
            button_frame,
            text="Edit Phonetics",
            command=lambda: self.launch_edit_phonetics(None),
            bg='black',
            fg='white',
            font=('Arial', 16, 'bold')
        )
        edit_phonetics_btn.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')
        
        # Row 2: Build Elemental and Build Words
        build_elemental_btn = tk.Button(
            button_frame,
            text="Build Elemental",
            command=lambda: self.launch_build_elemental(None),
            bg='black',
            fg='white',
            font=('Arial', 16, 'bold')
        )
        build_elemental_btn.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        
        build_words_btn = tk.Button(
            button_frame,
            text="Build Words",
            command=lambda: self.launch_build_words(None),
            bg='black',
            fg='white',
            font=('Arial', 16, 'bold')
        )
        build_words_btn.grid(row=1, column=1, padx=10, pady=10, sticky='nsew')
        
        # File Options Section
        options_frame = ttk.LabelFrame(main_frame, text="File Options", padding="10")
        options_frame.pack(fill='x', pady=10)
        
        # Build Elemental Options
        elemental_frame = ttk.Frame(options_frame)
        elemental_frame.pack(fill='x', pady=5)
        
        ttk.Label(elemental_frame, text="Build Elemental:", font=('Arial', 12, 'bold')).pack(anchor='w')
        
        elemental_inputs = ttk.Frame(elemental_frame)
        elemental_inputs.pack(fill='x', padx=10)
        
        ttk.Label(elemental_inputs, text="Anchors File:").grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.anchors_file_var = tk.StringVar()
        ttk.Entry(elemental_inputs, textvariable=self.anchors_file_var, width=40).grid(row=0, column=1, sticky='ew')
        ttk.Button(elemental_inputs, text="Browse...", command=lambda: self._browse_file(self.anchors_file_var, "Select Anchors File", [("JSON files", "*.json"), ("All files", "*.*")])).grid(row=0, column=2, padx=(5, 0))
        
        ttk.Label(elemental_inputs, text="Output File:").grid(row=1, column=0, sticky='w', padx=(0, 10))
        self.elemental_output_var = tk.StringVar()
        ttk.Entry(elemental_inputs, textvariable=self.elemental_output_var, width=40).grid(row=1, column=1, sticky='ew')
        ttk.Button(elemental_inputs, text="Browse...", command=lambda: self._browse_save_file(self.elemental_output_var, "Save Elemental Dictionary As", [("JSON files", "*.json"), ("All files", "*.*")])).grid(row=1, column=2, padx=(5, 0))
        
        elemental_inputs.grid_columnconfigure(1, weight=1)
        
        # Build Words Options
        words_frame = ttk.Frame(options_frame)
        words_frame.pack(fill='x', pady=5)
        
        ttk.Label(words_frame, text="Build Words:", font=('Arial', 12, 'bold')).pack(anchor='w')
        
        words_inputs = ttk.Frame(words_frame)
        words_inputs.pack(fill='x', padx=10)
        
        ttk.Label(words_inputs, text="Elemental Dict:").grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.words_elemental_var = tk.StringVar()
        ttk.Entry(words_inputs, textvariable=self.words_elemental_var, width=40).grid(row=0, column=1, sticky='ew')
        ttk.Button(words_inputs, text="Browse...", command=lambda: self._browse_file(self.words_elemental_var, "Select Elemental Dictionary File", [("JSON files", "*.json"), ("All files", "*.*")])).grid(row=0, column=2, padx=(5, 0))
        
        ttk.Label(words_inputs, text="Phonetic Dict:").grid(row=1, column=0, sticky='w', padx=(0, 10))
        self.words_phonetic_var = tk.StringVar()
        ttk.Entry(words_inputs, textvariable=self.words_phonetic_var, width=40).grid(row=1, column=1, sticky='ew')
        ttk.Button(words_inputs, text="Browse...", command=lambda: self._browse_file(self.words_phonetic_var, "Select Phonetic Dictionary File", [("JSON files", "*.json"), ("All files", "*.*")])).grid(row=1, column=2, padx=(5, 0))
        
        ttk.Label(words_inputs, text="Word List:").grid(row=2, column=0, sticky='w', padx=(0, 10))
        self.words_wordlist_var = tk.StringVar()
        ttk.Entry(words_inputs, textvariable=self.words_wordlist_var, width=40).grid(row=2, column=1, sticky='ew')
        ttk.Button(words_inputs, text="Browse...", command=lambda: self._browse_file(self.words_wordlist_var, "Select Word List File", [("Text files", "*.txt"), ("All files", "*.*")])).grid(row=2, column=2, padx=(5, 0))
        
        ttk.Label(words_inputs, text="Output File:").grid(row=3, column=0, sticky='w', padx=(0, 10))
        self.words_output_var = tk.StringVar()
        ttk.Entry(words_inputs, textvariable=self.words_output_var, width=40).grid(row=3, column=1, sticky='ew')
        ttk.Button(words_inputs, text="Browse...", command=lambda: self._browse_save_file(self.words_output_var, "Save Word Dictionary As", [("JSON files", "*.json"), ("All files", "*.*")])).grid(row=3, column=2, padx=(5, 0))
        
        words_inputs.grid_columnconfigure(1, weight=1)
        
        # Status label
        self.status_label = ttk.Label(
            main_frame,
            text="Ready to start building your conlang!",
            font=('Arial', 14),
            foreground='gray'
        )
        self.status_label.pack(pady=(20, 0))
    
    def _browse_file(self, var, title, filetypes):
        """Browse for a file and update the given StringVar"""
        filename = filedialog.askopenfilename(title=title, filetypes=filetypes)
        if filename:
            var.set(filename)
    
    def _browse_save_file(self, var, title, filetypes):
        """Browse for a save location and update the given StringVar"""
        filename = filedialog.asksaveasfilename(title=title, filetypes=filetypes)
        if filename:
            var.set(filename)
        
            
    def launch_edit_elements(self, instance):
        """Launch the elements editor"""
        self.status_label.config(text="Launching Elements Editor...")
        self.root.update()
        try:
            # Launch edit_elementals.py in a new process
            subprocess.Popen([sys.executable, 'edit_elementals.py'])
            self.root.after(1000, lambda: self._update_status("Elements Editor launched"))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch Elements Editor:\n{str(e)}")
            self.status_label.config(text="Ready to start building your conlang!")
    
    def launch_edit_phonetics(self, instance):
        """Launch the phonetics editor"""
        self.status_label.config(text="Launching Phonetics Editor...")
        self.root.update()
        try:
            # Launch edit_phonetic.py in a new process
            subprocess.Popen([sys.executable, 'edit_phonetic.py'])
            self.root.after(1000, lambda: self._update_status("Phonetics Editor launched"))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch Phonetics Editor:\n{str(e)}")
            self.status_label.config(text="Ready to start building your conlang!")
    
    def launch_build_elemental(self, instance):
        """Launch the elemental dictionary builder"""
        language_name = self.language_name_var.get().strip()
        if not language_name:
            messagebox.showerror("Error", "Please enter a language name first!")
            return
        
        # Get file paths from input fields (optional overrides)
        anchors_file = self.anchors_file_var.get().strip()
        output_file = self.elemental_output_var.get().strip()
        
        # Use file dialog if output file not provided in input field
        if not output_file:
            suggested_filename = f"{language_name}_elemental_data.json"
            output_file = filedialog.asksaveasfilename(
                title="Save Elemental Dictionary As",
                initialfile=suggested_filename,
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not output_file:  # User cancelled
                self.status_label.config(text="Ready to start building your conlang!")
                return
        
        # Check for anchors file (use input field if provided, otherwise check for default)
        if not anchors_file:
            # Check for custom anchors file
            anchors_file = f"{language_name.lower()}_anchors.json"
            if not os.path.exists(anchors_file):
                anchors_file = None  # Use default anchors
        
        self.status_label.config(text="Started building, this may take a while..")
        self.root.update()
        
        # Start the monitoring thread (uses thread-safe GUI updates directly)
        self.start_monitoring_thread()
        
        # Build command based on available options
        try:
            if anchors_file and os.path.exists(anchors_file):
                # Use custom anchors
                cmd = [sys.executable, 'build_elemental_dictionary.py', 
                       '--anchor', anchors_file, 
                       '--output', output_file]
            else:
                # Use default anchors
                cmd = [sys.executable, 'build_elemental_dictionary.py', 
                       '--output', output_file]
            
            subprocess.Popen(cmd)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to build elemental dictionary:\n{str(e)}")
            self.status_label.config(text="Ready to start building your conlang!")
    
    def launch_build_words(self, instance):
        """Launch the word generator"""
        language_name = self.language_name_var.get().strip()
        if not language_name:
            messagebox.showerror("Error", "Please enter a language name first!")
            return
        
        # Get file paths from input fields (optional overrides)
        elemental_file = self.words_elemental_var.get().strip()
        phonetic_file = self.words_phonetic_var.get().strip()
        wordlist_file = self.words_wordlist_var.get().strip()
        output_file = self.words_output_var.get().strip()
        
        # Use file dialogs if files not provided in input fields
        if not elemental_file:
            expected_filename = f"{language_name}_elemental_data.json"
            elemental_file = filedialog.askopenfilename(
                title="Select Elemental Dictionary File",
                initialfile=expected_filename,
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not elemental_file:  # User cancelled
                self.status_label.config(text="Ready to start building your conlang!")
                return
        
        if not output_file:
            suggested_filename = f"{language_name}_words_data.json"
            output_file = filedialog.asksaveasfilename(
                title="Save Word Dictionary As",
                initialfile=suggested_filename,
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not output_file:  # User cancelled
                self.status_label.config(text="Ready to start building your conlang!")
                return
        
        self.status_label.config(text="Building Word Dictionary...")
        self.root.update()
        
        try:
            #reset counter before we start
            f = open(".tmp.counter","w")
            f.write("0")
            f.close()
            # Build command based on available options
            cmd = [sys.executable, 'omega_alpha.py']
            
            # Add elemental dict (always required)
            cmd.extend(['--elemental-dict', elemental_file])
            
            # Add phonetic dict if specified
            if phonetic_file:
                cmd.extend(['--phonetic-dict', phonetic_file])
            
            # Add wordlist if specified
            if wordlist_file:
                cmd.extend(['--wordlist', wordlist_file])
            
            # Add output file
            cmd.extend(['--output', output_file])
            
            subprocess.Popen(cmd)
            self.root.after(1000, lambda: self._update_status(f"Building word dictionary for {language_name}..."))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to build word dictionary:\n{str(e)}")
            self.status_label.config(text="Ready to start building your conlang!")
    
    def _update_status(self, message):
        """Update status label"""
        self.status_label.config(text=message)
    
    def _reset_status(self):
        """Reset status to default"""
        self.status_label.config(text="Ready to start building your conlang!")


def main():
    root = tk.Tk()
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    app = MainTkApp(root)
    print("App launched", flush=True)
    root.mainloop()


if __name__ == '__main__':
    print("Launching app")
    main()
