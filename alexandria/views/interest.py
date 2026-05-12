from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from alexandria.models import Livro, Interesses, Troca
from alexandria.forms import AvaliacaoTrocaForm
from django.db.models import Q

@login_required(login_url="login")
def registrar_interesse(request, id):
    livro = get_object_or_404(Livro, id=id)
    if request.user == livro.id_dono:
        messages.error(request, 'Você não pode registrar interesse no seu próprio livro.')
        return redirect('detalhe_livro', id=livro.id)

    interesse, created = Interesses.objects.get_or_create(
        id_usuario=request.user,
        id_livro=livro,
        defaults={'status': 'P'}
    )
    if not created:
        messages.warning(request, 'Você já manifestou interesse neste livro.')
    else:
        messages.success(request, 'Interesse registrado com sucesso!')
    return redirect('detalhe_livro', id=livro.id)

@login_required(login_url="login")
def lista_interessados(request, id):
    livro = get_object_or_404(Livro, id=id)
    if request.user != livro.id_dono:
        messages.error(request, 'Você não tem permissão para ver esta lista.')
        return redirect('detalhe_livro', id=livro.id)

    interesses = Interesses.objects.filter(id_livro=livro).select_related('id_usuario').order_by('-data_interesse')
    return render(request, 'profile.html', {
        'livro': livro,
        'interesses': interesses,
    })

@login_required(login_url="login")
def aceitar_interesse(request, id):
    interesse = get_object_or_404(Interesses, id=id)
    livro = interesse.id_livro

    # Verifica se o usuário logado é o dono do livro
    if request.user != livro.id_dono:
        messages.error(request, 'Permissão negada.')
        return redirect('perfil')

    # Só aceita se o livro ainda estiver disponível
    if not livro.disponivel:
        messages.error(request, 'Este livro já está em processo de troca.')
        return redirect('perfil')

    # Marca o interesse como Aceito
    interesse.status = 'A'
    interesse.save()

    # Bloqueia o livro (indisponível para novos interesses)
    livro.disponivel = False
    livro.save()

    # Cria um registro de troca em andamento
    Troca.objects.create(
        livro=livro,
        id_dono=request.user,
        id_interessado=interesse.id_usuario,
        status='E'   # Em andamento
    )

    messages.success(request, f'Interesse aceito! Uma troca foi iniciada com {interesse.id_usuario.nome}. Entre em contato para combinar os detalhes.')
    return redirect('perfil')

@login_required(login_url="login")
def recusar_interesse(request, id):
    interesse = get_object_or_404(Interesses, id=id)
    livro = interesse.id_livro
    if request.user != livro.id_dono:
        messages.error(request, 'Permissão negada.')
        return redirect('perfil')
    interesse.status = 'R'
    interesse.save()
    messages.info(request, f'Interesse recusado para {interesse.id_usuario.nome}.')
    return redirect('perfil')

@login_required(login_url="login")
def desistir_troca(request, troca_id):
    troca = get_object_or_404(Troca, id=troca_id)
    user = request.user

    # Apenas o dono ou o interessado podem desistir
    if user not in [troca.id_dono, troca.id_interessado]:
        messages.error(request, 'Você não tem permissão para desistir desta troca.')
        return redirect('perfil')

    # Só pode desistir se ainda estiver em andamento
    if troca.status != 'E':
        messages.error(request, 'Esta troca já foi concluída ou cancelada.')
        return redirect('perfil')

    # Marca troca como desistida
    troca.status = 'D'
    troca.save()

    # Libera o livro novamente (disponível para novos interesses)
    livro = troca.livro
    livro.disponivel = True
    livro.save()

    # Opcional: remover o interesse aceito (ou mantê-lo com status 'A' – você decide)
    # Para não gerar confusão, podemos deletar o interesse aceito ou reverter para 'P'
    interesse_aceito = Interesses.objects.filter(id_livro=livro, id_usuario=troca.id_interessado, status='A').first()
    if interesse_aceito:
        interesse_aceito.status = 'P'   # volta a pendente (ou pode deletar)
        interesse_aceito.save()

    messages.success(request, 'Você desistiu da troca. O livro está novamente disponível.')
    return redirect('perfil')

@login_required(login_url="login")
def finalizar_troca(request, troca_id):
    troca = get_object_or_404(Troca, id=troca_id)
    user = request.user

    if user not in [troca.id_dono, troca.id_interessado]:
        messages.error(request, 'Permissão negada.')
        return redirect('perfil')

    if troca.status != 'E':
        messages.error(request, 'Esta troca não está em andamento.')
        return redirect('perfil')

    troca.status = 'C'
    troca.save()

    messages.success(request, 'Troca finalizada! Agora você pode avaliar a experiência.')
    return redirect('avaliar_troca', troca_id=troca.id)   # ← corrigido


@login_required(login_url="login")
def avaliar_troca(request, troca_id):
    troca = get_object_or_404(Troca, id=troca_id)
    user = request.user

    # Permissão: apenas os envolvidos
    if user not in [troca.id_dono, troca.id_interessado]:
        messages.error(request, 'Permissão negada.')
        return redirect('perfil')

    # Só pode avaliar se a troca estiver concluída
    if troca.status != 'C':
        messages.error(request, 'A troca precisa estar concluída para ser avaliada.')
        return redirect('perfil')

    # Verifica se o usuário já avaliou
    if user == troca.id_dono and troca.avaliacao_dono:
        messages.info(request, 'Você já avaliou esta troca.')
        return redirect('perfil')
    if user == troca.id_interessado and troca.avaliacao_interessado:
        messages.info(request, 'Você já avaliou esta troca.')
        return redirect('perfil')

    # Se for POST, processa o formulário
    if request.method == 'POST':
        form = AvaliacaoTrocaForm(request.POST)
        if form.is_valid():
            nota = form.cleaned_data['nota']
            comentario = form.cleaned_data['comentario']

            if user == troca.id_dono:
                troca.avaliacao_dono = nota
                troca.comentario_dono = comentario
            else:
                troca.avaliacao_interessado = nota
                troca.comentario_interessado = comentario

            troca.save()
            # Atualiza a confiabilidade da outra pessoa
            usuario_avaliado = troca.id_interessado if user == troca.id_dono else troca.id_dono
            atualizar_confiabilidade(usuario_avaliado)  # função que você já tem

            messages.success(request, 'Avaliação enviada com sucesso! Obrigado.')
            return redirect('perfil')
        else:
            messages.error(request, 'Erro no formulário. Tente novamente.')
    else:
        # GET: cria formulário vazio
        form = AvaliacaoTrocaForm()

    # Determina quem está sendo avaliado
    if user == troca.id_dono:
        avaliado = troca.id_interessado
        papel = "dono"
    else:
        avaliado = troca.id_dono
        papel = "interessado"

    total_trocas_avaliado = Troca.objects.filter(
        Q(id_dono=avaliado, status='C') | Q(id_interessado=avaliado, status='C')
    ).distinct().count()


    return render(request, 'rateExchange.html', {
        'troca': troca,
        'avaliado': avaliado,
        'form': form,
        'papel': papel,
        'total_trocas_avaliado': total_trocas_avaliado,
    })


def atualizar_confiabilidade(usuario):
    """
    Atualiza o campo confiability do usuário com a média de todas as notas
    que ele RECEBEU em trocas concluídas (como dono ou como interessado).
    """
    notas = []
    
    # 1. Notas recebidas como DONO (avaliacao_dono é a nota que o DONO deu para o INTERESSADO? CUIDADO!)
    # Revisão: avaliacao_dono = nota que o dono deu para o interessado.
    # Para saber a nota que o usuário RECEBEU:
    # - Se ele é dono: a nota que ele recebeu está em avaliacao_interessado (o interessado avaliou ele).
    # - Se ele é interessado: a nota que ele recebeu está em avaliacao_dono (o dono avaliou ele).
    
    # Portanto, quando o usuário é DONO, a nota que ele RECEBEU é 'avaliacao_interessado'
    trocas_como_dono = Troca.objects.filter(
        id_dono=usuario,
        status='C',
        avaliacao_interessado__isnull=False  # nota que o interessado deu ao dono
    )
    for t in trocas_como_dono:
        notas.append(t.avaliacao_interessado)
    
    # Quando o usuário é INTERESSADO, a nota que ele RECEBEU é 'avaliacao_dono'
    trocas_como_interessado = Troca.objects.filter(
        id_interessado=usuario,
        status='C',
        avaliacao_dono__isnull=False  # nota que o dono deu ao interessado
    )
    for t in trocas_como_interessado:
        notas.append(t.avaliacao_dono)
    
    if notas:
        media = sum(notas) / len(notas)
        # Arredonda para 1 casa decimal
        usuario.confiability = round(media, 1)
        usuario.save(update_fields=['confiability'])
        
        # Log para depuração (remova depois)
        print(f"[Confiability] Usuário {usuario.nome}: notas {notas}, média {media} -> {usuario.confiability}")
    else:
        usuario.confiability = None
        usuario.save(update_fields=['confiability'])
        print(f"[Confiability] Usuário {usuario.nome} não tem avaliações ainda.")