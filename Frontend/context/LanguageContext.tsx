import React, { createContext, useContext, useState, useEffect } from 'react';

interface LanguageContextType {
  language: string;
  setLanguage: (lang: string) => void;
  t: (key: keyof TranslationKeys) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

interface TranslationKeys {
  welcome: string;
  welcomeTitle: string;
  securityManagementSystem: string;
  getStarted: string;
  markAttendance: string;
  checkAttendance: string;
  userRegistration: string;
}

type LanguageCode = 'en' | 'si';

const translations: Record<LanguageCode, TranslationKeys> = {
  en: {
    welcome: 'Welcome',
    welcomeTitle: 'Welcome to',
    securityManagementSystem: 'Security Management System',
    getStarted: 'Get Started',
    markAttendance: 'Mark Attendance',
    checkAttendance: 'Check Attendance',
    userRegistration: 'User Registration'
  },
  si: {
    welcome: 'සාදරයෙන් සාදරයෙන්',
    welcomeTitle: 'ආයේ පිළිගැනීමට',
    markAttendance: 'සිටින් පිළිගැනීම',
    checkAttendance: 'සිටින් පරීක්ෂා කරන්න',
    userRegistration: 'යුසර් ලියාපදිංචි කිරීම',
    securityManagementSystem: 'රක්ෂාව කාර්ය පද්ධතිය',
    getStarted: 'ආරම්භ කරන්න',
    // Add more Sinhala translations here
  }
};

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguage] = useState<string>('en');

  // Translation function
  const t = (key: keyof TranslationKeys): string => {
    return translations[language as LanguageCode]?.[key] || key;
  };

  useEffect(() => {
    // Load language from storage or defaults
    const loadLanguage = async () => {
      try {
        // You can implement AsyncStorage or another storage solution here
        // const savedLanguage = await AsyncStorage.getItem('language');
        // setLanguage(savedLanguage || 'en');
      } catch (error) {
        console.error('Error loading language:', error);
      }
    };

    loadLanguage();
  }, []);

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
