# views.py
from django.views.generic import TemplateView
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, update_session_auth_hash
from alexandria.models import Livro, Interesses, Troca
from alexandria.forms import EditarPerfilForm, PasswordChangeForm
from alexandria.constants import REGIONS_CHOICES
from django.http import JsonResponse

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # 1. Meus livros 
        context['livros'] = Livro.objects.filter(id_dono=user, disponivel=True).order_by('-id')

        # 2. Solicitações RECEBIDAS (Interesses em meus livros) - apenas pendentes
        context['solicitacoes_recebidas'] = Interesses.objects.filter(
            id_livro__id_dono=user,
            status='P'
        ).select_related('id_usuario', 'id_livro')

        # 3. Meus Interesses ENVIADOS (livros que quero) - todos
        context['interesses_enviados'] = Interesses.objects.filter(
            id_usuario=user
        ).select_related('id_livro', 'id_livro__id_dono')

        # 4. Trocas concluídas (como dono ou interessado)
        context['trocas'] = Troca.objects.filter(
            Q(id_dono=user) | Q(id_interessado=user)
        ).order_by('-data_troca')

        # 👇 CONTAGENS PARA BADGES
        context['solicitacoes_pendentes_count'] = Interesses.objects.filter(
            id_livro__id_dono=user, status='P'
        ).count()

        context['interesses_pendentes_count'] = Interesses.objects.filter(
            id_usuario=user, status='P'
        ).count()

        # 2. Solicitações RECEBIDAS (Interesses em meus livros) - apenas pendentes
        context['solicitacoes_recebidas'] = Interesses.objects.filter(
            id_livro__id_dono=user,
            status='P'
        ).select_related('id_usuario', 'id_livro')


        context['trocas_andamento_count'] = Troca.objects.filter(
            Q(id_dono=user) | Q(id_interessado=user), status='E'
        ).count()
        context['password_form'] = PasswordChangeForm(user=self.request.user)

        # 5. Confiabilidade do usuário (rating)
        context['user_confiabilidade'] = user.confiabilidade if hasattr(user, 'confiabilidade') else None
        context['regioes_choices'] = REGIONS_CHOICES
        return context

@login_required(login_url="login")
def atualizar_perfil(request):
    user = request.user
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('perfil')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    return redirect('perfil')

@login_required(login_url="login")
def alterar_senha(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Senha alterada com sucesso!')
            return redirect('perfil')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    return redirect('perfil')

@login_required(login_url="login")
def desativar_conta(request):
    if request.method == 'POST':
        user = request.user
        user.ativo = False  # ou 'ativo = False' se seu modelo usar 'ativo'
        user.save()
        logout(request)
        messages.success(request, 'Sua conta foi desativada. Sentiremos sua falta!')
        return redirect('home')
    return redirect('perfil')


@login_required
def get_notification_counts(request):
    user = request.user
    data = {
        'solicitacoes': Interesses.objects.filter(id_livro__id_dono=user, status='P').count(),
        'interesses': Interesses.objects.filter(id_usuario=user, status='P').count(),
        'trocas': Troca.objects.filter(Q(id_dono=user) | Q(id_interessado=user), status='E').count(),
    }
    return JsonResponse(data)