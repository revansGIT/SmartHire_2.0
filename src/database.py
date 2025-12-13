import sqlite3

DB_PATH = "smarthire.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Stores the overall Job (e.g., "Senior Python Dev")
    c.execute('''CREATE TABLE IF NOT EXISTS jobs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  title TEXT, 
                  description TEXT, 
                  status TEXT, 
                  total_files INTEGER DEFAULT 0,
                  processed_files INTEGER DEFAULT 0)''')
    
    # Stores the Candidates
    c.execute('''CREATE TABLE IF NOT EXISTS candidates 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  job_id INTEGER, 
                  filename TEXT, 
                  score REAL, 
                  missing_skills TEXT, 
                  is_shortlisted BOOLEAN)''')
    conn.commit()
    conn.close()