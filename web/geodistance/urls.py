from django.urls import path
from . import views

app_name = 'geodistance'

urlpatterns = [
    path('', views.geo_distance_view, name='geo_distance'),
]
