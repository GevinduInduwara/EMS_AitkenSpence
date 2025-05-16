CREATE OR REPLACE FUNCTION calculate_shift_count(
    start_time TIME,
    end_time TIME
) RETURNS INTEGER AS $$
DECLARE
    total_hours INTERVAL;
    shift_count INTEGER;
BEGIN
    -- Calculate total hours worked
    IF end_time > start_time THEN
        total_hours := end_time - start_time;
    ELSE
        total_hours := (end_time + INTERVAL '24 hours') - start_time;
    END IF;

    -- Calculate shift count (1 shift = 12 hours)
    shift_count := CEIL(EXTRACT(EPOCH FROM total_hours) / (12 * 60 * 60));
    
    RETURN shift_count;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to automatically calculate total_work_hours and shift_count
CREATE OR REPLACE FUNCTION update_attendance_calculations()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate total work hours
    IF NEW.shift_end_time > NEW.shift_start_time THEN
        NEW.total_work_hours := NEW.shift_end_time - NEW.shift_start_time;
    ELSE
        NEW.total_work_hours := (NEW.shift_end_time + INTERVAL '24 hours') - NEW.shift_start_time;
    END IF;

    -- Calculate shift count
    NEW.shift_count := calculate_shift_count(NEW.shift_start_time, NEW.shift_end_time);
    
    -- Update updated_at timestamp
    NEW.updated_at = CURRENT_TIMESTAMP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_attendance_calculations
    BEFORE INSERT OR UPDATE ON attendance
    FOR EACH ROW
    EXECUTE FUNCTION update_attendance_calculations();
