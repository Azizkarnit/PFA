import { TranslatePipe } from '@ngx-translate/core';
import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, FormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ContactService } from '../../../core/services/contact.service';
import { CompanyService, Company } from '../../../core/services/company.service';

@Component({
  selector: 'app-add-contact',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule, RouterLink, TranslatePipe],
  templateUrl: './add-contact.html',
  styleUrls: ['./add-contact.css']
})
export class AddContact implements OnInit {
  private fb = inject(FormBuilder);
  private contactService = inject(ContactService);
  private companyService = inject(CompanyService);
  private router = inject(Router);

  contactForm!: FormGroup;
  companies: Company[] = [];
  isLoading = false;
  errorMessage = '';
  successMessage = '';

  isCompanyDropdownOpen = false;
  companySearchQuery = '';

  ngOnInit(): void {
    this.contactForm = this.fb.group({
      first_name: ['', [Validators.required, Validators.minLength(2)]],
      last_name: ['', [Validators.required, Validators.minLength(2)]],
      email: ['', [Validators.required, Validators.email]],
      phone_number: [''],
      company_id: ['', [Validators.required]],
      position: [''],
      is_primary_contact: [false]
    });

    this.loadCompanies();
    document.addEventListener('click', this.onDocumentClick);
  }

  ngOnDestroy() {
    document.removeEventListener('click', this.onDocumentClick);
  }

  onDocumentClick = (event: MouseEvent) => {
    const target = event.target as HTMLElement;
    if (!target.closest('.custom-dropdown-container')) {
      this.isCompanyDropdownOpen = false;
    }
  };

  loadCompanies(): void {
    this.companyService.getCompanies(0, 100, this.companySearchQuery || undefined).subscribe({
      next: (res) => {
        this.companies = res.items;
      },
      error: (err) => {
        console.error('Failed to load companies', err);
        this.errorMessage = 'Could not load companies. Please try again.';
      }
    });
  }

  onCompanySearch() {
    this.loadCompanies();
  }

  toggleCompanyDropdown(event: Event) {
    event.stopPropagation();
    this.isCompanyDropdownOpen = !this.isCompanyDropdownOpen;
  }

  get selectedCompanyName(): string {
    const id = this.contactForm.get('company_id')?.value;
    const comp = this.companies.find(c => c.id === id);
    return comp ? comp.company_name : 'Select a company...';
  }

  selectCompany(id: number) {
    this.contactForm.patchValue({ company_id: id });
    this.isCompanyDropdownOpen = false;
  }

  onSubmit(): void {
    if (this.contactForm.invalid) {
      this.contactForm.markAllAsTouched();
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    this.successMessage = '';

    const payload = { ...this.contactForm.value };
    payload.company_id = Number(payload.company_id);

    this.contactService.createContact(payload).subscribe({
      next: () => {
        this.isLoading = false;
        this.successMessage = 'Contact added successfully!';
        setTimeout(() => {
          this.router.navigate(['/admin/contacts']);
        }, 1500);
      },
      error: (err: any) => {
        this.isLoading = false;
        this.errorMessage = err.error?.detail || 'Failed to add contact. Please check your inputs.';
        console.error('Error adding contact:', err);
      }
    });
  }

  onCancel(): void {
    this.router.navigate(['/admin/contacts']);
  }
}
