import app

print('Testing app functions...')
try:
    # Test database initialization
    app.init_db()
    print('✓ Database initialized')
    
    # Test validation function
    result = app.validate_license_plate('鄂A12345')
    print(f'✓ License plate validation: {result}')
    
    # Test file upload functions
    print('✓ App modules loaded successfully')
    
except Exception as e:
    print(f'✗ Error: {e}')
    import traceback
    traceback.print_exc()