from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from alexandria.forms import AdicionarLivroForm


@login_required(login_url="login")
def adicionar_livro(request):
    if request.method == 'POST':
        form = AdicionarLivroForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Livro adicionado com sucesso!')
            # Redireciona para a lista de livros do usuário (ajuste a URL conforme seu urls.py)
            return redirect('perfil')
        else:
            # Junta todos os erros em uma única mensagem, usando o label do campo
            for field, errors in form.errors.items():
                label = form.fields[field].label if field in form.fields else field
                for error in errors:
                    messages.error(request, f'{label}: {error}')
    else:
        form = AdicionarLivroForm(user=request.user)

    return render(request, 'addBook.html', {'form': form})