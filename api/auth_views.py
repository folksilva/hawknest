from flask import request, render_template, redirect, url_for, flash, session, g, abort
from main import app, ldap, mongo

@app.route('/permissions', methods=['GET', 'POST'])
@ldap.login_required
def permissions():
    """List and update users permission levels"""
    if g.level < 4:
        return abort(401)
    permissions = mongo.db.permissions.find_one({'_id': 'main'})
    if request.method == 'POST':
        permissions_data = {
            '_id': 'main',
            'employees': request.form.get('employees').split(','),
            'managers': request.form.get('managers').split(',')
        }
        if permissions:
            mongo.db.permissions.update_one({'_id':'main'},{'$set':permissions_data})
        else:
            mongo.db.permissions.insert_one(permissions_data)
        return redirect(url_for('permissions'))
    
    if not permissions:
        permissions = {
            '_id': 'main',
            'employees': [],
            'managers': []
        }
    return render_template(
        'permissions.html',
        permissions=permissions
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    next = request.args.get('next', url_for('index'))
    if g.user:
        return redirect(next)

    error = None
    if request.method == 'POST':
        username = '%s@%s' % (request.form.get('username'), 
                              app.config['LDAP_DOMAIN'])
        password = request.form.get('password')
        if username and password:
            bind = ldap.bind_user(
                username, 
                password
            )
            if bind:
                session['user_id'] = username
                return redirect(next)
            error = 'INCORRECT_CREDENTIALS'
        else:
            error = 'NO_CREDENTIALS'

    return render_template(
        'login.html', 
        next=next,
        error=error
    )

@app.route('/logout')
@ldap.login_required
def logout():
    del session['user_id']
    g.user = None
    g.ldap_groups = None
    return redirect(url_for('login'))