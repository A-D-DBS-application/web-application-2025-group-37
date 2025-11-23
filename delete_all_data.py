from app import create_app, db
from app.models import Member, Child, Bike, Rental, Payment, Item

app = create_app()

with app.app_context():
    # Verwijder eerst gerelateerde data (foreign keys)
    Payment.query.delete()
    print("✅ Alle betalingen verwijderd")
    
    Rental.query.delete()
    print("✅ Alle verhuringen verwijderd")
    
    Child.query.delete()
    print("✅ Alle kinderen verwijderd")
    
    # Nu kunnen we leden en fietsen verwijderen
    Member.query.delete()
    print("✅ Alle leden verwijderd")
    
    Bike.query.delete()
    print("✅ Alle fietsen verwijderd")
    
    Item.query.delete()
    print("✅ Alle items verwijderd")
    
    db.session.commit()
    print("\n✅ Alle data succesvol verwijderd uit de database!")
