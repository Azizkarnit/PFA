import { TranslatePipe } from '@ngx-translate/core';
import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ContactService, Contact } from '../../../core/services/contact.service';
import { CompanyService } from '../../../core/services/company.service';

@Component({
  selector: 'app-contacts',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe],
  templateUrl: './contacts.html',
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
  `
})
export class Contacts implements OnInit {
  private contactService = inject(ContactService);
  private companyService = inject(CompanyService);

  contacts: Contact[] = [];
  companies: any[] = [];
  
  // Pagination
  currentPage = 1;
  pageSize = 10;
  totalCount = 0;
  
  // Filters
  searchQuery = '';
  companyFilter: number | '' = '';
  statusFilter = 'ALL';
  isFilterDropdownOpen = false;

  // Sidebar State
  selectedContact: Contact | null = null;
  isEditing = false;
  isAdding = false;
  isEditDropdownOpen = false;

  // Form Data
  formData: any = {
    first_name: '',
    last_name: '',
    email: '',
    phone_number: '',
    position: '',
    company_id: null,
    is_primary_contact: false
  };
  formErrors: string[] = [];
  isSaving = false;

  modalConfig: { isOpen: boolean; title: string; message: string; type: 'error' | 'confirm'; onConfirm?: () => void } = {
    isOpen: false, title: '', message: '', type: 'error'
  };

  ngOnInit() {
    this.loadContacts();
    this.loadCompanies();
    document.addEventListener('click', this.onDocumentClick);
  }

  ngOnDestroy() {
    document.removeEventListener('click', this.onDocumentClick);
  }

  onDocumentClick = (event: MouseEvent) => {
    const target = event.target as HTMLElement;
    if (!target.closest('.custom-dropdown-container')) {
      this.isFilterDropdownOpen = false;
      this.isEditDropdownOpen = false;
    }
  };

  loadContacts() {
    const skip = (this.currentPage - 1) * this.pageSize;
    this.contactService.getContacts(
      skip, 
      this.pageSize, 
      this.searchQuery, 
      this.companyFilter ? Number(this.companyFilter) : undefined, 
      this.statusFilter
    ).subscribe({
      next: (res) => {
        this.contacts = res.items;
        this.totalCount = res.total_count;
      },
      error: (err) => console.error('Error loading contacts', err)
    });
  }

  companySearchQuery = '';

  loadCompanies() {
    // Fetch up to 100 companies matching the search query
    this.companyService.getCompanies(0, 100, this.companySearchQuery || undefined).subscribe({
      next: (res) => {
        this.companies = res.items;
      }
    });
  }

  onCompanySearch() {
    this.loadCompanies();
  }

  toggleFilterDropdown(event: Event) {
    event.stopPropagation();
    this.isFilterDropdownOpen = !this.isFilterDropdownOpen;
    this.isEditDropdownOpen = false;
  }

  toggleEditDropdown(event: Event) {
    event.stopPropagation();
    this.isEditDropdownOpen = !this.isEditDropdownOpen;
    this.isFilterDropdownOpen = false;
  }

  get selectedCompanyFilterName(): string {
    const comp = this.companies.find(c => c.id === this.companyFilter);
    return comp ? comp.company_name : 'Selected Company';
  }

  get selectedFormDataCompanyName(): string {
    const comp = this.companies.find(c => c.id === this.formData.company_id);
    return comp ? comp.company_name : 'Select a company...';
  }

  get totalPages(): number {
    return Math.max(1, Math.ceil(this.totalCount / this.pageSize));
  }

  get startIndex(): number {
    return this.totalCount === 0 ? 0 : (this.currentPage - 1) * this.pageSize + 1;
  }

  get endIndex(): number {
    return Math.min(this.currentPage * this.pageSize, this.totalCount);
  }

  changePage(page: number) {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.loadContacts();
    }
  }

  onSearch() {
    this.currentPage = 1;
    this.loadContacts();
  }

  setStatusFilter(status: string) {
    this.statusFilter = status;
    this.currentPage = 1;
    this.loadContacts();
  }

  onCompanyFilterChange() {
    this.currentPage = 1;
    this.loadContacts();
  }

  clearFilters(event?: Event): void {
    if (event) {
      event.preventDefault();
    }
    this.searchQuery = '';
    this.companyFilter = '';
    this.statusFilter = 'ALL';
    this.currentPage = 1;
    this.loadContacts();
  }

  // --- Actions ---

  toggleStatus(contact: Contact) {
    const isDisabling = contact.status === 'ACTIVE';
    const action = isDisabling ? 'disable' : 'enable';
    
    this.showConfirm(
      `${isDisabling ? 'Disable' : 'Enable'} Contact`,
      `Are you sure you want to ${action} ${contact.first_name}?`,
      () => {
        this.contactService.toggleStatus(contact.id).subscribe({
          next: (res) => {
            contact.status = res.status;
            if (this.selectedContact?.id === contact.id) {
              this.selectedContact.status = res.status;
            }
          },
          error: (err) => console.error('Error toggling status', err)
        });
      }
    );
  }

  // --- Modal Logic ---
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

  // --- Sidebar Logic ---
  openDetails(contact: Contact) {
    this.selectedContact = contact;
    this.isEditing = false;
  }

  startEdit(contact: Contact) {
    this.selectedContact = contact;
    this.isEditing = true;
    this.formData = {
      first_name: contact.first_name,
      last_name: contact.last_name,
      email: contact.email,
      phone_number: contact.phone_number || '',
      position: contact.position || '',
      company_id: contact.company_id,
      is_primary_contact: contact.is_primary_contact
    };
  }

  closeSidebar() {
    this.selectedContact = null;
    this.isEditing = false;
  }

  resetForm() {
    this.formData = {
      first_name: '',
      last_name: '',
      email: '',
      phone_number: '',
      position: '',
      company_id: null,
      is_primary_contact: false
    };
    this.formErrors = [];
  }

  saveContact() {
    this.formErrors = [];
    if (!this.formData.first_name?.trim()) this.formErrors.push('First Name is required');
    if (!this.formData.last_name?.trim()) this.formErrors.push('Last Name is required');
    if (!this.formData.email?.trim()) this.formErrors.push('Email is required');
    if (!this.formData.company_id) this.formErrors.push('Company is required');

    if (this.formErrors.length > 0) return;

    this.isSaving = true;

    if (this.isEditing && this.selectedContact) {
      this.contactService.updateContact(this.selectedContact.id, this.formData).subscribe({
        next: (res) => {
          this.isSaving = false;
          this.closeSidebar();
          this.loadContacts();
        },
        error: (err) => {
          this.isSaving = false;
          this.formErrors.push(err.error?.detail || 'An error occurred while updating contact');
        }
      });
    }
  }
}
