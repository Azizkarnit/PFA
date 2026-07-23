import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject, Injector } from '@angular/core';
import { Router } from '@angular/router';
import { catchError } from 'rxjs/operators';
import { throwError } from 'rxjs';
import { AuthService } from '../../core/services/auth.service';
import { TranslateService } from '@ngx-translate/core';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const authService = inject(AuthService);
  const injector = inject(Injector);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401 && req.url.indexOf('/api/v1/auth/logout') === -1) {
        authService.logout();
        router.navigate(['/login']);
      }
      
      let clonedError = error;
      if (error.error && error.error.detail && typeof error.error.detail === 'string') {
        let errorKey = error.error.detail;
        
        // Map common backend hardcoded strings to translation keys
        const errorMapping: {[key: string]: string} = {
            "Email ou mot de passe incorrect.": "ERRORS.INVALID_CREDENTIALS",
            "Votre compte est verrouillé. Veuillez contacter l'administrateur.": "ERRORS.ACCOUNT_LOCKED",
            "Votre compte est désactivé.": "ERRORS.ACCOUNT_DISABLED",
            "Votre compte est verrouillé pour 24 heures en raison d'un grand nombre de tentatives OTP infructueuses.": "ERRORS.OTP_LOCKED",
            "Le mot de passe actuel est incorrect.": "ERRORS.WRONG_CURRENT_PASSWORD",
            "Le nouveau mot de passe ne peut pas être le même que l'actuel.": "ERRORS.SAME_PASSWORD",
            "Code OTP invalide ou expiré.": "ERRORS.INVALID_OTP",
            "Vous avez dépassé la limite de renvoi de code OTP. Veuillez patienter avant de réessayer.": "ERRORS.OTP_RATE_LIMIT",
            "Un code OTP valide a déjà été envoyé récemment. Veuillez vérifier votre boîte mail.": "ERRORS.OTP_ALREADY_SENT",
            "Email non trouvé.": "ERRORS.EMAIL_NOT_FOUND",
            "Lien invalide ou expiré.": "ERRORS.INVALID_LINK",
            "Le nouveau mot de passe est trop faible.": "ERRORS.WEAK_PASSWORD"
        };

        // Match start of string for rate limits which include dynamic numbers
        if (errorKey.startsWith("Trop de tentatives")) {
            errorKey = "ERRORS.RATE_LIMIT";
        } else if (errorMapping[errorKey]) {
            errorKey = errorMapping[errorKey];
        }

        const translate = injector.get(TranslateService);
        const translatedDetail = translate.instant(errorKey);
        if (translatedDetail !== error.error.detail) {
            clonedError = new HttpErrorResponse({
                error: { ...error.error, detail: translatedDetail },
                headers: error.headers,
                status: error.status,
                statusText: error.statusText,
                url: error.url || undefined
            });
        }
      }
      
      return throwError(() => clonedError);
    })
  );
};
