================================================================================
CUSTOM FONTS FOR RELEASE TESTING TOOL (RTT)
================================================================================

Directory: resources/fonts/

This folder contains custom TrueType fonts (.ttf) used by the application.

CURRENT FONTS
=============

Bungee-Regular.ttf
  - Used for the splash screen "- A R E S -" title
  - Location: resources/fonts/Bungee-Regular.ttf
  - Font size: 40pt bold
  - Status: Expected but optional (falls back to system fonts if missing)

ADDING CUSTOM FONTS
===================

1. Obtain the .ttf font file
   - Download or create a TrueType font
   - Ensure it has a .ttf extension

2. Place the font in this directory
   - Example: resources/fonts/MyFont.ttf

3. Update the code to use the font
   - In src/gui/splash.py, modify _get_font_path() to return the correct filename
   - Or add additional font paths for other UI elements

4. Rebuild the PyInstaller executable
   - The RTT.spec file is configured to bundle all fonts from this directory
   - Run: pyinstaller RTT.spec
   - The bundled exe will include all .ttf files

FONT REQUIREMENTS
=================

- Format: TrueType (.ttf) files only
- DPI: 72 dpi (standard screen resolution)
- Character sets: Must include characters used in the UI (ASCII minimum)
- Licensing: Ensure proper licensing for distribution

FALLBACK BEHAVIOR
=================

If a custom font file is missing or fails to load:
  1. PIL (Pillow) will attempt to use PIL's default 8x8 bitmap font
  2. The application will continue without errors
  3. Text will be rendered in a basic bitmap font (less polished)

DEVELOPMENT vs FROZEN MODE
============================

The font loading code automatically detects run mode:
  - Development: Looks for resources/fonts/ relative to src/
  - PyInstaller frozen: Looks for resources/fonts/ in the bundled _MEIPASS directory

This ensures fonts work in both development and compiled executables.

FONT LICENSE ATTRIBUTION
========================

When distributing the RTT executable with custom fonts, ensure:
  1. You have rights to distribute the font
  2. Font license terms are followed
  3. Attribution is provided if required by the license

================================================================================
