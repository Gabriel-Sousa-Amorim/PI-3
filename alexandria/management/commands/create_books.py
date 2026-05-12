from django.core.management.base import BaseCommand
from alexandria.models import Usuario, Livro

class Command(BaseCommand):
    help = 'Cria livros de exemplo no banco de dados'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=True, help='Email do dono do livro')
        parser.add_argument('--olid', type=str, required=True, help='OLID do livro (ex: OL45804W)')
        parser.add_argument('--estado', type=str, default='BOM', choices=['OTIMO', 'BOM', 'NORMAL', 'DANIFICADO'])

    def handle(self, *args, **options):
        email = options['email']
        olid = options['olid']
        estado = options['estado']

        try:
            dono = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'Usuário com email {email} não encontrado'))
            return

        livro = Livro.objects.create(
            id_dono=dono,
            cod_api=olid,
            estado=estado,
            disponivel=True,
            em_doacao=False
        )
        livro.populate_with_api()  # preenche título, autor, capa, sinopse

        self.stdout.write(self.style.SUCCESS(f'Livro {livro.id} criado com sucesso!'))