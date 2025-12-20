#!/usr/bin/env python3
"""
Components Anchors Editor - Tkinter version for better components editing
Creates a clean interface for editing components anchors JSON with proper tables
"""

import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os


class ComponentsEditorTk:
    def __init__(self, root):
        self.root = root
        self.root.title("Components Anchors Editor")
        self.root.geometry("800x600")
        
        # Load data
        self.anchors_data = self._load_anchors_data()
        
        # Create main interface
        self._create_main_interface()
        
        # Load data into widgets
        self._load_data_into_widgets()
    
    def _load_anchors_data(self):
        """Load components anchors dictionary from JSON file"""
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
            
            print(f"Loaded and saved anchors dictionary with {len(anchors_dict)} components")
            return anchors_dict
            
        except FileNotFoundError:
            print("Error: build_elemental_dictionary.py not found")
            return {}
        except Exception as e:
            print(f"Error parsing anchors dictionary: {e}")
            return {}
    
    def _create_main_interface(self):
        """Create the main interface with notebook for tabs and controls"""
        # Controls to manage components (add/rename/remove)
        ctrl_frame = ttk.Frame(self.root)
        ctrl_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(ctrl_frame, text="Components:").pack(side='left', padx=5)
        self.component_name_entry = ttk.Entry(ctrl_frame, width=30)
        self.component_name_entry.pack(side='left', padx=5)

        add_comp_btn = ttk.Button(ctrl_frame, text="Add Component", command=self._add_component)
        add_comp_btn.pack(side='left', padx=5)

        rename_comp_btn = ttk.Button(ctrl_frame, text="Rename Selected", command=self._rename_selected_component)
        rename_comp_btn.pack(side='left', padx=5)

        remove_comp_btn = ttk.Button(ctrl_frame, text="Remove Selected", command=self._remove_selected_component)
        remove_comp_btn.pack(side='left', padx=5)

        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create tabs for each element
        self.widgets = {}
        self.tab_to_component = {}
        
        for component_name, component_list in self.anchors_data.items():
            self._create_component_tab(component_name, component_list)
        
        # Add save button at bottom
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        save_btn = ttk.Button(button_frame, text="Save Components Anchors", command=self._save_data)
        save_btn.pack(side='right', padx=5)
        
        # Status label
        self.status_label = ttk.Label(button_frame, text="Ready")
        self.status_label.pack(side='left', padx=5)
    
    def _create_component_tab(self, component_name, component_list):
        """Create component tab with list editing"""
        # Create tab
        tab_frame = ttk.Frame(self.notebook)
        
        # Create styled tab with color
        self.notebook.add(tab_frame, text=component_name.upper())
        self.tab_to_component[str(tab_frame)] = component_name
        
        # Description
        desc_frame = ttk.Frame(tab_frame)
        desc_frame.pack(fill='x', pady=5)
        
        # Component title
        title_label = ttk.Label(desc_frame, text=f"=== {component_name.upper()} ===", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=5)
        
        # Component description
        desc_text = f"Edit {component_name} component concepts and anchors"
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
        
        entry_label = ttk.Label(entry_frame, text=f"Add {component_name} concept:")
        entry_label.pack(side='left', padx=5)
        
        entry = ttk.Entry(entry_frame, width=50)
        entry.pack(side='left', padx=5, fill='x', expand=True)
        entry.bind('<Return>', lambda e: self._add_list_item(listbox, entry))
        
        add_btn = ttk.Button(entry_frame, text="Add", command=lambda: self._add_list_item(listbox, entry))
        add_btn.pack(side='left', padx=5)
        
        remove_btn = ttk.Button(entry_frame, text="Remove Selected", command=lambda: self._remove_list_item(listbox))
        remove_btn.pack(side='left', padx=5)
        
        # Store reference
        self.widgets[component_name] = listbox
        # Populate initial items
        for item in component_list:
            listbox.insert('end', item)
    
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
        for component_name, widget in self.widgets.items():
            # Items are now loaded when tabs are created; keep method for compatibility
            pass
    
    def _save_data(self):
        """Save all data back to JSON file"""
        try:
            saved_data = {}
            
            # Save components categories
            for component_name, widget in self.widgets.items():
                component_list = []
                for i in range(widget.size()):
                    item_text = widget.get(i)
                    if item_text.strip():
                        component_list.append(item_text.strip())
                saved_data[component_name] = component_list
            
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
                messagebox.showinfo("Success", f"Components anchors saved to:\n{file_path}")
            else:
                self.status_label.config(text="Save cancelled")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error saving file: {str(e)}")
            self.status_label.config(text="Error saving")

    # Components management methods
    def _add_component(self):
        name = self.component_name_entry.get().strip()
        if not name:
            messagebox.showwarning("Add Component", "Please enter a component name.")
            return
        if name in self.widgets:
            messagebox.showwarning("Add Component", "Component already exists.")
            return
        # Create new tab and data entry
        self.anchors_data[name] = []
        self._create_component_tab(name, [])
        self.component_name_entry.delete(0, 'end')
        # Select the new tab
        tabs = self.notebook.tabs()
        if tabs:
            self.notebook.select(tabs[-1])
        self.status_label.config(text=f"Added component '{name}'")

    def _rename_selected_component(self):
        current_tab = self.notebook.select()
        if not current_tab:
            messagebox.showwarning("Rename Component", "No component tab selected.")
            return
        old_name = self.tab_to_component.get(current_tab)
        if not old_name:
            messagebox.showwarning("Rename Component", "Could not determine selected component.")
            return
        new_name = simpledialog.askstring("Rename Component", f"Rename '{old_name}' to:")
        if not new_name:
            return
        new_name = new_name.strip()
        if not new_name:
            return
        if new_name in self.widgets and new_name != old_name:
            messagebox.showwarning("Rename Component", "A component with that name already exists.")
            return
        # Update mappings and UI
        widget = self.widgets.pop(old_name)
        self.widgets[new_name] = widget
        if old_name in self.anchors_data:
            self.anchors_data[new_name] = self.anchors_data.pop(old_name)
        self.tab_to_component[current_tab] = new_name
        self.notebook.tab(current_tab, text=new_name.upper())
        # Update title label in the tab
        tab_widget = self.root.nametowidget(current_tab)
        # First child is desc_frame; its first child is title_label
        try:
            desc_frame = tab_widget.winfo_children()[0]
            title_label = desc_frame.winfo_children()[0]
            title_label.config(text=f"=== {new_name.upper()} ===")
            # Update description label (second child)
            desc_label = desc_frame.winfo_children()[1]
            desc_label.config(text=f"Edit {new_name} component concepts and anchors")
        except Exception:
            pass
        self.status_label.config(text=f"Renamed component to '{new_name}'")

    def _remove_selected_component(self):
        current_tab = self.notebook.select()
        if not current_tab:
            messagebox.showwarning("Remove Component", "No component tab selected.")
            return
        name = self.tab_to_component.get(current_tab)
        if not name:
            messagebox.showwarning("Remove Component", "Could not determine selected component.")
            return
        if not messagebox.askyesno("Remove Component", f"Remove component '{name}'? This cannot be undone."):
            return
        # Remove tab and data
        self.notebook.forget(current_tab)
        try:
            self.root.nametowidget(current_tab).destroy()
        except Exception:
            pass
        self.tab_to_component.pop(current_tab, None)
        self.widgets.pop(name, None)
        self.anchors_data.pop(name, None)
        self.status_label.config(text=f"Removed component '{name}'")


def main():
    root = tk.Tk()
    app = ComponentsEditorTk(root)
    root.mainloop()


if __name__ == '__main__':
    main()
