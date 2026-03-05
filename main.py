"""
Release Testing Tool - Main Entry Point

Run this file to launch the application.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gui.main_window import MainWindow


def main():
    """Application entry point."""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
