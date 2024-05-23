import os
import time
import pyautogui
import tkinter as tk
import keyboard
from tkinter import filedialog, messagebox
from PIL import ImageEnhance, ImageTk
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QDesktopWidget
import sys
from threading import Thread

BG_COLOR = "#121212"
FG_COLOR = "#EEEEEE"
PAD = 2


class CustomTab(tk.Canvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.config(borderwidth=0, highlightthickness=0)
        self.color = kwargs.get('color', 'lightblue')

    def draw_tab(self):
        x0, y0, x1, y1 = 0, 0, self.winfo_width(), self.winfo_height()
        self.create_polygon(x0, y0, x1, y0, x1, y1, x0 + 20, y1, outline='', fill=self.color)

class OverlayApp(QMainWindow):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.initUI(x, y, w, h)

    def initUI(self, x, y, w, h):
        screen = QDesktopWidget().screenGeometry()
        self.setGeometry(0, 0, screen.width(), screen.height())
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)  # Set window always on top

        # Set initial position and size of the rectangle
        self.x, self.y, self.w, self.h = x, y, w, h


    def updateWindow(self):
        # Redraw the window
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        custom_orange = QColor(255, 165, 0)
        painter.setPen(QPen(custom_orange, 2))
        painter.drawRect(self.x - PAD, self.y - PAD, self.w + PAD*2, self.h + PAD*2)


class InitialScreen:
    def __init__(self, master):
        self.master = master
        self.master.title("Swift Capture!")
        self.master.geometry("330x150+100+100")  # Add padding
        self.master.configure(bg=BG_COLOR)
        self.master.resizable(False, False)  # Make the window un-resizable


        self.instructions_label = tk.Label(master, text="\nPress the button to enter screenshot mode.", bg=BG_COLOR,
                                           fg=FG_COLOR)
        self.instructions_label.pack()

        self.enter_button = tk.Button(master, text="Screenshot mode", command=self.enter_screenshot_mode, bg="#28a745",
                                      fg="white", relief="flat", padx=10)
        self.enter_button.pack(pady=(10, 5))  # Add vertical space below the button

        self.browse_button = tk.Button(master, text="Browse", command=self.select_export_directory, bg="#fd7e14",
                                       fg="white", relief="flat", padx=10)
        self.browse_button.pack(pady=(5, 0))  # Add vertical space above the button

        link_label = tk.Label(master, text="About", fg="blue", cursor="hand2",
                              bg=BG_COLOR)
        link_label.place(relx=0.175, rely=0.8, anchor="ne")
        link_label.bind("<Button-1>", lambda event: self.open_about_window())

        self.app = None
        self.screenshot_window = None

        self.export_directory = os.getcwd()

    def open_about_window(self):
        messagebox.showinfo("About Swift Capture!", "Swift Capture! - A screenshot tool designed to capture regions "
                                           "of your screen quickly and efficiently.\n\n"
                                           "- Choose a specified directory.\n"
                                           "- Proceed to draw a rectangle on your screen.\n"
                                           "- Press 's' key to capture the selected region.\n"
                                           "- Export screenshots to a specified directory.\n\n"
                                           "Developed by dannythedev.")

    def enter_screenshot_mode(self):
        self.master.withdraw()  # Close the initial screen window
        time.sleep(0.25)
        self.screenshot_window = tk.Toplevel()  # Create a new window for screenshot mode
        self.app = ScreenshotApp(self.screenshot_window, self.master, export_dir=self.export_directory)

    def select_export_directory(self):
        self.export_directory = filedialog.askdirectory()


class ScreenshotApp:
    def __init__(self, master, top_master, export_dir):

        self.export_directory = None
        self.export_dir = export_dir if export_dir else os.getcwd()
        self.master = master
        self.top_master = top_master
        self.master.title("Swift Capture!")
        self.master.attributes('-fullscreen', True)  # Set window to fullscreen
        self.master.geometry("300x150+100+100")  # Add padding

        # Get the dimensions of the screen
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        # Take a screenshot of the current screen
        screenshot = pyautogui.screenshot()
        # Adjust the brightness of the screenshot
        screenshot = self.adjust_brightness(screenshot, 0.5)  # You can adjust the brightness factor here
        # Load the screenshot onto a PhotoImage
        self.screenshot_image = ImageTk.PhotoImage(screenshot)
        # Create a canvas with the dimensions of the screen
        self.canvas = tk.Canvas(master, width=screen_width, height=screen_height, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Display the screenshot on the canvas
        self.canvas.create_image(0, 0, anchor="nw", image=self.screenshot_image)

        self.coordinates = None
        self.rect = None
        self.thread = None
        self.overlay_app = None
        self.exit_button = None

        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

        # Register the 's' key press event globally
        keyboard.on_press_key("s", self.capture_screenshot)
        keyboard.on_press_key("esc", self.return_to_initial_screen)

    def return_to_initial_screen(self, event=None):
        self.unbind()
        if self.thread and self.thread.is_alive():
            self.thread.join()
        if self.overlay_app:
            self.overlay_app.quit()
        self.top_master.deiconify()
        self.master.destroy()

    def unbind(self):
        # Unbind all key bindings from the canvas
        self.canvas.unbind_all("<Button-1>")
        self.canvas.unbind_all("<B1-Motion>")
        self.canvas.unbind_all("<ButtonRelease-1>")
        # Unhook the 's' key
        keyboard.unhook_all()

    @staticmethod
    def adjust_brightness(image, brightness_factor):
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(brightness_factor)

    def on_canvas_click(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="#FFA500", width=2)

    def on_canvas_drag(self, event):
        self.end_x = event.x
        self.end_y = event.y
        self.canvas.coords(self.rect, self.start_x - PAD, self.start_y - PAD, self.end_x + PAD, self.end_y + PAD)

    def on_canvas_release(self, event):
        self.end_x = event.x
        self.end_y = event.y
        self.coordinates = (min(self.start_x, self.end_x), min(self.start_y, self.end_y),
                            max(self.start_x, self.end_x), max(self.start_y, self.end_y))
        x1, y1, x2, y2 = self.coordinates
        if (x2 - x1) * (y2 - y1) > 5000:
            print("Captured rectangle.")
            self.master.withdraw()
            self.master.attributes('-fullscreen', False)
            self.show_screenshot_mode_in_progress()  # Open a new window for screenshot mode
            # Start a new thread to draw the rectangle
            self.thread = Thread(target=self.start, args=(x1, y1, x2 - x1, y2 - y1,))
            self.thread.start()
        else:
            self.canvas.delete(self.rect)  # Delete the drawn rectangle
            self.coordinates = None

    def start(self, x, y, w, h):
        self.overlay_app = QApplication(sys.argv)
        self.window = OverlayApp(x, y, w, h)
        self.window.show()
        sys.exit(self.overlay_app.exec_())

    def end(self):
        self.unbind()
        self.window.close()
        self.overlay_app.quit()

    def show_screenshot_mode_in_progress(self):
        def open_directory():
            os.startfile(self.export_dir)

        # Create a new Toplevel window
        self.screenshot_progress_window = tk.Toplevel(self.master)
        self.screenshot_progress_window.configure(bg=BG_COLOR)
        self.screenshot_progress_window.resizable(True, False)  # Make the window un-resizable

        self.screenshot_progress_window.title("Swift Capture!")
        self.screenshot_progress_window.geometry("300x150+100+100")  # Add padding

        # Add a label indicating screenshot mode in progress
        progress_label = tk.Label(self.screenshot_progress_window, text="Screenshot mode in progress.\n"
                                                                        "Pressing 's' key will promptly\n"
                                                                        "export a screenshot.", bg=BG_COLOR,
                                  fg=FG_COLOR)

        progress_label.pack(pady=8)

        link_label = tk.Label(self.screenshot_progress_window, text=self.export_dir, fg="blue", cursor="hand2",
                              bg=BG_COLOR)
        link_label.pack(pady=0, padx=10)
        link_label.bind("<Button-1>", lambda event: open_directory())

        self.exit_button = tk.Button(self.screenshot_progress_window, text="Exit Mode",
                                     command=self.close_progress_window, bg="#fd7e14",
                                     fg="white", relief="flat", padx=10)
        self.exit_button.pack(pady=(5, 7))  # Add vertical space above the button

        self.screenshot_progress_window.attributes('-topmost', True)

        # Add a callback for closing the progress window
        self.screenshot_progress_window.protocol("WM_DELETE_WINDOW", self.close_progress_window)

    def close_progress_window(self):
        # When closing the progress window, bring back the InitialScreen window
        self.end()
        self.top_master.deiconify()
        self.master.destroy()

    def find_first_non_consecutive(self):
        files = os.listdir(self.export_dir)
        files = [file.rstrip(".png") for file in files if file.endswith('.png')]
        numbers = sorted(set(int(num) for num in files if num.isdigit()))
        return next((num for num in range(1, len(numbers) + 2) if num not in numbers), None)

    def capture_screenshot(self, event):
        if self.coordinates:
            # Count existing screenshots in the folder
            new_filename = f"{self.find_first_non_consecutive()}.png"
            x1, y1, x2, y2 = self.coordinates
            screenshot = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
            screenshot.save(f"{self.export_dir}\\{new_filename}")  # Save screenshot to the selected directory
            print(f"Screenshot saved as {new_filename}")


if __name__ == "__main__":
    root = tk.Tk()
    app = InitialScreen(root)
    root.mainloop()
