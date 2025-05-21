import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  TouchableOpacity,
  Dimensions,
  ActivityIndicator,
  Alert,
  ScrollView,
  Platform,
} from 'react-native';
import DropDownPicker from 'react-native-dropdown-picker';
import { ThemedText } from '../../components/ThemedText';
import { ThemedView } from '../../components/ThemedView';
import { LogoContainer } from '../../components/LogoContainer';
import { useLanguage } from '../../context/LanguageContext';
import { useRouter } from 'expo-router';
import axios from 'axios';
import * as SecureStore from 'expo-secure-store';
import { getApiUrl } from '../../config/api';

const { height } = Dimensions.get('window');

interface Employee {
  emp_no: string;
  name: string;
  rank: string;
}

const CallAttendanceSelectPage: React.FC = () => {
  const router = useRouter();
  const { t } = useLanguage();

  const [selectedRank, setSelectedRank] = useState<string>('');
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null);
  const [filteredEmployees, setFilteredEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  // DropDownPicker states
  const [open, setOpen] = useState(false);
  const [employeeItems, setEmployeeItems] = useState<any[]>([]);
  const [selectedEmpNo, setSelectedEmpNo] = useState<string | null>(null);

  useEffect(() => {
    const fetchEmployeesByRank = async () => {
      if (!selectedRank) {
        setFilteredEmployees([]);
        return;
      }
      setLoading(true);
      try {
        const response = await axios.get(getApiUrl(`/api/employees_by_rank?rank=${selectedRank}`), {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${await SecureStore.getItemAsync('userToken')}`
          },
        });

        if (response.status === 200) {
          const data = response.data?.employees || [];
          setFilteredEmployees(data);
        } else {
          throw new Error('Failed to fetch employees');
        }
      } catch (error) {
        console.error('Error fetching employees by rank:', error);
        setFilteredEmployees([]);
        Alert.alert('Error', 'Failed to fetch employees. Please try again later.', [{ text: 'OK' }]);
      } finally {
        setLoading(false);
      }
    };

    fetchEmployeesByRank();
  }, [selectedRank]);

  useEffect(() => {
    const items = filteredEmployees.map(emp => ({
      label: emp.name,
      value: emp.emp_no,
    }));
    setEmployeeItems(items);
  }, [filteredEmployees]);

  useEffect(() => {
    if (selectedEmpNo) {
      const found = filteredEmployees.find(e => e.emp_no === selectedEmpNo);
      setSelectedEmployee(found ?? null);
    }
  }, [selectedEmpNo]);

  const handleSubmit = () => {
    if (selectedEmployee && selectedRank) {
      router.push({
        pathname: '/call-attendance',
        params: {
          employeeId: selectedEmployee.emp_no,
          employeeName: selectedEmployee.name,  // Pass the name directly
          rank: selectedRank,
        },
      });
    }
  }; 

  return (
    <ThemedView style={styles.container}>
      <View style={styles.scrollView}>
        <View style={styles.scrollContainer}>
          <View style={styles.logoWrapper}>
            <LogoContainer style={styles.logoSize} />
          </View>

          <ThemedView style={styles.contentContainer}>
            <View style={styles.titleContainer}>
              <ThemedText style={styles.title}>{t('markAttendanceTitle')}</ThemedText>
            </View>

            <View style={styles.rankButtonContainer}>
              {['OIC', 'JSO', 'LSO'].map((rank) => (
                <TouchableOpacity
                  key={rank}
                  onPress={() => {
                    setSelectedRank(rank);
                    setSelectedEmployee(null);
                    setSelectedEmpNo(null);
                  }}
                  style={[
                    styles.rankButton,
                    selectedRank === rank && styles.selectedRankButton,
                  ]}
                >
                  <ThemedText
                    style={
                      selectedRank === rank
                        ? styles.selectedRankButtonText
                        : styles.rankButtonText
                    }
                  >
                    {rank}
                  </ThemedText>
                </TouchableOpacity>
              ))}
            </View>

            <View style={styles.dropdownWrapper}>
              {loading ? (
                <ActivityIndicator size="large" color="#007AFF" />
              ) : (
                <DropDownPicker
                  open={open}
                  setOpen={setOpen}
                  value={selectedEmpNo}
                  setValue={setSelectedEmpNo}
                  items={employeeItems}
                  setItems={setEmployeeItems}
                  placeholder={selectedRank ? `Select ${selectedRank}` : 'Select Employee'}
                  disabled={!selectedRank}
                  style={styles.dropdown}
                  dropDownContainerStyle={styles.dropdownList}
                  textStyle={styles.dropdownText}
                  zIndex={1000}
                  zIndexInverse={3000}
                />
              )}
            </View>

            <View style={styles.buttonContainer}>
              <TouchableOpacity
                style={[
                  styles.submitButton,
                  !selectedEmployee && styles.disabledButton,
                ]}
                onPress={handleSubmit}
                disabled={!selectedEmployee}
              >
                <ThemedText
                  style={
                    selectedEmployee
                      ? styles.submitButtonText
                      : styles.disabledButtonText
                  }
                >
                  {t('submit')}
                </ThemedText>
              </TouchableOpacity>
            </View>
          </ThemedView>
        </View>
      </View>
    </ThemedView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f0f6ff',
    paddingVertical: 20,
  },
  scrollView: {
    flex: 1,
    width: '100%',
  },
  scrollContent: {
    flexGrow: 1,
    paddingBottom: 40,
    paddingTop: 20,
    alignItems: 'center',
    justifyContent: 'flex-start',
  },
  scrollContainer: {
    width: '100%',
    alignItems: 'center',
    minHeight: height,
  },
  logoWrapper: {
    marginBottom: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoSize: {
    width: 160,
    height: 160,
  },
  contentContainer: {
    width: '90%',
    maxWidth: 500,
    backgroundColor: '#ffffff',
    borderRadius: 20,
    paddingVertical: 25,
    paddingHorizontal: 20,
    alignItems: 'center',
    elevation: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    marginVertical: 20,
  },
  titleContainer: {
    marginBottom: 20,
    paddingHorizontal: 10,
    width: '100%',
  },
  title: {
    fontSize: 26,
    fontWeight: '700',
    color: '#2c3e50',
    textAlign: 'center',
  },
  rankButtonContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-around',
    width: '100%',
    marginVertical: 15,
  },
  rankButton: {
    width: '30%',
    marginBottom: 12,
    backgroundColor: '#e6efff',
    paddingVertical: 12,
    paddingHorizontal: 10,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.12,
    shadowRadius: 2,
    elevation: 2,
  },
  selectedRankButton: {
    backgroundColor: '#007AFF',
  },
  rankButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#007AFF',
  },
  selectedRankButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#fff',
  },
  dropdownWrapper: {
    width: '100%',
    marginBottom: 25,
    zIndex: 1000,
  },
  dropdown: {
    backgroundColor: '#fff',
    borderColor: '#cfd8dc',
    borderRadius: 10,
    minHeight: 50,
  },
  dropdownList: {
    borderColor: '#cfd8dc',
    borderRadius: 10,
  },
  dropdownText: {
    fontSize: 16,
    color: '#1f2937',
  },
  buttonContainer: {
    width: '100%',
    marginTop: 10,
  },
  submitButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 4,
    shadowColor: '#007AFF',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 3,
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 17,
    fontWeight: '600',
  },
  disabledButton: {
    backgroundColor: '#d1d5db',
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  disabledButtonText: {
    color: '#6b7280',
    fontSize: 17,
    fontWeight: '600',
  },
});

export default CallAttendanceSelectPage;
