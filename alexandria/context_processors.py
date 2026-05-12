from alexandria.models import Interesses

def pending_requests_count(request):
    if request.user.is_authenticated:
        count = Interesses.objects.filter(
            id_livro__id_dono=request.user,
            status='P'
        ).count()
        return {'pending_requests_count': count}
    return {'pending_requests_count': 0}