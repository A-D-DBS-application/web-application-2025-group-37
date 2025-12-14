from app import create_app
from app.extensions import db
from app.models import User

app = create_app()

with app.app_context():
    try:
        # Check if users already exist
        existing = User.query.filter(User.email.in_(['depot@opwielekes.be', 'finance@opwielekes.be', 'admin@opwielekes.be'])).all()
        if existing:
            print(f"Found {len(existing)} existing users, deleti            typeof bootstrapng them first...")
            for user in existing:
                db.session.delete(user)
            db.session.commit()
        
        # Create Depot Manager
        depot_mgr = User(
            first_name='Depot',
            last_name='Manager',
            email='depot@opwielekes.be',
            role='depot_manager'
        )
        depot_mgr.set_password('depot123')
        db.session.add(depot_mgr)
        print("✓ Created Depot Manager: depot@opwielekes.be / depot123")
        
        # Create Finance Manager
        finance_mgr = User(
            first_name='Finance',
            last_name='Manager',
            email='finance@opwielekes.be',
            role='finance_manager'
        )
        finance_mgr.set_password('finance123')
        db.session.add(finance_mgr)
        print("✓ Created Finance Manager: finance@opwielekes.be / finance123")
        
        # Create Admin
        admin = User(
            first_name='Admin',
            last_name='User',
            email='admin@opwielekes.be',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print("✓ Created Admin: admin@opwielekes.be / admin123")
        
        db.session.commit()
        print("\n✅ All test users created successfully!")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
