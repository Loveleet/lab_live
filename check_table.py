#!/usr/bin/env python3
import psycopg2

try:
    # Connect to database
    conn = psycopg2.connect(
        host='150.241.244.23',
        user='postgres',
        password='IndiaNepal1-',
        database='labdb2'
    )
    
    cursor = conn.cursor()
    
    # Check table structure
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'tmux_log' 
        ORDER BY ordinal_position
    """)
    
    print("=== tmux_log Table Structure ===")
    columns = cursor.fetchall()
    for col in columns:
        print(f"Column: {col[0]}, Type: {col[1]}, Nullable: {col[2]}, Default: {col[3]}")
    
    # Check if table has any data
    cursor.execute("SELECT COUNT(*) FROM tmux_log")
    count = cursor.fetchone()[0]
    print(f"\nTotal rows in table: {count}")
    
    # Show sample data if any
    if count > 0:
        cursor.execute("SELECT * FROM tmux_log LIMIT 3")
        print("\nSample data:")
        for row in cursor.fetchall():
            print(row)
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
