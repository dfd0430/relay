
from flask import request, render_template, redirect, url_for, jsonify
from SPARQLWrapper import SPARQLWrapper, JSON
from datetime import datetime
import pytz
import os
import json
from docker_functions import *
from SQLiteDB import *
from ontop import deploy_ontop_container

DATA_FILE = "combined_containers.json"

def load_combinations():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []


def save_combinations(combos):
    with open(DATA_FILE, "w") as f:
        json.dump(combos, f, indent=2)


def log_query(ip, container_name,container_id,db_connection, query,rows,db, obda_name):
    utc_now = datetime.utcnow()
    germany_tz = pytz.timezone('Europe/Berlin')
    germany_time = pytz.utc.localize(utc_now).astimezone(germany_tz)
    db.insert_log(ip, container_name, container_id,db_connection, query, germany_time, rows, obda_name)