from django.views.generic import ListView
from ..models import Livro
from django.db.models import Q

class Explore(ListView):
    model = Livro
    template_name = "explore.html"
    context_object_name = "livros"
    paginate_by = 12

    def get_queryset(self):
        queryset = Livro.objects.filter(disponivel=True).exclude(titulo__isnull=True)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(Q(titulo__icontains=search) | Q(autor__icontains=search))
        
        regiao = self.request.GET.get('regiao')
        if regiao:
            queryset = queryset.filter(id_dono__regiao=regiao)
        
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        tipo = self.request.GET.get('tipo')
        if tipo == 'doacao':
            queryset = queryset.filter(em_doacao=True)
        elif tipo == 'troca':
            queryset = queryset.filter(em_doacao=False)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Adiciona os filtros atuais ao contexto para preencher os campos do formulário
        context['filtros'] = {
            'search': self.request.GET.get('search', ''),
            'regiao': self.request.GET.get('regiao', ''),
            'estado': self.request.GET.get('estado', ''),
            'tipo': self.request.GET.get('tipo', ''),
        }
        # Adiciona as regiões para o dropdown (vindo do model Usuario)
        from ..models import Usuario
        context['regioes'] = Usuario._meta.get_field('regiao').choices
        return context
