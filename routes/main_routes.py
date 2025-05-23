# routes/main_routes.py
import os
import json
from SPARQLWrapper import SPARQLWrapper, JSON
from flask import Flask, request, render_template, redirect, url_for,jsonify, flash
from docker_functions import *
from werkzeug.utils import secure_filename
from SQLiteDB import *
from ontop import deploy_ontop_container
from datetime import datetime
import pytz
from flask import render_template

def register_main_routes(app, db):
    @app.route("/")
    def index():
        return render_template("home.html")


    @app.route("/init", methods=["POST"])
    def initialize():
        try:
            from docker_functions import setup_nginx
            setup_nginx()
            return render_template("home.html", setup_result="Setup complete!")
        except Exception as e:
            return render_template("home.html", setup_result=f"Setup failed: {str(e)}")



