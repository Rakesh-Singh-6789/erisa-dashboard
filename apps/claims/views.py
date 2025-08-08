import csv
import io
from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, TemplateView, View
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Sum, Avg
from django.contrib import messages
from django.core.paginator import Paginator
from django.conf import settings
from .models import Claim, ClaimDetail, ClaimFlag, ClaimNote, DataUpload


class ClaimsListView(LoginRequiredMixin, ListView):
    """Main claims list view with search and filtering"""
    model = Claim
    template_name = 'claims/claims_list.html'
    context_object_name = 'claims'
    paginate_by = settings.CLAIMS_PER_PAGE

    def get_queryset(self):
        queryset = Claim.objects.select_related('detail').prefetch_related('flags', 'notes')
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(claim_id__icontains=search) |
                Q(patient_name__icontains=search) |
                Q(insurer_name__icontains=search)
            )
        
        # Status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Insurer filter
        insurer = self.request.GET.get('insurer')
        if insurer:
            queryset = queryset.filter(insurer_name=insurer)
        
        # Date range filter
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(discharge_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(discharge_date__lte=date_to)
        
        # Amount filters
        min_amount = self.request.GET.get('min_amount')
        max_amount = self.request.GET.get('max_amount')
        if min_amount:
            queryset = queryset.filter(billed_amount__gte=min_amount)
        if max_amount:
            queryset = queryset.filter(billed_amount__lte=max_amount)
        
        # Flagged claims filter
        flagged_only = self.request.GET.get('flagged_only')
        if flagged_only:
            queryset = queryset.filter(flags__is_active=True).distinct()
        
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter options
        context['status_choices'] = Claim.STATUS_CHOICES
        context['insurers'] = Claim.objects.values_list('insurer_name', flat=True).distinct().order_by('insurer_name')
        
        # Preserve current filters
        context['current_search'] = self.request.GET.get('search', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_insurer'] = self.request.GET.get('insurer', '')
        context['current_date_from'] = self.request.GET.get('date_from', '')
        context['current_date_to'] = self.request.GET.get('date_to', '')
        context['current_min_amount'] = self.request.GET.get('min_amount', '')
        context['current_max_amount'] = self.request.GET.get('max_amount', '')
        context['current_flagged_only'] = self.request.GET.get('flagged_only', '')
        
        return context


@login_required
def claim_detail_htmx(request, claim_id):
    """HTMX endpoint for claim detail modal"""
    claim = get_object_or_404(
        Claim.objects.select_related('detail').prefetch_related('notes__user', 'flags__user'), 
        claim_id=claim_id
    )
    return render(request, 'claims/partials/claim_detail_modal.html', {'claim': claim})


@login_required
def claim_details_htmx(request, claim_id):
    """HTMX endpoint for dynamic claim details"""
    claim = get_object_or_404(Claim, claim_id=claim_id)
    return render(request, 'claims/partials/claim_details.html', {'claim': claim})


@login_required
def add_flag_htmx(request, claim_id):
    """HTMX endpoint to add a flag to a claim"""
    if request.method == 'POST':
        claim = get_object_or_404(Claim, claim_id=claim_id)
        flag_type = request.POST.get('flag_type', 'review')
        reason = request.POST.get('reason', '')
        
        flag, created = ClaimFlag.objects.get_or_create(
            claim=claim,
            user=request.user,
            flag_type=flag_type,
            defaults={'reason': reason, 'is_active': True}
        )
        
        if not created:
            flag.is_active = True
            flag.reason = reason
            flag.save()
        
        # Return the full notes section to update the entire area
        return render(request, 'claims/partials/notes_section.html', {'claim': claim})
    
    claim = get_object_or_404(Claim, claim_id=claim_id)
    return render(request, 'claims/partials/add_flag_form.html', {
        'claim': claim,
        'flag_types': ClaimFlag.FLAG_TYPES
    })


@login_required
def add_note_htmx(request, claim_id):
    """HTMX endpoint to add a note to a claim"""
    if request.method == 'POST':
        claim = get_object_or_404(Claim, claim_id=claim_id)
        note_text = request.POST.get('note_text', '')
        
        if note_text:
            ClaimNote.objects.create(
                claim=claim,
                user=request.user,
                note=note_text
            )
        
        # Return the full notes section to update the entire area  
        return render(request, 'claims/partials/notes_section.html', {'claim': claim})
    
    claim = get_object_or_404(Claim, claim_id=claim_id)
    return render(request, 'claims/partials/add_note_form.html', {'claim': claim})


@login_required
def remove_flag_htmx(request, flag_id):
    """HTMX endpoint to remove a flag"""
    flag = get_object_or_404(ClaimFlag, id=flag_id, user=request.user)
    claim = flag.claim
    flag.is_active = False
    flag.save()
    
    return render(request, 'claims/partials/claim_flags.html', {'claim': claim})


class DashboardView(LoginRequiredMixin, TemplateView):
    """Admin dashboard with analytics and statistics"""
    template_name = 'claims/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Basic statistics
        total_claims = Claim.objects.count()
        total_billed = Claim.objects.aggregate(Sum('billed_amount'))['billed_amount__sum'] or 0
        total_paid = Claim.objects.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
        total_underpayment = total_billed - total_paid
        
        # Status breakdown
        status_breakdown = Claim.objects.values('status').annotate(
            count=Count('id'),
            total_billed=Sum('billed_amount'),
            total_paid=Sum('paid_amount')
        ).order_by('status')
        
        # Insurer analysis
        insurer_stats = Claim.objects.values('insurer_name').annotate(
            count=Count('id'),
            total_billed=Sum('billed_amount'),
            total_paid=Sum('paid_amount'),
            avg_payment_rate=Avg('paid_amount') * 100 / Avg('billed_amount')
        ).order_by('-count')[:10]
        
        # Flagged claims (ensure we show 0 if none)
        flagged_claims_count = Claim.objects.filter(flags__is_active=True).distinct().count() or 0
        
        # Average underpayment calculation
        from django.db import models
        underpaid_claims = Claim.objects.annotate(
            underpayment=models.F('billed_amount') - models.F('paid_amount')
        ).filter(underpayment__gt=0)
        
        avg_underpayment = underpaid_claims.aggregate(
            avg_underpayment=Avg('underpayment')
        )['avg_underpayment'] or 0
        
        # Recent activity
        recent_flags = ClaimFlag.objects.filter(is_active=True).select_related('claim', 'user')[:10]
        recent_notes = ClaimNote.objects.select_related('claim', 'user')[:10]
        
        # Top underpaid claims
        top_underpaid = underpaid_claims.order_by('-underpayment')[:10]
        
        context.update({
            'total_claims': total_claims,
            'total_billed': total_billed,
            'total_paid': total_paid,
            'total_underpayment': total_underpayment,
            'avg_underpayment': avg_underpayment,
            'payment_rate': (total_paid / total_billed * 100) if total_billed > 0 else 0,
            'status_breakdown': status_breakdown,
            'insurer_stats': insurer_stats,
            'flagged_claims': flagged_claims_count,
            'recent_flags': recent_flags,
            'recent_notes': recent_notes,
            'top_underpaid': top_underpaid,
        })
        
        return context


class DataUploadView(LoginRequiredMixin, View):
    """Handle CSV data uploads"""
    template_name = 'claims/data_upload.html'

    def get(self, request):
        recent_uploads = DataUpload.objects.all()[:10]
        return render(request, self.template_name, {'recent_uploads': recent_uploads})

    def post(self, request):
        claims_file = request.FILES.get('claims_file')
        details_file = request.FILES.get('details_file')
        mode = request.POST.get('mode', 'append')
        
        if not claims_file or not details_file:
            messages.error(request, 'Both claims and details files are required.')
            return redirect('claims:data_upload')
        
        try:
            # Process the uploaded files
            claims_count = self._process_claims_file(claims_file, mode)
            details_count = self._process_details_file(details_file)
            
            # Create upload record
            DataUpload.objects.create(
                upload_type=mode,
                file_name=f"{claims_file.name}, {details_file.name}",
                records_processed=claims_count,
                user=request.user,
                notes=f"Claims: {claims_count}, Details: {details_count}"
            )
            
            messages.success(
                request, 
                f'Successfully uploaded {claims_count} claims and {details_count} details.'
            )
            
        except Exception as e:
            messages.error(request, f'Error uploading data: {str(e)}')
        
        return redirect('claims:data_upload')

    def _detect_delimiter(self, first_line: str) -> str:
        """Detect CSV delimiter between pipe and comma (defaults to comma)."""
        return '|' if '|' in first_line else ','

    def _process_claims_file(self, file, mode):
        """Process uploaded claims CSV file"""
        if mode == 'overwrite':
            Claim.objects.all().delete()

        processed_count = 0

        file_content = file.read().decode('utf-8')
        lines = file_content.splitlines()
        if not lines:
            return 0
        delimiter = self._detect_delimiter(lines[0])
        reader = csv.DictReader(io.StringIO(file_content), delimiter=delimiter)

        for row in reader:
            try:
                discharge_date = datetime.strptime(row['discharge_date'], '%Y-%m-%d').date()

                # Note: Django will coerce strings to Decimal for DecimalField
                Claim.objects.update_or_create(
                    claim_id=row['id'],
                    defaults={
                        'patient_name': row['patient_name'],
                        'billed_amount': row['billed_amount'],
                        'paid_amount': row['paid_amount'],
                        'status': row['status'],
                        'insurer_name': row['insurer_name'],
                        'discharge_date': discharge_date,
                    }
                )
                processed_count += 1
            except (ValueError, KeyError):
                # Skip malformed rows
                continue

        return processed_count

    def _process_details_file(self, file):
        """Process uploaded details CSV file"""
        processed_count = 0
        file_content = file.read().decode('utf-8')
        lines = file_content.splitlines()
        if not lines:
            return 0
        delimiter = self._detect_delimiter(lines[0])
        reader = csv.DictReader(io.StringIO(file_content), delimiter=delimiter)

        for row in reader:
            try:
                claim = Claim.objects.get(claim_id=row['claim_id'])
                ClaimDetail.objects.update_or_create(
                    claim=claim,
                    defaults={
                        'denial_reason': row.get('denial_reason', ''),
                        'cpt_codes': row.get('cpt_codes', ''),
                    }
                )
                processed_count += 1
            except (Claim.DoesNotExist, KeyError):
                continue

        return processed_count


@login_required
def search_claims(request):
    """API endpoint for dynamic search"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    claims = Claim.objects.filter(
        Q(claim_id__icontains=query) |
        Q(patient_name__icontains=query) |
        Q(insurer_name__icontains=query)
    )[:10]
    
    results = []
    for claim in claims:
        results.append({
            'id': claim.claim_id,
            'text': f"{claim.claim_id} - {claim.patient_name} ({claim.insurer_name})",
            'patient_name': claim.patient_name,
            'insurer_name': claim.insurer_name,
            'status': claim.status,
            'billed_amount': str(claim.billed_amount),
            'paid_amount': str(claim.paid_amount),
        })
    
    return JsonResponse({'results': results})