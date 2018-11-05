import os
from flask import request, render_template, redirect, url_for, flash, abort, g
from main import app, ldap, mongo, es
from bson import ObjectId
from bson.json_util import dumps
from util import slugify, get_types
from datetime import datetime
from werkzeug.utils import secure_filename
import nlp
import json
from gridfs import GridFS
import tempfile

@app.route('/search')
@ldap.login_required
def search():
    """
    Search for a file, required parameter "q" is the term to search for

    Possible filters:
     - type = Limit only for this type of files
     - path = Limit only for files in this directory
    
    The search automatically add the following filters:
     - level = Limit only for files of level lowest or equals to current user's level
     - group = Limit only for files with least one group of the current user
    
    Extra parameters:
     - page = The number of page
    """
    query_text = request.args.get('q', '').lower()
    if not query_text:
        return abort(400)
    
    type_item=None
    type_id = request.args.get('type', None)
    path = request.args.get('path', '')
    page_size = 20
    page = int(request.args.get('page', 1)) - 1
    
    if type_id:
        type_item = mongo.db.types.find_one_or_404({'_id': ObjectId(type_id)})
        invalid_level = type_item['level'] > g.level
        if g.level < 3:
            type_groups = type_item['groups']
            user_groups = [group['_id'] for group in g.groups]
            invalid_group = len(type_groups) > 0 and set(user_groups).isdisjoint(type_groups)
        else:
            invalid_group = False
        if invalid_level or invalid_group:
            return abort(401)
        query_type = [type_id]
    else:
        query_type = [str(t['_id']) for t in get_types()]

    inherited_level = 1
    query = {
        'query': { 'bool': { 'must': [
            {'term': {'doc_type': 'doc'}},  # Only documents
            {'range': {'level': { 'lt': g.level + 1 }}},  # Only lower or equal than current user level
            {'terms': {'type.keyword': query_type}},  # Only allowed types
            {'regexp': {'path.keyword': '{}.*'.format(path)}},  # Only inside this path
            {'bool': {'should': [
                {'match': {'entities': '{}^6'.format(query_text)}},  # Match term in entities with 6 of boost
                {'match': {'name_lower': '{}^3'.format(query_text)}},  # Match term in name with 3 of boost
                {'match': {'description_lower': '{}'.format(query_text)}}  # Match term in description with no boost
            ], 'minimum_should_match': '1'}}  # Should match at least one of the above
        ]}},
        'size': page_size,
        'from': page_size * page
    }
    results = es.search(
        index=app.config['ELASTICSEARCH_INDEX'],
        doc_type='documents',
        body=query
    )
    
    return render_template(
        'search.html',
        type_item=type_item,
        path=None,
        query_text=query_text,
        inherited_level=inherited_level,
        results=results
    )


@app.route('/archive', defaults={'path':''})
@app.route('/archive/d/<path:path>')
@ldap.login_required
def archive(path=''):
    """Show archived documents and directories"""
    if g.level < 3:
        return abort(401)
    inherited_level = 1
    type_item=None
    items = None
    items_filter = {
        'type':None, 
        'doc_type': 'doc'
    }
    if path:
        path = path[:-1] if path.endswith('/') else path
        path_parts = path.split('/')
        path_slug = path_parts[-1]
        path_parent = os.path.join(*path_parts[:-1]) if len(path_parts) > 1 else ''
        parent = mongo.db.documents.find_one_or_404({
            'type': None,
            'slug': path_slug,
            'path': path_parent
        })
    
    items = list(mongo.db.documents.find(items_filter))
        
    return render_template(
        'app.html',
        type_item=type_item,
        path=path + '/' if path else '',
        path_parts=path.split('/') if path else [],
        inherited_level=inherited_level,
        items=items
    )


@app.route('/', defaults={'type_id':'','path':''})
@app.route('/<ObjectId:type_id>/d/', defaults={'path':''})
@app.route('/<ObjectId:type_id>/d/<path:path>/')
@ldap.login_required
def index(type_id='', path=''):
    """Show documents and directories"""
    inherited_level = 1
    type_item=None
    items = None
    path = path[:-1] if path.endswith('/') else path
    items_filter = {
        'type': type_id,
        'path': path
    }
    if type_id:
        type_item = mongo.db.types.find_one_or_404({'_id': type_id})
        invalid_level = type_item['level'] > g.level
        if g.level < 3:
            type_groups = type_item['groups']
            user_groups = [group['_id'] for group in g.groups]
            invalid_group = len(type_groups) > 0 and set(user_groups).isdisjoint(type_groups)
        else:
            invalid_group = False
        if invalid_level or invalid_group:
            return abort(401)
        items_filter['type'] = type_id
    
    if path:
        path_parts = path.split('/')
        path_slug = path_parts[-1]
        path_parent = os.path.join(*path_parts[:-1]) if len(path_parts) > 1 else ''
        parent = mongo.db.documents.find_one_or_404({
            'type': type_id,
            'slug': path_slug,
            'path': path_parent
        })
        if g.level < 3 and g.level < parent['level']:
            return abort(401)
        if parent['doc_type'] == 'doc':
            return redirect(url_for('document', type_id=type_id, path=path, doc_id=str(parent['_id'])))
        
    items = list(mongo.db.documents.find(items_filter))
        
    return render_template(
        'app.html',
        type_item=type_item,
        path=path,
        path_parts=path.split('/') if path else [],
        inherited_level=inherited_level,
        items=items
    )




@app.route('/<ObjectId:type_id>/d/create', defaults={'path':''}, methods=['GET','POST'])
@app.route('/<ObjectId:type_id>/d/<path:path>/create', methods=['GET','POST'])
@ldap.login_required
def create(type_id='', path=''):
    """Create a document or directory"""
    if g.level < 2:
        return abort(401)
    inherited_level = 1
    type_item=None
    path = path[:-1] if path.endswith('/') else path

    if type_id:
        type_item = mongo.db.types.find_one_or_404({'_id': type_id})
        inherited_level = type_item['level']
        invalid_level = type_item['level'] > g.level
        if g.level < 3:
            type_groups = type_item['groups']
            user_groups = [group['_id'] for group in g.groups]
            invalid_group = len(type_groups) > 0 and set(user_groups).isdisjoint(type_groups)
        else:
            invalid_group = False
        if invalid_level or invalid_group:
            return abort(401)
    if path:
        path_parts = path.split('/')
        path_slug = path_parts[-1]
        path_parent = os.path.join(*path_parts[:-1]) if len(path_parts) > 1 else ''
        parent = mongo.db.documents.find_one_or_404({
            'type': type_id,
            'slug': path_slug,
            'path': path_parent
        })
        if g.level < 3 and g.level < parent['level']:
            return abort(401)
        if parent['doc_type'] == 'doc':
            return abort(400)

    if request.method == 'POST':
        doc_name = request.form.get('name')
        doc_description = request.form.get('description')
        doc_type = request.form.get('doc_type')
        doc_level = int(request.form.get('level', 1))
        doc_slug = slugify(doc_name)
        item_exists = mongo.db.documents.count_documents({'path':path, 'slug':doc_slug}) > 0
        if item_exists:
            flash('Já existe um item com o nome "{}", informe outro nome'.format(doc_name))
            return redirect(url_for('create', type_id=type_id, path=path))
        doc_data = {
            'slug': doc_slug,
            'doc_type': doc_type,
            'name': doc_name,
            'name_lower': doc_name.lower(),
            'description': doc_description,
            'description_lower': doc_description.lower(),
            'path': path,
            'level': doc_level,
            'type': type_id,
            'creator': g.username,
            'creation_date': datetime.utcnow(),
            'entities': [],
            'file': None,
            'file_size': 0
        }
        if doc_type == 'doc':
            file = request.files['file']
            filename = secure_filename(file.filename)
            filepath = os.path.join(str(type_id), path, filename)
            tmp_file = os.path.join(tempfile.gettempdir(), filename)
            file.save(tmp_file)
            try:
                file_text = nlp.extract_text(tmp_file)
                file_entities = nlp.get_entities(file_text)
            except Exception as err:
                app.logger.error(err)
                flash('O arquivo está salvo, porém não foi possível ler o conteúdo, ele pode estar corrompido ou em um formato inválido')
                file_entities = []
            
            mongo.save_file(filepath, open(tmp_file, 'rb'))
            doc_data['file'] = filepath
            doc_data['file_size'] = os.stat(tmp_file).st_size
            doc_data['entities'] = [entity.lower() for entity in file_entities]
            os.remove(tmp_file)
        doc_id = mongo.db.documents.insert_one(doc_data).inserted_id
        doc_data['type'] = str(doc_data['type'])
        del doc_data['_id']
        res = es.index(
            index=app.config['ELASTICSEARCH_INDEX'],
            doc_type='documents',
            id=str(doc_id),
            body=doc_data
        )
        return redirect(url_for('index', type_id=type_id, path=os.path.join(path, doc_slug)))

    return render_template(
        'create.html',
        type_item=type_item,
        path=path,
        path_parts=path.split('/') if path else [],
        inherited_level=inherited_level
    )