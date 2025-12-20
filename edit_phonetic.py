#!/usr/bin/env python3
"""
Phonetic Editor - Tkinter version for better key-value editing
Creates a clean interface for editing phonetic dictionary JSON with proper tables
"""

import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os


class PhoneticEditorTk:
    def __init__(self, root):
        self.root = root
        self.root.title("Phonetic Dictionary Editor")
        self.root.geometry("800x600")
        
        # Load data
        self.phonetic_data = self._load_phonetic_data()
        
        # Create main interface
        self._create_main_interface()
        
        # Load data into widgets
        self._load_data_into_widgets()
    
    def _load_phonetic_data(self):
        """Load phonetic dictionary from JSON file"""
        try:
            with open('phonetic_dictionary.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"Loaded phonetic dictionary with {len(data)} categories")
            return data
        except FileNotFoundError:
            print("Error: phonetic_dictionary.json not found")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return {}
    
    def _create_main_interface(self):
        """Create the main interface with notebook for tabs"""
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create tabs for each category
        self.widgets = {}
        
        for category_name, category_data in self.phonetic_data.items():
            if category_name == 'constraints':
                self._create_constraints_tab(category_name, category_data)
            elif category_name == 'orthography':
                self._create_orthography_tab(category_name, category_data)
            elif isinstance(category_data, dict):
                self._create_phonetic_tab(category_name, category_data)
        
        # Add save button at bottom
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        save_btn = ttk.Button(button_frame, text="Save Phonetic Dictionary", command=self._save_data)
        save_btn.pack(side='right', padx=5)
        
        # Status label
        self.status_label = ttk.Label(button_frame, text="Ready")
        self.status_label.pack(side='left', padx=5)
    
    def _create_constraints_tab(self, category_name, category_data):
        """Create constraints tab with key-value table"""
        # Create tab
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Constraints")
        
        # Description
        desc_label = ttk.Label(tab_frame, text="Regex patterns to reject invalid word formations", font=('Arial', 10))
        desc_label.pack(pady=5)
        
        # Create treeview for key-value pairs
        columns = ('Pattern (regex)', 'Reason (optional)')
        
        tree = ttk.Treeview(tab_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        tree.heading('Pattern (regex)', text='Pattern (regex)')
        tree.heading('Reason (optional)', text='Reason (optional)')
        tree.column('Pattern (regex)', width=300)
        tree.column('Reason (optional)', width=300)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        tree_frame = ttk.Frame(tab_frame)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Button frame
        btn_frame = ttk.Frame(tab_frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        add_btn = ttk.Button(btn_frame, text="Add Row", command=lambda: self._add_tree_row(tree))
        add_btn.pack(side='left', padx=5)
        
        remove_btn = ttk.Button(btn_frame, text="Remove Selected", command=lambda: self._remove_tree_row(tree))
        remove_btn.pack(side='left', padx=5)
        
        # Store reference
        self.widgets[category_name] = tree
    
    def _create_orthography_tab(self, category_name, category_data):
        """Create orthography tab with key-value table"""
        # Create tab
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Orthography")
        
        # Description
        desc_label = ttk.Label(tab_frame, text="Spelling transformation rules (from -> to replacements)", font=('Arial', 10))
        desc_label.pack(pady=5)
        
        # Create treeview for key-value pairs
        columns = ('From', 'To')
        
        tree = ttk.Treeview(tab_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        tree.heading('From', text='From')
        tree.heading('To', text='To')
        tree.column('From', width=300)
        tree.column('To', width=300)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview directly to tab_frame
        tree.pack(fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y')
        
        # Button frame
        btn_frame = ttk.Frame(tab_frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        add_btn = ttk.Button(btn_frame, text="Add Row", command=lambda: self._add_tree_row(tree))
        add_btn.pack(side='left', padx=5)
        
        remove_btn = ttk.Button(btn_frame, text="Remove Selected", command=lambda: self._remove_tree_row(tree))
        remove_btn.pack(side='left', padx=5)
        
        # Input frame below everything
        input_frame = ttk.Frame(tab_frame)
        input_frame.pack(fill='x', padx=5, pady=(5, 10))
        
        ttk.Label(input_frame, text="From:").grid(row=0, column=0, padx=(0, 5))
        self.ortho_from_var = tk.StringVar()
        from_entry = ttk.Entry(input_frame, textvariable=self.ortho_from_var, width=20)
        from_entry.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Label(input_frame, text="To:").grid(row=0, column=2, padx=(0, 5))
        self.ortho_to_var = tk.StringVar()
        to_entry = ttk.Entry(input_frame, textvariable=self.ortho_to_var, width=20)
        to_entry.grid(row=0, column=3, padx=(0, 10))
        
        add_btn2 = ttk.Button(input_frame, text="Add Row", command=lambda: self._add_ortho_row(tree))
        add_btn2.grid(row=0, column=4, padx=5)
        
        # Bind selection change to populate inputs
        tree.bind('<<TreeviewSelect>>', lambda event: self._on_ortho_select(tree))
        
        # Bind input changes to update selected row
        self.ortho_from_var.trace('w', lambda *args: self._update_ortho_row(tree))
        self.ortho_to_var.trace('w', lambda *args: self._update_ortho_row(tree))
        
        # Bind double-click for editing
        tree.bind('<Double-1>', lambda event: self._edit_tree_item(tree, event))
        
        # Store reference
        self.widgets[category_name] = tree
    
    def _create_phonetic_tab(self, category_name, category_data):
        """Create phonetic tab with list editing"""
        # Create tab
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text=category_name.replace('_', ' ').title())
        
        # Description
        desc_label = ttk.Label(tab_frame, text=f"Edit {category_name} phonetic elements", font=('Arial', 10))
        desc_label.pack(pady=5)
        
        # POS information mapping
        pos_info = {
            'n': {'full': 'Noun', 'desc': 'A person place thing or idea', 'examples': 'dog / happiness / fire', 'sounds': 'Heavy clusters (Kn/Gr/Wr)'},
            'v': {'full': 'Verb', 'desc': 'An action or state of being', 'examples': 'run / exist / burn', 'sounds': 'Sharp percussive (T/P/K)'},
            'a': {'full': 'Adjective', 'desc': 'Descriptive word modifying a noun', 'examples': 'red / loud / soft', 'sounds': 'Breathy fricatives (F/S/H)'},
            'r': {'full': 'Adverb', 'desc': 'Modifies a verb or adjective', 'examples': 'quickly / very', 'sounds': 'Glides/Liquids (J/W/M)'},
            's': {'full': 'Adjective Satellite', 'desc': 'An adjective linked to a specific head word', 'examples': 'wet (linked to dry)', 'sounds': 'Sibilants (Z/S)'},
            'e': {'full': 'Exclamation', 'desc': 'Words expressing sudden emotion', 'examples': 'wow / oh / ouch', 'sounds': 'Breathy/Airy'},
            'k': {'full': 'Conjunction', 'desc': 'Connects words or clauses', 'examples': 'and / but / or', 'sounds': 'Hard Stops (G/K)'},
            'i': {'full': 'Preposition', 'desc': 'Shows relationship between nouns', 'examples': 'in / on / by', 'sounds': 'Labials (B/F/M)'},
            'd': {'full': 'Determiner', 'desc': 'Introduces a noun', 'examples': 'the / a / that', 'sounds': 'Dental Fricatives (Th/D)'},
            'o': {'full': 'Pronoun', 'desc': 'Substitutes for a noun', 'examples': 'he / it / they', 'sounds': 'Soft Air (H/W)'}
        }
        
        # Create scrollable frame for POS categories
        canvas = tk.Canvas(tab_frame)
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create sections for each POS
        self.widgets[category_name] = {}  # Store as dict for POS sub-categories
        
        for sub_key, phonetic_list in category_data.items():
            # Get POS info
            info = pos_info.get(sub_key, {})
            
            # POS section frame
            pos_frame = ttk.LabelFrame(scrollable_frame, text=f"{sub_key.upper()} - {info.get('full', sub_key.upper())}", padding=10)
            pos_frame.pack(fill='x', padx=5, pady=5)
            
            # Add description if available
            if info:
                desc_text = f"{info['desc']} | Examples: {info['examples']} | Sounds: {info['sounds']}"
                desc_label = ttk.Label(pos_frame, text=desc_text, font=('Arial', 9), foreground='gray')
                desc_label.pack(anchor='w', pady=(0, 5))
            
            # Listbox for phonetic elements
            list_frame = ttk.Frame(pos_frame)
            list_frame.pack(fill='x', pady=5)
            
            phonetic_listbox = tk.Listbox(list_frame, height=4)
            phonetic_listbox.pack(side='left', fill='x', expand=True)
            
            # Buttons for this POS
            pos_btn_frame = ttk.Frame(pos_frame)
            pos_btn_frame.pack(fill='x', pady=2)
            
            entry = ttk.Entry(pos_btn_frame, width=30)
            entry.pack(side='left', padx=5, fill='x', expand=True)
            entry.bind('<Return>', lambda e, lb=phonetic_listbox, ent=entry: self._add_phonetic_item(lb, ent))
            
            add_btn = ttk.Button(pos_btn_frame, text="Add", command=lambda lb=phonetic_listbox, ent=entry: self._add_phonetic_item(lb, ent))
            add_btn.pack(side='left', padx=2)
            
            remove_btn = ttk.Button(pos_btn_frame, text="Remove", command=lambda lb=phonetic_listbox: self._remove_phonetic_item(lb))
            remove_btn.pack(side='left', padx=2)
            
            # Store reference
            self.widgets[category_name][sub_key] = phonetic_listbox
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel for scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)
    
    def _add_tree_row(self, tree):
        """Add a new row to treeview"""
        # Get column count
        columns = tree['columns']
        values = ['' for _ in columns]
        tree.insert('', 'end', values=values)
    
    def _remove_tree_row(self, tree):
        """Remove selected row from treeview"""
        selection = tree.selection()
        if selection:
            tree.delete(selection[0])
    
    def _edit_tree_item(self, tree, event):
        """Edit treeview item on double-click"""
        # Get the item and column that was clicked
        item = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        
        if not item:
            return
        
        # Get column index
        if column == '#1':
            col_index = 0
        elif column == '#2':
            col_index = 1
        else:
            return
        
        # Get current value
        values = tree.item(item)['values']
        current_value = values[col_index] if col_index < len(values) else ''
        
        # Create edit window
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Value")
        edit_window.geometry("300x100")
        edit_window.transient(self.root)
        edit_window.grab_set()
        
        # Entry widget
        entry = ttk.Entry(edit_window)
        entry.insert(0, current_value)
        entry.pack(pady=10, padx=10, fill='x', expand=True)
        entry.select_range(0, 'end')
        entry.focus()
        
        def save_edit():
            new_value = entry.get()
            # Update the treeview
            new_values = list(values)
            new_values[col_index] = new_value
            tree.item(item, values=new_values)
            edit_window.destroy()
        
        def cancel_edit():
            edit_window.destroy()
        
        # Buttons
        btn_frame = ttk.Frame(edit_window)
        btn_frame.pack(pady=5)
        
        ttk.Button(btn_frame, text="Save", command=save_edit).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cancel", command=cancel_edit).pack(side='left', padx=5)
        
        # Bind Enter key to save
        entry.bind('<Return>', lambda e: save_edit())
        entry.bind('<Escape>', lambda e: cancel_edit())
    
    def _on_ortho_select(self, tree):
        """Handle selection change in orthography treeview"""
        selection = tree.selection()
        if selection:
            item = selection[0]
            values = tree.item(item)['values']
            if len(values) >= 2:
                self.ortho_from_var.set(values[0])
                self.ortho_to_var.set(values[1])
        else:
            self.ortho_from_var.set("")
            self.ortho_to_var.set("")
    
    def _update_ortho_row(self, tree):
        """Update selected row when input fields change"""
        selection = tree.selection()
        if selection:
            item = selection[0]
            from_val = self.ortho_from_var.get()
            to_val = self.ortho_to_var.get()
            tree.item(item, values=(from_val, to_val))
    
    def _add_ortho_row(self, tree):
        """Add new row using input field values"""
        from_val = self.ortho_from_var.get()
        to_val = self.ortho_to_var.get()
        tree.insert('', 'end', values=(from_val, to_val))
        # Clear inputs after adding
        self.ortho_from_var.set("")
        self.ortho_to_var.set("")
    
    def _add_phonetic_item(self, listbox, entry):
        """Add new phonetic item to listbox"""
        text = entry.get().strip()
        if text:
            listbox.insert('end', text)
            entry.delete(0, 'end')
    
    def _remove_phonetic_item(self, listbox):
        """Remove selected item from listbox"""
        selection = listbox.curselection()
        if selection:
            # Remove from bottom up to avoid index issues
            for idx in reversed(selection):
                listbox.delete(idx)
    
    def _load_data_into_widgets(self):
        """Load data into all widgets"""
        for category_name, widget in self.widgets.items():
            category_data = self.phonetic_data.get(category_name, {})
            
            if category_name == 'constraints':
                # Load constraints into treeview
                for rule in category_data:
                    pattern = rule.get('pattern', '')
                    reason = rule.get('reason', '')
                    widget.insert('', 'end', values=(pattern, reason))
            
            elif category_name == 'orthography':
                # Load orthography into treeview
                for rule in category_data:
                    from_pat = rule.get('from', '')
                    to_pat = rule.get('to', '')
                    widget.insert('', 'end', values=(from_pat, to_pat))
            
            elif isinstance(category_data, dict) and isinstance(widget, dict):
                # Load phonetic data into individual POS listboxes
                for sub_key, phonetic_list in category_data.items():
                    if sub_key in widget:
                        listbox = widget[sub_key]
                        for item in phonetic_list:
                            listbox.insert('end', item)
    
    def _save_data(self):
        """Save all data back to JSON file"""
        try:
            saved_data = {}
            
            # Save constraints
            if 'constraints' in self.widgets:
                constraints = []
                tree = self.widgets['constraints']
                for child in tree.get_children():
                    values = tree.item(child)['values']
                    pattern, reason = values[0], values[1]
                    if pattern:  # Only include non-empty patterns
                        constraints.append({'pattern': pattern, 'reason': reason})
                saved_data['constraints'] = constraints
            
            # Save orthography
            if 'orthography' in self.widgets:
                orthography = []
                tree = self.widgets['orthography']
                for child in tree.get_children():
                    values = tree.item(child)['values']
                    from_pat, to_pat = values[0], values[1]
                    if from_pat:  # Only include non-empty patterns
                        orthography.append({'from': from_pat, 'to': to_pat})
                saved_data['orthography'] = orthography
            
            # Save phonetic categories
            for category_name, widget in self.widgets.items():
                if category_name not in ['constraints', 'orthography'] and isinstance(widget, dict):
                    # Parse individual POS listboxes back into dictionary format
                    category_dict = {}
                    for sub_key, listbox in widget.items():
                        phonetic_list = []
                        for i in range(listbox.size()):
                            item_text = listbox.get(i)
                            if item_text.strip():
                                phonetic_list.append(item_text.strip())
                        if phonetic_list:  # Only include non-empty categories
                            category_dict[sub_key] = phonetic_list
                    saved_data[category_name] = category_dict
            
            # Show save dialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile="phonetic_dictionary.json"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(saved_data, f, indent=2, ensure_ascii=False)
                
                self.status_label.config(text=f"Saved to {os.path.basename(file_path)}")
                messagebox.showinfo("Success", f"Phonetic dictionary saved to:\n{file_path}")
            else:
                self.status_label.config(text="Save cancelled")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error saving file: {str(e)}")
            self.status_label.config(text="Error saving")


def main():
    root = tk.Tk()
    app = PhoneticEditorTk(root)
    root.mainloop()


if __name__ == '__main__':
    main()
