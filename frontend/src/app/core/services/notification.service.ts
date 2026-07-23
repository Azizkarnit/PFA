import { Injectable, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, Subscription, timer } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AuthService } from './auth.service';
import { MatSnackBar } from '@angular/material/snack-bar';

export interface AppNotification {
  id: number;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  action_url?: string;
  created_at: string;
}

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private ws: WebSocket | null = null;
  private reconnectSubscription: Subscription | null = null;
  
  private notificationsSubject = new BehaviorSubject<AppNotification[]>([]);
  public notifications$ = this.notificationsSubject.asObservable();
  
  private unreadCountSubject = new BehaviorSubject<number>(0);
  public unreadCount$ = this.unreadCountSubject.asObservable();

  constructor(
    private http: HttpClient,
    private authService: AuthService,
    private snackBar: MatSnackBar,
    @Inject(PLATFORM_ID) private platformId: Object
  ) {
  }

  init() {
    if (isPlatformBrowser(this.platformId)) {
      const user = this.authService.getCurrentUser();
      if (user) {
        this.fetchInitialNotifications();
        this.connectWebSocket();
      }
    }
  }

  private fetchInitialNotifications() {
    this.http.get<AppNotification[]>(`${environment.apiUrl}/notifications/`).subscribe({
      next: (notifications) => {
        this.notificationsSubject.next(notifications);
        this.updateUnreadCount(notifications);
      },
      error: (err) => console.error('Failed to fetch notifications', err)
    });
  }

  private updateUnreadCount(notifications: AppNotification[]) {
    const unread = notifications.filter(n => !n.is_read).length;
    this.unreadCountSubject.next(unread);
  }

  private connectWebSocket() {
    this.disconnectWebSocket();

    const token = this.authService.getToken();
    if (!token) return;

    // Convert http(s) URL to ws(s)
    let wsUrl = environment.apiUrl.replace('http', 'ws');
    // Construct full ws URL
    const fullWsUrl = `${wsUrl}/notifications/ws?token=${token}`;

    this.ws = new WebSocket(fullWsUrl);

    this.ws.onopen = () => {
      console.log('Notification WebSocket connected');
      if (this.reconnectSubscription) {
        this.reconnectSubscription.unsubscribe();
        this.reconnectSubscription = null;
      }
    };

    this.ws.onmessage = (event) => {
      if (event.data === 'pong') return;
      try {
        const newNotif: AppNotification = JSON.parse(event.data);
        
        // Show Toast
        this.snackBar.open(`${newNotif.title}: ${newNotif.message}`, 'Close', {
          duration: 5000,
          horizontalPosition: 'end',
          verticalPosition: 'bottom',
          panelClass: `toast-${newNotif.type.toLowerCase()}`
        });

        // Add to list
        const currentList = this.notificationsSubject.value;
        const updatedList = [newNotif, ...currentList].slice(0, 50); // Keep max 50
        this.notificationsSubject.next(updatedList);
        this.updateUnreadCount(updatedList);
      } catch (e) {
        console.error('Failed to parse WebSocket message', e);
      }
    };

    this.ws.onclose = (event) => {
      console.log('Notification WebSocket closed', event);
      if (this.authService.getCurrentUser()) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket Error', error);
      // onclose will be called after this
    };
  }

  private disconnectWebSocket() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    if (this.reconnectSubscription) {
      this.reconnectSubscription.unsubscribe();
      this.reconnectSubscription = null;
    }
  }

  private scheduleReconnect() {
    if (!this.reconnectSubscription) {
      console.log('Scheduling WebSocket reconnect in 5 seconds...');
      this.reconnectSubscription = timer(5000).subscribe(() => {
        this.connectWebSocket();
      });
    }
  }

  public markAsRead(id: number) {
    this.http.put(`${environment.apiUrl}/notifications/${id}/read`, {}).subscribe({
      next: () => {
        const currentList = this.notificationsSubject.value.map(n => 
          n.id === id ? { ...n, is_read: true } : n
        );
        this.notificationsSubject.next(currentList);
        this.updateUnreadCount(currentList);
      }
    });
  }

  public markAllAsRead() {
    this.http.put(`${environment.apiUrl}/notifications/read-all`, {}).subscribe({
      next: () => {
        const currentList = this.notificationsSubject.value.map(n => ({ ...n, is_read: true }));
        this.notificationsSubject.next(currentList);
        this.updateUnreadCount(currentList);
      }
    });
  }
}
