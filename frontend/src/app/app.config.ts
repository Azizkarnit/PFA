import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideAnimations } from '@angular/platform-browser/animations';
import { provideRouter } from '@angular/router';
import { HttpClient, provideHttpClient, withInterceptorsFromDi, withInterceptors } from '@angular/common/http';
import { provideTranslateService } from '@ngx-translate/core';
import { provideTranslateHttpLoader } from '@ngx-translate/http-loader';
import { routes } from './app.routes';

import { jwtInterceptor } from './auth/interceptors/jwt-interceptor';
import { errorInterceptor } from './auth/interceptors/error-interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideAnimations(),
    provideRouter(routes),
    provideHttpClient(withInterceptors([jwtInterceptor, errorInterceptor]), withInterceptorsFromDi()),
    provideTranslateService({
      lang: 'fr',
      fallbackLang: 'fr'
    }),
    provideTranslateHttpLoader({
      prefix: '/i18n/',
      suffix: '.json'
    })
  ]
};
