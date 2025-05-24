from flask import Flask, session
import os
from SQLiteDB import SQLiteDB

app = Flask(__name__)
UPLOAD_FOLDER = "/tmp/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs("/volume/backup", exist_ok=True)

# Setup DB
db = SQLiteDB("sqlite:////volume/backup/relay.db")
db.create_db_connection_table()
db.create_logs_table()
db.create_obda_configuration_table()

app.secret_key = 'super_secret_key'
# Register all routes
from routes import register_routes
register_routes(app, db)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
