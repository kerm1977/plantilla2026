from app import app, db
from flask_migrate import Migrate

# Configurar Flask-Migrate
migrate = Migrate(app, db)

if __name__ == '__main__':
    app.run(debug=True)
