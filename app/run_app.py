import app
import sys
import os

if __name__ == '__main__':
    print("Starting Flask application...")
    try:
        # Initialize database
        app.init_db()
        print("Database initialized")
        
        # Add test data
        app.add_test_data()
        print("Test data added")
        
        # Start Flask app
        print("Starting Flask server on http://localhost:5000")
        app.app.run(host='0.0.0.0', port=5000, debug=False)
        
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)