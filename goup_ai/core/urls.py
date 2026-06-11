from django.urls import path
from .views import (
    DashboardView, DashboardDataView,
    AtletaListView, AtletaDetailView, AtletaCreateView, AtletaUpdateView, AtletaDeleteView,
    LesioListView, LesioCreateView, LesioUpdateView,
    AlimentacioCreateView, AlimentacioUpdateView,
    SessioListView, SessioCreateView,
    UbicacioListView, UbicacioCreateView, ValoracioCreateView,
    RegistreDiariCreateView, InformeIADetailView, ExerciciCreateView,
    DescansListView, DescansCreateView, DescansUpdateView, DescansDeleteView,
    AtletaAutocompleteView, ExerciciAutocompleteView
)

urlpatterns = [
    # Dashboard Overview
    path("", DashboardView.as_view(), name="dashboard"),
    path("api/dashboard-data/", DashboardDataView.as_view(), name="dashboard_data"),
    path("api/atletes-autocomplete/", AtletaAutocompleteView.as_view(), name="atleta_autocomplete"),
    path("api/exercicis-autocomplete/", ExerciciAutocompleteView.as_view(), name="exercici_autocomplete"),
    
    # Atletes CRUD
    path("atletes/", AtletaListView.as_view(), name="atleta_list"),
    path("atletes/nou/", AtletaCreateView.as_view(), name="atleta_create"),
    path("atletes/<str:dni>/", AtletaDetailView.as_view(), name="atleta_detail"),
    path("atletes/<str:dni>/editar/", AtletaUpdateView.as_view(), name="atleta_update"),
    path("atletes/<str:dni>/eliminar/", AtletaDeleteView.as_view(), name="atleta_delete"),
    
    # Lesions CRUD
    path("lesions/", LesioListView.as_view(), name="lesio_list"),
    path("lesions/nova/", LesioCreateView.as_view(), name="lesio_create"),
    path("lesions/<str:dni>/<int:id_lesio>/editar/", LesioUpdateView.as_view(), name="lesio_update"),
    
    # Alimentacio CRUD
    path("atletes/<str:dni>/alimentacio/nova/", AlimentacioCreateView.as_view(), name="alimentacio_create"),
    path("atletes/<str:dni>/alimentacio/editar/", AlimentacioUpdateView.as_view(), name="alimentacio_update"),

    # Descans CRUD
    path("descans/", DescansListView.as_view(), name="descans_list"),
    path("descans/nou/", DescansCreateView.as_view(), name="descans_create"),
    path("descans/<int:pk>/editar/", DescansUpdateView.as_view(), name="descans_update"),
    path("descans/<int:pk>/eliminar/", DescansDeleteView.as_view(), name="descans_delete"),

    # Sessions d'Entrenament CRUD
    path("sessions/", SessioListView.as_view(), name="sessio_list"),
    path("sessions/nova/", SessioCreateView.as_view(), name="sessio_create"),
    
    # Exercicis
    path("exercicis/nou/", ExerciciCreateView.as_view(), name="exercici_create"),
    
    # Ubicacions i Valoracions
    path("ubicacions/", UbicacioListView.as_view(), name="ubicacio_list"),
    path("ubicacions/nova/", UbicacioCreateView.as_view(), name="ubicacio_create"),
    path("valorar/", ValoracioCreateView.as_view(), name="valoracio_create"),
    
    # Registres Diaris i Informes IA
    path("atletes/<str:dni>/registre-diari/nou/", RegistreDiariCreateView.as_view(), name="registre_diari_create"),
    path("informe-ia/<int:registre_id>/", InformeIADetailView.as_view(), name="informe_ia_detail"),
]
