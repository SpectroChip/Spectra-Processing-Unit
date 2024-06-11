import tkinter as tk
from tkinter import ttk, simpledialog, filedialog
from PIL import Image, ImageTk
import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
0

class App:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)
        self.ROI = 500  # initialize ROI setting
        self.rows_number = 10  # initialize row numbers
        self.brightness = 500  # initialize Brightness setting
        self.gain = 8 # initialize Gain setting

        # initialize USB camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise ValueError("Camera No work")

        # camera setting
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 800)
        self.cap.set(cv2.CAP_PROP_MODE, 2)
        self.cap.set(cv2.CAP_PROP_CONVERT_RGB, 0)
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, 300)
        self.cap.set(cv2.CAP_PROP_GAIN, 8)

        # Create UI interface
        self.create_widgets()

        # set timing
        self.delay = 50
        self.update()

        self.window.mainloop()

    def create_widgets(self):
        # create button
        self.buttons_frame = tk.Frame(self.window)
        self.buttons_frame.grid(row=1, column=0, columnspan=2, pady=10)

        self.setting_button = ttk.Button(self.buttons_frame, text="Setting", command=self.open_setting)
        self.setting_button.pack(side=tk.LEFT, padx=2)

        self.save_button = ttk.Button(self.buttons_frame, text="Save", command=self.save_data)
        self.save_button.pack(side=tk.LEFT, padx=2)

        self.exit_button = ttk.Button(self.buttons_frame, text="Exit", command=self.exit_app)
        self.exit_button.pack(side=tk.LEFT, padx=2)

        # create left window（Original camera picture）
        self.camera_frame = ttk.Label(self.window)
        self.camera_frame.grid(row=0, column=0, padx=10, pady=12)

        # create right window（analyze ROI result）
        self.plot_frame = tk.Frame(self.window)
        self.plot_frame.grid(row=0, column=1, padx=10, pady=12)

        # Initialize Matplotlib figure and axes for plotting
        self.fig, self.ax = plt.subplots(figsize=(4, 3))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.widget = self.canvas.get_tk_widget()
        self.widget.pack(fill=tk.BOTH, expand=True)

    def update(self):
        # capture picture from camera
        ret, frame = self.cap.read()

        # if capture success, refresh left picture
        if ret:
            a = frame[0][::2].astype(np.uint16)  # Starting from 0, take every 2 pixel
            b = frame[0][1::2].astype(np.uint16)  # Starting from 1, take every 2 pixel
            if len(frame[0]) % 2 != 0:
                b = np.append(b, 0)  # Make sure a and b are the same length

            combined = ((a << 4) | (b - 128)).astype(np.uint16)
            result = combined.reshape(800, 1280).astype(np.float64)
            normalized_result = (result / 4096 * 254).astype(np.uint8)

            start_point = (0, self.ROI - self.rows_number)  # Start point
            end_point = (normalized_result.shape[1], self.ROI + self.rows_number)  # End point
            color = (255, 0, 0)  # BGR color setting，Red
            thickness = 2  # Line thickness

            # make red frame on resized_image
            cv2.rectangle(normalized_result, start_point, end_point, color, thickness)
            resized_image = cv2.resize(normalized_result, (0, 0), fx=0.4, fy=0.4)

            self.photo = ImageTk.PhotoImage(image=Image.fromarray(resized_image))
            self.camera_frame.config(image=self.photo)
            self.analyze_roi(result, self.ROI, self.rows_number)
            self.window.after(self.delay, self.update)

    def analyze_roi(self, result, ROI, rows_number):
        roi = result[ROI - rows_number: ROI + rows_number, :]
        roi_avg = np.mean(roi, axis=0)
        self.draw_plot(roi_avg)

    def draw_plot(self, data):

        # Clear the previous data
        self.ax.clear()

        # Plot new data
        self.ax.plot(data)
        self.ax.set_xlim([0, 1280])  # Set x-axis limits
        self.ax.set_ylim([0, 4100])  # Set y-axis limits
        self.ax.set_title("Real-time Spectrum")
        self.ax.set_xlabel("Wavelength (pixel)")
        self.ax.set_ylabel("Average Value")

        self.canvas.draw()

    def open_setting(self):
        self.setting_window = tk.Toplevel(self.window)
        self.setting_window.title("Settings")

        # ROI setting
        tk.Label(self.setting_window, text="ROI:").grid(row=0, column=0)
        self.roi_var = tk.IntVar(value=self.ROI)
        self.roi_scale = tk.Scale(self.setting_window, from_=0, to_=900, orient=tk.HORIZONTAL, variable=self.roi_var,
                                  command=self.update_roi_display)
        self.roi_scale.grid(row=0, column=1)
        self.roi_value_label = tk.Label(self.setting_window, text=str(self.ROI))
        self.roi_value_label.grid(row=0, column=2)

        # Rows Number setting
        tk.Label(self.setting_window, text="Rows Number:").grid(row=1, column=0)
        self.rows_number_var = tk.IntVar(value=self.rows_number)
        self.rows_number_scale = tk.Scale(self.setting_window, from_=1, to_=30, orient=tk.HORIZONTAL,
                                          variable=self.rows_number_var, command=self.update_rows_number_display)
        self.rows_number_scale.grid(row=1, column=1)
        self.rows_number_value_label = tk.Label(self.setting_window, text=str(self.rows_number))
        self.rows_number_value_label.grid(row=1, column=2)

        # Brightness setting
        tk.Label(self.setting_window, text="Exposure:").grid(row=2, column=0)
        self.brightness_var = tk.IntVar(value=self.brightness)
        self.brightness_scale = tk.Scale(self.setting_window, from_=0, to_=800, orient=tk.HORIZONTAL, variable=self.brightness_var,
                                          command=self.update_brightness_display)
        self.brightness_scale.grid(row=2, column=1)
        self.brightness_value_label = tk.Label(self.setting_window, text=str(self.brightness))
        self.brightness_value_label.grid(row=2, column=2)

        # Gain setting
        tk.Label(self.setting_window, text="Gain:").grid(row=3, column=0)
        self.gain_var = tk.IntVar(value=self.gain)
        self.gain_scale = tk.Scale(self.setting_window, from_=1, to_=32, orient=tk.HORIZONTAL, variable=self.gain_var,
                                          command=self.update_gain_display)
        self.gain_scale.grid(row=3, column=1)
        self.gain_value_label = tk.Label(self.setting_window, text=str(self.gain))
        self.gain_value_label.grid(row=3, column=2)


    def update_roi_display(self, value):
        self.ROI = int(value)
        self.roi_value_label.config(text=str(self.ROI))

    def update_rows_number_display(self, value):
        self.rows_number = int(value)
        self.rows_number_value_label.config(text=str(self.rows_number))

    def update_brightness_display(self, value):
        self.brightness = int(value)
        self.brightness_value_label.config(text=str(self.brightness))
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, self.brightness)  # Dynamically update camera brightness

    def update_gain_display(self, value):
        self.gain = int(value)
        self.gain_value_label.config(text=str(self.gain))
        self.cap.set(cv2.CAP_PROP_GAIN, self.gain)  # Dynamically update camera gain

    def save_data(self):
        # Prompts the user to select a storage path and save the data
        filepath = filedialog.asksaveasfilename(defaultextension=".txt")
        if filepath:
            np.savetxt(filepath, self.ax.lines[0].get_ydata(), fmt='%f')

    def exit_app(self):
        self.window.quit()
        self.window.destroy()


# create window and start application
app = App(tk.Tk(), "ROI Monitor")
