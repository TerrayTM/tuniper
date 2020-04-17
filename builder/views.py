import threading

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.http import HttpResponse
from .core import build
from .settings import TOKEN

class Builder(APIView):
    def get(self, request):
        return Response({ "status": "success" })

    def post(self, request):
        validation = ["repository", "name", "callback", "token", "return", "pass"]
        if not all(i in request.data for i in validation):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if not request.data["token"] == TOKEN:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        kwargs = { key: request.data[key] for key in validation }
        job = threading.Thread(target=build, kwargs=kwargs)
        job.setDaemon(True)
        job.start()
        return Response({ "status": "running" })

class Wake(APIView):
    def post(self, request):
        if not "identifier" in request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return HttpResponse(request.data['identifier'])
