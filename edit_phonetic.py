#!/usr/bin/env python3
"""
Phonetic Editor - Dynamic UI for editing phonetic dictionary JSON
Creates TabbedPanel interface with Unicode chip inputs for list editing
"""

import json
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
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


class PhoneticEditorApp(App):
    """Main application for editing phonetic dictionary"""
    
    def build(self):
        """Build the main application interface"""
        self.title = "Phonetic Dictionary Editor"
        
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
        
        # Load JSON data
        self.phonetic_data = self._load_phonetic_data()
        self.chip_inputs = {}  # Store references to all chip inputs
        
        # Create sections for each category
        for category_name, category_data in self.phonetic_data.items():
            self._create_category_section(category_name, category_data, main_grid)
        
        # Create info box
        info_box = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(50),
            padding=dp(20),
            spacing=dp(10)
        )
        
        info_label = Label(
            text='How to: Click items to delete.  Press the comma "," key to enter a new phoneme.',
            color=(1, 1, 1, 1),  # White color
            font_size='18sp',      # Bigger font size
            bold=True,             # Bold text
            halign='left',
            text_size=(dp(600), None)
        )
        info_box.add_widget(info_label)
        
        # Add save button
        save_button = Button(
            text='Save Phonetic Dictionary',
            size_hint=(1, None),
            height=dp(50),
            background_color=(0.2, 0.8, 0.2, 1)
        )
        save_button.bind(on_press=self._save_phonetic_data)
        
        scroll_view.add_widget(main_grid)
        
        # Assemble main layout
        main_layout.add_widget(scroll_view)
        main_layout.add_widget(info_box)
        main_layout.add_widget(save_button)
        
        return main_layout
    
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
    
    def _create_category_section(self, category_name, category_data, main_grid):
        """Create a section with title and inputs for a phonetic category"""
        # Create section title
        section_title = Label(
            text=f"=== {category_name.replace('_', ' ').upper()} ===",
            size_hint=(1, None),
            height=dp(40),
            font_size='20sp',
            bold=True,
            color=(0.1, 0.3, 0.8, 1),
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
        left_line = Label(text='', color=(0.2, 0.2, 0.2, 1), size_hint=(0.4, 1))
        right_line = Label(text='', color=(0.2, 0.2, 0.2, 1), size_hint=(0.4, 1))
        separator.add_widget(left_line)
        separator.add_widget(right_line)
        main_grid.add_widget(separator)
        
        # Create chip inputs for each sub-key
        for sub_key, phonetic_list in category_data.items():
            # Create label for sub-key
            label = Label(
                text=f"{sub_key}:",
                size_hint=(1, None),
                height=dp(30),
                font_size='16sp',
                bold=True,
                halign='left',
                text_size=(dp(400), None),
                color=(0.2, 0.2, 0.2, 1)
            )
            main_grid.add_widget(label)
            
            # Create chip input
            chip_input = UnicodeChipInput(
                hint_text=f"Enter {sub_key} phonetics...",
                data_list=list(phonetic_list) if phonetic_list else []
            )
            main_grid.add_widget(chip_input)
            
            # Store reference for saving
            self.chip_inputs[f"{category_name}.{sub_key}"] = chip_input
    
        
    def _save_phonetic_data(self, instance):
        """Show file dialog and save current phonetic data to selected file"""
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
            text='phonetic_dictionary.json',
            size_hint=(1, None),
            height=dp(40),
            multiline=False,
            hint_text='Enter filename...'
        )
        
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
            title='Save Phonetic Dictionary',
            content=dialog_layout,
            size_hint=(0.9, 0.8),
            auto_dismiss=False
        )
        
        # Bind buttons
        save_button.bind(on_press=lambda x: self._perform_save(filechooser.path, filename_input.text, popup))
        cancel_button.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def _perform_save(self, directory, filename, popup):
        """Actually save the data to the specified file"""
        try:
            # Ensure filename has .json extension
            if not filename.endswith('.json'):
                filename += '.json'
            
            # Create full filepath
            filepath = os.path.join(directory, filename)
            
            # Reconstruct dictionary from chip inputs
            saved_data = {}
            
            for key, chip_input in self.chip_inputs.items():
                category_name, sub_key = key.split('.', 1)
                
                if category_name not in saved_data:
                    saved_data[category_name] = {}
                
                saved_data[category_name][sub_key] = chip_input.data_list
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(saved_data, f, indent=2, ensure_ascii=False)
            
            # Close save dialog
            popup.dismiss()
            
            # Show success message
            self._show_message_popup('Success', f'Phonetic dictionary saved to:\n{os.path.basename(filepath)}')
            
        except Exception as e:
            print(f"Error saving phonetic dictionary: {e}")
            # Show error message
            self._show_message_popup('Error', f'Error saving: {str(e)}')
    
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
    PhoneticEditorApp().run()
