import sqlite3

def create_table():
    # Connect to the SQLite database (it will create the db file if it doesn't exist)
    conn = sqlite3.connect('medical_db.db')
    cursor = conn.cursor()

    # Create the predictionreport table
    create_table_query = """
    CREATE TABLE IF NOT EXISTS predictionreport (
        report_id INTEGER PRIMARY KEY AUTOINCREMENT,
        prediction_result TEXT,
        disease_type TEXT,
        patient_id INTEGER,
        liver_record_id INTEGER,
        diabetes_record_id INTEGER,
        kideny_record_id INTEGER,
        FOREIGN KEY (patient_id) REFERENCES userbase(userid),
        FOREIGN KEY (liver_record_id) REFERENCES LiverRecord(Liver_Record_ID),
        FOREIGN KEY (diabetes_record_id) REFERENCES DiabetesRecord(Diabetes_Record_ID),
        FOREIGN KEY (kideny_record_id) REFERENCES KidneyRecord(Kidney_record_ID)
    );
    """
    
    cursor.execute(create_table_query)
    conn.commit()
    print("Table 'predictionreport' created successfully!")

    conn.close()

# Main function to run the script
def main():
    # Create the table if not exists
    create_table()

# Run the main function
if __name__ == "__main__":
    main()
