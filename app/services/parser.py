import pandas as pd

def parse_file(file):

    if file.filename.endswith(".csv"):
        df = pd.read_csv(file.file)

    elif file.filename.endswith(".xlsx"):
        df = pd.read_excel(file.file)

    else:
        raise ValueError("Unsupported file type")

    return df