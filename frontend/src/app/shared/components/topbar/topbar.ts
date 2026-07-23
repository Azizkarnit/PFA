import { Component, EventEmitter, Input, Output, inject, HostListener, OnInit } from '@angular/core';
import { LanguageService } from '../../../core/services/language.service';
import { AuthService } from '../../../core/services/auth.service';

import { TranslatePipe } from '@ngx-translate/core';
import { CommonModule } from '@angular/common';
import { NotificationService, AppNotification } from '../../../core/services/notification.service';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';

@Component({
  selector: 'app-topbar',
  standalone: true,
  imports: [CommonModule, TranslatePipe, RouterLink, RouterLinkActive],
  templateUrl: './topbar.html',
  styleUrl: './topbar.css',
})
export class Topbar implements OnInit {
  @Input() title: string = 'Dashboard';
  @Input() isPortalMode: boolean = false;
  @Output() menuToggled = new EventEmitter<void>();
  private langService = inject(LanguageService);
  private authService = inject(AuthService);
  private router = inject(Router);
  public notifService = inject(NotificationService);
  
  isLangMenuOpen = false;
  isNotifMenuOpen = false;

  ngOnInit() {
    this.notifService.init();
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }

  onNotificationClick(event: Event, notif: AppNotification) {
    event.preventDefault();
    event.stopPropagation();
    
    if (!notif.is_read) {
      this.notifService.markAsRead(notif.id);
    }
    
    this.isNotifMenuOpen = false;
    
    if (notif.action_url) {
      this.router.navigateByUrl(notif.action_url);
    }
  }

  toggleLangMenu(event: Event) {
    event.stopPropagation();
    this.isLangMenuOpen = !this.isLangMenuOpen;
    this.isNotifMenuOpen = false;
  }

  toggleNotifMenu(event: Event) {
    event.stopPropagation();
    this.isNotifMenuOpen = !this.isNotifMenuOpen;
    this.isLangMenuOpen = false;
  }

  @HostListener('document:click', ['$event'])
  closeMenus(event: Event) {
    this.isLangMenuOpen = false;
    this.isNotifMenuOpen = false;
  }

  toggleMobileMenu() {
    this.menuToggled.emit();
  }

  setLanguage(lang: string, event: Event) {
    event.preventDefault();
    this.langService.use(lang);
    if (this.authService.isLoggedIn()) {
      this.authService.updatePreferredLanguage(lang).subscribe();
    }
    this.isLangMenuOpen = false;
  }

  get currentUser(): any {
    return this.authService.getCurrentUser();
  }

  get displayName(): string {
    const u = this.currentUser;
    if (!u) return '';
    if (u.first_name || u.last_name) {
      return `${u.first_name || ''} ${u.last_name || ''}`.trim();
    }
    return u.email || '';
  }

  get currentLang(): string {
    return this.langService.currentLang();
  }

  get platformName(): string {
    const lang = this.langService.currentLang();
    switch (lang) {
      case 'fr': return 'STATISTIQUES TUNISIE';
      case 'ar': return 'إحصائيات تونس';
      case 'en':
      default: return 'TUNISIA STATISTICS';
    }
  }
}
