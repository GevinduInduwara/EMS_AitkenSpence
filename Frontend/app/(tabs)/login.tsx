import React, { useState } from 'react';
import { View, Image, TextInput, TouchableOpacity, StyleSheet, Dimensions, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import axios from 'axios';
import * as SecureStore from 'expo-secure-store';
import { getApiUrl } from '../../config/api';

import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';

const { width, height } = Dimensions.get('window');

const LoginPage: React.FC = () => {
  const router = useRouter();
  const [employeeNo, setEmployeeNo] = useState('');
  const [password, setPassword] = useState('');
  const [employeeNoError, setEmployeeNoError] = useState(false);
  const [passwordError, setPasswordError] = useState(false);

  const handleLogin = async () => {
    // Reset previous errors
    setEmployeeNoError(false);
    setPasswordError(false);

    // Validate inputs
    let isValid = true;

    if (employeeNo.trim() === '') {
      setEmployeeNoError(true);
      isValid = false;
    }
    if (password.trim() === '') {
      setPasswordError(true);
      isValid = false;
    }

    if (!isValid) {
      Alert.alert(
        'Validation Error', 
        'Please fill in all required fields.',
        [{ text: 'OK' }]
      );
      return;
    }

    try {
      const response = await axios.post(getApiUrl() + '/api/login', {
        emp_no: employeeNo.trim(),
        password: password
      }, {  
        headers: { 'Content-Type': 'application/json' },
        timeout: 10000,  // Increased timeout (10 seconds)
      });

      // Store authentication details securely
      await SecureStore.setItemAsync('userToken', String(response.data.token));
      await SecureStore.setItemAsync('userRole', String(response.data.role));
      await SecureStore.setItemAsync('userRank', String(response.data.rank));
      await SecureStore.setItemAsync('userName', String(response.data.name));
      await SecureStore.setItemAsync('userEmpNo', String(response.data.emp_no));

      // Navigate to home page
      router.push('/home');

    } catch (error: unknown) {
      console.error('Login error:', error);
      
      let errorMessage = 'Login failed. Please check your internet connection and try again.';

      if (error instanceof Error) {
        errorMessage = error.message || errorMessage;
      } else if (typeof error === 'object' && error !== null && 'response' in error) {
        const axiosError = error as { response: { data: { message: string } } };
        const responseMessage = axiosError.response?.data.message;
        
        switch (responseMessage) {
          case 'Employee not found or not authorized to log in':
            errorMessage = 'Access denied. Only OIC rank employees can log in to the system.';
            break;
          case 'Invalid credentials':
            errorMessage = 'Incorrect password. Please try again.';
            break;
          default:
            errorMessage = 'Login failed. Please check your credentials and try again.';
        }
      }

      Alert.alert(
        'Login Failed',
        errorMessage,
        [{ text: 'OK' }]
      );
    }
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

      <View style={styles.inputContainer}>
        <TextInput
          style={[
            styles.input, 
            employeeNoError && styles.inputError
          ]}
          placeholder="Employee Number"
          value={employeeNo}
          onChangeText={(text) => {
            setEmployeeNo(text);
            setEmployeeNoError(false);
          }}
          placeholderTextColor="#666"
        />
        {employeeNoError && (
          <ThemedText style={styles.errorText}>
            Employee Number is required
          </ThemedText>
        )}

        <TextInput
          style={[
            styles.input, 
            passwordError && styles.inputError
          ]}
          placeholder="Password"
          value={password}
          onChangeText={(text) => {
            setPassword(text);
            setPasswordError(false);
          }}
          secureTextEntry={true}
          placeholderTextColor="#666"
        />
        {passwordError && (
          <ThemedText style={styles.errorText}>
            Password is required
          </ThemedText>
        )}

        <TouchableOpacity 
          style={styles.button} 
          onPress={handleLogin}
        >
          <ThemedText type="defaultSemiBold" style={styles.buttonText}>
            Login
          </ThemedText>
        </TouchableOpacity>
      </View>
    </ThemedView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: 'white',
  },
  logoContainer: {
    marginBottom: 200,  // Adjusted margin to fit the content better
    width: width, 
    height: height * 0.2, 
    alignItems: 'center',
    justifyContent: 'center',
  },
  logo: {
    width: '100%', 
    height: '100%',
  },
  inputContainer: {
    width: width * 0.8, 
    alignSelf: 'center', 
    position: 'absolute', 
    top: height * 0.45,  // Adjusted to fit the screen better
  },
  input: {
    width: '100%',
    height: 50,
    borderWidth: 1,
    borderColor: '#005A9C',
    borderRadius: 10,
    marginBottom: 10,
    paddingHorizontal: 15,
    color: '#000', 
    fontSize: 16, 
  },
  inputError: {
    borderColor: 'red',
  },
  errorText: {
    color: 'red',
    fontSize: 12,
    marginBottom: 10,
  },
  button: {
    backgroundColor: '#005A9C',
    paddingVertical: 15,
    borderRadius: 10,
    alignItems: 'center',
    marginTop: 10,
  },
  buttonText: {
    color: 'white',
  },
});

export default LoginPage;
