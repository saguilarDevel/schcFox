import os

import openpyxl as openpyxl

from Entities.SCHCLogger import SCHCLogger

os.chdir("stats")
with open("output.txt", 'w') as output_file:
    for foldername in ["0_ul", "10_ul", "20_ul", "10_uldl", "20_uldl"]:
        if foldername in ["0_ul", "10_ul", "20_ul"]:
            spreadsheet_name = 'Template Results UL.xlsx'
        else:
            spreadsheet_name = 'Template Results ULDL.xlsx'

        spreadsheet = openpyxl.load_workbook(filename=spreadsheet_name)
        output_file.write(f"============== FOLDER: {foldername} ==============\n\n")
        for filename in os.listdir(f'results/{foldername}'):
            print(f"Extracting data from {foldername}/{filename}")
            SCHCLogger.extract_data(foldername, filename, output_file, spreadsheet)
        spreadsheet.save(spreadsheet_name)
