import sqlite3

DB_PATH = "smarthire.db"

def init_db():
    """Initialize database with proper connection handling"""
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        
        # Create jobs table
        c.execute('''CREATE TABLE IF NOT EXISTS jobs 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      title TEXT, 
                      description TEXT, 
                      status TEXT, 
                      total_files INTEGER DEFAULT 0,
                      processed_files INTEGER DEFAULT 0)''')
        
        # Create candidates table
        c.execute('''CREATE TABLE IF NOT EXISTS candidates 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      job_id INTEGER, 
                      filename TEXT, 
                      score REAL, 
                      missing_skills TEXT, 
                      is_shortlisted BOOLEAN)''')
        
        # Check if found_skills column exists, if not add it
        try:
            c.execute("SELECT found_skills FROM candidates LIMIT 1")
        except sqlite3.OperationalError:
            # Column doesn't exist, add it
            c.execute("ALTER TABLE candidates ADD COLUMN found_skills TEXT")
        
        conn.commit()
    finally:
        conn.close()