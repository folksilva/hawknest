"""

Data models:

TYPE:
- _id = ObjectId do tipo
- name = Nome do tipo
- level = Nível de acesso do tipo
- groups = Grupos com acesso ao tipo

GROUP
- _id = ObjectId do grupo
- name = Nome do grupo
- users = Usuários no grupo

PERMISSIONS
- _id = ObjectId da permissão (fixo como 'main')
- employees = Usuários com nível colaborador (2)
- managers = Usuários com nível gerente (3)

"""
import os
import secrets
from flask import Flask
from flask_simpleldap import LDAP
from flask_pymongo import PyMongo
from flask_cors import CORS
from session import MongoSessionInterface
from elasticsearch import Elasticsearch

app = Flask(__name__)

# Configure App
app.config['MONGO_URI'] = 'mongodb://%s/%s' % (
    os.getenv('MONGO_HOST'),
    os.getenv('MONGO_DBNAME')
)
app.config['LDAP_HOST'] = os.getenv('LDAP_HOST')
app.config['LDAP_USERNAME'] = os.getenv('LDAP_USERNAME')
app.config['LDAP_PASSWORD'] = os.getenv('LDAP_PASSWORD')
app.config['LDAP_BASE_DN'] = os.getenv('LDAP_BASE_DN')
app.config['LDAP_DOMAIN'] = os.getenv('LDAP_DOMAIN')
app.config['APP_NAME'] = os.getenv('APP_NAME', 'Hawknest')
app.config['ADMIN_USERS'] = os.getenv('ADMIN_USERS', '')
app.config['ELASTICSEARCH_URI'] = os.getenv('ELASTICSEARCH_URI')
app.config['ELASTICSEARCH_INDEX'] = os.getenv('ELASTICSEARCH_INDEX')
app.secret_key = secrets.token_urlsafe(128)

# Initialize extensions
mongo = PyMongo(app)
ldap = LDAP(app)
cors = CORS(app)
app.session_interface = MongoSessionInterface(db=mongo.db)
es = Elasticsearch([app.config['ELASTICSEARCH_URI']])
import util
import errors

# Configure routes
import document_views
import type_views
import group_views
import auth_views
import search_views
