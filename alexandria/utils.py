from alexandria.models import Livro, Usuario

def criar_livro(dono: Usuario, **dados):
    """
    Cria um livro associado a um dono.
    dados podem conter: cod_api, titulo, autor, capa_url, sinopse, estado, disponivel, em_doacao
    Retorna o objeto Livro criado.
    """
    livro = Livro(id_dono=dono)
    for field in ['cod_api', 'titulo', 'autor', 'capa_url', 'sinopse', 'estado', 'disponivel', 'em_doacao']:
        if field in dados:
            setattr(livro, field, dados[field])
    livro.save()
    return livro