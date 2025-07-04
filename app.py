import secrets

from flask import Flask, session
import os
from SQLiteDB import SQLiteDB
from ontop import init_directories

app = Flask(__name__)
UPLOAD_FOLDER = "/tmp/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs("/volume/backup", exist_ok=True)
init_directories()
# Setup DB
db = SQLiteDB("sqlite:////volume/backup/relay.db")
db.create_db_connection_table()
db.create_logs_table()
db.create_obda_configuration_table()
db.create_temp_db_connection_table()
db.create_temp_obda_configuration_table()
db.create_databank_table()
app.secret_key = secrets.token_hex(32)

# Register all routes
from routes import register_routes
register_routes(app, db)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
