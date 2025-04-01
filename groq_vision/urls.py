from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('process_image/', views.process_image_view, name='process_image'),
    path('process_text/', views.process_text_view, name='process_text'),
]