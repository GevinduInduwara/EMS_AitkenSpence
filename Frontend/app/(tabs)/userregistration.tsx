import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import { TextInput, Button } from 'react-native-paper';
import DropDownPicker from 'react-native-dropdown-picker';
import { useForm, Controller, SubmitHandler } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { useRouter } from 'expo-router';
import { ThemedText } from '@/components/ThemedText';

// Styles for error text
const errorStyles = {
  errorText: {
    color: '#ff0000',
    fontSize: 12,
    marginBottom: 8,
  }
};
import { ThemedView } from '../../components/ThemedView';
import axios from 'axios';

interface DropdownItem {
  label: string;
  value: string;
}

interface AdminFormData {
  emp_no: string;
  id: string;
  name: string;
  rank: string;
  role: string;
  company_name: string;
  security_firm: string;
  password: string;
  confirmPassword: string;
  address: string;
  tel: string;
  nic: string;
}



interface AdminFormData {
  emp_no: string;
  id: string;
  name: string;
  rank: string;
  role: string;
  company_name: string;
  security_firm: string;
  password: string;
  confirmPassword: string;
  address: string;
  tel: string;
  nic: string;
}

const rankOptions: DropdownItem[] = [
  { label: 'OIC', value: 'OIC' },
  { label: 'JSO', value: 'JSO' },
  { label: 'LSO', value: 'LSO' }
];

const roleOptions: DropdownItem[] = [
  { label: 'Admin', value: 'admin' },
  { label: 'Acting Admin', value: 'acting_admin' },
  { label: 'User', value: 'user' }
];

const companyOptions: DropdownItem[] = [
  { label: 'ASPDL', value: 'ASPDL' },
];

const securityFirmOptions: DropdownItem[] = [
  { label: 'Oracle', value: 'oracle' },
  { label: 'Shadow Watch', value: 'shadow_watch' },
];

const adminSchema = yup.object().shape({
  emp_no: yup.string().required('Employee number is required'),
  id: yup.string().required('ID is required'),
  name: yup.string().required('Name is required'),
  rank: yup.string().required('Rank is required'),
  role: yup.string().required('Role is required'),
  company_name: yup.string().required('Company is required'),
  security_firm: yup.string().required('Security firm is required'),
  password: yup.string().required('Password is required'),
  confirmPassword: yup.string()
    .required('Confirm password is required')
    .oneOf([yup.ref('password')], 'Passwords must match'),
  address: yup.string().required('Address is required'),
  tel: yup.string()
    .required('Phone number is required')
    .matches(/^[0-9]+$/, 'Phone number must contain only numbers'),
  nic: yup.string().required('NIC is required')
});

const UserRegistration = () => {
  const router = useRouter();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [companyOpen, setCompanyOpen] = useState(false);
  const [securityFirmOpen, setSecurityFirmOpen] = useState(false);
  const [rankOpen, setRankOpen] = useState(false);
  const [roleOpen, setRoleOpen] = useState(false);
  const [currentRank, setCurrentRank] = useState<string | null>(null);

  const { control, handleSubmit, formState: { errors }, reset, setValue } = useForm<AdminFormData>({
    resolver: yupResolver(adminSchema),
  });

  const closeAllDropdowns = () => {
    setCompanyOpen(false);
    setSecurityFirmOpen(false);
    setRankOpen(false);
    setRoleOpen(false);
  };

  const onSubmit: SubmitHandler<AdminFormData> = async (data) => {
    try {
      setLoading(true);
      setError('');

      const response = await axios.post('http://172.20.10.3:5001/api/employee/add', data, {
        headers: { 'Content-Type': 'application/json' },
        timeout: 10000,  // Increased timeout (10 seconds)
      });

      if (response.status === 201) {
        Alert.alert('Success', 'Registration successful');
        reset();
        router.push('/login');
      } else {
        setError(response.data?.message || 'Registration failed');
      }
    } catch (err: any) {
      if (axios.isAxiosError(err)) {
        if (err.code === 'ECONNABORTED') {
          setError('The request timed out. Please try again.');
        } else {
          setError(err.response?.data?.message || 'Registration failed');
        }
      } else {
        setError('An unexpected error occurred');
      }
    } finally {
      setLoading(false);
    }
  };

  const renderInput = (name: keyof AdminFormData, label: string, secureTextEntry = false, keyboardType?: 'default' | 'numeric') => (
    <Controller
      control={control}
      name={name}
      render={({ field: { onChange, onBlur, value }, fieldState: { error } }) => (
        <View>
          <TextInput
            label={label}
            value={value}
            onBlur={onBlur}
            onChangeText={onChange}
            style={styles.input}
            secureTextEntry={secureTextEntry}
            keyboardType={keyboardType}
            theme={{ colors: { primary: '#000', onSurface: '#000', placeholder: '#000', background: '#fff' } }}
          />
          {error && <ThemedText style={errorStyles.errorText}>{error?.message}</ThemedText>}
        </View>
      )}
    />
  );

  return (
    <ThemedView style={styles.container}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.keyboardAvoidingView}>
        <ScrollView style={styles.formScroll}>
          <View style={styles.form}>
            <ThemedText style={styles.pageTitle}>User Registration</ThemedText>

            {error ? <ThemedText style={errorStyles.errorText}>{error}</ThemedText> : null}

            {/* Basic Info */}
            <View style={styles.section}>
              <ThemedText style={styles.sectionTitle}>Basic Information</ThemedText>
              {renderInput('emp_no', 'Employee Number')}
              {renderInput('id', 'ID Number')}
              {renderInput('name', 'Full Name')}
            </View>

            {/* Credentials */}
            <View style={styles.section}>
              <ThemedText style={styles.sectionTitle}>Credentials</ThemedText>
              {renderInput('password', 'Password', true)}
              {renderInput('confirmPassword', 'Confirm Password', true)}
            </View>

            {/* Company Info */}
            <View style={styles.section}>
              <ThemedText style={styles.sectionTitle}>Company Information</ThemedText>

              <Controller
                control={control}
                name="company_name"
                render={({ field: { value, onChange } }) => (
                  <DropDownPicker
                    open={companyOpen}
                    value={value}
                    items={companyOptions}
                    setOpen={(open) => {
                      closeAllDropdowns();
                      setCompanyOpen(open);
                    }}
                    setValue={(callbackOrValue) => {
                      const selected = typeof callbackOrValue === 'function' ? callbackOrValue(value) : callbackOrValue;
                      onChange(selected);
                    }}
                    placeholder="Select Company"
                    style={styles.dropDown}
                    dropDownContainerStyle={styles.dropDownContainer}
                    listMode="SCROLLVIEW"
                    zIndex={4000}
                    zIndexInverse={1000}
                  />
                )}
              />

              <Controller
                control={control}
                name="security_firm"
                render={({ field: { value, onChange } }) => (
                  <DropDownPicker
                    open={securityFirmOpen}
                    value={value}
                    items={securityFirmOptions}
                    setOpen={(open) => {
                      closeAllDropdowns();
                      setSecurityFirmOpen(open);
                    }}
                    setValue={(callbackOrValue) => {
                      const selected = typeof callbackOrValue === 'function' ? callbackOrValue(value) : callbackOrValue;
                      onChange(selected);
                    }}
                    placeholder="Select Security Firm"
                    style={styles.dropDown}
                    dropDownContainerStyle={styles.dropDownContainer}
                    listMode="SCROLLVIEW"
                    zIndex={3000}
                    zIndexInverse={999}
                  />
                )}
              />
            </View>

            {/* Rank and Role */}
            <View style={styles.section}>
              <ThemedText style={styles.sectionTitle}>Rank and Role</ThemedText>

              <Controller
                control={control}
                name="rank"
                render={({ field: { value, onChange } }) => (
                  <DropDownPicker
                    open={rankOpen}
                    value={value}
                    items={rankOptions}
                    setOpen={(open) => {
                      closeAllDropdowns();
                      setRankOpen(open);
                    }}
                    setValue={(callbackOrValue) => {
                      const selected = typeof callbackOrValue === 'function' ? callbackOrValue(value) : callbackOrValue;
                      onChange(selected);
                      setCurrentRank(selected);
                      if (selected === 'JSO' || selected === 'LSO') {
                        setValue('role', 'user');
                      }
                    }}
                    placeholder="Select Rank"
                    style={styles.dropDown}
                    dropDownContainerStyle={styles.dropDownContainer}
                    listMode="SCROLLVIEW"
                    zIndex={2000}
                    zIndexInverse={998}
                  />
                )}
              />

              {currentRank === 'OIC' && (
                <Controller
                  control={control}
                  name="role"
                  render={({ field: { value, onChange } }) => (
                    <DropDownPicker
                      open={roleOpen}
                      value={value}
                      items={roleOptions}
                      setOpen={(open) => {
                        closeAllDropdowns();
                        setRoleOpen(open);
                      }}
                      setValue={(callbackOrValue) => {
                        const selected = typeof callbackOrValue === 'function' ? callbackOrValue(value) : callbackOrValue;
                        onChange(selected);
                      }}
                      placeholder="Select Role"
                      style={styles.dropDown}
                      dropDownContainerStyle={styles.dropDownContainer}
                      listMode="SCROLLVIEW"
                      zIndex={1000}
                      zIndexInverse={997}
                    />
                  )}
                />
              )}
            </View>

            {/* Contact Info */}
            <View style={styles.section}>
              <ThemedText style={styles.sectionTitle}>Contact Information</ThemedText>
              {renderInput('address', 'Address')}
              {renderInput('tel', 'Phone Number', false, 'numeric')}
              {renderInput('nic', 'NIC', false, 'numeric')}
            </View>

            <Button mode="contained" onPress={handleSubmit(onSubmit)} style={styles.submitButton} loading={loading}>
              Register
            </Button>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </ThemedView>
  );
};

export default UserRegistration;

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#ffffff' },
  keyboardAvoidingView: { flex: 1 },
  formScroll: { flex: 1 },
  form: { padding: 16 },
  pageTitle: { fontSize: 24, fontWeight: '600', textAlign: 'center', marginBottom: 24, color: '#2d3748' },
  section: { marginBottom: 24 },
  sectionTitle: { fontSize: 18, fontWeight: '600', marginBottom: 16, color: '#2d3748' },
  input: { marginBottom: 16 },
  dropDown: { marginBottom: 16 },
  dropDownContainer: { marginBottom: 16 },
  submitButton: { marginTop: 24 },
});
