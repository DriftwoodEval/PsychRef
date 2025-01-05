import logging
import threading

import customtkinter

from constants import APP_EXPECTED_COLUMNS, DEM_EXPECTED_COLUMNS, REF_EXPECTED_COLUMNS
from psychref import read_custom_dir, write_custom_dir
from utils import (
    check_file_columns,
    load_csv,
    pick_file,
    pick_folder,
    setup_logger,
    truncate_text,
)


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        App.instance = self
        self.dem_sheet = None
        self.ref_sheet = None
        self.app_sheet = None

        self.title("PsychRef")
        self.geometry("700x700")
        self.grid_columnconfigure((0, 1, 2), weight=1)
        self.grid_rowconfigure(3, weight=1)  # Make the log frame row expandable

        starting_directory = read_custom_dir()
        if starting_directory:
            starting_directory_display = (
                f"Current Output Directory: {starting_directory}"
            )
        else:
            starting_directory_display = "Select Output Directory"

        self.custom_directory_button = customtkinter.CTkButton(
            self,
            text=starting_directory_display,
            command=self.set_output_dir,
        )
        self.custom_directory_button.grid(
            row=0, column=0, columnspan=3, padx=5, pady=10, sticky="ew"
        )

        self.dem_sheet_button = customtkinter.CTkButton(
            self, text="Select Demographics Sheet", command=self.get_dem_sheet
        )
        self.dem_sheet_button.grid(row=1, column=0, padx=5, pady=10)

        self.ref_sheet_button = customtkinter.CTkButton(
            self, text="Select Referral Sheet", command=self.get_ref_sheet
        )
        self.ref_sheet_button.grid(row=1, column=1, padx=5, pady=10)

        self.app_sheet_button = customtkinter.CTkButton(
            self,
            text="Select Appointments Sheet",
            command=self.get_app_sheet,
        )
        self.app_sheet_button.grid(row=1, column=2, padx=5, pady=10)

        self.process_button = customtkinter.CTkButton(
            self, text="Process!", command=self.process_thread, state="disabled"
        )
        self.process_button.grid(
            row=2, column=0, columnspan=3, padx=20, pady=10, sticky="ew"
        )

        self.log_frame = customtkinter.CTkFrame(self)
        self.log_frame.grid(
            row=3, column=0, columnspan=3, padx=20, pady=10, sticky="nsew"
        )  # Changed to "nsew" to expand in all directions

        self.log_text = customtkinter.CTkTextbox(
            self.log_frame,
            wrap="word",
            state="normal",
        )
        self.log_text.pack(side="left", fill="both", expand=True)

        # Set up custom logger
        setup_logger(gui_mode=True, text_widget=self.log_text)

    def set_output_dir(self):
        folder = pick_folder("Output Directory")
        if folder:
            write_custom_dir(folder)
            self.custom_directory_button.configure(text=folder)

    def get_dem_sheet(self):
        file = pick_file("Demographics Sheet")
        if file:
            df = load_csv(file)
            if df is not None and check_file_columns(
                df, DEM_EXPECTED_COLUMNS, "Demographics"
            ):
                self.dem_sheet = df
                self.dem_sheet_button.configure(text=truncate_text(file.split("/")[-1]))
                self.check_process_button_state()
            else:
                self.dem_sheet = None
                self.dem_sheet_button.configure(text="Select Demographics Sheet")

    def get_ref_sheet(self):
        file = pick_file("Referral Sheet")
        if file:
            df = load_csv(file)
            if df is not None and check_file_columns(
                df, REF_EXPECTED_COLUMNS, "Referral"
            ):
                self.ref_sheet = df
                self.ref_sheet_button.configure(text=truncate_text(file.split("/")[-1]))
                self.check_process_button_state()
            else:
                self.ref_sheet = None
                self.ref_sheet_button.configure(text="Select Referral Sheet")

    def get_app_sheet(self):
        file = pick_file("Appointments Sheet")
        if file:
            df = load_csv(file)
            if df is not None and check_file_columns(
                df, APP_EXPECTED_COLUMNS, "Appointments"
            ):
                self.app_sheet = df
                self.app_sheet_button.configure(text=truncate_text(file.split("/")[-1]))
                self.check_process_button_state()
            else:
                self.app_sheet = None
                self.app_sheet_button.configure(text="Select Appointments Sheet")

    def process_thread(self):
        # Create a new thread for the processing
        processing_thread = threading.Thread(target=self._process_data)
        processing_thread.start()

    def _process_data(self):
        from psychref import process_data  # Import here to avoid circular imports

        process_data(self.dem_sheet, self.ref_sheet, self.app_sheet)

    def check_process_button_state(self):
        if (
            self.dem_sheet is not None
            and self.ref_sheet is not None
            and self.app_sheet is not None
        ):
            self.process_button.configure(state="normal")
            logging.info("All sheets loaded. Ready to process.")
        else:
            self.process_button.configure(state="disabled")
