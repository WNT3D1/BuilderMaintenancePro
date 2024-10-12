import os
from app import app, db

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    
    # Ensure database tables are created
    with app.app_context():
        db.create_all()
    
    # Use Gunicorn for production
    if os.environ.get('FLASK_ENV') == 'production':
        import gunicorn.app.base

        class StandaloneApplication(gunicorn.app.base.BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()

            def load_config(self):
                config = {key: value for key, value in self.options.items()
                          if key in self.cfg.settings and value is not None}
                for key, value in config.items():
                    self.cfg.set(key.lower(), value)

            def load(self):
                return self.application

        options = {
            'bind': f'0.0.0.0:{port}',
            'workers': 4,
            'worker_class': 'sync',
        }
        StandaloneApplication(app, options).run()
    else:
        app.run(host="0.0.0.0", port=port)
