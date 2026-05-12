from django.core.management.base import BaseCommand
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from alexandria.models import Usuario  # ajuste o import conforme seu app

class Command(BaseCommand):
    help = 'Cria um novo usuário comum (não administrador)'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True, help='E-mail do usuário')
        parser.add_argument('--nome', required=True, help='Nome completo')
        parser.add_argument('--password', required=True, help='Senha')
        parser.add_argument('--regiao', default='CENTRO', 
                            choices=['NORTE 1', 'NORTE 2', 'LESTE 1', 'LESTE 2', 
                                     'SUL', 'SUDESTE', 'SUDOESTE', 'OESTE', 
                                     'CENTRO', 'REGIAO METROPOLITANA'],
                            help='Região (padrão: CENTRO)')
        parser.add_argument('--cidade', default='São Paulo', help='Cidade (padrão: São Paulo)')

    def handle(self, *args, **options):
        email = options['email']
        nome = options['nome']
        password = options['password']
        regiao = options['regiao']
        cidade = options['cidade']

        # Validação básica do e-mail
        try:
            validate_email(email)
        except ValidationError:
            self.stderr.write(self.style.ERROR(f'E-mail inválido: {email}'))
            return

        # Verifica se já existe um usuário com esse e-mail
        if Usuario.objects.filter(email=email).exists():
            self.stderr.write(self.style.ERROR(f'Usuário com e-mail {email} já existe'))
            return

        # Cria o usuário comum usando o método create_user do manager
        usuario = Usuario.objects.create_user(
            email=email,
            nome=nome,
            password=password
        )
        # Atualiza campos adicionais
        usuario.regiao = regiao
        usuario.cidade = cidade
        usuario.save()

        self.stdout.write(self.style.SUCCESS(
            f'Usuário criado com sucesso!\n'
            f'E-mail: {email}\n'
            f'Nome: {nome}\n'
            f'Região: {regiao}\n'
            f'Cidade: {cidade}'
        ))