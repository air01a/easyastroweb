// i18n.ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Import des traductions
import en from './locales/en.json';
import fr from './locales/fr.json';



// Langues supportées
const supportedLanguages = ['en', 'fr'];

// Configuration du détecteur de langue personnalisé
const customLanguageDetector = {
  name: 'customDetector',
  lookup: (): string | undefined => {
    // 1. Vérifier d'abord le store
    const storeLanguage = null;
    if (storeLanguage && supportedLanguages.includes(storeLanguage)) {
      return storeLanguage;
    }
    
    // 2. Si pas de langue fixée dans le store, détecter depuis le navigateur
    const browserLanguage = navigator.language.split('-')[0]; // 'fr-FR' -> 'fr'
    if (supportedLanguages.includes(browserLanguage)) {
      return browserLanguage;
    }
    
    // 3. Fallback vers l'anglais
    return 'en';
  },
  cacheUserLanguage: () => {
    // On ne cache pas car on gère ça via le store
  }
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      fr: { translation: fr },
    },
    fallbackLng: 'en',
    supportedLngs: supportedLanguages,
    
    // Configuration du détecteur
    detection: {
      order: ['customDetector'], // Utilise notre détecteur personnalisé
      caches: [], // Pas de cache automatique
    },
    
    interpolation: {
      escapeValue: false, // React échappe déjà
    },
    
    // Désactiver les warnings pour les clés manquantes en dev
    debug: process.env.NODE_ENV === 'development',
  });

// Ajouter le détecteur personnalisé
i18n.services.languageDetector.addDetector(customLanguageDetector);

export default i18n;