import React, { useState, useEffect } from 'react';
import { View, Modal, StyleSheet, TouchableOpacity, Platform } from 'react-native';
import { ThemedText } from '../../components/ThemedText';
import DateTimePicker from '@react-native-community/datetimepicker';

export interface UpdateAttendanceFormProps {
  visible: boolean;
  initialRecord: {
    id: number;
    shift_start_time: string | null;
    shift_end_time: string | null;
  } | null;
  onClose: () => void;
  onSave: (updated: {
    shift_start_time: string;
    shift_end_time: string | null;
  }) => void;
}

const parseDateSafe = (dateString: string | null | undefined): Date | null => {
  if (!dateString) return null;
  const parsed = new Date(dateString);
  return isNaN(parsed.getTime()) ? null : parsed;
};

// Helper to check if two dates are the same day
function isSameDay(a: Date | null | undefined, b: Date | null | undefined) {
  if (!a || !b) return false;
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}

const UpdateAttendanceForm: React.FC<UpdateAttendanceFormProps> = ({
  visible,
  initialRecord,
  onClose,
  onSave,
}) => {
  const recordDate = parseDateSafe(initialRecord?.shift_start_time) || new Date();
  const [shiftStart, setShiftStart] = useState<Date | null>(parseDateSafe(initialRecord?.shift_start_time) || new Date());
  const [shiftEnd, setShiftEnd] = useState<Date | null>(
  parseDateSafe(initialRecord?.shift_end_time) || parseDateSafe(initialRecord?.shift_start_time) || new Date()
);

  const [showStartPicker, setShowStartPicker] = useState(false);
  const [showEndPicker, setShowEndPicker] = useState(false);
  const [tempStartTime, setTempStartTime] = useState<Date | null>(shiftStart);
  const [tempEndTime, setTempEndTime] = useState<Date | null>(shiftEnd);

  useEffect(() => {
    setShiftStart(parseDateSafe(initialRecord?.shift_start_time) || new Date());
    setShiftEnd(parseDateSafe(initialRecord?.shift_end_time));
    setTempStartTime(parseDateSafe(initialRecord?.shift_start_time) || new Date());
    setTempEndTime(parseDateSafe(initialRecord?.shift_end_time));
  }, [initialRecord]);

  const handleSave = () => {
    // Commit any temp values if pickers are open
    if (showStartPicker && tempStartTime) setShiftStart(tempStartTime);
    if (showEndPicker && tempEndTime) setShiftEnd(tempEndTime);

    // Use the latest selected time (from temp if available, otherwise from state)
    const start = tempStartTime || shiftStart;
    const end = tempEndTime || shiftEnd;

    if (!start) {
      // Optional validation alert here if needed
      return;
    }
    onSave({
      shift_start_time: start.toTimeString().slice(0, 8),
      shift_end_time: end ? end.toTimeString().slice(0, 8) : null,
    });
  };

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.container}>
          <ThemedText style={styles.title}>Update Attendance Record</ThemedText>

          <TouchableOpacity onPress={() => setShowStartPicker(true)} style={styles.inputBox}>
            <ThemedText style={styles.inputLabel}>Date:</ThemedText>
            <ThemedText style={styles.inputText}>{recordDate ? recordDate.toLocaleDateString() : 'No date'}</ThemedText>
          </TouchableOpacity>

          <TouchableOpacity onPress={() => setShowStartPicker(true)} style={styles.inputBox}>
            <ThemedText style={styles.inputLabel}>Shift Start Time:</ThemedText>
            <ThemedText style={styles.inputText}>
              {shiftStart ? shiftStart.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'No time set'}
            </ThemedText>
          </TouchableOpacity>
          {showStartPicker && (
            <Modal
              visible={showStartPicker}
              transparent
              animationType="fade"
              onRequestClose={() => setShowStartPicker(false)}
            >
              <View style={styles.timePickerModalOverlay}>
                <View style={styles.timePickerModalContent}>
                  <DateTimePicker
                    value={shiftStart || new Date()}
                    mode="time"
                    display={Platform.OS === 'ios' ? 'spinner' : 'default'}
                    textColor={Platform.OS === 'ios' ? '#000' : undefined}
                    onChange={(_, date) => {
                      if (date !== undefined && date !== null) {
                        setTempStartTime(date);
                      }
                    }}
                    style={{ width: '100%' }}
                  />
                  <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 16 }}>
                    <TouchableOpacity style={[styles.cancelButton, { flex: 1, marginRight: 8 }]} onPress={() => setShowStartPicker(false)}>
                      <ThemedText style={styles.cancelButtonText}>Cancel</ThemedText>
                    </TouchableOpacity>
                    <TouchableOpacity style={[styles.saveButton, { flex: 1, marginLeft: 8 }]} onPress={() => {
                      if (tempStartTime) setShiftStart(tempStartTime);
                      setShowStartPicker(false);
                    }}>
                      <ThemedText style={styles.saveButtonText}>Confirm</ThemedText>
                    </TouchableOpacity>
                  </View>
                </View>
              </View>
            </Modal>
          )}

          <TouchableOpacity onPress={() => setShowEndPicker(true)} style={styles.inputBox}>
            <ThemedText style={styles.inputLabel}>Shift End Time:</ThemedText>
            <ThemedText style={styles.inputText}>
              {shiftEnd ? shiftEnd.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'No time set'}
            </ThemedText>
          </TouchableOpacity>
          {showEndPicker && (
            <Modal
              visible={showEndPicker}
              transparent
              animationType="fade"
              onRequestClose={() => setShowEndPicker(false)}
            >
              <View style={styles.timePickerModalOverlay}>
                <View style={styles.timePickerModalContent}>
                  <DateTimePicker
                    value={tempEndTime || shiftEnd || shiftStart || new Date()}
                    mode="time"
                    display={Platform.OS === 'ios' ? 'spinner' : 'default'}
                    textColor={Platform.OS === 'ios' ? '#000' : undefined}
                    onChange={(_, date) => {
                      if (date !== undefined && date !== null) {
                        setTempEndTime(date);
                      }
                    }}
                    style={{ width: '100%' }}
                  />
                  <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 16 }}>
                    <TouchableOpacity style={[styles.cancelButton, { flex: 1, marginRight: 8 }]} onPress={() => setShowEndPicker(false)}>
                      <ThemedText style={styles.cancelButtonText}>Cancel</ThemedText>
                    </TouchableOpacity>
                    <TouchableOpacity style={[styles.saveButton, { flex: 1, marginLeft: 8 }]} onPress={() => {
                      if (tempEndTime) setShiftEnd(tempEndTime);
                      setShowEndPicker(false);
                    }}>
                      <ThemedText style={styles.saveButtonText}>Confirm</ThemedText>
                    </TouchableOpacity>
                  </View>
                </View>
              </View>
            </Modal>
          )}

          <View style={styles.buttonRow}>
            <TouchableOpacity
              style={styles.saveButton}
              onPress={handleSave}
            >
              <ThemedText style={styles.saveButtonText}>Save</ThemedText>
            </TouchableOpacity>
            {(shiftStart && !isSameDay(shiftStart, recordDate)) && (
              <ThemedText style={{ color: 'red', textAlign: 'center', marginTop: 8 }}>
                Start time date must match the record date ({recordDate ? recordDate.toLocaleDateString() : ''}).
              </ThemedText>
            )}
            {(shiftEnd && !isSameDay(shiftEnd, recordDate)) && (
              <ThemedText style={{ color: 'red', textAlign: 'center', marginTop: 8 }}>
                End time date must match the record date ({recordDate ? recordDate.toLocaleDateString() : ''}).
              </ThemedText>
            )}
            <TouchableOpacity style={styles.cancelButton} onPress={onClose}>
              <ThemedText style={styles.cancelButtonText}>Cancel</ThemedText>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  timePickerModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  timePickerModalContent: {
    backgroundColor: '#fff',
    borderRadius: 18,
    padding: 24,
    alignItems: 'center',
    width: 320,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.13,
    shadowRadius: 18,
    elevation: 10,
  },
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  container: {
    backgroundColor: '#fff',
    borderRadius: 20,
    paddingVertical: 24,
    paddingHorizontal: 20,
    width: '100%',
    maxWidth: 360,
    alignItems: 'stretch',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.1,
    shadowRadius: 20,
    elevation: 10,
  },
  title: {
    fontWeight: '700',
    fontSize: 20,
    marginBottom: 18,
    textAlign: 'center',
    color: '#000',
  },
  inputBox: {
    backgroundColor: '#f5f7fa',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#ced4da',
    paddingHorizontal: 15,
    paddingVertical: 14,
    marginVertical: 12,
    flexDirection: 'row',
    alignItems: 'center',
  },
  inputLabel: {
    fontWeight: '600',
    fontSize: 16,
    color: '#444',
    width: 110,
  },
  inputText: {
    fontSize: 16,
    color: '#000',
    flex: 1,
  },
  pickerWrapper: {
    backgroundColor: '#f5f7fa',
    borderRadius: 14,
    paddingVertical: 12,
    paddingHorizontal: 15,
    marginVertical: 12,
    alignSelf: 'stretch',
    maxWidth: 350,
    alignItems: 'center',
  },
  buttonRow: {
    flexDirection: 'row',
    marginTop: 30,
    justifyContent: 'space-between',
  },
  saveButton: {
    flex: 1,
    backgroundColor: '#28a745',
    paddingVertical: 14,
    marginRight: 12,
    borderRadius: 14,
    alignItems: 'center',
    shadowColor: '#28a745',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 6,
  },
  cancelButton: {
    flex: 1,
    backgroundColor: '#dc3545',
    paddingVertical: 14,
    marginLeft: 12,
    borderRadius: 14,
    alignItems: 'center',
    shadowColor: '#dc3545',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 6,
  },
  saveButtonText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 17,
  },
  cancelButtonText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 17,
  },
});

export default UpdateAttendanceForm;
