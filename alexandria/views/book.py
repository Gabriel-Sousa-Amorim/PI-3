import logging
logger = logging.getLogger(__name__)
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView
from alexandria.models import Livro, Interesses, Troca   # <-- Use Interesses (singular)
from django.core.cache import cache
import requests
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from alexandria.forms import EditarLivroForm

class BookDetailView(DetailView):
    model = Livro
    template_name = 'book.html'
    context_object_name = 'livro'
    pk_url_kwarg = 'id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        livro = self.get_object()
        user = self.request.user
        dono = livro.id_dono
        context['confiabilidade_dono'] = dono.confiability if hasattr(dono, 'confiability') else None

        if user.is_authenticated:
            # Se for o dono, mostra total de interesses
            if user.id == dono.id:  # <-- compare ids corretamente
                context['total_interesses'] = Interesses.objects.filter(id_livro=livro).count()
            else:
                # Verifica se o usuário já tem Interesses
                context['ja_interessado'] = Interesses.objects.filter(id_usuario=user, id_livro=livro).exists()

        # Verifica se o usuário atual tem um Interesses aceito para este livro
        show_donor = False
        if user.is_authenticated:
            interesse_aceito = Interesses.objects.filter(  # <-- use nome diferente da classe
                id_usuario=user,
                id_livro=livro,
                status='A'
            ).first()
            show_donor = interesse_aceito is not None
        
        context['show_donor_details'] = show_donor

        # TOTAL DE AVALIAÇÕES DO LIVRO
        # Pega todas as trocas concluídas deste livro
        trocas_concluidas = Troca.objects.filter(id_dono=dono.id, status='C')

        # Conta quantas avaliações existem (nota do dono + nota do interessado)
        total_avaliacoes = trocas_concluidas.exclude(avaliacao_dono__isnull=True).count()
        total_avaliacoes += trocas_concluidas.exclude(avaliacao_interessado__isnull=True).count()

        context['total_avaliacoes'] = total_avaliacoes

        return context


import logging
from requests.exceptions import Timeout, ConnectionError, RequestException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=2, max=5),
    retry=retry_if_exception_type((Timeout, ConnectionError))
)
def chamar_openlibrary(params):
    url = 'https://openlibrary.org/search.json'
    # Timeout: (conexão, leitura) – leitura agora com 30s
    resp = requests.get(url, params=params, timeout=(5, 30))
    resp.raise_for_status()
    return resp

@csrf_exempt
@require_http_methods(["GET"])
def buscar_livros_api(request):
    termo = request.GET.get('q', '').strip()
    if not termo:
        return JsonResponse({'erro': 'Digite um termo para busca'}, status=400)

    params = {
        'q': termo,
        'fields': 'key,title,author_name,cover_i',
        'limit': 20
    }
    
    try:
        resp = chamar_openlibrary(params)
        dados = resp.json()
    except Timeout:
        logger.error("Timeout ao consultar OpenLibrary após retentativas")
        return JsonResponse({'erro': 'O serviço de busca está muito lento. Tente novamente mais tarde.'}, status=504)
    except ConnectionError:
        logger.error("Conexão falhou com OpenLibrary")
        return JsonResponse({'erro': 'Não foi possível conectar ao serviço de busca. Verifique sua internet.'}, status=503)
    except RequestException as e:
        logger.error(f"Erro na requisição: {e}")
        return JsonResponse({'erro': 'Erro ao consultar a API externa. Tente novamente.'}, status=500)
    except Exception as e:
        logger.exception(f"Erro inesperado: {e}")
        return JsonResponse({'erro': 'Erro interno no servidor.'}, status=500)

    resultados = []
    for doc in dados.get('docs', []):
        titulo = doc.get('title', 'Sem título')
        autor_lista = doc.get('author_name')
        autor = autor_lista[0] if autor_lista else 'Autor desconhecido'
        cover_id = doc.get('cover_i')
        key = doc.get('key', '')
        if key:
            resultados.append({
                'titulo': titulo,
                'autor': autor,
                'cover_id': cover_id,
                'key': key,
            })

    return JsonResponse(resultados, safe=False)

@login_required
def editar_livro(request, id):
    """View AJAX para editar livro inline"""
    livro = get_object_or_404(Livro, id=id)
    
    if request.user != livro.id_dono:
        return JsonResponse({'error': 'Permissão negada'}, status=403)
    
    if request.method == 'POST':
        form = EditarLivroForm(request.POST, instance=livro)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Livro atualizado com sucesso!'})
        else:
            return JsonResponse({'error': form.errors}, status=400)
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)



@login_required
def deletar_livro(request, id):
    livro = get_object_or_404(Livro, id=id)
    if request.user != livro.id_dono:
        messages.error(request, 'Permissão negada.')
        return redirect('perfil')
    if request.method == 'POST':
        titulo = livro.titulo
        Interesses.objects.filter(id_livro=livro).delete()
        livro.delete()
        messages.success(request, f'Livro "{titulo}" removido com sucesso.')
        return redirect('perfil')
    return redirect('perfil')

