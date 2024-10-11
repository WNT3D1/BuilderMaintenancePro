import os
from app import app

if __name__ == "__main__":
    is_production = os.environ.get('FLASK_ENV') == 'production'
    host = '0.0.0.0'
    port = int(os.environ.get('PORT', 5000))
    debug = not is_production
    app.run(host=host, port=port, debug=debug)
