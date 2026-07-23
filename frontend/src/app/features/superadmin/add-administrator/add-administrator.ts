import { TranslatePipe } from '@ngx-translate/core';
import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { UserService } from '../../../core/services/user.service';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-add-administrator',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, TranslatePipe],
  templateUrl: './add-administrator.html',
  styleUrls: ['./add-administrator.css']
})
export class AddAdministrator implements OnInit {
  private fb = inject(FormBuilder);
  private userService = inject(UserService);
  private router = inject(Router);
  private authService = inject(AuthService);

  adminForm!: FormGroup;
  roles: { id: number; code: string; name: string; description: string }[] = [];
  isLoading = false;
  errorMessage = '';
  successMessage = '';

  ngOnInit(): void {
    this.adminForm = this.fb.group({
      first_name: ['', [Validators.required, Validators.minLength(2)]],
      last_name: ['', [Validators.required, Validators.minLength(2)]],
      email: ['', [Validators.required, Validators.email]],
      phone: ['', [Validators.required]],
      role_id: ['', [Validators.required]]
    });

    this.fetchRoles();
  }

  fetchRoles(): void {
    const currentUser = this.authService.getCurrentUser();
    
    this.userService.getRoles().subscribe({
      next: (res: any[]) => {
        // Since this is adding an "administrator", only show admin roles
        this.roles = res.filter(r => r.code !== 'COMPANY_CONTACT');
        
        // Prevent Account Managers from seeing/adding System Administrators
        if (currentUser?.role === 'ACCOUNT_MANAGER') {
          this.roles = this.roles.filter(r => r.code !== 'SYSTEM_ADMINISTRATOR');
        }
      },
      error: (err: any) => {
        console.error('Failed to fetch roles', err);
        this.errorMessage = 'Could not load roles. Please try again.';
      }
    });
  }

  onSubmit(): void {
    if (this.adminForm.invalid) {
      this.adminForm.markAllAsTouched();
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    this.successMessage = '';

    const payload = { ...this.adminForm.value };
    payload.role_id = Number(payload.role_id);

    this.userService.createUser(payload).subscribe({
      next: () => {
        this.isLoading = false;
        this.successMessage = 'Administrator added successfully! They will receive an email shortly to set their password.';
        setTimeout(() => {
          this.router.navigate(['/admin/administrators']);
        }, 2000);
      },
      error: (err: any) => {
        this.isLoading = false;
        this.errorMessage = err.error?.detail || 'Failed to add administrator. Please check your inputs.';
        console.error('Error adding admin:', err);
      }
    });
  }

  onCancel(): void {
    this.router.navigate(['/admin/administrators']);
  }
}
