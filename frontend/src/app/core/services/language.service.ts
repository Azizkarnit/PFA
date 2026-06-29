import { Injectable, inject, signal } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';

const LANG_KEY = 'ins_lang';
const SUPPORTED = ['fr', 'en', 'ar'];

@Injectable({ providedIn: 'root' })
export class LanguageService {
  private translate = inject(TranslateService);
  private _currentLang = signal<string>('fr');
  currentLang = this._currentLang.asReadonly();

  constructor() {
    const saved = localStorage.getItem(LANG_KEY);
    const lang = saved && SUPPORTED.includes(saved) ? saved : 'fr';
    this._currentLang.set(lang);
  }

  /** Returns the currently active language */
  get current(): string {
    return this._currentLang();
  }

  /**
   * Call once at app startup (in App constructor or APP_INITIALIZER).
   * Reads the saved language from localStorage and applies it.
   */
  init(): void {
    const saved = localStorage.getItem(LANG_KEY);
    const lang = saved && SUPPORTED.includes(saved) ? saved : 'fr';
    this._currentLang.set(lang);
    this.translate.use(lang);
  }

  /**
   * Change the active language and persist the choice to localStorage.
   */
  use(lang: string): void {
    const lowerLang = lang.toLowerCase();
    if (!SUPPORTED.includes(lowerLang)) return;
    localStorage.setItem(LANG_KEY, lowerLang);
    this._currentLang.set(lowerLang);
    this.translate.use(lowerLang);
  }
}
