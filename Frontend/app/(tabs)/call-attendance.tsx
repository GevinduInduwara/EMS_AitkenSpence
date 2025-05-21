import React, { useEffect, useState, FC } from 'react';
import {
  View,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { ThemedText } from '../../components/ThemedText';
import { ThemedView } from '../../components/ThemedView';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useLanguage } from '../../context/LanguageContext';
import { getApiUrl } from '../../config/api';
import * as SecureStore from 'expo-secure-store';
import axios from 'axios';
import { format } from 'date-fns';
import UpdateAttendanceForm from './UpdateAttendanceForm';

interface EmployeeData {
  employeeId: string;
  rank: string;
  name: string;
  role?: string;
  tel?: string;
  companyName?: string;
  securityFirm?: string;
}

interface AttendanceRecord {
  id: number;
  emp_no: string;
  shift_start_time: string;
  shift_end_time: string | null;
  status: string;
}

const CallAttendancePage: FC = () => {
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState<AttendanceRecord | null>(null);

  const router = useRouter();
  const { t } = useLanguage();

  const { employeeId, employeeName, rank } = useLocalSearchParams<{
    employeeId: string;
    employeeName?: string;
    rank: string;
  }>();

  const [employeeData, setEmployeeData] = useState<EmployeeData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [recordsLoading, setRecordsLoading] = useState(false);

  const fetchEmployeeDetails = async (empId: string) => {
    if (!empId) return;
    
    setIsLoading(true);
    try {
      const token = await SecureStore.getItemAsync('userToken');
      if (!token) {
        console.error('No authentication token found');
        // Instead of redirecting, show an error and allow the user to log in from the current screen
        Alert.alert(
          'Session Expired',
          'Your session has expired. Please log in again.',
          [
            {
              text: 'OK',
              onPress: () => router.replace('/login')
            }
          ]
        );
        return;
      }

      const response = await axios.get(
        `${getApiUrl('/api/employee')}/${empId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.data) {
        // Ensure employeeId is set from emp_no if available, otherwise use the provided empId
        const empNo = response.data.emp_no || empId;
        console.log('Employee data received:', response.data);
        setEmployeeData({
          employeeId: empNo,
          rank: response.data.rank || rank || 'N/A',
          name: response.data.name || employeeName || 'Employee',
          role: response.data.role,
          tel: response.data.tel,
          companyName: response.data.company_name,
          securityFirm: response.data.security_firm,
        });
      }
    } catch (error: any) {
      console.error('Error fetching employee details:', error);
      
      // Handle 401 Unauthorized
      if (error.response?.status === 401) {
        Alert.alert(
          'Session Expired',
          'Your session has expired. Please log in again.',
          [
            {
              text: 'OK',
              onPress: () => router.replace('/login')
            }
          ]
        );
        return;
      }
      
      // If there's an error but we have basic info, still show that
      if (employeeName) {
        setEmployeeData({
          employeeId: empId,
          rank: rank || 'N/A',
          name: employeeName,
        });
      } else {
        Alert.alert(
          'Error',
          'Failed to load employee details. Please try again.',
          [{ text: 'OK' }]
        );
        router.back();
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!employeeId || !rank) {
      router.back();
      return;
    }

    // If we have the name from the params, use it immediately
    if (employeeName) {
      setEmployeeData({
        employeeId,
        rank,
        name: employeeName,
      });
    }

    // Fetch full employee details
    fetchEmployeeDetails(employeeId);
  }, [employeeId, rank, router, employeeName]);

  // Fetch attendance records for the employee
  const fetchAttendanceRecords = async (empNo: string) => {
    setRecordsLoading(true);
    try {
      const token = await SecureStore.getItemAsync('userToken');
      if (!token) return;
      const response = await axios.get(
        `${getApiUrl('/api/attendance/records')}?emp_no=${empNo}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (response.data.success) {
        setRecords(response.data.records);
      } else {
        setRecords([]);
      }
    } catch (e) {
      setRecords([]);
    } finally {
      setRecordsLoading(false);
    }
  };

  useEffect(() => {
    if (employeeData?.employeeId) {
      fetchAttendanceRecords(employeeData.employeeId);
    }
  }, [employeeData?.employeeId]);

  const handleBack = () => {
    router.back();
  };

  const markAttendance = async (status: 'IN' | 'OUT') => {
    if (!employeeData?.employeeId) {
      Alert.alert('Error', 'No employee data found');
      return;
    }

    try {
      const token = await SecureStore.getItemAsync('userToken');
      if (!token) {
        Alert.alert(
          'Session Expired',
          'Your session has expired. Please log in again.',
          [
            {
              text: 'OK',
              onPress: () => router.replace('/login')
            }
          ]
        );
        return;
      }

      const endpointUrl = status === 'IN'
        ? getApiUrl('/api/attendance/checkin')
        : getApiUrl('/api/attendance/checkout');
      const response = await axios.post(
        endpointUrl,
        { emp_no: employeeData.employeeId },
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          timeout: 10000 // 10 seconds timeout
        }
      );

      if (response.data.success) {
        const message = status === 'IN' 
          ? `Successfully checked in ${response.data.data?.name || employeeData.name}`
          : `Successfully checked out ${response.data.data?.name || employeeData.name}`;
        
        // Show detailed success message
        const details = response.data.data || {};
        const detailMessage = status === 'IN'
          ? `Check-in time: ${details.checkin_time}\n` +
            `Scheduled check-out: ${details.checkout_time}`
          : `Check-in time: ${details.checkin_time}\n` +
            `Check-out time: ${details.checkout_time}\n` +
            `Total work hours: ${details.total_work_hours}`;
        
        Alert.alert(
          'Success',
          `${message}\n\n${detailMessage}`,
          [{ text: 'OK' }],
          { cancelable: false }
        );
        
        // Refresh employee details to update the status
        fetchEmployeeDetails(employeeData.employeeId);
        fetchAttendanceRecords(employeeData.employeeId);
      } else {
        throw new Error(response.data.message || 'Failed to process attendance');
      }
    } catch (error: any) {
      console.error(`Error marking ${status}:`, error);
      let errorMessage = `Failed to mark ${status}. Please try again.`;
      
      if (error.response) {
        errorMessage = error.response.data?.message || errorMessage;
      } else if (error.request) {
        errorMessage = 'No response from server. Please check your connection.';
      } else {
        errorMessage = error.message || errorMessage;
      }
      
      Alert.alert('Error', errorMessage);
    }
  };

  const handleInPress = () => {
    markAttendance('IN');
  };

  const handleOutPress = () => {
    markAttendance('OUT');
  };

  if (isLoading) {
    return (
      <ThemedView style={[styles.container, styles.loadingContainer]}>
        <ActivityIndicator size="large" color="#007AFF" />
      </ThemedView>
    );
  }

  return (
    <ThemedView style={styles.container}>
      <View style={styles.content}>
        <View style={styles.card}>
          <View style={styles.profilePlaceholder}>
            <ThemedText style={styles.placeholderText}>
              {employeeData?.name?.charAt(0).toUpperCase() || 'E'}
            </ThemedText>
          </View>

          <ThemedText style={styles.name}>{employeeData?.name || 'Employee'}</ThemedText>
          <ThemedText style={styles.subtext}>ID: {employeeData?.employeeId || 'N/A'}</ThemedText>

          <View style={styles.rankBadge}>
            <ThemedText style={styles.rankBadgeText}>{employeeData?.rank || 'N/A'}</ThemedText>
          </View>

          <View style={styles.buttonRow}>
            <TouchableOpacity style={styles.inButton} onPress={handleInPress}>
              <ThemedText style={styles.buttonText}>IN</ThemedText>
            </TouchableOpacity>
            <TouchableOpacity style={styles.outButton} onPress={handleOutPress}>
              <ThemedText style={styles.buttonText}>OUT</ThemedText>
            </TouchableOpacity>
          </View>
        </View>

        <ThemedText style={styles.previousTitle}>Previous Records</ThemedText>
        {recordsLoading ? (
          <ActivityIndicator size="small" color="#007AFF" />
        ) : records.length === 0 ? (
          <View style={styles.recordBox}>
            <ThemedText style={styles.recordText}>No previous records found.</ThemedText>
          </View>
        ) : (
          <ScrollView style={styles.recordList}>
            {records.map((rec) => (
              <TouchableOpacity
                key={rec.id}
                style={styles.recordBox}
                onPress={() => {
                  setSelectedRecord(rec);
                  setEditModalVisible(true);
                }}
              >
                <ThemedText style={styles.recordText}>
                  ID: {rec.id} | shift_start_time: {String(rec.shift_start_time)} | shift_end_time: {String(rec.shift_end_time)} | Status: {rec.status}
                </ThemedText>
              </TouchableOpacity>
            ))}

            <UpdateAttendanceForm
              visible={editModalVisible}
              initialRecord={selectedRecord}
              onClose={() => setEditModalVisible(false)}
              onSave={async (updated) => {
                if (!selectedRecord) return;
                try {
                  const token = await SecureStore.getItemAsync('userToken');
                  await axios.put(
                    `${getApiUrl('/api/attendance/records')}/${selectedRecord.id}`,
                    updated,
                    { headers: { Authorization: `Bearer ${token}` } }
                  );
                  setEditModalVisible(false);
                  setSelectedRecord(null);
                  if (employeeData) {
                    fetchAttendanceRecords(employeeData.employeeId);
                  }
                } catch (e) {
                  Alert.alert('Error', 'Failed to update record');
                }
              }}
            />
          </ScrollView>
        )}

        <TouchableOpacity style={styles.backButton} onPress={handleBack}>
          <ThemedText style={styles.backButtonText}>{t('back')}</ThemedText>
        </TouchableOpacity>
      </View>
    </ThemedView>
  );
};

const styles = StyleSheet.create({
  recordList: {
    maxHeight: 200,
    marginBottom: 10,
  },
  deleteButton: {
    marginLeft: 10,
    backgroundColor: '#ff4d4d',
    padding: 5,
    borderRadius: 5,
  },
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  content: {
    flex: 1,
    width: '100%',
    padding: 20,
    alignItems: 'center',
  },
  loadingContainer: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 20,
    width: '100%',
    alignItems: 'center',
    paddingVertical: 30,
    paddingHorizontal: 20,
    marginBottom: 30,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 6,
    elevation: 6,
  },
  profilePlaceholder: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#d1d5db',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 15,
  },
  placeholderText: {
    fontSize: 36,
    color: '#666666',
    fontWeight: 'bold',
  },
  name: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 5,
  },
  subtext: {
    fontSize: 14,
    color: '#4b5563',
    marginBottom: 8,
  },
  rankBadge: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
    marginBottom: 20,
  },
  rankBadgeText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 20,
    width: '80%',
  },
  inButton: {
    backgroundColor: '#10B981',
    borderRadius: 50,
    paddingVertical: 12,
    paddingHorizontal: 30,
    flex: 1,
    alignItems: 'center',
  },
  outButton: {
    backgroundColor: '#B91C1C',
    borderRadius: 50,
    paddingVertical: 12,
    paddingHorizontal: 30,
    flex: 1,
    alignItems: 'center',
  },
  buttonText: {
    color: '#ffffff',
    fontWeight: '600',
    fontSize: 16,
  },
  previousTitle: {
    color: '#000',
    fontSize: 16,
    alignSelf: 'flex-start',
    marginBottom: 8,
  },
  recordBox: {
    width: '100%',
    backgroundColor: '#f3f4f6',
    borderRadius: 10,
    padding: 15,
    marginBottom: 30,
  },
  recordText: {
    color: '#374151',
    fontSize: 14,
  },
  backButton: {
    backgroundColor: '#333333',
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
    width: '100%',
  },
  backButtonText: {
    color: '#007AFF',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default CallAttendancePage;