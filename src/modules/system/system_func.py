import functools
import logging
import os
import subprocess
import pyautogui
from pathlib import Path
from shutil import copy2
import shutil 
import webbrowser
from modules.base_func import BaseAutomationModule # Ensure this is imported

# Decorator for safe execution and uniform error handling
def safe_action(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            logging.error(f"Error in {func.__name__}:", exc_info=True)
            return f"[FAIL] Failed to {func.__name__.replace('_', ' ')}."
    return wrapper

class SystemAutomation(BaseAutomationModule):
    """
    Provides basic OS automation: file management, application launch,
    mouse and keyboard control via pyautogui.
    """

    def __init__(self):
        pyautogui.FAILSAFE = True  # Move mouse to top-left corner to abort

    def get_description(self) -> str:
        """
        Returns a brief description of the module's capabilities for the LLM's conversational context.
        """
        return "perform system automation tasks such as listing, creating, reading, writing, moving, and deleting files and folders, launching applications, and controlling mouse and keyboard"

    def get_supported_actions(self) -> dict:
        """
        Maps action names (from LLM intent) to internal method names, descriptions, and examples.
        """
        return {
            "create_folder": {
                "method_name": "create_folder",
                "description": "Creates a new folder at the specified path.",
                "example_json": '{"action":"create_folder","folder":"DIRECTORY"}'
            },
            "create_file": {
                "method_name": "create_file",
                "description": "Creates a new file at the specified path. Optionally, include content to write immediately.",
                "example_json": '{"action":"create_file","filename":"DIRECTORY/FILENAME","content":"Optional text"}'
            },
            "write_file": { 
                "method_name": "write_file",
                "description": "Writes content to an existing file.",
                "example_json": '{"action":"write_file","filename":"mylog.txt","content":"New log entry."}'
            },
            "read_file": {
                "method_name": "read_file",
                "description": "Reads and returns the text content of a specified file.",
                "example_json": '{"action":"read_file","filename":"my_document.txt"}'
            },
            "delete_file": {
                "method_name": "delete_file",
                "description": "Deletes a file.",
                "example_json": '{"action":"delete_file","filename":"FILENAME"}'
            },
            "delete_folder": {
                "method_name": "delete_folder",
                "description": "Deletes a folder and its contents.",
                "example_json": '{"action":"delete_folder","folder":"DIRECTORY"}'
            },
            "list_directory": {
                "method_name": "list_directory",
                "description": "Lists the contents (files and subfolders) of a specified **directory**.",
                "example_json": '{"action":"list_directory","directory":"my_folder"}'
            },
            "rename_file": {
                "method_name": "rename_file",
                "description": "Renames a file.",
                "example_json": '{"action":"rename_file","src":"old_name.txt","dest":"new_name.txt"}'
            },
            "copy_file": {
                "method_name": "copy_file",
                "description": "Copies a file from source to destination.",
                "example_json": '{"action":"copy_file","src":"source.txt","dest":"destination/copy.txt"}'
            },
            "move_file": {
                "method_name": "move_file",
                "description": "Moves a file from source to destination.",
                "example_json": '{"action":"move_file","src":"source.txt","dest":"destination/moved.txt"}'
            },
            "open_application": {
                "method_name": "open_application",
                "description": "Opens an application by its full path or common name. On Windows, it tries to find the executable in PATH or uses shell execution.",
                "example_json": '{"action":"open_application","path":"notepad.exe"}' 
            },
            "move_mouse": {
                "method_name": "move_mouse",
                "description": "Moves the mouse cursor to specific X and Y coordinates.",
                "example_json": '{"action":"move_mouse","x":100,"y":200}'
            },
            "click": {
                "method_name": "click",
                "description": "Performs a mouse click at the current cursor position or specified coordinates.",
                "example_json": '{"action":"click"}'
            },
            "type_text": {
                "method_name": "type_text",
                "description": "Types the specified text using the keyboard.",
                "example_json": '{"action":"type_text","text":"Hello World"}'
            },
            "press_key": {
                "method_name": "press_key",
                "description": "Presses a specific keyboard key (e.g., 'enter', 'esc', 'alt').",
                "example_json": '{"action":"press_key","key":"enter"}'
            },
            "open_webpage": {
                "method_name": "open_webpage",
                "description": "Opens a web page in the default browser.",
                "example_json": '{"action":"open_webpage","url":"https://www.google.com"}'
            }
        }

    # --- File Management ---
    @safe_action
    def create_folder(self, folder: str) -> str:
        folder_path = Path(folder)
        absolute_path = folder_path.absolute()
        if folder_path.exists():
            return f"Folder already exists and was not created: '{absolute_path}'"
        
        folder_path.mkdir(parents=True, exist_ok=True)
        return f"Folder successfully created at: '{absolute_path}'"

    @safe_action
    def create_file(self, filename: str, content: str = None) -> str:
        """Create a new file, optionally writing initial content."""
        file_path = Path(filename)
        absolute_path = file_path.absolute()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            if content:
                f.write(content)

        if content:
            return f"File created at: '{absolute_path}'\nInitial content written:\n---\n{content}\n---"
        
        return f"Empty file created at: '{absolute_path}'"

    @safe_action
    def write_file(self, filename: str, content: str) -> str:
        """Write text to an existing file."""
        file_path = Path(filename)
        absolute_path = file_path.absolute()
        if not file_path.exists():
            return f"[FAIL] File not found. Could not write content to '{filename}'."
        
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(content)
            
        return f"Successfully wrote content to '{absolute_path}'.\nContent written:\n---\n{content}\n---"

    @safe_action
    def read_file(self, filename: str) -> str:
        """
        Reads and returns the text content of a specified file.
        """
        filepath = Path(filename)
        absolute_path = filepath.absolute()
        if not filepath.exists():
            return f"[FAIL] File not found. Could not read content from '{filename}'."
        if not filepath.is_file():
            return f"[FAIL] Path is not a file. Please specify a file to read its contents at: '{absolute_path}'"
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return f"Reading content from '{absolute_path}':\n---\n{content}\n---"
        except Exception as e:
            return f"[FAIL] Error reading file '{filename}': {e}"

    @safe_action
    def delete_file(self, filename: str) -> str:
        file_path = Path(filename)
        absolute_path = file_path.absolute()
        file_path.unlink()
        return f"File successfully deleted: '{absolute_path}'"
    
    @safe_action
    def delete_folder(self, folder: str) -> str:
        folder_path = Path(folder)
        absolute_path = folder_path.absolute()
        try:
            shutil.rmtree(folder)
            return f"Folder and all its contents successfully deleted: '{absolute_path}'"
        except Exception as e:
            return f"[FAIL] Error deleting folder '{folder}': {e}"

    @safe_action
    def list_directory(self, directory: str) -> str:
        dir_path = Path(directory)
        absolute_path = dir_path.absolute()
        # Check if the path exists and is a directory
        if not dir_path.exists():
            return f"[FAIL] Directory not found. Could not list contents of: '{absolute_path}'"
        if not dir_path.is_dir():
            return f"[FAIL] Path is not a directory. Please specify a folder to list contents of: '{absolute_path}'"

        files = os.listdir(directory)
        files_list = "\n".join(files) if files else "<empty>"
        return f"Contents of '{absolute_path}':\n{files_list}"

    # --- File Operations: rename, copy, move ---
    @safe_action
    def rename_file(self, src: str, dest: str) -> str:
        src_path = Path(src)
        dest_path = Path(dest)
        src_path.rename(dest)
        return f"File successfully renamed/moved.\nFrom: '{src_path.absolute()}'\nTo: '{dest_path.absolute()}'"

    @safe_action
    def copy_file(self, src: str, dest: str) -> str:
        src_path = Path(src)
        dest_path = Path(dest)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        copy2(src, dest)
        return f"File successfully copied.\nSource: '{src_path.absolute()}'\nDestination: '{dest_path.absolute()}'"

    @safe_action
    def move_file(self, src: str, dest: str) -> str:
        """Moves a file from one location to another, overwriting if the destination exists."""
        src_path = Path(src)
        dest_path = Path(dest)

        # Explicitly check for the source path
        if not src_path.exists():
            return f"[FAIL] Error: Source file '{src}' not found."
        
        # Create the destination directory if it does not exist
        if not dest_path.parent.exists():
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
        # Determine the final destination path. If the destination is a directory,
        # the file keeps its original name inside that directory.
        if dest_path.is_dir():
            final_dest = dest_path / src_path.name
        else:
            final_dest = dest_path
            
        try:
            # Use shutil.move, which is more robust and can overwrite files
            shutil.move(str(src_path), str(final_dest))
            return f"File successfully moved.\nFrom: '{src_path.absolute()}'\nTo: '{Path(final_dest).absolute()}'"
        except shutil.Error as e:
            return f"[FAIL] Failed to move file due to a shutil error: {e}"
        except Exception as e:
            return f"[FAIL] Failed to move file: {e}"

    # --- Application Control ---
    @safe_action
    def open_application(self, path: str) -> str:
        # Windows-specific logic (since only Windows is used)
        # 1. Try to find the executable in PATH
        found_path = shutil.which(path)
        if found_path:
            try:
                os.startfile(found_path)
                return f"Launched application: {found_path}"
            except Exception as e:
                return f"Error launching '{found_path}' via os.startfile: {e}"
        else:
            # 2. If not found in PATH, try to launch directly via shell (relies on Windows' own lookup)
            try:
                os.startfile(path)
                return f"Attempted to launch application: {path} (Windows shell lookup)"
            except Exception as e:
                return f"Could not find or launch application '{path}'. Please provide a full path or ensure it's in your system's PATH or a well-known Windows application. Error: {e}"

    # --- Mouse & Keyboard ---
    @safe_action
    def move_mouse(self, x: int, y: int) -> str:
        pyautogui.moveTo(x, y)
        return f"Mouse moved to ({x}, {y})"

    @safe_action
    def click(self, x: int = None, y: int = None) -> str:
        if x is not None and y is not None:
            pyautogui.click(x, y)
        else:
            pyautogui.click()
        return "Mouse click executed"

    @safe_action
    def type_text(self, text: str) -> str:
        pyautogui.write(text)
        return f"Typed text: {text}"

    @safe_action
    def press_key(self, key: str) -> str:
        pyautogui.press(key)
        return f"Key pressed: {key}"
    
    @safe_action
    def open_webpage(self, url: str) -> str:
        try:
            webbrowser.open(url)
            return f"Opened web page: {url} in the default browser."
        except Exception as e:
            return f"[FAIL] Could not open web page '{url}'. Error: {e}"    

