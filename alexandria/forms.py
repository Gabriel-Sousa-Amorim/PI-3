from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm as BasePasswordChangeForm
from django.core.exceptions import ValidationError

import alexandria.constants as app_constants
from alexandria.models import Livro, Troca

Usuario = get_user_model()


# ----------------------------------------------------------------------
# Mixin para formulários que precisam do usuário logado
# ----------------------------------------------------------------------
class UsuarioMixin:
    """Mixin que injeta o usuário no formulário e o utiliza no save."""

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.id_dono = self.user
        if commit:
            instance.save()
        return instance


# ----------------------------------------------------------------------
# Cadastro de Usuário
# ----------------------------------------------------------------------
class CadastroUsuarioForm(forms.ModelForm):
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-neutral-300 rounded-2xl focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'Mínimo 8 caracteres',
            'required': True,
        }),
        min_length=8,
        help_text='A senha deve ter pelo menos 8 caracteres.'
    )
    password_confirm = forms.CharField(
        label='Confirmar senha',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-neutral-300 rounded-2xl focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'Digite a senha novamente',
            'required': True,
        })
    )
    terms = forms.BooleanField(
        label='Aceito os Termos de Uso',
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded text-indigo-600 focus:ring-indigo-500',
            'required': True,
        })
    )

    class Meta:
        model = Usuario
        fields = ['nome', 'email', 'regiao', 'estado', 'cidade', 'zona']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-neutral-300 rounded-2xl focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'Insira seu nome completo',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-neutral-300 rounded-2xl focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'Insira seu email (exemplo@email.com)',
                'required': True,
            }),
            'regiao': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-neutral-300 rounded-2xl focus:ring-indigo-500 focus:border-indigo-500 bg-white',
                'required': True,
            }),
            'estado': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-neutral-300 rounded-2xl focus:ring-indigo-500 focus:border-indigo-500 bg-white',
                'required': True,
            }),
            'cidade': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-neutral-300 rounded-2xl focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'Digite o nome da sua cidade',
            }),
            'zona': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-neutral-300 rounded-2xl focus:ring-indigo-500 focus:border-indigo-500 bg-white',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Estado começa vazio; será populado dinamicamente se houver região
        self.fields['estado'].choices = [('', 'Selecione um estado')]
        self.fields['zona'].required = True
        self.fields['zona'].choices = [('', 'Selecione uma zona')] + list(
            self.fields['zona'].choices
        )[1:]

        regiao = self.initial.get('regiao') or self.data.get('regiao')
        if regiao:
            self.fields['estado'].choices = self._get_estados_por_regiao(regiao)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_estados_por_regiao(self, regiao):
        """Retorna choices do campo estado de acordo com a região."""
        if not regiao or regiao not in app_constants.REGIONS:
            return [('', 'Selecione um estado')]
        estados = app_constants.REGIONS[regiao].get('states', [])
        choices = [('', 'Selecione um estado')]
        choices.extend(
            (sigla, dict(app_constants.STATE_CHOICES).get(sigla, sigla))
            for sigla in estados
        )
        return choices

    # ------------------------------------------------------------------
    # Validações
    # ------------------------------------------------------------------
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise ValidationError('As senhas não coincidem. Por favor, verifique.')
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and Usuario.objects.filter(email=email).exists():
            raise ValidationError('Este email já está registrado.')
        return email

    def clean_regiao(self):
        regiao = self.cleaned_data.get('regiao')
        if not regiao:
            raise ValidationError('Selecione uma região.')
        if regiao not in dict(app_constants.REGIONS_CHOICES):
            raise ValidationError('Região inválida.')
        return regiao

    def clean_estado(self):
        estado = self.cleaned_data.get('estado')
        regiao = self.cleaned_data.get('regiao')

        if not estado:
            raise ValidationError('Selecione um estado.')
        if estado not in dict(app_constants.STATE_CHOICES):
            raise ValidationError('Estado inválido.')

        if regiao:
            estados_validos = app_constants.REGIONS.get(regiao, {}).get('states', [])
            if estado not in estados_validos:
                raise ValidationError('O estado selecionado não pertence à região escolhida.')
        return estado

    # ------------------------------------------------------------------
    # Persistência
    # ------------------------------------------------------------------
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


# ----------------------------------------------------------------------
# Adicionar Livro
# ----------------------------------------------------------------------
class AdicionarLivroForm(UsuarioMixin, forms.ModelForm):
    cod_api = forms.CharField(
        label='Código OpenLibrary (OLID)',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-neutral-300 rounded-2xl focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'Ex: OL17887662W (opcional)',
        }),
    )
    titulo = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-neutral-300 rounded-2xl focus:ring-indigo-500 focus:border-indigo-500'
        })
    )
    autor = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-neutral-300 rounded-2xl focus:ring-indigo-500 focus:border-indigo-500'
        })
    )
    sinopse = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'w-full px-4 py-2 border border-neutral-300 rounded-2xl'
        })
    )
    estado = forms.ChoiceField(
        choices=Livro.ESTADO_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-neutral-300 rounded-2xl bg-white'
        })
    )
    em_doacao = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'rounded text-indigo-600'})
    )
    disponivel = forms.BooleanField(
        initial=True,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Livro
        fields = [
            'cod_api', 'titulo', 'autor', 'sinopse', 'capa_url',
            'estado', 'em_doacao', 'disponivel'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['estado'].required = True
        self.fields['disponivel'].initial = True
        self.fields['disponivel'].widget = forms.HiddenInput()
        self.fields['sinopse'].required = False
        self.fields['capa_url'].required = False
        self.fields['capa_url'].widget = forms.URLInput(attrs={
            'readonly': 'readonly',
            'class': 'w-full px-4 py-2 border border-neutral-300 rounded-2xl bg-gray-100',
            'placeholder': 'URL da capa (preenchido automaticamente)',
        })
        self.fields['capa_url'].label = 'URL da capa'

    # ------------------------------------------------------------------
    # Validações
    # ------------------------------------------------------------------
    def clean_cod_api(self):
        cod = self.cleaned_data.get('cod_api')
        if not cod:
            return cod
        if not (cod.startswith('OL') and (cod.endswith('W') or cod.endswith('M'))):
            raise ValidationError('OLID inválido. Use formato OLxxxxxW ou OLxxxxxM.')
        return cod

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('titulo') and not cleaned_data.get('cod_api'):
            raise ValidationError('Informe o título ou o código OLID.')
        return cleaned_data

    # ------------------------------------------------------------------
    # Persistência
    # ------------------------------------------------------------------
    def save(self, commit=True):
        livro = super().save(commit=False)   # UsuarioMixin já atribui id_dono

        # Se informou OLID e não tem título, busca dados da API
        if livro.cod_api and not livro.titulo:
            livro.populate_with_api()

        if commit:
            livro.save()
        return livro


# ----------------------------------------------------------------------
# Editar Livro
# ----------------------------------------------------------------------
class EditarLivroForm(forms.ModelForm):
    class Meta:
        model = Livro
        fields = ['estado', 'em_doacao', 'disponivel']
        widgets = {
            'estado': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-xl focus:ring-indigo-500'
            }),
            'em_doacao': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500'
            }),
            'disponivel': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500'
            }),
        }


# ----------------------------------------------------------------------
# Editar Perfil
# ----------------------------------------------------------------------
class EditarPerfilForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nome', 'cidade', 'estado', 'regiao', 'zona']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg'
            }),
            'cidade': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg'
            }),
            'estado': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg'
            }),
            'regiao': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg'
            }),
            'zona': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg'
            }),
        }


# ----------------------------------------------------------------------
# Desativar Conta
# ----------------------------------------------------------------------
class DesativarContaForm(forms.Form):
    confirmar = forms.BooleanField(
        label='Confirmo que quero desativar minha conta permanentemente',
        required=True
    )


# ----------------------------------------------------------------------
# Alterar Senha
# ----------------------------------------------------------------------
class PasswordChangeForm(BasePasswordChangeForm):
    """
    Formulário personalizado para alteração de senha.
    Mantém a validação padrão do Django.
    """
    old_password = forms.CharField(
        label='Senha atual',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-neutral-300 rounded-lg focus:ring-indigo-500',
            'placeholder': 'Digite sua senha atual'
        })
    )
    new_password1 = forms.CharField(
        label='Nova senha',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-neutral-300 rounded-lg focus:ring-indigo-500',
            'placeholder': 'Mínimo de 8 caracteres'
        }),
        help_text='Sua senha deve ter pelo menos 8 caracteres e não pode ser totalmente numérica.'
    )
    new_password2 = forms.CharField(
        label='Confirmar nova senha',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-neutral-300 rounded-lg focus:ring-indigo-500',
            'placeholder': 'Digite a nova senha novamente'
        })
    )

    class Meta:
        fields = ['old_password', 'new_password1', 'new_password2']

class AvaliacaoTrocaForm(forms.Form):
    nota = forms.IntegerField(min_value=1, max_value=5, widget=forms.HiddenInput())
    comentario = forms.CharField(widget=forms.Textarea(attrs={
        'rows': 3,
        'class': 'w-full px-3 py-2 border border-gray-300 rounded-xl focus:ring-indigo-500',
        'placeholder': 'Compartilhe sua experiência (opcional)'
    }), required=False)