import csv
import os
from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth.models import User
from apps.claims.models import Claim, ClaimDetail, DataUpload


class Command(BaseCommand):
    help = 'Load claims data from CSV files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--claims-file',
            type=str,
            default='claim_list_data.csv',
            help='Path to claims list CSV file'
        )
        parser.add_argument(
            '--details-file',
            type=str,
            default='claim_detail_data.csv',
            help='Path to claims detail CSV file'
        )
        parser.add_argument(
            '--mode',
            type=str,
            choices=['append', 'overwrite'],
            default='overwrite',
            help='Data loading mode: append or overwrite existing data'
        )

    def handle(self, *args, **options):
        claims_file = options['claims_file']
        details_file = options['details_file']
        mode = options['mode']

        # Check if files exist
        if not os.path.exists(claims_file):
            raise CommandError(f'Claims file "{claims_file}" does not exist.')
        if not os.path.exists(details_file):
            raise CommandError(f'Details file "{details_file}" does not exist.')

        self.stdout.write(
            self.style.SUCCESS(f'Starting data load in {mode} mode...')
        )

        try:
            with transaction.atomic():
                if mode == 'overwrite':
                    self.stdout.write('Clearing existing data...')
                    Claim.objects.all().delete()
                    ClaimDetail.objects.all().delete()

                # Load claims data
                claims_count = self._load_claims(claims_file)
                
                # Load claim details
                details_count = self._load_claim_details(details_file)

                # Create upload record
                upload_record = DataUpload.objects.create(
                    upload_type='overwrite' if mode == 'overwrite' else 'append',
                    file_name=f"{os.path.basename(claims_file)}, {os.path.basename(details_file)}",
                    records_processed=claims_count,
                    notes=f"Claims: {claims_count}, Details: {details_count}"
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully loaded {claims_count} claims and {details_count} details'
                    )
                )

        except Exception as e:
            raise CommandError(f'Error loading data: {str(e)}')

    def _load_claims(self, file_path):
        """Load claims from CSV file"""
        count = 0
        
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter='|')
            
            for row in reader:
                try:
                    # Parse date
                    discharge_date = datetime.strptime(row['discharge_date'], '%Y-%m-%d').date()
                    
                    # Parse amounts
                    billed_amount = Decimal(row['billed_amount'])
                    paid_amount = Decimal(row['paid_amount'])
                    
                    # Create or update claim
                    claim, created = Claim.objects.update_or_create(
                        claim_id=row['id'],
                        defaults={
                            'patient_name': row['patient_name'],
                            'billed_amount': billed_amount,
                            'paid_amount': paid_amount,
                            'status': row['status'],
                            'insurer_name': row['insurer_name'],
                            'discharge_date': discharge_date,
                        }
                    )
                    
                    if created:
                        count += 1
                        
                    if count % 100 == 0:
                        self.stdout.write(f'Processed {count} claims...')
                        
                except (ValueError, InvalidOperation, KeyError) as e:
                    self.stdout.write(
                        self.style.WARNING(f'Skipping invalid row: {row} - Error: {e}')
                    )
                    continue
                    
        return count

    def _load_claim_details(self, file_path):
        """Load claim details from CSV file"""
        count = 0
        
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter='|')
            
            for row in reader:
                try:
                    # Find the corresponding claim
                    try:
                        claim = Claim.objects.get(claim_id=row['claim_id'])
                    except Claim.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(f'Claim {row["claim_id"]} not found for detail record')
                        )
                        continue
                    
                    # Create or update claim detail
                    detail, created = ClaimDetail.objects.update_or_create(
                        claim=claim,
                        defaults={
                            'denial_reason': row.get('denial_reason', ''),
                            'cpt_codes': row.get('cpt_codes', ''),
                        }
                    )
                    
                    if created:
                        count += 1
                        
                    if count % 100 == 0:
                        self.stdout.write(f'Processed {count} claim details...')
                        
                except KeyError as e:
                    self.stdout.write(
                        self.style.WARNING(f'Skipping invalid detail row: {row} - Error: {e}')
                    )
                    continue
                    
        return count