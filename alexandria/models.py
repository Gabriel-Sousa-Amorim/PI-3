from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from django.contrib.auth.models import AbstractUser
from django.db import models

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

import alexandria.constants as app_constants

import requests
import datetime

class UsuarioManager(BaseUserManager):
    def create_user(self, email, nome, password=None, **extra_fields):
        if not email:
            raise ValueError('O e-mail é obrigatório')
        email = self.normalize_email(email)
        user = self.model(email=email, nome=nome, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nome, password=None, **extra_fields):
        extra_fields.setdefault('administrador', True)
        extra_fields.setdefault('moderador', True)
        extra_fields.setdefault('ativo', True)
        return self.create_user(email, nome, password, **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Modelo customizado sem username, usando e-mail como login.
    Permissões baseadas nos campos moderador, administrador e ativo.
    """
    id = models.AutoField(primary_key=True)
    # Campos da tabela original
    nome = models.CharField(max_length=255, verbose_name='Nome completo do usuário')
    email = models.EmailField(max_length=255, unique=True, verbose_name='E‑mail único por usuário')
    regiao = models.CharField(max_length=255, choices=app_constants.REGIONS_CHOICES, verbose_name='Região', default=None, db_column="regiao")
    estado = models.CharField(
        max_length=2, 
        choices=app_constants.STATE_CHOICES, 
        verbose_name='Estado de Residência', 
        blank=True,
        null=True
    )
    cidade = models.CharField(max_length=50, default='São Paulo')
    zona = models.CharField(
        max_length=1,
        choices=[
            ('N', 'Norte'),
            ('L', 'Leste'),
            ('S', 'Sul'),
            ('O', 'Oeste'),
            ('C', 'Central'),
            ('X', 'Outras'),
        ],  # suas escolhas
        verbose_name='Zona na cidade de residência',
        db_column="zona",
        null=True
    )
    password = models.CharField(max_length=128, db_column='senha', verbose_name='Senha')
    joined_at = models.DateTimeField(default=datetime.datetime.now, blank=True)
    # Campo de avaliação (rating) - de 0 a 5
    confiability = models.FloatField(
        null=True,  
        blank=True,
        verbose_name='Confiabilidade',
        help_text='Avaliação de confiabilidade 0 a 5 estrelas. Se nulo, significa não avaliado.'
    )
    # Seus campos booleanos personalizados
    moderador = models.BooleanField(db_column='moderador', default=False)
    administrador = models.BooleanField(db_column='administrador', default=False)
    ativo = models.BooleanField(db_column='ativo', default=True)

    # Remove campos desnecessários do AbstractBaseUser/PermissionsMixin
    # Mas PermissionsMixin exige is_superuser, is_staff, is_active – vamos sobrescrever como propriedades
    # Para evitar colunas extras, usamos properties que leem nossos campos.

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome']

    objects = UsuarioManager()

    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuário'

    def __str__(self):
        return self.nome

    # Propriedades exigidas pelo Django
    @property
    def is_staff(self):
        """Usuário com `administrador` ou `moderador` pode acessar o admin."""
        return self.administrador or self.moderador

    @property
    def is_superuser(self):
        """Usuário com `administrador` é considerado superusuário."""
        return self.administrador

    @property
    def is_active(self):
        """Usa o campo `ativo` para desativar login."""
        return self.ativo

    def get_rating_display(self):
        """Retorna string para exibição da avaliação (confiability)"""
        if self.confiability is None:
            return "Não avaliado"
        return f"{self.confiability:.1f} / 5.0"

    # Permissões personalizadas (opcional)
    def has_perm(self, perm, obj=None):
        # Se for administrador, tem todas as permissões
        if self.administrador:
            return True
        # Se for moderador, pode ter permissões específicas (ex: moderar livros)
        # Implemente conforme sua lógica
        return False

    def has_module_perms(self, app_label):
        return self.administrador or self.moderador

    def get_regiao_display_full(self):
        return app_constants.REGIONS.get(self.regiao, {}).get("label", self.regiao)

    def get_estado_display_full(self):
        return dict(app_constants.STATE_CHOICES).get(self.estado, self.estado)

    def get_zona_display_full(self):
        zonas = dict(self._meta.get_field('zona').choices)
        return zonas.get(self.zona, self.zona or 'Não informada')

    @property
    def states_for_region(self):
        return app_constants.REGIONS.get(self.regiao, {}).get("states", [])

class Livro(models.Model):
    ESTADO_CHOICES = [
        ('OTIMO', 'Ótimo'),
        ('BOM', 'Bom'),
        ('NORMAL', 'Normal'),
        ('DANIFICADO', 'Danificado'),
    ]

    id = models.AutoField(primary_key=True)
    id_dono = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='id_dono')
    
    # Identificador na API externa (OLID)
    cod_api = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        verbose_name='OLID (OpenLibrary ID)',
        unique=False
    )
    
    # Campos de cache da API
    titulo = models.CharField(max_length=500, blank=True, null=True, verbose_name='Título')
    autor = models.CharField(max_length=500, blank=True, null=True, verbose_name='Autor')
    capa_url = models.URLField(max_length=500, blank=True, null=True, verbose_name='URL da capa')
    sinopse = models.TextField(blank=True, null=True, verbose_name='Sinopse')
    
    # Campos originais
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, verbose_name='Estado de conservação', db_column='estado', null=True)
    disponivel = models.BooleanField(default=True, verbose_name='Disponível para troca')
    em_doacao = models.BooleanField(default=False, verbose_name='Disponível para doação')

    class Meta:
        db_table = 'livros'
        verbose_name = 'Livro'
        verbose_name_plural = 'Livros'

    def get_queryset(self):
        queryset = Livro.objects.filter(disponivel=True) \
                                 .exclude(titulo__isnull=True) \
                                 .exclude(titulo__exact='') \
                                 .select_related('id_dono')

        # Filtro de busca (título ou autor)
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(titulo__icontains=search) | Q(autor__icontains=search)
            )

        # Filtro por região (baseada no dono do livro)
        regiao = self.request.GET.get('regiao', '')
        if regiao and regiao != 'todas':
            queryset = queryset.filter(id_dono__regiao=regiao)

        # Filtro por estado de conservação
        estado = self.request.GET.get('estado', '')
        if estado and estado != 'todos':
            queryset = queryset.filter(estado=estado)

        # Filtro por tipo (troca/doação)
        tipo = self.request.GET.get('tipo', '')
        if tipo == 'doacao':
            queryset = queryset.filter(em_doacao=True)
        elif tipo == 'troca':
            queryset = queryset.filter(em_doacao=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Preserva os filtros atuais no template para manter os valores nos campos
        context['filtros'] = {
            'search': self.request.GET.get('search', ''),
            'regiao': self.request.GET.get('regiao', ''),
            'estado': self.request.GET.get('estado', ''),
            'tipo': self.request.GET.get('tipo', ''),
        }
        # Lista de regiões para o dropdown (vinda do modelo Usuario)
        context['regioes'] = Usuario._meta.get_field('regiao').choices
        return context

    def populate_with_api(self):
        print(f"🔁 Chamando populate_with_api para livro {self.id}, cod_api={self.cod_api}")
        raw_olid = self.cod_api.strip()
        tamanho_capa = "M"
        # Remove prefixo '/works/' ou '/books/' se existir
        if raw_olid.startswith('/works/'):
            raw_olid = raw_olid.replace('/works/', '')
        if raw_olid.startswith('/books/'):
            raw_olid = raw_olid.replace('/books/', '')

        # 1. Identificar se é obra (W) ou edição (M)
        work_olid = None
        edition_olid = None
        if raw_olid.endswith('W'):
            work_olid = raw_olid
            print(f"📖 OLID identificado como OBRA: {work_olid}")
        elif raw_olid.endswith('M'):
            edition_olid = raw_olid
            print(f"📗 OLID identificado como EDIÇÃO: {edition_olid}")
            # Buscar a obra a partir da edição
            edition_url = f'https://openlibrary.org/books/{edition_olid}.json'
            try:
                resp_ed = requests.get(edition_url, timeout=10)
                resp_ed.raise_for_status()
                edition_data = resp_ed.json()
                # A obra está em works[0].key
                works = edition_data.get('works', [])
                if works:
                    work_key = works[0].get('key', '')
                    work_olid = work_key.replace('/works/', '')
                    print(f"🔗 Obra associada à edição: {work_olid}")
                else:
                    print("❌ Edição não possui referência para obra")
                    return False
            except Exception as e:
                print(f"❌ Erro ao buscar dados da edição: {e}")
                return False
        else:
            print(f"❌ OLID com formato desconhecido: {raw_olid}")
            return False

        # 2. Buscar dados da obra (work)
        work_url = f'https://openlibrary.org/works/{work_olid}.json'
        print(f"📡 Buscando obra: {work_url}")
        try:
            resp_work = requests.get(work_url, timeout=10)
            resp_work.raise_for_status()
            work_data = resp_work.json()
            print(f"✅ Obra encontrada: {work_data.get('title')}")
        except Exception as e:
            print(f"❌ Erro ao buscar obra: {e}")
            return False

        # Título
        titulo = work_data.get('title', '')[:500]

        # Autor
        autor = ''
        autores = work_data.get('authors', [])
        if autores:
            author_key = autores[0].get('author', {}).get('key')
            if author_key:
                author_url = f'https://openlibrary.org{author_key}.json'
                try:
                    resp_author = requests.get(author_url, timeout=10)
                    if resp_author.status_code == 200:
                        autor = resp_author.json().get('name', '')[:500]
                except:
                    pass

        # 3. Buscar edições em português
        editions_url = f'https://openlibrary.org/works/{work_olid}/editions.json?limit=50'
        sinopse = ''
        cover_id = None
        pt_edition_olid = None
        try:
            resp_editions = requests.get(editions_url, timeout=10)
            resp_editions.raise_for_status()
            editions_data = resp_editions.json()
            entries = editions_data.get('entries', [])
            print(f"📚 Total de edições encontradas: {len(entries)}")
            for edition in entries:
                languages = edition.get('languages', [])
                for lang in languages:
                    lang_key = lang.get('key', '')
                    if 'por' in lang_key.lower():
                        pt_edition_olid = edition.get('key', '').replace('/books/', '')
                        print(f"🇵🇹 Edição em português: {pt_edition_olid}")
                        # Descrição da edição
                        desc = edition.get('description', '')
                        if isinstance(desc, dict):
                            sinopse = desc.get('value', '')
                        else:
                            sinopse = desc
                        # Capa da edição (cover_i)
                        if edition.get('covers') and len(edition['covers']) > 0:
                            cover_id = edition['covers'][0]
                            print(f"🖼️ cover_id da edição: {cover_id}")
                        break
                if sinopse and cover_id:
                    break
            if not sinopse:
                print("⚠️ Sem sinopse na edição, usando da obra")
                desc = work_data.get('description', '')
                if isinstance(desc, dict):
                    sinopse = desc.get('value', '')
                else:
                    sinopse = desc
            if not cover_id and work_data.get('covers') and len(work_data['covers']) > 0:
                cover_id = work_data['covers'][0]
                print(f"🖼️ cover_id da obra: {cover_id}")
        except Exception as e:
            print(f"❌ Erro ao buscar edições: {e}")
            desc = work_data.get('description', '')
            if isinstance(desc, dict):
                sinopse = desc.get('value', '')
            else:
                sinopse = desc

        # 4. Definir URL da capa
        if cover_id:
            self.capa_url = f'https://covers.openlibrary.org/b/id/{cover_id}-{tamanho_capa}.jpg'
            print(f"✅ Capa via cover_id: {self.capa_url}")
        else:
            # Fallback: usa o OLID da edição em português ou da obra
            fallback_olid = pt_edition_olid if pt_edition_olid else work_olid
            self.capa_url = f'https://covers.openlibrary.org/b/olid/{fallback_olid}-{tamanho_capa}.jpg'
            print(f"✅ Capa via OLID (fallback): {self.capa_url}")

        # Verificar se a capa existe (opcional)
        try:
            resp_capa = requests.head(self.capa_url, timeout=30)
            print(resp_capa)
            if resp_capa.status_code >= 400:
                print(f"⚠️ Capa não encontrada (status {resp_capa.status_code})")
                self.capa_url = '/static/images/noCover.png'
        except Exception:
            self.capa_url = '/static/images/noCover.png'

        # Salvar campos
        self.titulo = titulo
        self.autor = autor
        self.sinopse = sinopse[:5000]
        self.save(update_fields=['titulo', 'autor', 'capa_url', 'sinopse'])
        print(f"✅ Livro {self.id} atualizado com sucesso!")
        return True

    def __str__(self):
        return self.titulo or f'Livro {self.id}'

class Interesses(models.Model):
    STATUS_CHOICES = [
        ('P', 'Pendente'),
        ('A', 'Aceito'),
        ('R', 'Recusado'),
    ]
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    id_livro = models.ForeignKey(Livro, on_delete=models.CASCADE)
    data_interesse = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'interesse'
        verbose_name = 'Interesse'
        verbose_name_plural = 'interesses'
        unique_together = ('id_usuario', 'id_livro')  

class Troca(models.Model):
    STATUS_CHOICES = (
        ('E', 'Em andamento'),
        ('C', 'Concluída'),
        ('D', 'Desistida'),
    )
    livro = models.ForeignKey(Livro, on_delete=models.CASCADE, null=True)
    id_dono = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='trocas_como_dono')
    id_interessado = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='trocas_como_interessado')
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='E')
    data_troca = models.DateTimeField(auto_now_add=True)
    avaliacao_dono = models.PositiveSmallIntegerField(null=True, blank=True)  # nota para o interessado
    avaliacao_interessado = models.PositiveSmallIntegerField(null=True, blank=True)  # nota para o dono
    comentario_dono = models.TextField(blank=True)
    comentario_interessado = models.TextField(blank=True)
    class Meta:
        db_table = 'troca'
        verbose_name = 'Troca'
        verbose_name_plural = 'Trocas'

    def __str__(self):
        return f'Troca {self.id} - Livro {self.id_livro.id}'