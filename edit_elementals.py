#!/usr/bin/env python3
"""
Elemental Anchors Editor - Dynamic UI for editing elemental anchors dictionary
Creates scrollable interface with Unicode chip inputs for list editing
"""

import json
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.properties import ListProperty, StringProperty, ObjectProperty, NumericProperty
from kivy.uix.filechooser import FileChooserListView


class UnicodeChipInput(StackLayout):
    """Custom widget for editing lists with chip/token input supporting Unicode"""
    
    data_list = ListProperty([])
    hint_text = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'lr-tb'
        self.spacing = [dp(5), dp(5)]
        self.padding = [dp(10), dp(5)]
        self.size_hint_y = None
        self.chip_widgets = {}
        
        # Add text input field
        self.text_input = TextInput(
            hint_text=self.hint_text or 'Enter items separated by commas...',
            size_hint=(None, None),
            size=(dp(150), dp(30)),
            multiline=False,
            font_size='14sp'
        )
        self.text_input.bind(text=self._on_text_change)
        self.add_widget(self.text_input)
        
        # Set initial height after widgets are added
        self.height = dp(40)
        
        # Bind to data_list changes
        self.bind(data_list=self._on_data_list_change)
        
        # Force initial display update after a short delay
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self._on_data_list_change(self, self.data_list), 0.1)
    
    def _on_text_change(self, instance, value):
        """Handle text input changes for comma/Enter detection"""
        if ',' in value or '\n' in value:
            # Split on comma or newline
            items = value.replace('\n', ',').split(',')
            for item in items:
                clean_item = item.strip()
                if clean_item and clean_item not in self.data_list:
                    self.data_list.append(clean_item)
                    self._create_chip(clean_item)
            self.text_input.text = ''
            self._update_height()
    
    def _create_chip(self, text):
        """Create a chip button for the given text"""
        chip = Button(
            text=text,
            size_hint=(None, None),
            size=(dp(len(text) * 8 + 20), dp(25)),
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1),
            font_size='12sp'
        )
        chip.bind(on_press=lambda x: self._remove_chip(text))
        self.chip_widgets[text] = chip
        
        # Insert chip before text input
        self.remove_widget(self.text_input)
        self.add_widget(chip)
        self.add_widget(self.text_input)
    
    def _remove_chip(self, text):
        """Remove chip and update data_list"""
        if text in self.data_list:
            self.data_list.remove(text)
        
        if text in self.chip_widgets:
            chip = self.chip_widgets[text]
            self.remove_widget(chip)
            del self.chip_widgets[text]
        
        self._update_height()
    
    def _on_data_list_change(self, instance, value):
        """Handle external data_list changes"""
        # Clear existing chips
        for chip in list(self.chip_widgets.values()):
            self.remove_widget(chip)
        self.chip_widgets.clear()
        
        # Recreate chips from data_list
        for text in value:
            self._create_chip(text)
        
        self._update_height()
    
    def _update_height(self):
        """Calculate and update widget height based on content"""
        # Calculate total width needed
        total_width = dp(20)  # padding
        current_row_width = 0
        max_row_width = self.width or dp(400)
        row_count = 1
        
        # Add chip widths
        for chip in self.chip_widgets.values():
            chip_width = chip.width + dp(5)  # spacing
            if current_row_width + chip_width > max_row_width:
                row_count += 1
                current_row_width = chip_width
            else:
                current_row_width += chip_width
        
        # Add text input width
        if self.text_input:
            if current_row_width + self.text_input.width > max_row_width:
                row_count += 1
        
        # Calculate new height
        new_height = row_count * dp(35) + dp(10)  # 35px per row + padding
        self.height = max(new_height, dp(40))  # minimum height
    
    def on_size(self, instance, value):
        """Recalculate height when widget is resized"""
        if hasattr(self, 'chip_widgets'):
            self._update_height()


class ElementalsEditorApp(App):
    """Main application for editing elemental anchors dictionary"""
    
    def build(self):
        """Build the main application interface"""
        self.title = "Elemental Anchors Editor"
        
        # Main layout
        main_layout = BoxLayout(orientation='vertical')
        
        # Create main scrollable container
        scroll_view = ScrollView(size_hint=(1, 0.85))
        
        # Create main grid layout for all content
        main_grid = GridLayout(
            cols=1,
            spacing=dp(15),
            padding=dp(15),
            size_hint_y=None
        )
        main_grid.bind(minimum_height=main_grid.setter('height'))
        
        # Load anchors data
        self.anchors_data = self._load_anchors_data()
        self.chip_inputs = {}  # Store references to all chip inputs
        
        # Create sections for each element
        for element_name, element_list in self.anchors_data.items():
            self._create_element_section(element_name, element_list, main_grid)
        
        # Create info box
        info_box = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(50),
            padding=dp(20),
            spacing=dp(10)
        )
        
        info_label = Label(
            text='How to: Click items to delete. Press the comma "," key to enter a new elemental concept.',
            color=(1, 1, 1, 1),  # White color
            font_size='18sp',      # Bigger font size
            bold=True,             # Bold text
            halign='left',
            text_size=(dp(600), None)
        )
        info_box.add_widget(info_label)
        
        # Add save button
        save_button = Button(
            text='Save Elemental Anchors',
            size_hint=(1, None),
            height=dp(50),
            background_color=(0.2, 0.8, 0.2, 1)
        )
        save_button.bind(on_press=self._save_anchors_data)
        
        scroll_view.add_widget(main_grid)
        
        # Assemble main layout
        main_layout.add_widget(scroll_view)
        main_layout.add_widget(info_box)
        main_layout.add_widget(save_button)
        
        return main_layout
    
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
    
    def _create_element_section(self, element_name, element_list, main_grid):
        """Create a section with title and inputs for an elemental category"""
        # Create section title with element-appropriate color
        element_colors = {
            'air': (0.5, 0.7, 1.0, 1),      # Light blue
            'water': (0.2, 0.5, 0.8, 1),     # Blue
            'earth': (0.6, 0.4, 0.2, 1),     # Brown
            'fire': (1.0, 0.3, 0.2, 1)        # Red-orange
        }
        
        color = element_colors.get(element_name.lower(), (0.3, 0.3, 0.3, 1))
        
        section_title = Label(
            text=f"=== {element_name.upper()} ===",
            size_hint=(1, None),
            height=dp(40),
            font_size='20sp',
            bold=True,
            color=color,
            halign='center',
            text_size=(dp(600), None)
        )
        main_grid.add_widget(section_title)
        
        # Create section separator line using Labels
        separator = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(2),
            spacing=dp(10)
        )
        left_line = Label(text='', color=color, size_hint=(0.4, 1))
        right_line = Label(text='', color=color, size_hint=(0.4, 1))
        separator.add_widget(left_line)
        separator.add_widget(right_line)
        main_grid.add_widget(separator)
        
        # Create chip input for this element
        chip_input = UnicodeChipInput(
            hint_text=f"Enter {element_name} elemental concepts...",
            data_list=list(element_list) if element_list else []
        )
        main_grid.add_widget(chip_input)
        
        # Store reference for saving
        self.chip_inputs[element_name] = chip_input
    
    def _save_anchors_data(self, instance):
        """Show file dialog and save current anchors data to selected file"""
        self._show_save_dialog()
    
    def _show_save_dialog(self):
        """Show file save dialog"""
        # Create file chooser
        filechooser = FileChooserListView(
            path=os.getcwd(),
            filters=['*.json'],
            show_hidden=False
        )
        
        # Create filename input
        filename_input = TextInput(
            text='custom_anchors.json',
            size_hint=(1, None),
            height=dp(40),
            multiline=False,
            hint_text='Enter filename...'
        )
        
        # Bind file selection to update input field
        filechooser.bind(selection=lambda instance, selection: self._on_file_selected(selection, filename_input))
        
        # Create dialog layout
        dialog_layout = BoxLayout(orientation='vertical', spacing=dp(10))
        dialog_layout.add_widget(Label(text='Choose location and filename:', size_hint=(1, None), height=dp(30)))
        dialog_layout.add_widget(filechooser)
        dialog_layout.add_widget(filename_input)
        
        # Create buttons
        button_layout = BoxLayout(size_hint=(1, None), height=dp(50), spacing=dp(10))
        save_button = Button(text='Save', background_color=(0.2, 0.8, 0.2, 1))
        cancel_button = Button(text='Cancel', background_color=(0.8, 0.2, 0.2, 1))
        button_layout.add_widget(save_button)
        button_layout.add_widget(cancel_button)
        dialog_layout.add_widget(button_layout)
        
        # Create popup
        popup = Popup(
            title='Save Elemental Anchors',
            content=dialog_layout,
            size_hint=(0.9, 0.8),
            auto_dismiss=False
        )
        
        # Bind buttons
        save_button.bind(on_press=lambda x: self._perform_save(filechooser.path, filename_input.text, popup))
        cancel_button.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def _perform_save(self, directory, filename, popup):
        """Actually save the data to the specified JSON file"""
        try:
            # Ensure filename has .json extension
            if not filename.endswith('.json'):
                filename += '.json'
            
            # Create full filepath
            filepath = os.path.join(directory, filename)
            
            # Reconstruct dictionary from chip inputs
            saved_anchors = {}
            
            for element_name, chip_input in self.chip_inputs.items():
                saved_anchors[element_name] = chip_input.data_list
            
            # Save as JSON file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(saved_anchors, f, indent=2, ensure_ascii=False)
            
            # Close save dialog
            popup.dismiss()
            
            # Show success message
            self._show_message_popup('Success', f'Elemental anchors saved to:\n{os.path.basename(filepath)}')
            
        except Exception as e:
            print(f"Error saving elemental anchors: {e}")
            # Show error message
            self._show_message_popup('Error', f'Error saving: {str(e)}')
    
    def _on_file_selected(self, selection, filename_input):
        """Handle file selection in file chooser"""
        if selection:
            # Get the selected file path
            selected_file = selection[0]
            # Update the filename input with just the filename
            filename_input.text = os.path.basename(selected_file)
    
    def _show_message_popup(self, title, message):
        """Show a simple message popup"""
        popup_content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        popup_content.add_widget(Label(text=message))
        
        close_button = Button(text='Close', size_hint=(1, None), height=dp(40))
        popup_content.add_widget(close_button)
        
        popup = Popup(
            title=title,
            content=popup_content,
            size_hint=(0.8, 0.4),
            auto_dismiss=False
        )
        close_button.bind(on_press=popup.dismiss)
        popup.open()


if __name__ == '__main__':
    ElementalsEditorApp().run()
