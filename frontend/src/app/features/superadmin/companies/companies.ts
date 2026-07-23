import { LanguageService } from '../../../core/services/language.service';
import { TranslatePipe } from '@ngx-translate/core';
import { Component, OnInit, inject, HostListener, ElementRef } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { CompanyService, Company, Sector, Activity } from '../../../core/services/company.service';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-companies',
  imports: [RouterLink, CommonModule, FormsModule, ReactiveFormsModule, TranslatePipe],
  templateUrl: './companies.html',
  styles: `
    .details-sidebar {
      position: fixed;
      top: 0;
      right: 0;
      bottom: 0;
      width: 100%;
      max-width: 400px;
      z-index: 1060;
      transform: translateX(100%);
      transition: transform 0.3s ease-in-out;
    }
    
    .details-sidebar.open {
      transform: translateX(0);
    }
    
    .sidebar-backdrop {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background-color: rgba(0, 0, 0, 0.5);
      z-index: 1050;
    }

    @media (max-width: 991.98px) {
      .details-sidebar {
        max-width: 100%;
      }
    }
  `,
  providers: [DatePipe]
})
export class Companies implements OnInit {
  public langService = inject(LanguageService);
  private authService = inject(AuthService);

  get currentUserRole(): string | null {
    const user = this.authService.getCurrentUser();
    return user ? user.role : null;
  }

  get canEditCompany(): boolean {
    return this.currentUserRole === 'SYSTEM_ADMINISTRATOR';
  }

  

  companies: Company[] = [];
  totalCount: number = 0;
  currentPage: number = 1;
  limit: number = 10;

  selectedCompany: Company | null = null;
  isEditing = false;
  isSaving = false;
  editForm!: FormGroup;
  sectors: Sector[] = [];
  activities: Activity[] = [];

  // Filters
  searchInput = '';
  searchQuery = '';
  selectedSector = '';
  selectedActivity = '';
  selectedGovernorate = '';
  selectedStatus = '';

  // Modal State
  modalConfig: {
    isOpen: boolean;
    title: string;
    message: string;
    type: 'confirm' | 'error';
    onConfirm?: () => void;
  } = { isOpen: false, title: '', message: '', type: 'confirm' };

  private companyService = inject(CompanyService);
  private fb = inject(FormBuilder);
  private el = inject(ElementRef);

  get totalPages(): number {
    return Math.ceil(this.totalCount / this.limit) || 1;
  }

  get startIndex(): number {
    return this.totalCount > 0 ? (this.currentPage - 1) * this.limit + 1 : 0;
  }

  get endIndex(): number {
    return Math.min(this.currentPage * this.limit, this.totalCount);
  }

  ngOnInit(): void {
    this.editForm = this.fb.group({
      identifier: ['', Validators.required],
      company_name: ['', Validators.required],
      email: [''],
      phone: [''],
      tax_number: [''],
      address: [''],
      postal_code: [''],
      governorate: [''],
      sector_id: [''],
      activity_id: ['']
    });
    this.loadCompanies();
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

  loadCompanies(): void {
    const skip = (this.currentPage - 1) * this.limit;
    
    const sectorId = this.selectedSector ? Number(this.selectedSector) : undefined;
    const activityId = this.selectedActivity ? Number(this.selectedActivity) : undefined;
    const governorate = this.selectedGovernorate ? this.selectedGovernorate : undefined;
    const status = this.selectedStatus ? this.selectedStatus : undefined;

    this.companyService.getCompanies(skip, this.limit, this.searchQuery || undefined, sectorId, activityId, governorate, status).subscribe({
      next: (data) => {
        this.companies = data.items;
        this.totalCount = data.total_count;
      },
      error: (err) => {
        console.error('Error fetching companies', err);
      }
    });
  }

  onSearch(): void {
    this.searchQuery = this.searchInput;
    this.currentPage = 1;
    this.loadCompanies();
  }

  onFilterChange(): void {
    this.currentPage = 1;
    this.loadCompanies();
  }

  clearFilters(event?: Event): void {
    if (event) {
      event.preventDefault();
    }
    this.searchInput = '';
    this.searchQuery = '';
    this.selectedSector = '';
    this.selectedActivity = '';
    this.selectedGovernorate = '';
    this.selectedStatus = '';
    this.currentPage = 1;
    this.loadCompanies();
  }


  changePage(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.loadCompanies();
    }
  }

  showError(message: string): void {
    this.modalConfig = { isOpen: true, title: 'Error', message, type: 'error' };
  }

  showConfirm(title: string, message: string, onConfirm: () => void): void {
    this.modalConfig = { isOpen: true, title, message, type: 'confirm', onConfirm };
  }

  closeModal(): void {
    this.modalConfig.isOpen = false;
  }

  confirmModal(): void {
    if (this.modalConfig.onConfirm) this.modalConfig.onConfirm();
    this.closeModal();
  }

  selectCompany(company: Company, event?: Event): void {
    if (event) {
      event.stopPropagation();
    }
    this.selectedCompany = company;
    this.isEditing = false;
    document.body.style.overflow = 'hidden';
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (!this.selectedCompany) return;
    
    const sidebar = this.el.nativeElement.querySelector('.details-sidebar');
    if (sidebar && sidebar.contains(event.target)) {
      return;
    }
    
    this.closeSidebar();
  }

  closeSidebar(): void {
    this.selectedCompany = null;
    this.isEditing = false;
    document.body.style.overflow = '';
  }

  toggleEditMode(): void {
    if (!this.selectedCompany) return;
    this.isEditing = true;
    
    this.editForm.patchValue({
      identifier: this.selectedCompany.identifier || '',
      company_name: this.selectedCompany.company_name || '',
      email: this.selectedCompany.email || '',
      phone: this.selectedCompany.phone || '',
      tax_number: this.selectedCompany.tax_number || '',
      address: this.selectedCompany.address || '',
      postal_code: this.selectedCompany.postal_code || '',
      governorate: this.selectedCompany.governorate || '',
      sector_id: this.selectedCompany.sector.id || '',
      activity_id: this.selectedCompany.activity.id || ''
    });
  }

  cancelEdit(): void {
    this.isEditing = false;
  }

  saveEdit(): void {
    if (this.editForm.invalid || !this.selectedCompany) return;

    this.isSaving = true;
    const payload = { ...this.editForm.value };
    if (payload.sector_id) payload.sector_id = Number(payload.sector_id);
    if (payload.activity_id) payload.activity_id = Number(payload.activity_id);

    this.companyService.updateCompany(this.selectedCompany.id, payload).subscribe({
      next: (updatedCompany) => {
        this.isSaving = false;
        this.isEditing = false;
        this.selectedCompany = updatedCompany;
        const idx = this.companies.findIndex(c => c.id === updatedCompany.id);
        if (idx !== -1) {
          this.companies[idx] = updatedCompany;
        }
      },
      error: (err) => {
        this.isSaving = false;
        console.error('Error updating company:', err);
        this.showError('Failed to update company.');
      }
    });
  }

  toggleCompanyStatus(company: Company | null, event?: Event): void {
    if (event) event.stopPropagation();
    if (!company) return;
    
    const isArchiving = company.status === 'ACTIVE';
    const action = isArchiving ? 'Archive' : 'Activate';
    const newStatus = isArchiving ? 'INACTIVE' : 'ACTIVE';
    
    this.showConfirm(
      `${action} Company`,
      `Are you sure you want to ${action.toLowerCase()} this company?`,
      () => {
        this.companyService.updateCompanyStatus(company.id, newStatus).subscribe({
          next: () => {
            company.status = newStatus;
            if (this.selectedCompany?.id === company.id) {
              this.selectedCompany.status = newStatus;
            }
          },
          error: (err) => {
            console.error(`Error ${action.toLowerCase()}ing company:`, err);
            this.showError(`Failed to ${action.toLowerCase()} company.`);
          }
        });
      }
    );
  }
}
