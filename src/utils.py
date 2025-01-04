import argparse
import logging
from os import getcwd
from tkinter import filedialog

from chardet import detect
from pandas import errors as pandas_errors
from pandas import read_csv


def truncate_text(text: str, max_length=20):
    if len(text) > max_length:
        return text[: max_length - 3] + "..."
    return text


def pick_file(title):
    return filedialog.askopenfilename(
        title=title, initialdir=getcwd(), filetypes=[("Allowed Types", "*.csv")]
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Make referral sheets.")
    parser.add_argument(
        "--dem", "-d", help="Path to demographics CSV file", metavar="FILE"
    )
    parser.add_argument(
        "--ref", "-r", help="Path to referral report CSV file", metavar="FILE"
    )
    parser.add_argument(
        "--app", "-a", help="Path to appointments csv file", metavar="FILE"
    )
    return parser.parse_args()


class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.insert("end", msg + "\n")
        self.text_widget.see("end")


def setup_logger(gui_mode=False, text_widget=None):
    """
    Set up the logger for either GUI or console mode.

    Args:
        gui_mode (bool): True if running in GUI mode, False for console mode.
        text_widget: The text widget to log to in GUI mode (only used if gui_mode is True).

    Returns:
        None
    """
    # Get the root logger and set its level
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create a formatter for log messages
    log_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s", datefmt="%H:%M:%S"
    )

    if gui_mode and text_widget:
        # Set up logging for GUI mode
        handler = TextHandler(text_widget)
    else:
        # Set up logging for console mode
        handler = logging.StreamHandler()

    # Apply the formatter and add the handler to the logger
    handler.setFormatter(log_formatter)
    logger.addHandler(handler)

    logging.info("Logger setup complete.")


def load_csv(file_path):
    """
    Loads a CSV file with error handling and automatic encoding detection.

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        pandas.DataFrame or None: DataFrame containing CSV data if successful, None otherwise.
    """
    logging.info(f"Loaded {file_path}.")
    try:
        # Read file in binary mode for encoding detection
        with open(file_path, "rb") as file:
            raw_data = file.read()

        # Detect file encoding
        detected_encoding = detect(raw_data)["encoding"]

        # Read CSV file with detected encoding
        df = read_csv(file_path, encoding=detected_encoding)
        return df

    except UnicodeDecodeError as e:
        logging.error(f"Error decoding file: {e}")
    except pandas_errors.EmptyDataError as e:
        logging.error(f"Error reading file, may be empty or corrupt: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

    return None


def check_file_columns(df, expected_columns, file_type):
    missing_columns = [col for col in expected_columns if col not in df.columns]
    if missing_columns:
        logging.error(
            f"{file_type} file is missing expected columns: {', '.join(missing_columns)}"
        )
        return False
    return True
