# Release Testing Tool

A Python-based tool for analyzing PDFs, reading/writing Excel sheets, and managing folder structures as part of release testing workflows.

## Project Structure

```
ReleaseTestingTool/
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── README.md                # This file
│
├── src/                     # Source code
│   ├── __init__.py
│   ├── core/                # Core business logic
│   │   └── __init__.py
│   ├── models/              # Data models
│   │   └── __init__.py
│   ├── utils/               # Utility functions and helpers
│   │   └── __init__.py
│   └── gui/                 # GUI components
│       ├── __init__.py
│       ├── main_window.py   # Main application window
│       ├── dialogs/         # Dialog windows
│       ├── widgets/         # Custom widgets
│       └── styles/          # Themes and styling
│
├── resources/               # Application resources
│   ├── icons/               # Icon files (.ico, .png, .svg)
│   │   ├── toolbar/         # Toolbar icons
│   │   └── status/          # Status indicator icons
│   └── images/              # Image assets
│
├── config/                  # Configuration files
│   └── settings.json        # Application settings
│
├── docs/                    # Documentation
│   └── help/                # Help text files
│       ├── getting_started.txt
│       ├── user_guide.txt
│       ├── faq.txt
│       ├── shortcuts.txt
│       └── troubleshooting.txt
│
├── tests/                   # Unit and integration tests
│   ├── __init__.py
│   ├── test_core.py
│   └── test_gui.py
│
├── data/                    # Input data files
├── output/                  # Test results and exported reports
└── logs/                    # Application log files
```

## Getting Started

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   python main.py
   ```

## Requirements

- Python 3.8+
