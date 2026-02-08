import os
import pandas as pd
from tkinter import Tk, filedialog

# Function to classify MACD-Hist state with missing check
def classify_macd_hist(macd, hist):
    if pd.isna(macd) or pd.isna(hist):
        return 'None'
    if macd == 'UP' and hist:
        return 'Light Green'
    if macd == 'UP' and not hist:
        return 'Dark Green'
    if macd == 'DOWN' and hist:
        return 'Light Red'
    if macd == 'DOWN' and not hist:
        return 'Dark Red'
    return 'None'

# Function to process one Excel file
def process_excel_file(file_path):
    try:
        df = pd.read_excel(file_path, sheet_name="Sheet1")
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return

    intervals = ['1d', '4h', '1h', '30m', '15m', '5m', '3m', '1m']
    
    for interval in intervals:
        macd_col = f'macd_{interval}'
        hist_col = f'Hist_De_{interval}'
        new_col = f'macd_hist_state_{interval}'

        # Add classification column using .get() to handle missing fields gracefully
        df[new_col] = df.apply(
            lambda row: classify_macd_hist(row.get(macd_col), row.get(hist_col)),
            axis=1
        )
    
    # Save with "_With_MACD_Hist" suffix
    base_dir, file_name = os.path.split(file_path)
    name, ext = os.path.splitext(file_name)
    new_file_path = os.path.join(base_dir, f"{name}_With_MACD_Hist{ext}")
    
    try:
        df.to_excel(new_file_path, index=False)
        print(f"✅ Saved: {new_file_path} (Rows: {len(df)})")
    except Exception as e:
        print(f"❌ Error saving {new_file_path}: {e}")

# Main function for file selection
def main():
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    
    file_paths = filedialog.askopenfilenames(
        title="Select Excel Files",
        filetypes=[("Excel files", "*.xlsx *.xls")]
    )

    for file_path in file_paths:
        process_excel_file(file_path)

    print("\n🎉 All files processed without dropping any trades.")

if __name__ == "__main__":
    main()