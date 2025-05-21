import React from 'react';
import { View, Image, TouchableOpacity, StyleSheet, Dimensions } from 'react-native';
import { useRouter } from 'expo-router';

import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';
import LanguageButton from '@/components/LanguageButton';
import { useLanguage } from '@/context/LanguageContext';

const { width, height } = Dimensions.get('window');

const HomePage: React.FC = () => {
  const router = useRouter();
  const { t } = useLanguage();

  const handleCallAttendance = () => {
    router.push('./selectemployee');
  };
  
  return (
    <ThemedView style={styles.container}>
      <View style={styles.logoContainer}>
        <Image 
          source={require('@/assets/images/logoHD.png')} 
          style={styles.logo} 
          resizeMode="contain" 
        />
      </View>
      
      <View style={styles.languageButtonContainer}>
        <LanguageButton />
      </View>

      <View style={styles.cardContainer}>
        <TouchableOpacity 
          style={styles.card} 
          onPress={handleCallAttendance}
        >
          <ThemedText type="defaultSemiBold" style={styles.cardTitle}>
            {t('markAttendance')}
          </ThemedText>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.card} 
          onPress={() => router.push('/(tabs)/userregistration')}
        >
          <ThemedText type="defaultSemiBold" style={styles.cardTitle}>
            {t('userRegistration')}
          </ThemedText>
        </TouchableOpacity>
      </View>
    </ThemedView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#e8f0fe', // Soft light blue background
    paddingHorizontal: 20,
    paddingVertical: 30,
  },
  logoContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: -40,
  },
  logo: {
    width: width * 0.55,
    height: height * 0.22,
  },
  languageButtonContainer: {
    position: 'absolute',
    top: 50,
    right: 20,
    zIndex: 100,
  },
  cardContainer: {
    flex: 1.3,
    justifyContent: 'center',
    width: '100%',
  },
  card: {
    backgroundColor: '#0078d4', // Brighter blue
    paddingVertical: 22,
    paddingHorizontal: 25,
    borderRadius: 16,
    width: '100%',
    alignItems: 'center',
    marginBottom: 24,
    // Soft shadow for iOS
    shadowColor: '#1a73e8',
    shadowOffset: {
      width: 0,
      height: 6,
    },
    shadowOpacity: 0.25,
    shadowRadius: 10,
    // Elevation for Android
    elevation: 10,
  },
  cardTitle: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '700',
    textAlign: 'center',
    letterSpacing: 0.8,
  },
});

export default HomePage;
