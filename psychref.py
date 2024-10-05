import logging
import os
from collections import defaultdict
from datetime import datetime

import pandas as pd
from fpdf import FPDF

from constants import APP_EXPECTED_COLUMNS, DEM_EXPECTED_COLUMNS, REF_EXPECTED_COLUMNS
from utils import (
    check_file_columns,
    load_csv,
    parse_args,
    setup_logger,
)

global_gui_mode = False
PROCESSED_CLIENTS_FILE = "SentClientList.txt"


def get_clients(dem_sheet, ref_sheet, app_sheet, code):
    app_sheet["STARTTIME"] = pd.to_datetime(app_sheet["STARTTIME"], errors="coerce")
    future_appointments = app_sheet[app_sheet["STARTTIME"] > datetime.now()]
    target_appointments = future_appointments[
        future_appointments["NAME"].str.contains(code, na=False)
    ]

    results = []

    for _, appointment in target_appointments.iterrows():
        client_id = appointment["CLIENT_ID"]

        client_info = dem_sheet[dem_sheet["CLIENT_ID"] == client_id].iloc[0]

        first_name = client_info["FIRSTNAME"]
        preferred_name = client_info.get("PREFERRED_NAME", "")
        if pd.notna(preferred_name) and preferred_name.lower() != first_name.lower():
            first_name += f' "{preferred_name}"'

        client_name_for_lookup = f"{client_info['FIRSTNAME']} {client_info['LASTNAME']}"
        client_name = f"{first_name} {client_info['LASTNAME']}"

        referral_info = ref_sheet[ref_sheet["Client Name"] == client_name_for_lookup]

        if referral_info.empty and pd.notna(preferred_name):
            preferred_name_lookup = f"{preferred_name} {client_info['LASTNAME']}"
            referral_info = ref_sheet[ref_sheet["Client Name"] == preferred_name_lookup]

        referral_source = (
            referral_info["Referral Name"].iloc[0]
            if not referral_info.empty
            else "Unknown"
        )

        appointment_time = (
            "Unknown Time"
            if pd.isna(appointment["STARTTIME"])
            else appointment["STARTTIME"].strftime("%m/%d/%Y %I:%M %p")
        )

        results.append(
            {
                "client_id": client_id,
                "client_name": client_name,
                "appointment_time": appointment_time,
                "referral_source": referral_source,
            }
        )

    return results


def create_referral_pdfs(clients):
    referral_groups = defaultdict(list)
    for client in clients:
        if client["referral_source"].lower() not in [
            "unknown",
            "no referral source",
            "",
            "babynet",
        ]:
            referral_groups[client["referral_source"]].append(client)

    for referral_source, clients in referral_groups.items():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Times", size=12)
        pdf.image("Logo.jpg", w=100, x=50)

        referral_name = referral_source.split("(")[0].strip().title()

        pdf.ln(5)
        pdf.multi_cell(0, 10, f"Hi {referral_name},")
        pdf.ln(1)
        pdf.multi_cell(
            0,
            10,
            "Thank you for referring the following clients. Here is a list of their tentative evaluation appointments:",
        )
        pdf.ln(5)

        # Write client appointments
        for client in clients:
            if client["appointment_time"] != "Unknown Time":
                # Parse the datetime
                appointment_datetime = datetime.strptime(
                    client["appointment_time"], "%m/%d/%Y %I:%M %p"
                )
                # Format the appointment string
                appointment_str = (
                    f"{client['client_name']} on "
                    f"{appointment_datetime.strftime('%m/%d/%Y')} at "
                    f"{appointment_datetime.strftime('%-I:%M %p')}"
                )
            else:
                appointment_str = f"{client['client_name']} - Appointment time unknown"

            pdf.multi_cell(0, 10, appointment_str)

        pdf.ln(5)
        pdf.multi_cell(0, 10, "Thank you again!")
        pdf.multi_cell(0, 10, "Driftwood Evaluation Center")

        safe_filename = referral_name.rstrip()
        pdf_filename = f"PDFs/{safe_filename}.pdf"

        # Check if the file already exists
        counter = 1
        while os.path.exists(pdf_filename):
            pdf_filename = f"PDFs/{safe_filename}_{counter}.pdf"
            counter += 1

        pdf.output(pdf_filename)


def process_data(dem_sheet, ref_sheet, app_sheet):
    os.makedirs("PDFs/", exist_ok=True)
    if dem_sheet is not None and ref_sheet is not None and app_sheet is not None:
        clients_96136 = get_clients(dem_sheet, ref_sheet, app_sheet, "96136")

        create_referral_pdfs(clients_96136)

        logging.info(
            f"Found {len(clients_96136)} new clients with '96136' appointments."
        )
    else:
        logging.error("One or more required sheets are missing.")


def main():
    args = parse_args()
    global global_gui_mode
    if args.dem and args.ref and args.app:
        setup_logger(gui_mode=False)
        logging.info("Starting in command-line mode.")
        dem_sheet = load_csv(args.dem)
        ref_sheet = load_csv(args.ref)
        app_sheet = load_csv(args.app)

        if (
            check_file_columns(dem_sheet, DEM_EXPECTED_COLUMNS, "Demographics")
            and check_file_columns(ref_sheet, REF_EXPECTED_COLUMNS, "Referral")
            and check_file_columns(app_sheet, APP_EXPECTED_COLUMNS, "Appointments")
        ):
            process_data(dem_sheet, ref_sheet, app_sheet)

    else:
        global_gui_mode = True
        logging.info("Starting in GUI mode.")
        from gui import App

        app = App()
        app.mainloop()


if __name__ == "__main__":
    main()
