import os

import openpyxl as openpyxl

from Entities.SCHCLogger import SCHCLogger

with open("output.txt", 'w', encoding='ISO-8859-1') as output_file:
    # for foldername in ["results/ul_0", "results/ul_10", "results/ul_20", "results/uldl_10", "results/uldl_20"]:
    for foldername in ["results/ul_0", "results/ul_10", "results/ul_20"]:
        if foldername in ["results/ul_0", "results/ul_10", "results/ul_20"]:
            spreadsheet_name = 'results/Template Results UL.xlsx'
        else:
            spreadsheet_name = 'results/Template Results ULDL.xlsx'

        spreadsheet = openpyxl.load_workbook(filename=spreadsheet_name)
        output_file.write(f"============== FOLDER: {foldername} ==============\n\n")
        for filename in os.listdir(f'{foldername}'):
            print(f"Extracting data from {foldername}/{filename}")
            SCHCLogger.extract_data(foldername, filename, output_file, spreadsheet)
        spreadsheet.save(spreadsheet_name)
