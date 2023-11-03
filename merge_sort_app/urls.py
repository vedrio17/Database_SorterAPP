from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_csv, name='upload_csv'),
   path('download/<str:file_name>/', views.download_sorted_csv, name='download_sorted_csv'),



]
