from app import create_app
from app.routes import main
import traceback

app = create_app()

print('Testing dashboard route...')
try:
    with app.app_context():
        with app.test_request_context('/dashboard'):
            from flask import session
            session['user_id'] = 'test-user-id'
            from app.routes import dashboard
            result = dashboard()
            print('✓ Dashboard route works!')
            print('Template rendered successfully')
except Exception as e:
    print('✗ Error in dashboard:')
    traceback.print_exc()
    import sys
    sys.exit(1)
