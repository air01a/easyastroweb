// hooks/useLanguage.ts
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';

type SupportedLanguage = 'en' | 'fr' ;

const supportedLanguages: SupportedLanguage[] = ['en', 'fr'];

const isLanguageSupported = (lang: string): lang is SupportedLanguage => {
  return supportedLanguages.includes(lang as SupportedLanguage);
};

export const useLanguage = () => {
  const { i18n } = useTranslation();
  
  // Récupérer la langue depuis le store
  const storeLanguage = null;
  
  // Fonction pour changer la langue
  const changeLanguage = (language: string | null): void => {
    if (language === null) {
      // Mode auto-detect : détecter depuis le navigateur
      const browserLang = navigator.language.split('-')[0];
      const detectedLang = isLanguageSupported(browserLang) ? browserLang : 'en';
      
      i18n.changeLanguage(detectedLang);
    } else {
      // Langue fixée manuellement
      if (isLanguageSupported(language)) {
        i18n.changeLanguage(language);
      } else {
        console.warn(`Langue non supportée: ${language}`);
      }
    }
  };
  
  // Écouter les changements de langue dans le store
  useEffect(() => {
    if (storeLanguage === null) {
      // Mode auto-detect
      const browserLang = navigator.language.split('-')[0];
      const detectedLang = isLanguageSupported(browserLang) ? browserLang : 'en';
      
      if (i18n.language !== detectedLang) {
        i18n.changeLanguage(detectedLang);
      }
    } else {
      // Langue fixée
      if (i18n.language !== storeLanguage) {
        i18n.changeLanguage(storeLanguage);
      }
    }
  }, [storeLanguage, i18n]);
  
  return {
    currentLanguage: i18n.language as SupportedLanguage,
    isAutoDetect: storeLanguage === null,
    changeLanguage,
    supportedLanguages,
  };
};