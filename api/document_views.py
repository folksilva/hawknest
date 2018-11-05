import os
import re
from flask import request, render_template, redirect, url_for, flash, abort, g
from main import app, ldap, mongo, es
from bson import ObjectId
from util import slugify
from datetime import datetime
from werkzeug.utils import secure_filename
import nlp

@app.route('/download/<path:filename>', methods=['GET'])
@ldap.login_required
def download(filename):
    """Download a file"""
    return mongo.send_file(filename)

@app.route('/archive/d/<path:path>/<ObjectId:doc_id>', defaults={'type_id':None})
@app.route('/<ObjectId:type_id>/d/<path:path>/<ObjectId:doc_id>')
@ldap.login_required
def document(type_id, path, doc_id):
    """Show a document"""
    type_item = None
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
    elif g.level < 3:
        return abort(401)
    
    document = mongo.db.documents.find_one_or_404({
        '_id': doc_id
    })
    if g.level < 3 and g.level < document['level']:
        return abort(401)

    return render_template(
        'file.html',
        type_item=type_item,
        path=path,
        path_parts=path.split('/') if path else [],
        document=document
    )

@app.route('/<ObjectId:type_id>/d/<path:path>/<ObjectId:doc_id>/archive', methods=['GET', 'POST'])
def archive_document(type_id, path, doc_id):
    type_item = mongo.db.types.find_one_or_404({'_id': type_id})
    invalid_level = type_item['level'] > g.level
    path = path[:-1] if path.endswith('/') else path
    
    if g.level < 3:
        type_groups = type_item['groups']
        user_groups = [group['_id'] for group in g.groups]
        invalid_group = len(type_groups) > 0 and set(user_groups).isdisjoint(type_groups)
    else:
        invalid_group = False
    if invalid_level or invalid_group:
        return abort(401)

    document = mongo.db.documents.find_one_or_404({
        '_id': doc_id
    })
    if g.level < 3 and g.level < document['level']:
        return abort(401)
    
    if request.method == 'POST':
        parent_path = '/'.join(path.split('/')[:-1])
        total = 1
        if document['doc_type'] == 'dir':
            path_regex = re.compile('^{}'.format(path))
            total += mongo.db.documents.update_many({
                'type': type_id,
                'path': path_regex
            }, {
                '$set': {'type': None}
            }).modified_count
            es.update_by_query(
                index=app.config['ELASTICSEARCH_INDEX'],
                doc_type='documents',
                body={
                    'script': {
                        'lang': 'painless',
                        'source': 'ctx._source.type=null'
                    },
                    'query': {
                        'bool': {
                            'must': [
                                {
                                    'term': {
                                        'type': str(type_id)
                                    }
                                },
                                {
                                    'regexp': {
                                        'path.keyword': '{}.*'.format(path)
                                    }
                                }
                            ]
                        }
                    }
                }
            )

        mongo.db.documents.update_one({
            '_id': doc_id
        }, {
            '$set':{'type': None}
        })
        es.update(
            index=app.config['ELASTICSEARCH_INDEX'],
            doc_type='documents',
            id=str(doc_id),
            body={
                'doc': {
                    'type': None
                }
            }
        )

        if total > 1:
            flash('{} itens foram movidos para o arquivo.'.format(total))
        elif total == 0:
            flash('Nenhum item foi movido para o arquivo.')
        else:
            flash('Um item foi movido para o arquivo.')
        return redirect(url_for('index', type_id=str(type_id), path=parent_path))
    
    return render_template(
        'archive.html',
        type_item=type_item,
        path=path,
        path_parts=path.split('/') if path else [],
        document=document
    )