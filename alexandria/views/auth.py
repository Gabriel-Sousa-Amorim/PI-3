from alexandria.forms import CadastroUsuarioForm
from alexandria.models import Interesses, Livro, Usuario
import alexandria.constants as app_constants
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect

class LoginView(TemplateView):
    """Página única com login à esquerda e cadastro à direita"""
    template_name = "login.html" 
    
    def dispatch(self, request, *args, **kwargs):
        # Se o usuário já está logado, redireciona para a home
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Adiciona o next se existir
        context['next'] = self.request.GET.get('next', 'home')
        return context

class SigninView(TemplateView):
    template_name = 'signin.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        form = CadastroUsuarioForm()
        return render(request, self.template_name, {'form': form, 'next': request.GET.get('next', 'home')})

    def post(self, request, *args, **kwargs):
        form = CadastroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Cadastro realizado com sucesso! Bem-vindo(a), {user.nome}.')
            return redirect('home')
        # Se o formulário for inválido, reexibe com os erros
        return render(request, self.template_name, {'form': form, 'next': request.POST.get('next', 'home')})

def get_estados_por_regiao(request):
    """Retorna JSON com os estados de uma região (usado pelo front-end)"""
    regiao = request.GET.get('regiao')
    if not regiao or regiao not in app_constants.REGIONS:
        return JsonResponse({'estados': []})
    estados_raw = app_constants.REGIONS[regiao].get('states', [])
    estados = [{'sigla': sigla, 'nome': dict(app_constants.STATE_CHOICES).get(sigla, sigla)} for sigla in estados_raw]
    return JsonResponse({'estados': estados})

class LogoutView(TemplateView):
    """Processa o logout"""
    http_method_names = ['get']
    
    def get(self, request, *args, **kwargs):
        logout(request)
        messages.info(request, 'Até logo, espero que nos encontremos bem na próxima.')
        return redirect('login')

class ProcessLogin(TemplateView):
    """Processa o login via POST"""
    http_method_names = ['post']
    
    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        password = request.POST.get('password')
        next_url = request.POST.get('next', 'home')
        
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Bem-vindo(a) de volta, {user.nome}!')
            return redirect('login')
        else:
            messages.error(request, 'E-mail ou senha inválidos.')
            return redirect('login')


class ProcessSignin(TemplateView):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        # 1. Pegar todos os dados do POST
        nome = request.POST.get('nome', '').strip()
        email = request.POST.get('email', '').strip()
        regiao = request.POST.get('regiao')
        estado = request.POST.get('estado')
        cidade = request.POST.get('cidade', '').strip()
        zona = request.POST.get('zona') or None  # campo opcional
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        terms = request.POST.get('terms')  # checkbox

        # 2. Validações de campo obrigatório
        if not nome:
            messages.error(request, 'O campo Nome é obrigatório.')
            return redirect('signin')
        if not email:
            messages.error(request, 'O campo E-mail é obrigatório.')
            return redirect('signin')
        if not regiao:
            messages.error(request, 'Selecione uma região.')
            return redirect('signin')
        if not estado:
            messages.error(request, 'Selecione um estado.')
            return redirect('signin')
        if not password:
            messages.error(request, 'A senha é obrigatória.')
            return redirect('signin')
        if not password_confirm:
            messages.error(request, 'Confirme sua senha.')
            return redirect('signin')
        if not terms:
            messages.error(request, 'Você deve aceitar os Termos de Uso.')
            return redirect('signin')

        # 3. Validação de senha (tamanho e igualdade)
        if len(password) < 8:
            messages.error(request, 'A senha deve ter pelo menos 8 caracteres.')
            return redirect('signin')
        if password != password_confirm:
            messages.error(request, 'As senhas não coincidem.')
            return redirect('signin')

        # 4. Validar se e-mail já existe
        if Usuario.objects.filter(email=email).exists():
            messages.error(request, 'Este e-mail já está cadastrado.')
            return redirect('signin')

        # 5. Validar se a região existe nas constantes
        regioes_validas = dict(app_constants.REGIONS_CHOICES)
        if regiao not in regioes_validas:
            messages.error(request, 'Região inválida.')
            return redirect('signin')

        # 6. Validar se o estado pertence à região escolhida
        estados_da_regiao = app_constants.REGIONS.get(regiao, {}).get('states', [])
        if estado not in estados_da_regiao:
            messages.error(request, f'O estado selecionado não pertence à região {regioes_validas[regiao]}.')
            return redirect('signin')

        # 7. Validar estado (se existe na lista oficial)
        estados_validos = dict(app_constants.STATE_CHOICES)
        if estado not in estados_validos:
            messages.error(request, 'Estado inválido.')
            return redirect('signin')

        # 8. Validar zona (se for preenchida, deve ser um dos valores permitidos)
        zonas_validas = ['N', 'L', 'S', 'O', 'C', 'X']
        if zona and zona not in zonas_validas:
            messages.error(request, 'Zona inválida.')
            return redirect('signin')

        # 9. Criação do usuário (usando o método create_user do manager)
        try:
            user = Usuario.objects.create_user(
                email=email,
                nome=nome,
                password=password,
                regiao=regiao,
                estado=estado,
                cidade=cidade or 'São Paulo',  # valor padrão se vazio
                zona=zona
            )
        except Exception as e:
            messages.error(request, f'Erro ao criar usuário: {str(e)}')
            return redirect('signin')

        # 10. Autenticar e logar automaticamente
        user_authenticated = authenticate(request, email=email, password=password)
        if user_authenticated:
            login(request, user_authenticated)
            messages.success(request, f'Cadastro realizado com sucesso! Bem-vindo(a), {nome}!')
            return redirect('home')
        else:
            messages.error(request, 'Não foi possível fazer login automaticamente. Faça o login manualmente.')
            return redirect('login')

        # Fallback (nunca deve chegar aqui)
        return redirect('signin')

def get_estados_por_regiao(request):
    """
    View que retorna uma lista de estados (sigla e nome)
    para a região informada via GET.
    Exemplo de uso: /get-estados-por-regiao/?regiao=SE
    """
    regiao = request.GET.get('regiao')
    
    # Verifica se a região existe nas constantes
    if not regiao or regiao not in app_constants.REGIONS:
        return JsonResponse({'estados': []})
    
    # Obtém as siglas dos estados daquela região
    estados_raw = app_constants.REGIONS[regiao].get('states', [])
    
    # Converte para lista de dicionários com sigla e nome completo
    estados = [
        {
            'sigla': sigla,
            'nome': dict(app_constants.STATE_CHOICES).get(sigla, sigla)
        }
        for sigla in estados_raw
    ]
    
    return JsonResponse({'estados': estados})

@login_required(login_url="login")
def aceitar_interesse(request, interesse_id):
    Interesses = get_object_or_404(Interesses, pk=interesse_id)
    livro = Interesses.id_livro
    
    # Verifica se o usuário logado é o dono do livro
    if request.user != livro.id_dono:
        messages.error(request, 'Você não tem permissão para aceitar este Interesses.')
        return redirect('detalhe_livro', pk=livro.id)
    
    # Se já aceito, não faz nada
    if Interesses.status == 'A':
        messages.info(request, 'Este Interesses já foi aceito.')
    else:
        Interesses.status = 'A'
        Interesses.save()
        messages.success(request, f'Interesses aceito! O usuário {Interesses.id_usuario.nome} agora pode ver seus dados de localização.')
    
    return redirect('detalhe_livro', pk=livro.id)