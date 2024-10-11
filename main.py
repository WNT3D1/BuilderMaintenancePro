import os
from app import app, db

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    
    # Ensure database tables are created
    with app.app_context():
        db.create_all()
    
    app.run(host="0.0.0.0", port=port, debug=False)
