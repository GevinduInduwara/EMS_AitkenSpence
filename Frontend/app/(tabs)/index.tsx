import React from 'react';
import { View, Image, TouchableOpacity, StyleSheet, Dimensions, SafeAreaView } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter, useFocusEffect } from 'expo-router';
import { BlurView } from 'expo-blur';
import Animated, { 
  useSharedValue, 
  useAnimatedStyle, 
  withTiming, 
  FadeIn,
  FadeOut,
  SlideInDown,
  SlideOutDown
} from 'react-native-reanimated';

import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';
import LanguageButton from '@/components/LanguageButton';
import { useLanguage } from '@/context/LanguageContext';

const { width, height } = Dimensions.get('window');

const WelcomePage: React.FC = () => {
  const router = useRouter();
  const { t } = useLanguage();

  // Shared values for animations
  const characterTranslateY = useSharedValue(height);
  const titleButtonContainerOpacity = useSharedValue(0);

  // Animated styles
  const characterAnimatedStyle = useAnimatedStyle(() => ({
    transform: [{ translateY: withTiming(characterTranslateY.value, { duration: 700 }) }]
  }));

  const titleButtonContainerAnimatedStyle = useAnimatedStyle(() => ({
    opacity: withTiming(titleButtonContainerOpacity.value, { duration: 500 })
  }));

  // Reset animations when page becomes focused
  useFocusEffect(
    React.useCallback(() => {
      // Entrance animations
      characterTranslateY.value = 0;
      titleButtonContainerOpacity.value = 1;
    }, [])
  );

  const handleGetStarted = () => {
    // Exit animations
    characterTranslateY.value = height;
    titleButtonContainerOpacity.value = 0;

    // Navigate after animation
    setTimeout(() => {
      router.push('/login');
    }, 400);
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.logoContainer}>
        <Image 
          source={require('@/assets/images/logoHD.png')} 
          style={styles.logo} 
          resizeMode="contain" 
        />
        <LanguageButton />
      </View>

      <Animated.View 
        style={[styles.characterContainer, characterAnimatedStyle]}
        entering={SlideInDown.duration(700)}
        exiting={SlideOutDown.duration(400)}
      >
        <Image
          source={require('@/assets/images/Officer.png')}
          style={styles.characterImage}
        />
      </Animated.View>

      <Animated.View 
        style={[styles.titleButtonContainer, titleButtonContainerAnimatedStyle]}
        entering={FadeIn.duration(500)}
        exiting={FadeOut.duration(300)}
      >
        <BlurView intensity={20} style={styles.blurContainer}>
          <View style={styles.titleButtonInnerContainer}>
            <View style={styles.textContainer}>
              <ThemedText type="title" style={styles.titleText}>
                {t('welcomeTitle')}
              </ThemedText>
              <ThemedText type="subtitle" style={styles.subtitleText}>
                {t('securityManagementSystem')}
              </ThemedText>
            </View>
            
            <TouchableOpacity 
              style={styles.button} 
              onPress={handleGetStarted}
            >
              <LinearGradient 
                colors={['#0077BE', '#005A9C']}
                start={{x: 0, y: 0}}
                end={{x: 1, y: 0}}
                style={styles.buttonGradient}
              >
                <ThemedText type="defaultSemiBold" style={styles.buttonText}>
                  {t('getStarted')}
                </ThemedText>
              </LinearGradient>
            </TouchableOpacity>
          </View>
        </BlurView>
      </Animated.View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 40,
    backgroundColor: 'white',
  },
  logoContainer: {
    width: width, 
    height: height * 0.25, 
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  logo: {
    width: '80%', 
    height: '100%',
    resizeMode: 'contain',
  },
  characterContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  characterImage: {
    width: width * 0.8, 
    height: height * 0.4, 
    resizeMode: 'contain',
  },
  titleButtonContainer: {
    width: '100%',
    alignItems: 'center',
    marginBottom: 20,
  },
  blurContainer: {
    width: '100%',
    borderRadius: 20,
    overflow: 'hidden',
  },
  titleButtonInnerContainer: {
    backgroundColor: 'rgb(255, 255, 255)',
    borderRadius: 20,
    padding: 50,
    alignItems: 'center',
    width: '100%',
  },
  textContainer: {
    marginBottom: 20,
    alignItems: 'center',
  },
  titleText: {
    fontSize: 26,
    fontWeight: 'bold',
    color: '#005A9C',
    marginBottom: 10,
    textAlign: 'center',
  },
  subtitleText: {
    fontSize: 16,
    color: '#333',
    marginBottom: 10,
    textAlign: 'center',
  },
  button: {
    width: '100%',
    borderRadius: 10,
    overflow: 'hidden',
  },
  buttonGradient: {
    paddingVertical: 15,
    paddingHorizontal: 30,
    borderRadius: 10,
    alignItems: 'center',
    width: '100%',
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default WelcomePage;