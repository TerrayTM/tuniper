from django.urls import path
from .views import Builder, Wake

urlpatterns = [
    path("", Builder.as_view(), name="builder"),
    path("wake", Wake.as_view(), name="wake")
]
