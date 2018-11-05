from flask import request, render_template, redirect, url_for, flash, g, abort
from main import app, ldap, mongo, es
from util import get_all_groups
from bson import ObjectId

@app.route('/types/new', methods=['GET', 'POST'])
@ldap.login_required
def new_type():
    """Create a new type of file"""
    if g.level < 3:
        return abort(401)
    if request.method == 'POST':
        type_name = request.form.get('name')
        type_level = int(request.form.get('level', 1))
        type_groups = request.form.get('groups', ',').split(',')
        type_data = {
            'name': type_name,
            'level': type_level,
            'groups': [ObjectId(group) for group in type_groups if group]
        }
        type_id = mongo.db.types.insert_one(type_data).inserted_id
        return redirect(url_for('index', type=str(type_id)))
    groups = get_all_groups()
    return render_template(
        'types-new.html',
        type_id=None,
        groups=groups
    )

@app.route('/types/<ObjectId:type_id>', methods=['GET','POST'])
@ldap.login_required
def type(type_id):
    """Update a type of file"""
    if g.level < 3:
        return abort(401)
    type_item = mongo.db.types.find_one_or_404({'_id': type_id})
    if request.method == 'POST':
        type_name = request.form.get('name')
        type_level = int(request.form.get('level', 1))
        type_groups = request.form.get('groups', ',').split(',')
        type_data = {
            'name': type_name,
            'level': type_level,
            'groups': [ObjectId(group) for group in type_groups if group]
        }
        mongo.db.types.update_one(
            {'_id': type_id},
            {'$set': type_data}
        )
        return redirect(url_for('index', type=str(type_id)))
    groups = get_all_groups()
    return render_template(
        'types-view.html',
        type_id=type_id,
        type={
            '_id': str(type_item['_id']),
            'name': type_item['name'],
            'level': type_item['level'],
            'groups': [str(group) for group in type_item['groups']]
        },
        groups=groups
    )

@app.route('/types/<ObjectId:type_id>/delete', methods=['GET','POST'])
@ldap.login_required
def type_delete(type_id):
    """Delete a type of file"""
    if g.level < 3:
        return abort(401)
    type_item = mongo.db.types.find_one_or_404({'_id': type_id})
    if request.method == 'POST':
        total = mongo.db.documents.update_many({
            'type': type_id
        }, {
            '$set': {'type': None}
        }).modified_count
        es.update_by_query(
            index=app.config['ELASTICSEARCH_INDEX'],
            doc_type='documents',
            body={
                'doc': {
                    'type': null
                },
                'query': {
                    'term': {
                        'type': str(type_id)
                    }
                }
            }
        )
        mongo.db.types.delete_one({'_id': type_id})
        if total > 1:
            flash('Tipo {} excluído! {} itens foram movidos para o arquivo.'.format(type_item['name'], total))
        elif total == 0:
            flash('Tipo {} excluído! Nenhum item foi movido para o arquivo.'.format(type_item['name']))
        else:
            flash('Tipo {} excluído! Um item foi movido para o arquivo.'.format(type_item['name']))
        return redirect(url_for('index'))
    return render_template(
        'types-delete.html',
        type=type_item
    )