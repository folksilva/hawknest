import re
import secrets
import translitcodec
import codecs
from flask import request, g, abort, session
from main import app, ldap, mongo

def convert(data):
    """Converts bytes to string"""
    if isinstance(data, bytes):      return data.decode('utf-8','ignore')
    if isinstance(data, dict):       return dict(map(convert, data.items()))
    if isinstance(data, tuple):      return tuple(map(convert, data))
    if isinstance(data, list):       return list(map(convert, data))
    if isinstance(data, set):        return set(map(convert, data))
    return data

@app.before_request
def before_request():
    g.user = None
    g.username = None
    g.groups = []
    g.level = 1
    if 'user_id' in session:
        g.user = convert(ldap.get_object_details(user=session['user_id']))
        g.username = g.user['sAMAccountName'][0]
        g.groups = list(mongo.db.groups.find({'users': g.username}))
        permissions = mongo.db.permissions.find_one({'_id': 'main'})
        if g.username in app.config['ADMIN_USERS'].split(','):
            g.level = 4
        elif permissions:
            if g.username in permissions['managers']:
                g.level = 3
            elif g.username in permissions['employees']:
                g.level = 2
            else:
                g.level = 1
    app.jinja_env.globals['csrf_token'] = generate_csrf_token
    app.jinja_env.globals['types'] = get_types()
    app.jinja_env.globals['get_path'] = get_path

#@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(403)

@app.template_filter('pluralize')
def pluralize(number, singular='', plural='s'):
    if number == 1:
        return singular
    return plural

@app.template_filter('filename')
def filename(path):
    return path.split('/')[-1]

@app.template_filter('filesize')
def filesize(size):
    power = 2 ** 10
    n = 0
    power_n = {0:'', 1:'K', 2:'M', 3:'G', 4:'T'}
    while size > power:
        size /= power
        n += 1
    return '{0:.2f} {1}b'.format(size, power_n[n])

@app.template_filter('datetime')
def format_datetime(value, format='medium'):
    if format == 'full':
        format = '%A, %d de %B de %Y %H:%M'
    elif format == 'medium':
        format = '%d/%m/%Y %H:%M'
    return value.strftime(format)

@app.template_filter('sort_docs')
def sort_docs(docs):
    def sorter(doc):
        doc_type = 'D' if doc['doc_type'] == 'dir' else 'F'
        doc_time = doc['creation_date'].timestamp()
        return '{}-{}'.format(doc_type, doc_time)
    return sorted(docs, key=sorter)


def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_urlsafe(64)
    return session['_csrf_token']


def get_path(type_id, path):
    parts = path.split('/')
    slug = parts[-1]
    path = '/'.join(parts[:-1])
    return mongo.db.documents.find_one({'type':type_id, 'path':path, 'slug':slug})

def get_types():
    user_groups = [group['_id'] for group in g.groups]
    user_level = g.level
    type_query = {}
    if user_level < 3:
        type_query = {
            '$or': [
                {'groups':{'$in': user_groups}},
                {'groups':{'$size': 0}}
            ],
            'level': {
                '$lte': user_level
            }
        }
    return list(mongo.db.types.find(type_query))

def get_groups():
    return list(mongo.db.groups.find({}))

def get_all_groups():
    return list(mongo.db.groups.find({}))

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')

def slugify(text, delim=u'-'):
    """
    Generates an ASCII-only slug.
    http://flask.pocoo.org/snippets/5/
    """
    result = []
    for word in _punct_re.split(text.lower()):
        word = codecs.encode(word, 'translit/long')
        if word:
            result.append(word)
    return delim.join(result)