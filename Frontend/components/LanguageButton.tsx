import React from 'react';
import { TouchableOpacity, StyleSheet } from 'react-native';
import { useLanguage } from '../context/LanguageContext';
import { ThemedText } from './ThemedText';

interface LanguageButtonProps {
  onPress?: () => void;
  style?: any;
}

export default function LanguageButton({ onPress, style }: LanguageButtonProps) {
  const { language, setLanguage } = useLanguage();

  const handlePress = () => {
    // Toggle between languages
    setLanguage(language === 'en' ? 'si' : 'en');
    onPress?.();
  };

  return (
    <TouchableOpacity
      onPress={handlePress}
      style={[styles.button, style]}
    >
      <ThemedText type="default">
        {language === 'en' ? 'EN' : 'SI'}
      </ThemedText>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    padding: 8,
    borderRadius: 8,
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
  },
});
