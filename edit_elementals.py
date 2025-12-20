#!/usr/bin/env python3
"""
Elemental Anchors Editor - Tkinter version for better elemental editing
Creates a clean interface for editing elemental anchors JSON with proper tables
"""

import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os


class ElementalsEditorTk:
    def __init__(self, root):
        self.root = root
        self.root.title("Elemental Anchors Editor")
        self.root.geometry("800x600")
        
        # Load data
        self.anchors_data = self._load_anchors_data()
        
        # Create main interface
        self._create_main_interface()
        
        # Load data into widgets
        self._load_data_into_widgets()
    
    def _load_anchors_data(self):
        """Load elemental anchors dictionary from JSON file"""
        try:
            # Try to load from a default anchors JSON file first
            default_file = 'default_anchors.json'
            if os.path.exists(default_file):
                with open(default_file, 'r', encoding='utf-8') as f:
                    anchors_dict = json.load(f)
                print(f"Loaded anchors dictionary from {default_file}")
                return anchors_dict
            
            # If default doesn't exist, try to extract from build_elemental_dictionary.py and save as JSON
            with open('build_elemental_dictionary.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract the anchors dictionary using a simple approach
            # Look for the anchors dictionary definition
            anchors_start = content.find('anchors =')
            if anchors_start == -1:
                print("Error: anchors dictionary not found in build_elemental_dictionary.py")
                return {}
            
            # Find the opening brace
            brace_start = content.find('{', anchors_start)
            if brace_start == -1:
                print("Error: anchors dictionary format not found")
                return {}
            
            # Find the matching closing brace (simple approach - count braces)
            brace_count = 1
            pos = brace_start + 1
            while pos < len(content) and brace_count > 0:
                if content[pos] == '{':
                    brace_count += 1
                elif content[pos] == '}':
                    brace_count -= 1
                pos += 1
            
            if brace_count != 0:
                print("Error: Could not parse anchors dictionary")
                return {}
            
            # Extract the dictionary string
            anchors_str = content[brace_start:pos]
            
            # Evaluate the dictionary string safely
            anchors_dict = eval(anchors_str)
            
            # Save as default JSON file for future use
            with open(default_file, 'w', encoding='utf-8') as f:
                json.dump(anchors_dict, f, indent=2, ensure_ascii=False)
            
            print(f"Loaded and saved anchors dictionary with {len(anchors_dict)} elements")
            return anchors_dict
            
        except FileNotFoundError:
            print("Error: build_elemental_dictionary.py not found")
            return {}
        except Exception as e:
            print(f"Error parsing anchors dictionary: {e}")
            return {}
    
    def _create_main_interface(self):
        """Create the main interface with notebook for tabs"""
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create tabs for each element
        self.widgets = {}
        
        for element_name, element_list in self.anchors_data.items():
            self._create_element_tab(element_name, element_list)
        
        # Add save button at bottom
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        save_btn = ttk.Button(button_frame, text="Save Elemental Anchors", command=self._save_data)
        save_btn.pack(side='right', padx=5)
        
        # Status label
        self.status_label = ttk.Label(button_frame, text="Ready")
        self.status_label.pack(side='left', padx=5)
    
    def _create_element_tab(self, element_name, element_list):
        """Create element tab with list editing"""
        # Create tab
        tab_frame = ttk.Frame(self.notebook)
        
        # Element-appropriate colors for styling
        element_colors = {
            'air': '#87CEEB',      # Light blue
            'water': '#4169E1',    # Blue
            'earth': '#8B4513',    # Brown
            'fire': '#FF4500'       # Red-orange
        }
        
        color = element_colors.get(element_name.lower(), '#808080')
        
        # Create styled tab with color
        self.notebook.add(tab_frame, text=element_name.upper())
        
        # Description with element-specific styling
        desc_frame = ttk.Frame(tab_frame)
        desc_frame.pack(fill='x', pady=5)
        
        # Element title
        title_label = ttk.Label(desc_frame, text=f"=== {element_name.upper()} ===", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=5)
        
        # Element description
        desc_text = f"Edit {element_name} elemental concepts and anchors"
        desc_label = ttk.Label(desc_frame, text=desc_text, font=('Arial', 10))
        desc_label.pack(pady=2)
        
        # Create listbox with scrollbar
        list_frame = ttk.Frame(tab_frame)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Entry for adding new items
        entry_frame = ttk.Frame(tab_frame)
        entry_frame.pack(fill='x', padx=5, pady=5)
        
        entry_label = ttk.Label(entry_frame, text=f"Add {element_name} concept:")
        entry_label.pack(side='left', padx=5)
        
        entry = ttk.Entry(entry_frame, width=50)
        entry.pack(side='left', padx=5, fill='x', expand=True)
        entry.bind('<Return>', lambda e: self._add_list_item(listbox, entry))
        
        add_btn = ttk.Button(entry_frame, text="Add", command=lambda: self._add_list_item(listbox, entry))
        add_btn.pack(side='left', padx=5)
        
        remove_btn = ttk.Button(entry_frame, text="Remove Selected", command=lambda: self._remove_list_item(listbox))
        remove_btn.pack(side='left', padx=5)
        
        # Store reference
        self.widgets[element_name] = listbox
    
    def _add_list_item(self, listbox, entry):
        """Add new item to listbox"""
        text = entry.get().strip()
        if text:
            listbox.insert('end', text)
            entry.delete(0, 'end')
    
    def _remove_list_item(self, listbox):
        """Remove selected item from listbox"""
        selection = listbox.curselection()
        if selection:
            # Remove from bottom up to avoid index issues
            for idx in reversed(selection):
                listbox.delete(idx)
    
    def _load_data_into_widgets(self):
        """Load data into all widgets"""
        for element_name, widget in self.widgets.items():
            element_list = self.anchors_data.get(element_name, [])
            for item in element_list:
                widget.insert('end', item)
    
    def _save_data(self):
        """Save all data back to JSON file"""
        try:
            saved_data = {}
            
            # Save elemental categories
            for element_name, widget in self.widgets.items():
                element_list = []
                for i in range(widget.size()):
                    item_text = widget.get(i)
                    if item_text.strip():
                        element_list.append(item_text.strip())
                saved_data[element_name] = element_list
            
            # Show save dialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile="custom_anchors.json"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(saved_data, f, indent=2, ensure_ascii=False)
                
                self.status_label.config(text=f"Saved to {os.path.basename(file_path)}")
                messagebox.showinfo("Success", f"Elemental anchors saved to:\n{file_path}")
            else:
                self.status_label.config(text="Save cancelled")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error saving file: {str(e)}")
            self.status_label.config(text="Error saving")


def main():
    root = tk.Tk()
    app = ElementalsEditorTk(root)
    root.mainloop()


if __name__ == '__main__':
    main()
