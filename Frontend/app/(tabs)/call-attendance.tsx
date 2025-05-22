import React, { useEffect, useState, FC } from 'react';
import {
  View,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { format } from 'date-fns';
import { useRouter } from 'expo-router';
import { useLanguage } from '../../context/LanguageContext';
import { useLocalSearchParams } from 'expo-router';
import { getApiUrl } from '../../config/api';
import * as SecureStore from 'expo-secure-store';
import axios from 'axios';
import DateTimePicker, { DateTimePickerEvent } from '@react-native-community/datetimepicker';
import UpdateAttendanceForm from './UpdateAttendanceForm';
import { ThemedText } from '../../components/ThemedText';
import { ThemedView } from '../../components/ThemedView';

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

function formatCustomDate(date: Date): string {
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const dd = String(date.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

const CallAttendancePage: FC = () => {
  const router = useRouter();
  const { t } = useLanguage();

  const [isLoading, setIsLoading] = useState(true);
  const [employeeData, setEmployeeData] = useState<EmployeeData | null>(null);
  const [attendanceRecords, setAttendanceRecords] = useState<AttendanceRecord[]>([]);
  const [recordsLoading, setRecordsLoading] = useState(false);
  const [dateFilter, setDateFilter] = useState('today');
  const [customDate, setCustomDate] = useState<Date | null>(null);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState<AttendanceRecord | null>(null);
  const [showCustomPicker, setShowCustomPicker] = useState(false);

  const { employeeId, employeeName, rank } = useLocalSearchParams<{
    employeeId: string;
    employeeName?: string;
    rank: string;
  }>();

  const fetchEmployeeDetails = async (empId: string) => {
    if (!empId) return;

    setIsLoading(true);
    try {
      const token = await SecureStore.getItemAsync('userToken');
      if (!token) {
        Alert.alert(
          'Session Expired',
          'Your session has expired. Please log in again.',
          [{ text: 'OK', onPress: () => router.replace('/login') }]
        );
        return;
      }

      const response = await axios.get(`${getApiUrl('/api/employee')}/${empId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.data) {
        const empNo = response.data.emp_no || empId;
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
      if (error.response?.status === 401) {
        Alert.alert(
          'Session Expired',
          'Your session has expired. Please log in again.',
          [{ text: 'OK', onPress: () => router.replace('/login') }]
        );
        return;
      }
      if (employeeName) {
        setEmployeeData({ employeeId: empId, rank: rank || 'N/A', name: employeeName });
      } else {
        Alert.alert('Error', 'Failed to load employee details. Please try again.', [{ text: 'OK' }]);
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
    if (employeeName) {
      setEmployeeData({ employeeId, rank, name: employeeName });
    }
    fetchEmployeeDetails(employeeId);
  }, [employeeId, rank, router, employeeName]);

  const fetchAttendanceRecords = async (empNo: string, filter: string = dateFilter) => {
    setRecordsLoading(true);
    try {
      const token = await SecureStore.getItemAsync('userToken');
      if (!token) return;
      const response = await axios.get(
        `${getApiUrl('/api/attendance/records')}?emp_no=${empNo}&date_filter=${encodeURIComponent(filter)}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (response.data.success) setAttendanceRecords(response.data.records);
      else setAttendanceRecords([]);
    } catch {
      setAttendanceRecords([]);
    } finally {
      setRecordsLoading(false);
    }
  };

  useEffect(() => {
    if (employeeData?.employeeId) fetchAttendanceRecords(employeeData.employeeId, dateFilter);
  }, [employeeData?.employeeId, dateFilter]);

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
        Alert.alert('Session Expired', 'Your session has expired. Please log in again.', [
          { text: 'OK', onPress: () => router.replace('/login') },
        ]);
        return;
      }
      const endpointUrl =
        status === 'IN' ? getApiUrl('/api/attendance/checkin') : getApiUrl('/api/attendance/checkout');
      const response = await axios.post(
        endpointUrl,
        { emp_no: employeeData.employeeId },
        { headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, timeout: 10000 }
      );

      if (response.data.success) {
        const details = response.data.data || {};
        const message =
          status === 'IN'
            ? `Successfully checked in ${details.name || employeeData.name}`
            : `Successfully checked out ${details.name || employeeData.name}`;
        const detailMessage =
          status === 'IN'
            ? `Check-in time: ${details.checkin_time}\nScheduled check-out: ${details.checkout_time}`
            : `Check-in time: ${details.checkin_time}\nCheck-out time: ${details.checkout_time}\nTotal work hours: ${details.total_work_hours}`;
        Alert.alert('Success', `${message}\n\n${detailMessage}`, [{ text: 'OK' }], { cancelable: false });
        fetchEmployeeDetails(employeeData.employeeId);
        fetchAttendanceRecords(employeeData.employeeId);
      } else throw new Error(response.data.message || 'Failed to process attendance');
    } catch (error: any) {
      let errorMessage = `Failed to mark ${status}. Please try again.`;
      if (error.response) errorMessage = error.response.data?.message || errorMessage;
      else if (error.request) errorMessage = 'No response from server. Please check your connection.';
      else errorMessage = error.message || errorMessage;
      Alert.alert('Error', errorMessage);
    }
  };

  if (isLoading)
    return (
      <ThemedView style={[styles.container, styles.loadingContainer]}>
        <ActivityIndicator size="large" color="#007AFF" />
      </ThemedView>
    );

  return (
    <ThemedView style={styles.container}>
      <View style={styles.content}>
        {/* Profile Card */}
        <View style={styles.card}>
          <View style={styles.profilePlaceholder}>
            <ThemedText style={styles.placeholderText}>{employeeData?.name?.charAt(0).toUpperCase() || 'E'}</ThemedText>
          </View>
          <ThemedText style={styles.name}>{employeeData?.name || 'Employee'}</ThemedText>
          <ThemedText style={styles.subtext}>ID: {employeeData?.employeeId || 'N/A'}</ThemedText>
          <View style={styles.rankBadge}>
            <ThemedText style={styles.rankBadgeText}>{employeeData?.rank || 'N/A'}</ThemedText>
          </View>
          <View style={styles.buttonRow}>
            <TouchableOpacity style={styles.inButton} onPress={() => markAttendance('IN')}>
              <ThemedText style={styles.buttonText}>IN</ThemedText>
            </TouchableOpacity>
            <TouchableOpacity style={styles.outButton} onPress={() => markAttendance('OUT')}>
              <ThemedText style={styles.buttonText}>OUT</ThemedText>
            </TouchableOpacity>
          </View>
        </View>

        {/* Date Filter Buttons */}
        <View style={styles.dateFilterRow}>
          {['today', 'yesterday', 'custom'].map((filter) => (
              <TouchableOpacity
                key={filter}
                style={[
                  styles.dateFilterButton,
                  (dateFilter === filter || (filter === 'custom' && !['today', 'yesterday'].includes(dateFilter))) && styles.dateFilterButtonActive,
                ]}
                onPress={() => {
                  if (filter === 'custom') setShowCustomPicker(true);
                  else {
                    setDateFilter(filter);
                    setCustomDate(null);
                  }
                }}
              >
                <ThemedText
                  style={[
                    styles.dateFilterText,
                    (dateFilter === filter || (filter === 'custom' && !['today', 'yesterday'].includes(dateFilter))) && styles.dateFilterTextActive,
                  ]}
                >
                  {filter === 'custom' && customDate
                    ? formatCustomDate(customDate)
                    : filter.charAt(0).toUpperCase() + filter.slice(1)}
                </ThemedText>
              </TouchableOpacity>
            ))}
        </View>

        {showCustomPicker && (
          <DateTimePicker
            value={customDate || new Date()}
            mode="date"
            display="default"
            onChange={(_event: DateTimePickerEvent, selectedDate?: Date) => {
              setShowCustomPicker(false);
              if (selectedDate) {
                setCustomDate(selectedDate);
                setDateFilter(formatCustomDate(selectedDate));
              }
            }}
          />
        )}

        {/* Attendance List */}
        {/* <View style={styles.attendanceList}>
          {attendanceRecords.map((record) => (
            <View key={record.id} style={styles.attendanceItem}>
              <ThemedText style={styles.timeText}>{record.shift_start_time}</ThemedText>
              <ThemedText style={styles.statusText}>{record.status}</ThemedText>
            </View>
          ))}
        </View> */}

        {/* Previous Records Section */}
        <ThemedText style={styles.previousTitle}>Previous Records</ThemedText>
        <View style={styles.previousRecordsContainer}>
          {recordsLoading ? (
            <ActivityIndicator size="small" color="#007AFF" />
          ) : attendanceRecords.length === 0 ? (
            <ThemedText style={styles.recordText}>No previous records found.</ThemedText>
          ) : (
            <ScrollView style={{ maxHeight: 140 }}>
              {attendanceRecords
                .slice()
                .sort((a, b) => b.id - a.id)
                .map((rec) => (
                  <TouchableOpacity
                    key={rec.id}
                    style={styles.previousRecordBox}
                    onPress={() => {
                      setSelectedRecord(rec);
                      setEditModalVisible(true);
                    }}
                  >
                    <ThemedText style={styles.recordText}>
                      ID: {rec.id} | shift_start_time: {rec.shift_start_time} | shift_end_time: {rec.shift_end_time} | Status: {rec.status}
                    </ThemedText>
                  </TouchableOpacity>
                ))}
            </ScrollView>
          )}
        </View>

        {/* Back Button */}
        <TouchableOpacity style={styles.backButton} onPress={handleBack}>
          <ThemedText style={styles.backButtonText}>{t('back')}</ThemedText>
        </TouchableOpacity>

        {/* Update Modal */}
        <UpdateAttendanceForm
          visible={editModalVisible}
          initialRecord={selectedRecord}
          onClose={() => setEditModalVisible(false)}
          onSave={async (updated) => {
            if (!selectedRecord) return;
            try {
              const token = await SecureStore.getItemAsync('userToken');
              const payload = {
                shift_start_time: updated.shift_start_time,
                shift_end_time: updated.shift_end_time,
              };
              await axios.put(`${getApiUrl('/api/attendance/records')}/${selectedRecord.id}`, payload, {
                headers: { Authorization: `Bearer ${token}` },
              });
              setEditModalVisible(false);
              setSelectedRecord(null);
              if (employeeData) fetchAttendanceRecords(employeeData.employeeId);
            } catch {
              Alert.alert('Error', 'Failed to update record');
            }
          }}
        />
      </View>
    </ThemedView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
    paddingHorizontal: 15,
    paddingTop: 20,
  },
  content: {
    backgroundColor: '#fff',
    borderRadius: 15,
    padding: 20,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 6,
    position: 'relative',
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 15,
    padding: 20,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 6,
    position: 'relative',
  },
  profilePlaceholder: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: '#0A73FF',
    justifyContent: 'center',
    alignItems: 'center',
    position: 'absolute',
    top: -35,
    alignSelf: 'center',
    borderWidth: 3,
    borderColor: '#fff',
  },
  placeholderText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 28,
  },
  name: {
    marginTop: 45,
    fontWeight: 'bold',
    fontSize: 18,
    color: '#666',
    textAlign: 'center',
    opacity: 0.6,
  },
  subtext: {
    fontSize: 14,
    color: '#333',
    marginTop: 5,
    textAlign: 'center',
  },
  rankBadge: {
    backgroundColor: '#FFD700',
    borderRadius: 15,
    paddingVertical: 7,
    marginTop: 10,
    alignItems: 'center',
    width: '60%',
    alignSelf: 'center',
  },
  rankBadgeText: {
    color: '#222',
    fontWeight: 'bold',
    fontSize: 14,
  },
  buttonRow: {
    flexDirection: 'row',
    marginTop: 20,
    justifyContent: 'space-between',
  },
  inButton: {
    backgroundColor: '#00A14B',
    paddingVertical: 14,
    flex: 1,
    marginRight: 12,
    borderRadius: 8,
  },
  outButton: {
    backgroundColor: '#E63946',
    paddingVertical: 14,
    flex: 1,
    marginLeft: 12,
    borderRadius: 8,
  },
  buttonText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 16,
    textAlign: 'center',
  },
  dateFilterRow: {
    flexDirection: 'row',
    marginBottom: 20,
    justifyContent: 'space-between',
  },
  dateFilterButton: {
    flex: 1,
    marginHorizontal: 5,
    paddingVertical: 10,
    borderRadius: 8,
    backgroundColor: '#d3d3d3',
    alignItems: 'center',
  },
  dateFilterButtonActive: {
    backgroundColor: '#0A73FF',
  },
  dateFilterText: {
    color: '#333',
    fontWeight: '600',
  },
  dateFilterTextActive: {
    color: '#fff',
  },
  attendanceList: {
    marginBottom: 20,
  },
  attendanceItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    borderBottomColor: '#ddd',
    borderBottomWidth: 1,
    paddingVertical: 12,
    opacity: 0.4,
  },
  timeText: {
    fontSize: 14,
    color: '#999',
  },
  statusText: {
    fontSize: 14,
    color: '#999',
  },
  previousTitle: {
    fontWeight: 'bold',
    fontSize: 18,
    marginBottom: 10,
  },
  previousRecordsContainer: {
    backgroundColor: '#f0f0f0',
    borderRadius: 10,
    paddingVertical: 10,
    paddingHorizontal: 12,
  },
  previousRecordBox: {
    backgroundColor: '#fff',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
  },
  recordText: {
    fontSize: 14,
    color: '#222',
  },
  backButton: {
    backgroundColor: '#222',
    paddingVertical: 18,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 15,
  },
  backButtonText: {
    color: '#0A73FF',
    fontSize: 16,
    fontWeight: '600',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

export default CallAttendancePage;
