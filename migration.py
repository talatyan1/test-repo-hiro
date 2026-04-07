import sqlite3
import os

db_path = r'c:\Users\nagas\.gemini\antigravity\Hiro\crowd_agent\data\agent.db'

def run_migration():
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Adding columns if they don't exist...")
    # SQL to add columns
    try:
        cursor.execute("ALTER TABLE jobs ADD COLUMN is_applied BOOLEAN NOT NULL DEFAULT 0")
        print("Added is_applied column.")
    except sqlite3.OperationalError as e:
        print(f"is_applied column already exists or error: {e}")

    try:
        cursor.execute("ALTER TABLE jobs ADD COLUMN application_error TEXT")
        print("Added application_error column.")
    except sqlite3.OperationalError as e:
        print(f"application_error column already exists or error: {e}")

    print("Resetting status for matched but unapplied jobs...")
    # Update status for matched but unapplied jobs to allow retry
    # Note: Our new get_unprocessed_jobs will pick up (status=='judged' AND ai_match=='matched' AND is_applied==0)
    # So we don't necessarily need to change 'status' to 'new', but we need to ensure is_applied is 0.
    cursor.execute("UPDATE jobs SET is_applied = 0 WHERE is_applied IS NULL")
    
    # Optional: If there were any jobs marked as 'judged' but we want to be sure they are retried,
    # and they didn't have is_applied set (which they didn't anyway before this change).
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'judged' AND ai_judge_result = 'matched' AND is_applied = 0")
    count = cursor.fetchone()[0]
    print(f"Found {count} matched but unapplied jobs that will be retried.")

    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    run_migration()
