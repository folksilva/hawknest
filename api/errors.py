from main import app
from flask import render_template

@app.errorhandler(400)
def bad_request(e):
    return render_template(
        'error.html', 
        code=400, 
        icon='mood_bad',
        message='Inválido', 
        description='O servidor não é capaz de entender a sua requisição, verifique se as informações estão corretas.'
    ), 400

@app.errorhandler(401)
def unauthorized(e):
    return render_template(
        'error.html', 
        code=401, 
        icon='lock',
        message='Não Autorizado', 
        description='Você não está autorizado a utilizar este recurso.'
    ), 401

@app.errorhandler(403)
def forbidden(e):
    return render_template(
        'error.html', 
        code=403, 
        icon='block',
        message='Acesso Proibido', 
        description='O uso deste recurso está negado para você no momento.'
    ), 403

@app.errorhandler(404)
def not_found(e):
    return render_template(
        'error.html', 
        code=404, 
        icon='warning',
        message='Não Encontrado', 
        description='O servidor não encontrou o recurso que você solicitou, verifique se digitou o endereço corretamente.'
    ), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template(
        'error.html', 
        code=500, 
        icon='error',
        message='Erro Interno', 
        description='Ocorreu uma falha interna no servidor, tente novamente em instantes, caso o problema continue entre em contato com o suporte.'
    ), 500
