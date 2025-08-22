# gui/main_window.py
import sys
import os
import importlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def main():
    login_module = importlib.import_module("gui.login_window")
    login_module.login_window()

if __name__ == "__main__":
    main()