from django.shortcuts import render
from .db import ObjectNotFoundError, DatabaseError

class DatabaseErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, ObjectNotFoundError):
            return render(request, 'error.html', {
                'title': 'Object Not Found / ไม่พบฟังก์ชัน',
                'message': str(exception)
            }, status=503)
        elif isinstance(exception, DatabaseError):
            return render(request, 'error.html', {
                'title': 'Database Error / ปัญหาฐานข้อมูล',
                'message': str(exception)
            }, status=503)
        return None
