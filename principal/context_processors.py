from students.models import EnrollmentRequest

def pending_requests(request):
    if request.user.is_authenticated:
        try:
            if request.user.profile.role == 'principal':
                count = EnrollmentRequest.objects.filter(status='pending').count()
                return {'pending_requests_count': count}
        except:
            pass
    return {'pending_requests_count': 0}