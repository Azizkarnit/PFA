import { TranslatePipe } from '@ngx-translate/core';
import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { UserService } from '../../../core/services/user.service';

@Component({
  selector: 'app-locked-accounts',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslatePipe],
  templateUrl: './locked-accounts.html',
  styles: ``,
})
export class LockedAccounts implements OnInit {
  private userService = inject(UserService);

  lockedAccounts: any[] = [];
  filteredAccounts: any[] = [];
  searchInput = '';
  isLoading = false;
  errorMessage = '';

  // Pagination
  currentPage = 1;
  pageSize = 10;

  get totalPages(): number {
    return Math.ceil(this.filteredAccounts.length / this.pageSize) || 1;
  }

  get startIndex(): number {
    return this.filteredAccounts.length > 0 ? (this.currentPage - 1) * this.pageSize + 1 : 0;
  }

  get endIndex(): number {
    return Math.min(this.currentPage * this.pageSize, this.filteredAccounts.length);
  }

  get paginatedAccounts(): any[] {
    const start = (this.currentPage - 1) * this.pageSize;
    return this.filteredAccounts.slice(start, start + this.pageSize);
  }

  onSearch(): void {
    if (!this.searchInput) {
      this.filteredAccounts = [...this.lockedAccounts];
    } else {
      const q = this.searchInput.toLowerCase();
      this.filteredAccounts = this.lockedAccounts.filter(acc => 
        (acc.first_name + ' ' + acc.last_name).toLowerCase().includes(q) ||
        acc.email.toLowerCase().includes(q)
      );
    }
    this.currentPage = 1;
  }

  clearFilters(event?: Event): void {
    if (event) {
      event.preventDefault();
    }
    this.searchInput = '';
    this.onSearch();
  }

  changePage(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
    }
  }

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

  ngOnInit(): void {
    this.loadLockedAccounts();
  }

  loadLockedAccounts(): void {
    this.isLoading = true;
    this.errorMessage = '';
    this.userService.getLockedAccounts().subscribe({
      next: (data: any[]) => {
        this.lockedAccounts = data;
        this.filteredAccounts = [...data];
        this.isLoading = false;
      },
      error: (err: any) => {
        this.errorMessage = 'Failed to load locked accounts.';
        this.isLoading = false;
        console.error(err);
      }
    });
  }

  unlockUser(userId: number): void {
    this.showConfirm(
      'Unlock Account',
      'Are you sure you want to unlock this account?',
      () => {
        this.userService.unlockAccount(userId).subscribe({
          next: () => {
            this.loadLockedAccounts();
          },
          error: (err: any) => {
            console.error('Failed to unlock user', err);
            this.showError('Failed to unlock user.');
          }
        });
      }
    );
  }
}
