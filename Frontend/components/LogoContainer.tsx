import React from 'react';
import { View, Image, StyleSheet, StyleProp, ViewStyle } from 'react-native';

interface LogoContainerProps {
  size?: number;
  style?: StyleProp<ViewStyle>;
}

const LogoContainer: React.FC<LogoContainerProps> = ({ size = 100, style }) => {
  return (
    <View style={[styles.container, style]}>
      <Image
        source={require('../assets/images/logoHD.png')} // Make sure you have a logo image in your assets
        style={[styles.logo, { width: size, height: size }]}
        resizeMode="contain"
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  logo: {
    width: 100,
    height: 100,
  },
});

export { LogoContainer };
