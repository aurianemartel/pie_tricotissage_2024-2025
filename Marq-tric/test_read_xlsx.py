

import pandas as pd
import sys

# Read the Excel file into a Pandas DataFrame
df = pd.read_excel(sys.argv[1], sheet_name="coordinates")  # Replace "Sheet1" with the actual sheet name

print(">> shape")
print(df.shape)

print(">> HEAD")
# Accessing data
print(df.head())  # Print the first few rows of the DataFrame

print(">> df.loc")
# Accessing specific elements
print(df.loc[0, "COORD_X"])  # Access the value in the first row and the "Column1" column

print(">> for index, row in df.iterrows()")
for index, row in df.iterrows():
    print(row["COORD_X"], row["COORD_Y"], row["ANGLE"],
          row["COORD_X2"], row["COORD_Y2"], row["ANGLE"])

print(">> for i in range")
for i in range(df.shape[0]-1):
    print(df.loc[i+1, "COORD_X2"] - df.loc[i, "COORD_X2"])
