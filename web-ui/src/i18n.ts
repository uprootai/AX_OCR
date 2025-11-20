import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import ko from './locales/ko.json';
import en from './locales/en.json';

// 브라우저 언어 감지 또는 localStorage에서 저장된 언어 불러오기
const savedLanguage = localStorage.getItem('language') || 'ko';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      ko: { translation: ko },
      en: { translation: en },
    },
    lng: savedLanguage,
    fallbackLng: 'ko',
    interpolation: {
      escapeValue: false,
    },
  });

// 언어 변경 시 localStorage에 저장
i18n.on('languageChanged', (lng) => {
  localStorage.setItem('language', lng);
});

export default i18n;
