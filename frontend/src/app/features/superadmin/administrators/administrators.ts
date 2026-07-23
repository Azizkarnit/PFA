import { Component, OnInit, inject, HostListener, ElementRef } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { UserService, UserAdmin } from '../../../core/services/user.service';
import { AuthService } from '../../../core/services/auth.service';
import { TranslatePipe } from '@ngx-translate/core';

@Component({
  selector: 'app-administrators',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule, ReactiveFormsModule, TranslatePipe],
  templateUrl: './administrators.html',
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
export class Administrators implements OnInit {
  private userService = inject(UserService);
  private authService = inject(AuthService);

  get currentUserRole(): string | null {
    const user = this.authService.getCurrentUser();
    return user ? user.role : null;
  }
  private fb = inject(FormBuilder);
  private el = inject(ElementRef);

  users: UserAdmin[] = [];
  selectedUser: UserAdmin | null = null;
  
  isEditing = false;
  isSaving = false;
  editForm!: FormGroup;
  roles: any[] = [];
  
  // Pagination
  currentPage = 1;
  pageSize = 10;
  totalItems = 0;

  get totalPages(): number {
    return Math.ceil(this.totalItems / this.pageSize) || 1;
  }

  
  // Filters
  searchInput = '';
  searchQuery = '';
  selectedStatus = 'all';
  selectedRole = 'all';

  // Modal State
  modalConfig: {
    isOpen: boolean;
    title: string;
    message: string;
    type: 'confirm' | 'error';
    onConfirm?: () => void;
  } = { isOpen: false, title: '', message: '', type: 'confirm' };

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


  canEditUser(user: UserAdmin): boolean {
    return this.currentUserRole === 'SYSTEM_ADMINISTRATOR';
  }

  ngOnInit(): void {
    this.editForm = this.fb.group({
      first_name: ['', Validators.required],
      last_name: ['', Validators.required],
      phone: ['', Validators.required],
      role_id: ['', Validators.required]
    });
    this.loadRoles();
    this.loadData();
  }

  loadRoles(): void {
    this.userService.getRoles().subscribe({
      next: (data) => {
        // Since this is the administrators page, filter out COMPANY_CONTACT for everyone
        let filteredRoles = data.filter((r: any) => r.code !== 'COMPANY_CONTACT');
        
        // Prevent Account Managers from escalating to System Administrator
        if (this.currentUserRole === 'ACCOUNT_MANAGER') {
          filteredRoles = filteredRoles.filter((r: any) => r.code !== 'SYSTEM_ADMINISTRATOR');
        }
        
        this.roles = filteredRoles;
      },
      error: (err) => console.error('Error fetching roles', err)
    });
  }

  loadData(): void {
    const skip = (this.currentPage - 1) * this.pageSize;
    
    this.userService.getUsers(skip, this.pageSize, this.searchQuery, this.selectedStatus, this.selectedRole)
      .subscribe({
        next: (res) => {
          this.users = res.items;
          this.totalItems = res.total_count;
        },
        error: (err) => console.error('Error fetching users:', err)
      });
  }

  onSearch(): void {
    this.searchQuery = this.searchInput;
    this.currentPage = 1; // Reset to first page
    this.loadData();
  }

  onFilterChange(): void {
    this.currentPage = 1;
    this.loadData();
  }

  clearFilters(event?: Event): void {
    if (event) {
      event.preventDefault();
    }
    this.searchInput = '';
    this.searchQuery = '';
    this.selectedStatus = 'all';
    this.selectedRole = 'all';
    this.currentPage = 1;
    this.loadData();
  }

  nextPage(): void {
    if (this.currentPage * this.pageSize < this.totalItems) {
      this.currentPage++;
      this.loadData();
    }
  }

  prevPage(): void {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.loadData();
    }
  }

  get startIndex(): number {
    return this.totalItems === 0 ? 0 : (this.currentPage - 1) * this.pageSize + 1;
  }

  get endIndex(): number {
    return Math.min(this.currentPage * this.pageSize, this.totalItems);
  }

  selectUser(user: UserAdmin, event?: Event): void {
    if (event) {
      event.stopPropagation();
    }
    this.selectedUser = user;
    this.isEditing = false;
    document.body.style.overflow = 'hidden'; // Prevent background scrolling on mobile
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (!this.selectedUser) return;
    
    const sidebar = this.el.nativeElement.querySelector('.details-sidebar');
    if (sidebar && sidebar.contains(event.target)) {
      return;
    }
    
    this.closeSidebar();
  }

  closeSidebar(): void {
    this.selectedUser = null;
    this.isEditing = false;
    document.body.style.overflow = '';
  }

  toggleEditMode(): void {
    if (!this.selectedUser) return;
    this.isEditing = true;
    
    // Find role ID by role name
    const roleId = this.roles.find(r => r.name === this.selectedUser?.role_name)?.id || '';

    let firstName = this.selectedUser.first_name;
    let lastName = this.selectedUser.last_name;

    // Fallback: If no explicit first/last name (e.g. legacy/seed users), derive from the display name
    if (!firstName && !lastName && this.selectedUser.name) {
      const parts = this.selectedUser.name.split(' ');
      firstName = parts[0] || '';
      lastName = parts.slice(1).join(' ') || parts[0] || ''; // Default last name to first name if only one word
    }

    this.editForm.patchValue({
      first_name: firstName || '',
      last_name: lastName || '',
      phone: this.selectedUser.phone || '',
      role_id: roleId
    });
  }

  cancelEdit(): void {
    this.isEditing = false;
  }

  saveEdit(): void {
    if (this.editForm.invalid || !this.selectedUser) return;

    this.isSaving = true;
    const payload = { ...this.editForm.value };
    payload.role_id = Number(payload.role_id);

    this.userService.updateUser(this.selectedUser.id, payload).subscribe({
      next: (updatedUser) => {
        this.isSaving = false;
        this.isEditing = false;
        this.selectedUser = updatedUser;
        // Update user in the list
        const idx = this.users.findIndex(u => u.id === updatedUser.id);
        if (idx !== -1) {
          this.users[idx] = updatedUser;
        }
      },
      error: (err) => {
        this.isSaving = false;
        console.error('Error updating user:', err);
        this.showError('Failed to update user.');
      }
    });
  }

  toggleUserStatus(user: UserAdmin | null, event?: Event): void {
    if (event) event.stopPropagation();
    if (!user) return;
    
    const isDisabling = user.status !== 'DISABLED';
    const action = isDisabling ? 'disable' : 're-enable';
    const newStatus = isDisabling ? 'DISABLED' : 'ACTIVE';
    
    this.showConfirm(
      `${isDisabling ? 'Disable' : 'Enable'} Account`,
      `Are you sure you want to ${action} this account?`,
      () => {
        this.userService.updateUserStatus(user.id, newStatus).subscribe({
          next: () => {
            user.status = newStatus;
            if (this.selectedUser?.id === user.id) {
              this.selectedUser.status = newStatus;
            }
          },
          error: (err) => {
            console.error(`Error ${action}ing user:`, err);
            this.showError(`Failed to ${action} user.`);
          }
        });
      }
    );
  }
}
