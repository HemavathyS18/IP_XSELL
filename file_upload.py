import mysql.connector
import pandas as pd

# Database Connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Hema@mysql2004",
    database="xselldb"
)
cursor = conn.cursor()

# File Details
file_path = "D:/semester 6/innovation practices/Template/Content Syndication - MKTO (1).xlsx"  # File location
file_name = file_path.split("/")[-1]  # Extract filename
file_type = "content-syndication"  # Change this as needed

# Insert File Details into Database (Keeping Original Path)
query = "INSERT INTO picklist (pname, ptype, ppath, uploaded_at) VALUES (%s, %s, %s, NOW())"
values = (file_name, file_type, file_path)

cursor.execute(query, values)
conn.commit()

print(f"File '{file_name}' path stored in MySQL successfully!")

# Read the Excel File
df = pd.read_excel(file_path)
print("File Content:")
print(df)

# Close Connection
cursor.close()
conn.close()
