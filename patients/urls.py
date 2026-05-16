from django.urls import path
from . import views

urlpatterns = [
    path('', views.home),
    path('add/', views.add_patient),
    path('appointment/', views.quick_appointment),
    path('appointments/', views.upcoming_appointments),
    path('debts/', views.debt_list),
    path('add-debt/', views.add_debt),
    path('delete-patient/', views.delete_patient),
    path('patients/', views.all_patients),
    path('patient-history/', views.patient_history, name='patient_history'),   
    path('api/search-patients/', views.search_patients_api),
    path('login/', views.login_view),
    path('logout/', views.logout_view),
]