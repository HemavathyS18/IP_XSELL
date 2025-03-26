import pandas as pd

class ExcelToCSVConverter:
    def __init__(self, excel_file, sheet_name=0):
        """
        Initialize the converter with an Excel file.
        :param excel_file: Path to the Excel file.
        :param sheet_name: Sheet name or index to read from.
        """
        self.excel_file = excel_file
        self.sheet_name = sheet_name

    def convert_to_csv(self, output_csv_file):
        """
        Convert an Excel sheet to CSV.
        :param output_csv_file: Path to save the converted CSV file.
        """
        try:
            # Read Excel file
            df = pd.read_excel(self.excel_file, sheet_name=self.sheet_name)
            
            # Convert to CSV
            df.to_csv(output_csv_file, index=False)  # Save without index column
            
            print(f"Excel file '{self.excel_file}' successfully converted to CSV '{output_csv_file}'")
        except Exception as e:
            print(f"Error converting Excel to CSV: {e}")


    