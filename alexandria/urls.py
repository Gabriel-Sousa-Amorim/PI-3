"""
URL configuration for alexandria project.

The `urlpatterns` list routes URLs to Home.as_view() more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from alexandria.forms import CadastroUsuarioForm

from alexandria.views.home import Home
from alexandria.views.explore import Explore
from alexandria.views.auth import SigninView, LoginView, ProcessLogin, ProcessSignin, LogoutView, get_estados_por_regiao
from alexandria.views.profile import ProfileView, atualizar_perfil, desativar_conta, alterar_senha, get_notification_counts
from alexandria.views.book import BookDetailView, buscar_livros_api,  editar_livro, deletar_livro
from alexandria.views.addBooks import adicionar_livro
from alexandria.views.interest import lista_interessados, registrar_interesse, aceitar_interesse, recusar_interesse, finalizar_troca, avaliar_troca, desistir_troca
from alexandria.views.views import como_funciona, error_400, error_403, error_404, error_500
from django.conf.urls import handler400, handler403, handler404, handler500

handler400 = 'alexandria.views.views.error_400'  # Bad Request
handler403 = 'alexandria.views.views.error_403'  # Forbidden
handler404 = 'alexandria.views.views.error_404'  # Not Found
handler500 = 'alexandria.views.views.error_500'  # Internal Server Error

urlpatterns = [
    # Páginas principais e estáticas
    path("", Home.as_view(), name="home"),
    path("explorar/", Explore.as_view(), name="explorar"),
    path("como-funciona/", como_funciona, name="como-funciona"),
    path("termos/", Home.as_view(), name="termos"),
    path("privacidade/", Home.as_view(), name="privacidade"),
    path("suporte/", Home.as_view(), name="suporte"),
    path("regioes/", Home.as_view(), name="regioes"),  # mantido por compatibilidade

    # Autenticação
    path("entrar/", LoginView.as_view(), name="login"),
    path("cadastrar/", SigninView.as_view(), name="signin"),
    path("sair/", LogoutView.as_view(), name="logout"),
    path("auth/login/", ProcessLogin.as_view(), name="auth_login"),
    path("auth/cadastrar/", ProcessSignin.as_view(), name="auth_signin"),

    # Perfil do usuário
    path("perfil/", ProfileView.as_view(), name="perfil"),
    path("perfil/editar/", atualizar_perfil, name="atualizar_perfil"),
    path("perfil/alterar-senha/", alterar_senha, name="alterar_senha"),
    path("perfil/desativar/", desativar_conta, name="desativar_conta"),

    # Livros (CRUD e detalhes)
    path("livros/adicionar/", adicionar_livro, name="adicionar_livro"),
    path("livros/<int:id>/", BookDetailView.as_view(), name="detalhe_livro"),
    path("livros/<int:id>/editar/", editar_livro, name="editar_livro"),
    path("livros/<int:id>/deletar/", deletar_livro, name="deletar_livro"),

    # Interesses em livros
    path("livros/<int:id>/interessar/", registrar_interesse, name="registrar_interesse"),
    path("livros/<int:id>/interessados/", lista_interessados, name="interesses_livro"),
    path("interesses/<int:id>/aceitar/", aceitar_interesse, name="aceitar_interesse"),
    path("interesses/<int:id>/recusar/", recusar_interesse, name="recusar_interesse"),

    # Trocas
    path("trocas/<int:troca_id>/desistir/", desistir_troca, name="desistir_troca"),
    path("trocas/<int:troca_id>/finalizar/", finalizar_troca, name="finalizar_troca"),
    path("trocas/<int:troca_id>/avaliar/", avaliar_troca, name="avaliar_troca"),

    # API (endpoints para requisições JS)
    path("api/buscar-livros/", buscar_livros_api, name="buscar_livros"),
    path("api/estados-por-regiao/", get_estados_por_regiao, name="get_estados_por_regiao"),
    path("api/livro/", adicionar_livro, name="post_adicionar_livro"),
    path("api/notificacoes/contagens/", get_notification_counts, name="notificacoes_counts"),
    # Admin do Django
    path('admin/', admin.site.urls),
]