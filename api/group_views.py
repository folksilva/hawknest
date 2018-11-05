from flask import request, render_template, redirect, url_for, flash, g, abort
from main import app, ldap, mongo
from util import get_all_groups
from bson import ObjectId

@app.route('/groups', methods=['GET', 'POST'])
@ldap.login_required
def groups():
    """List all groups or create a new one"""
    if g.level < 4:
        return abort(401)
    if request.method == 'POST':
        group_name = request.form.get('name', None)
        if not group_name:
            flash('Informe o nome do grupo para criar')
            return redirect(url_for('groups'))
        group_id = mongo.db.groups.insert_one({
            'name': group_name,
            'users': [g.username]
        }).inserted_id
        return redirect(url_for('group', group_id=str(group_id)))
    groups = get_all_groups()
    return render_template(
        'groups-index.html', 
        groups=groups
    )

@app.route('/groups/<group_id>', methods=['GET', 'POST'])
@ldap.login_required
def group(group_id):
    """Get or update a group"""
    if g.level < 4:
        return abort(401)
    group_item = mongo.db.groups.find_one_or_404({'_id': ObjectId(group_id)})
    if request.method == 'POST':
        users = request.form.get('users', '').split(',')
        mongo.db.groups.update_one(
            {'_id': ObjectId(group_id)},
            {'$set': {'users': users}}
        )
        return redirect(url_for('group', group_id=group_id))
    return render_template(
        'groups-view.html', 
        group={
            '_id': str(group_item['_id']),
            'name': group_item['name'],
            'users': group_item['users']
        }
    )

@app.route('/groups/<group_id>/delete', methods=['GET', 'POST'])
@ldap.login_required
def group_delete(group_id):
    """Remove a group"""
    group_item = mongo.db.groups.find_one_or_404({'_id': ObjectId(group_id)})
    if request.method == 'POST':
        count_types = mongo.db.types.update_many(
            {},
            {
                '$pull': {
                    'groups': ObjectId(group_id)
                }
            }
        ).modified_count
        mongo.db.groups.delete_one({'_id': ObjectId(group_id)})
        if count_types > 1:
            flash('Grupo {} excluído e removido de {} tipos de documentos.'.format(group_item['name'], count_types))
        elif count_types == 0:
            flash('Grupo {} excluído.'.format(group_item['name']))
        else:
            flash('Grupo {} excluído e removido de um tipo de documento.'.format(group_item['name']))
        return redirect(url_for('groups'))
    return render_template(
        'groups-delete.html',
        group=group_item
    )