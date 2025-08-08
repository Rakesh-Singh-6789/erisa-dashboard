from django.urls import path
from . import views

app_name = 'claims'

urlpatterns = [
    # Main views
    path('', views.ClaimsListView.as_view(), name='claims_list'),
    path('claim/<str:claim_id>/', views.claim_detail_htmx, name='claim_detail'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # HTMX endpoints
    path('htmx/claim-details/<str:claim_id>/', views.claim_details_htmx, name='claim_details_htmx'),
    path('htmx/add-flag/<str:claim_id>/', views.add_flag_htmx, name='add_flag_htmx'),
    path('htmx/add-note/<str:claim_id>/', views.add_note_htmx, name='add_note_htmx'),
    path('htmx/remove-flag/<int:flag_id>/', views.remove_flag_htmx, name='remove_flag_htmx'),
    
    # Data management
    path('upload/', views.DataUploadView.as_view(), name='data_upload'),
    
    # API endpoints for search/filter
    path('api/search/', views.search_claims, name='search_claims'),
]