"""
Claims models for ERISA Assessment project.

This module contains models for managing insurance claims data, including
claim details, flags, notes, and data upload tracking.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TimestampedModel(models.Model):
    """Abstract base model with timestamp fields."""
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the record was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the record was last updated"
    )
    
    class Meta:
        abstract = True


class Claim(TimestampedModel):
    """
    Main claim information from claim_list_data.csv.
    
    Represents an insurance claim with billing and payment information.
    """
    
    STATUS_CHOICES = [
        ('Paid', 'Paid'),
        ('Denied', 'Denied'),
        ('Under Review', 'Under Review'),
    ]
    
    # Primary claim ID from CSV
    claim_id = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Unique identifier for the claim",
        verbose_name="Claim ID"
    )
    
    patient_name = models.CharField(
        max_length=200,
        help_text="Name of the patient",
        verbose_name="Patient Name"
    )
    
    billed_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Amount billed by the provider",
        verbose_name="Billed Amount"
    )
    
    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Amount paid by the insurer",
        verbose_name="Paid Amount"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        db_index=True,
        help_text="Current status of the claim",
        verbose_name="Status"
    )
    
    insurer_name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Name of the insurance company",
        verbose_name="Insurer Name"
    )
    
    discharge_date = models.DateField(
        help_text="Date when the patient was discharged",
        verbose_name="Discharge Date"
    )
    
    class Meta:
        ordering = ['-discharge_date', 'claim_id']
        indexes = [
            models.Index(fields=['status', 'insurer_name']),
            models.Index(fields=['discharge_date']),
            models.Index(fields=['billed_amount']),
            models.Index(fields=['paid_amount']),
        ]
        verbose_name = "Claim"
        verbose_name_plural = "Claims"
    
    def __str__(self) -> str:
        """String representation of the claim."""
        return f"Claim {self.claim_id} - {self.patient_name}"
    
    def clean(self) -> None:
        """Validate the model data."""
        super().clean()
        
        # Ensure paid amount doesn't exceed billed amount
        if self.paid_amount and self.billed_amount and self.paid_amount > self.billed_amount:
            raise ValidationError({
                'paid_amount': 'Paid amount cannot exceed billed amount.'
            })
        
        # Log validation
        logger.debug(f"Validated claim {self.claim_id}")
    
    def save(self, *args, **kwargs) -> None:
        """Save the model with validation."""
        self.full_clean()
        super().save(*args, **kwargs)
        logger.info(f"Saved claim {self.claim_id}")
    
    @property
    def underpayment_amount(self) -> Decimal:
        """
        Calculate underpayment amount.
        
        Returns:
            Decimal: The difference between billed and paid amounts.
        """
        return self.billed_amount - self.paid_amount
    
    @property
    def payment_percentage(self) -> float:
        """
        Calculate payment percentage.
        
        Returns:
            float: Percentage of billed amount that was paid (0-100).
        """
        if self.billed_amount > 0:
            return float((self.paid_amount / self.billed_amount) * 100)
        return 0.0
    
    @property
    def is_denied(self) -> bool:
        """
        Check if the claim is denied.
        
        Returns:
            bool: True if the claim status is 'Denied'.
        """
        return self.status == 'Denied'
    
    @property
    def is_underpaid(self) -> bool:
        """
        Check if claim is significantly underpaid (less than 80% paid).
        
        Returns:
            bool: True if payment percentage is less than 80%.
        """
        return self.payment_percentage < 80.0
    
    @property
    def is_fully_paid(self) -> bool:
        """
        Check if the claim is fully paid.
        
        Returns:
            bool: True if paid amount equals billed amount.
        """
        return self.paid_amount >= self.billed_amount
    
    def get_underpayment_severity(self) -> str:
        """
        Get the severity level of underpayment.
        
        Returns:
            str: Severity level ('none', 'low', 'medium', 'high').
        """
        percentage = self.payment_percentage
        
        if percentage >= 95:
            return 'none'
        elif percentage >= 80:
            return 'low'
        elif percentage >= 50:
            return 'medium'
        else:
            return 'high'


class ClaimDetail(models.Model):
    """Detailed claim information from claim_detail_data.csv"""
    
    claim = models.OneToOneField(Claim, on_delete=models.CASCADE, related_name='detail')
    denial_reason = models.TextField(blank=True, null=True)
    cpt_codes = models.TextField(help_text="Comma-separated CPT codes")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Details for {self.claim.claim_id}"
    
    @property
    def cpt_codes_list(self):
        """Return CPT codes as a list"""
        if self.cpt_codes:
            return [code.strip() for code in self.cpt_codes.split(',')]
        return []


class ClaimFlag(models.Model):
    """User-generated flags for claims requiring review"""
    
    FLAG_TYPES = [
        ('review', 'Review Required'),
        ('urgent', 'Urgent'),
        ('appeal', 'Appeal Candidate'),
        ('investigate', 'Needs Investigation'),
        ('follow_up', 'Follow Up'),
    ]
    
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name='flags')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    flag_type = models.CharField(max_length=20, choices=FLAG_TYPES, default='review')
    reason = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('claim', 'user', 'flag_type')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_flag_type_display()} - {self.claim.claim_id} by {self.user.username}"


class ClaimNote(models.Model):
    """User-generated notes and annotations for claims"""
    
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name='notes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.TextField()
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Note on {self.claim.claim_id} by {self.user.username}"


class DataUpload(models.Model):
    """Track CSV data uploads and refreshes"""
    
    UPLOAD_TYPES = [
        ('initial', 'Initial Load'),
        ('append', 'Append Data'),
        ('overwrite', 'Overwrite Data'),
    ]
    
    upload_type = models.CharField(max_length=20, choices=UPLOAD_TYPES)
    file_name = models.CharField(max_length=255)
    records_processed = models.PositiveIntegerField()
    upload_timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-upload_timestamp']
    
    def __str__(self):
        return f"{self.get_upload_type_display()} - {self.file_name} ({self.records_processed} records)"