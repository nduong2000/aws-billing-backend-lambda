import os
import sqlite3
import logging
import traceback
import time
from contextlib import contextmanager

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("db")

# Global SQLite connection - will be initialized when the module is loaded
_db_connection = None

def dict_factory(cursor, row):
    """Convert SQLite row to dictionary to match psycopg2 RealDictCursor behavior"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_connection():
    """Get the SQLite database connection"""
    global _db_connection
    
    if _db_connection is None:
        logger.info("Initializing in-memory SQLite database connection")
        # Create a new connection or return the existing one
        from config.db_init import initialize_db
        _db_connection = initialize_db()
        logger.info("In-memory SQLite database connection established successfully")
    
    return _db_connection

@contextmanager
def get_cursor():
    """Context manager for database cursor"""
    conn = get_connection()
    # Set up dictionary row factory
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    try:
        yield cursor
    finally:
        cursor.close()

def query(query_text, params=None):
    """Execute a query and return the results"""
    try:
        # Convert PostgreSQL-style placeholders (%s) to SQLite-style (?)
        query_text = query_text.replace('%s', '?')
        
        with get_cursor() as cursor:
            logger.debug(f"Executing query: {query_text}")
            if params:
                logger.debug(f"Query parameters: {params}")
            
            cursor.execute(query_text, params if params else [])
            
            if query_text.strip().upper().startswith(("SELECT", "WITH")):
                result = cursor.fetchall()
                logger.debug(f"Query returned {len(result) if result else 0} rows")
                return result
            
            get_connection().commit()
            if cursor.rowcount > 0:
                logger.debug(f"Query affected {cursor.rowcount} rows")
                return {"rowCount": cursor.rowcount}
            
            logger.debug("Query executed successfully (no rows affected)")
            return None
    except Exception as e:
        error_detail = str(e) + "\n" + traceback.format_exc()
        logger.error(f"Query error: {error_detail}")
        logger.error(f"Query: {query_text}")
        if params:
            logger.error(f"Parameters: {params}")
        
        # Re-raise the exception for the caller to handle
        raise

def test_connection():
    """Test database connection and return True if successful, False otherwise"""
    try:
        with get_cursor() as cursor:
            cursor.execute("SELECT 1 AS connection_test")
            result = cursor.fetchone()
            
            if result and result.get('connection_test') == 1:
                logger.info("Database connection test successful")
                
                # Additional schema validation
                try:
                    # Check if essential tables exist
                    tables_to_check = ['patients', 'providers', 'appointments', 'claims', 'claim_items', 'payments', 'services']
                    for table in tables_to_check:
                        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", [table])
                        if not cursor.fetchone():
                            logger.error(f"Schema validation failed: Table '{table}' does not exist")
                            return False
                    
                    logger.info("Schema validation successful")
                except Exception as schema_error:
                    logger.error(f"Schema validation error: {schema_error}")
                    return False
                
                return True
            else:
                logger.error("Database connection test failed: Unexpected result")
                return False
    except Exception as e:
        error_detail = str(e) + "\n" + traceback.format_exc()
        logger.error(f"Database connection test failed: {error_detail}")
        return False

def execute_transaction(queries):
    """Execute multiple queries in a single transaction"""
    conn = get_connection()
    try:
        # Set up dictionary row factory
        conn.row_factory = dict_factory
        with conn:  # This automatically handles commit/rollback
            cursor = conn.cursor()
            for query_text, params in queries:
                # Convert PostgreSQL-style placeholders (%s) to SQLite-style (?)
                query_text = query_text.replace('%s', '?')
                cursor.execute(query_text, params if params else [])
            
            return True
    except Exception as e:
        error_detail = str(e) + "\n" + traceback.format_exc()
        logger.error(f"Transaction error: {error_detail}")
        
        # Re-raise the exception for the caller to handle
        raise

# Initialize logging level based on environment
if os.getenv("NODE_ENV") == "development":
    logging.getLogger("db").setLevel(logging.DEBUG)
else:
    logging.getLogger("db").setLevel(logging.INFO)

# No need to test connection on module load as we're using in-memory database
# that will be created in main.py
