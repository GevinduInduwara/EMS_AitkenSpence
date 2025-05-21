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

    try {
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
        throw new Error('Please fill in all required fields.');
      }

      console.log('Attempting to log in to:', getApiUrl() + '/api/login');
      
      const response = await axios.post(
        getApiUrl() + '/api/login',
        {
          emp_no: employeeNo.trim(),
          password: password
        },
        {
          headers: { 
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          timeout: 15000,  // 15 seconds timeout
          validateStatus: (status) => status < 500  // Handle 4xx responses as well
        }
      );

      console.log('Login response:', response.status, response.data);

      if (response.data && response.data.token) {
        // Store authentication details securely
        await Promise.all([
          SecureStore.setItemAsync('userToken', String(response.data.token)),
          SecureStore.setItemAsync('userRole', String(response.data.role || '')),
          SecureStore.setItemAsync('userRank', String(response.data.rank || '')),
          SecureStore.setItemAsync('userName', String(response.data.name || '')),
          SecureStore.setItemAsync('userEmpNo', String(response.data.emp_no || ''))
        ]);

        // Navigate to home page
        router.replace('/home');
      } else {
        throw new Error('Invalid response from server');
      }

    } catch (error: any) {
      console.error('Login error:', error);
      
      let errorMessage = 'Login failed. Please check your internet connection and try again.';
      let title = 'Login Failed';

      if (error.message === 'Please fill in all required fields.') {
        title = 'Validation Error';
        errorMessage = error.message;
      } else if (error.code === 'ECONNABORTED') {
        errorMessage = 'Request timed out. Please check your internet connection.';
      } else if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        const { status, data } = error.response;
        console.error('Error response:', status, data);
        
        if (status === 401) {
          errorMessage = data.message === 'Invalid credentials' 
            ? 'Incorrect password. Please try again.'
            : 'Invalid employee number or password.';
        } else if (status === 403) {
          errorMessage = 'Access denied. You do not have permission to log in.';
        } else if (status === 404) {
          errorMessage = 'Employee not found. Please check your employee number.';
        } else if (status >= 500) {
          errorMessage = 'Server error. Please try again later.';
        } else {
          errorMessage = data.message || 'An unexpected error occurred. Please try again.';
        }
      } else if (error.request) {
        // The request was made but no response was received
        console.error('No response received:', error.request);
        errorMessage = 'Could not connect to the server. Please check your internet connection.';
      } else if (error.message) {
        // Something happened in setting up the request that triggered an Error
        console.error('Request setup error:', error.message);
        errorMessage = `Error: ${error.message}`;
      }

      Alert.alert(
        title,
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
