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
    // Navigate to call attendance employee selection page
    router.push('./call-attendance-select');
  };

  const handleCheckAttendance = () => {
    // Navigate to check attendance employee selection page
    router.push('./check-attendance-select');
  };

  const handleAdminRegistration = () => {
    router.push('./admin-registration');
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
    backgroundColor: '#f5f5f5',
    paddingHorizontal: 20,
  },
  logoContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: -50,
  },
  logo: {
    width: width * 0.5,
    height: height * 0.2,
  },
  languageButtonContainer: {
    position: 'absolute',
    top: 40,
    right: 20,
    zIndex: 100,
  },
  titleContainer: {
    marginBottom: 40,
  },
  pageTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#2c3e50',
    textAlign: 'center',
    marginBottom: 10,
  },
  cardContainer: {
    flex: 1,
    justifyContent: 'center',
    width: '100%',
  },
  card: {
    backgroundColor: '#005A9C',
    padding: 20,
    borderRadius: 12,
    width: '100%',
    alignItems: 'center',
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.2,
    shadowRadius: 4.65,
    elevation: 8,
  },
  cardTitle: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
  },
});

export default HomePage;
