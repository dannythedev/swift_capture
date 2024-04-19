# Swift Capture!

Swift Capture! is a screenshot tool designed to capture regions of your screen quickly and efficiently. With its intuitive interface and easy-to-use features, Swift Capture! makes capturing screenshots a breeze.

## Features

- **Select Screenshot Mode:** Press a button to enter screenshot mode and start capturing your screen.
- **Export to Specified Directory:** Choose a directory to export your screenshots to.
- **Easy Rectangular Selection:** Simply draw a rectangle on your screen to capture the desired region.
- **Prompt Screenshot Export:** Press the 's' key to promptly export a screenshot.

## Requirements

Make sure you have the following dependencies installed:

- Python 3
- PyAutoGUI
- Tkinter
- Keyboard
- Pillow (PIL)
- PyQt5

Install the dependencies using the following command:

``pip install -r requirements.txt``

## Usage

1. Run the `app.py` script.
2. Press the "Screenshot mode" button to enter screenshot mode.
3. Optionally, click on the "Browse" button to choose a directory for exporting screenshots.
4. Draw a rectangle on your screen to select the region you want to capture. Press the 's' key to capture the selected region.
5. Screenshots are automatically saved to the specified export directory.


## File Structure

- `app.py`: Main Python script containing the tkinter application and image manipulation functions.
- `requirements.txt`: List of Python dependencies required for the project.
- `README.md`: This file providing an overview of the project and instructions for usage.