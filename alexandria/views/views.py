from django.shortcuts import render
from django.shortcuts import render

def como_funciona(request):
    return render(request, 'howItWorks.html')

def error_400(request, exception=None):
    return render(request, 'error.html', {
        'error_code': 400,
        'error_title': 'Requisição inválida',
        'error_message': 'A requisição não pôde ser processada. Verifique os dados enviados.'
    }, status=400)

def error_403(request, exception=None):
    return render(request, 'error.html', {
        'error_code': 403,
        'error_title': 'Acesso negado',
        'error_message': 'Você não tem permissão para acessar esta página.'
    }, status=403)

def error_404(request, exception=None):
    return render(request, 'error.html', {
        'error_code': 404,
        'error_title': 'Página não encontrada',
        'error_message': 'O livro ou página que você procura não está disponível. Pode ter sido removido ou o endereço está incorreto.'
    }, status=404)

def error_500(request):
    return render(request, 'error.html', {
        'error_code': 500,
        'error_title': 'Erro interno',
        'error_message': 'Ocorreu uma falha no servidor. Nossa equipe foi notificada e está trabalhando na solução.'
    }, status=500)