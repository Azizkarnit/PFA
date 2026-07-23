import { LanguageService } from '../../../core/services/language.service';
import { TranslatePipe } from '@ngx-translate/core';
import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { CompanyService, Sector, Activity } from '../../../core/services/company.service';

@Component({
  selector: 'app-add-company',
  imports: [RouterLink, CommonModule, FormsModule, ReactiveFormsModule, TranslatePipe],
  templateUrl: './add-company.html',
  styles: ``
})
export class AddCompany implements OnInit {
  public langService = inject(LanguageService);

  

  addForm!: FormGroup;
  isSaving = false;
  errorMessage = '';
  
  sectors: Sector[] = [];
  activities: Activity[] = [];

  private fb = inject(FormBuilder);
  private companyService = inject(CompanyService);
  private router = inject(Router);

  ngOnInit(): void {
    this.addForm = this.fb.group({
      identifier: ['', Validators.required],
      company_name: ['', Validators.required],
      email: [''],
      phone: [''],
      tax_number: [''],
      address: [''],
      postal_code: [''],
      governorate: [''],
      sector_id: ['', Validators.required],
      activity_id: ['', Validators.required]
    });

    this.loadSectorsAndActivities();
  }

  loadSectorsAndActivities(): void {
    this.companyService.getSectors().subscribe({
      next: (res) => this.sectors = res,
      error: (err) => console.error('Error fetching sectors', err)
    });
    this.companyService.getActivities().subscribe({
      next: (res) => this.activities = res,
      error: (err) => console.error('Error fetching activities', err)
    });
  }

  onSubmit(): void {
    if (this.addForm.invalid) {
      this.addForm.markAllAsTouched();
      return;
    }

    this.isSaving = true;
    this.errorMessage = '';
    
    const payload = { ...this.addForm.value };
    payload.sector_id = Number(payload.sector_id);
    payload.activity_id = Number(payload.activity_id);

    this.companyService.createCompany(payload).subscribe({
      next: () => {
        this.isSaving = false;
        this.router.navigate(['/admin/companies']);
      },
      error: (err) => {
        this.isSaving = false;
        this.errorMessage = err.error?.detail || 'Failed to create company. Please try again.';
      }
    });
  }
}
