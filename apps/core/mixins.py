"""
Common mixins for views.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from typing import Any, Dict


class BaseViewMixin:
    """Base mixin with common functionality."""
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add common context data."""
        context = super().get_context_data(**kwargs)
        context.update({
            'app_name': 'ERISA Assessment',
            'app_version': '1.0.0',
        })
        return context


class PaginationMixin:
    """Mixin to handle pagination consistently."""
    
    paginate_by = settings.CLAIMS_PER_PAGE
    page_kwarg = 'page'
    
    def paginate_queryset(self, queryset, page_size=None):
        """Paginate the queryset."""
        if page_size is None:
            page_size = self.paginate_by
            
        paginator = Paginator(queryset, page_size)
        page = self.request.GET.get(self.page_kwarg)
        
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
            
        return page_obj


class FilterMixin:
    """Mixin to handle filtering consistently."""
    
    filter_fields = []
    search_fields = []
    
    def filter_queryset(self, queryset):
        """Apply filters to the queryset."""
        # Apply search
        search = self.request.GET.get('search')
        if search and self.search_fields:
            from django.db.models import Q
            search_q = Q()
            for field in self.search_fields:
                search_q |= Q(**{f"{field}__icontains": search})
            queryset = queryset.filter(search_q)
        
        # Apply filters
        for field in self.filter_fields:
            value = self.request.GET.get(field)
            if value:
                queryset = queryset.filter(**{field: value})
                
        return queryset
    
    def get_filter_context(self):
        """Get context data for filters."""
        return {
            'current_search': self.request.GET.get('search', ''),
            'current_filters': {
                field: self.request.GET.get(field, '')
                for field in self.filter_fields
            }
        }