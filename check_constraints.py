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
    
    # Check table constraints
    cursor.execute("""
        SELECT kcu.column_name, tc.constraint_name, tc.constraint_type 
        FROM information_schema.table_constraints tc 
        JOIN information_schema.key_column_usage kcu 
        ON tc.constraint_name = kcu.constraint_name 
        WHERE tc.table_name = 'tmux_log' 
        AND tc.constraint_type IN ('PRIMARY KEY', 'UNIQUE')
    """)
    
    print("=== tmux_log Table Constraints ===")
    constraints = cursor.fetchall()
    for constraint in constraints:
        print(f"Column: {constraint[0]}, Constraint: {constraint[1]} ({constraint[2]})")
    
    # Check if code column has any constraints
    cursor.execute("""
        SELECT column_name, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'tmux_log' AND column_name = 'code'
    """)
    
    print("\n=== Code Column Details ===")
    code_col = cursor.fetchone()
    if code_col:
        print(f"Column: {code_col[0]}, Nullable: {code_col[1]}, Default: {code_col[2]}")
    else:
        print("Code column not found")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
