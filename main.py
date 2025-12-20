#!/usr/bin/env python3
"""
Main Application - Central hub for conlang development tools
Provides interface for editing elements, phonetics, and building dictionaries
"""

import os
import subprocess
import sys
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.clock import Clock


class MainApp(App):
    """Main application for conlang development tools"""
    
    def build(self):
        """Build the main application interface"""
        self.title = "Conlang Development Studio"
        
        # Main layout
        main_layout = BoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(15)
        )
        
        # Title
        title_label = Label(
            text="Conlang Development Studio",
            font_size='24sp',
            bold=True,
            size_hint=(1, None),
            height=dp(60),
            color=(0.2, 0.4, 0.8, 1)
        )
        main_layout.add_widget(title_label)
        
        # Language Name input section
        name_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(50),
            spacing=dp(10)
        )
        
        name_label = Label(
            text="Language Name:",
            size_hint=(0.3, 1),
            font_size='16sp',
            bold=True,
            halign='right',
            text_size=(None, None)
        )
        
        self.language_name_input = TextInput(
            text="MyConlang",
            size_hint=(0.7, 1),
            font_size='16sp',
            multiline=False,
            hint_text="Enter your language name..."
        )
        
        name_layout.add_widget(name_label)
        name_layout.add_widget(self.language_name_input)
        main_layout.add_widget(name_layout)
        
        # Button grid layout
        button_grid = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(200),
            spacing=dp(10)
        )
        
        # Row 1: Edit Elements and Edit Phonetics
        row1 = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(90),
            spacing=dp(10)
        )
        
        edit_elements_btn = Button(
            text="Edit Elements",
            size_hint=(1, 1),
            background_color=(0.3, 0.6, 0.9, 1),
            color=(1, 1, 1, 1),
            font_size='16sp',
            bold=True
        )
        edit_elements_btn.bind(on_press=self.launch_edit_elements)
        
        edit_phonetics_btn = Button(
            text="Edit Phonetics",
            size_hint=(1, 1),
            background_color=(0.6, 0.3, 0.9, 1),
            color=(1, 1, 1, 1),
            font_size='16sp',
            bold=True
        )
        edit_phonetics_btn.bind(on_press=self.launch_edit_phonetics)
        
        row1.add_widget(edit_elements_btn)
        row1.add_widget(edit_phonetics_btn)
        
        # Row 2: Build Elemental and Build Words
        row2 = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(90),
            spacing=dp(10)
        )
        
        build_elemental_btn = Button(
            text="Build Elemental",
            size_hint=(1, 1),
            background_color=(0.9, 0.6, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size='16sp',
            bold=True
        )
        build_elemental_btn.bind(on_press=self.launch_build_elemental)
        
        build_words_btn = Button(
            text="Build Words",
            size_hint=(1, 1),
            background_color=(0.3, 0.9, 0.6, 1),
            color=(1, 1, 1, 1),
            font_size='16sp',
            bold=True
        )
        build_words_btn.bind(on_press=self.launch_build_words)
        
        row2.add_widget(build_elemental_btn)
        row2.add_widget(build_words_btn)
        
        button_grid.add_widget(row1)
        button_grid.add_widget(row2)
        main_layout.add_widget(button_grid)
        
        # Status label
        self.status_label = Label(
            text="Ready to start building your conlang!",
            size_hint=(1, None),
            height=dp(30),
            font_size='14sp',
            color=(0.5, 0.5, 0.5, 1),
            halign='center',
            text_size=(dp(400), None)
        )
        main_layout.add_widget(self.status_label)
        
        return main_layout
    
    def launch_edit_elements(self, instance):
        """Launch the elements editor"""
        self.status_label.text = "Launching Elements Editor..."
        try:
            # Launch edit_elementals.py in a new process
            subprocess.Popen([sys.executable, 'edit_elementals.py'])
            Clock.schedule_once(lambda dt: self._update_status("Elements Editor launched"), 1)
        except Exception as e:
            self._show_error_popup("Error", f"Failed to launch Elements Editor:\n{str(e)}")
            self.status_label.text = "Ready to start building your conlang!"
    
    def launch_edit_phonetics(self, instance):
        """Launch the phonetics editor"""
        self.status_label.text = "Launching Phonetics Editor..."
        try:
            # Launch edit_phonetic.py in a new process
            subprocess.Popen([sys.executable, 'edit_phonetic.py'])
            Clock.schedule_once(lambda dt: self._update_status("Phonetics Editor launched"), 1)
        except Exception as e:
            self._show_error_popup("Error", f"Failed to launch Phonetics Editor:\n{str(e)}")
            self.status_label.text = "Ready to start building your conlang!"
    
    def launch_build_elemental(self, instance):
        """Launch the elemental dictionary builder"""
        language_name = self.language_name_input.text.strip()
        if not language_name:
            self._show_error_popup("Error", "Please enter a language name first!")
            return
        
        self.status_label.text = "Building Elemental Dictionary..."
        
        # Check for custom anchors file
        anchors_file = f"{language_name.lower()}_anchors.json"
        if os.path.exists(anchors_file):
            # Use custom anchors
            try:
                cmd = [sys.executable, 'build_elemental_dictionary.py', 
                       '--anchor', anchors_file, 
                       '--output', f'{language_name.lower()}_elemental.json']
                subprocess.Popen(cmd)
                Clock.schedule_once(lambda dt: self._update_status(f"Building elemental dictionary for {language_name}..."), 1)
            except Exception as e:
                self._show_error_popup("Error", f"Failed to build elemental dictionary:\n{str(e)}")
                self.status_label.text = "Ready to start building your conlang!"
        else:
            # Use default anchors
            try:
                cmd = [sys.executable, 'build_elemental_dictionary.py', 
                       '--output', f'{language_name.lower()}_elemental.json']
                subprocess.Popen(cmd)
                Clock.schedule_once(lambda dt: self._update_status(f"Building elemental dictionary for {language_name}..."), 1)
            except Exception as e:
                self._show_error_popup("Error", f"Failed to build elemental dictionary:\n{str(e)}")
                self.status_label.text = "Ready to start building your conlang!"
    
    def launch_build_words(self, instance):
        """Launch the word generator"""
        language_name = self.language_name_input.text.strip()
        if not language_name:
            self._show_error_popup("Error", "Please enter a language name first!")
            return
        
        # Check for elemental dictionary
        elemental_file = f"{language_name.lower()}_elemental.json"
        if not os.path.exists(elemental_file):
            self._show_error_popup("Error", f"Elemental dictionary not found: {elemental_file}\nPlease run 'Build Elemental' first!")
            return
        
        self.status_label.text = "Building Word Dictionary..."
        
        try:
            # Launch logo_gene.py (assuming it takes the elemental dictionary as input)
            cmd = [sys.executable, 'logo_gene.py', 
                   '--input', elemental_file,
                   '--output', f'{language_name.lower()}_words.json']
            subprocess.Popen(cmd)
            Clock.schedule_once(lambda dt: self._update_status(f"Building word dictionary for {language_name}..."), 1)
        except Exception as e:
            self._show_error_popup("Error", f"Failed to build word dictionary:\n{str(e)}")
            self.status_label.text = "Ready to start building your conlang!"
    
    def _update_status(self, message):
        """Update status label"""
        self.status_label.text = message
        # Reset status after 3 seconds
        Clock.schedule_once(lambda dt: self._reset_status(), 3)
    
    def _reset_status(self):
        """Reset status to default"""
        self.status_label.text = "Ready to start building your conlang!"
    
    def _show_error_popup(self, title, message):
        """Show an error popup"""
        popup_content = BoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(10)
        )
        
        error_label = Label(
            text=message,
            size_hint=(1, None),
            height=dp(100),
            halign='center',
            text_size=(dp(300), None)
        )
        
        close_button = Button(
            text='Close',
            size_hint=(1, None),
            height=dp(40),
            background_color=(0.8, 0.2, 0.2, 1),
            color=(1, 1, 1, 1)
        )
        
        popup_content.add_widget(error_label)
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
    MainApp().run()
