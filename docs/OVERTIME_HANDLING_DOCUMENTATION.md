# Overtime Handling Documentation

## Overview

The Venus AutoFill system now supports **automatic overtime handling** for attendance records. When a record contains overtime hours, the system automatically creates separate entries for normal and overtime hours, each with the appropriate transaction type selection.

## How It Works

### 1. Record Processing Logic

The system uses the `create_overtime_entries()` method to process each record:

```python
def create_overtime_entries(self, record: Dict) -> List[Dict]:
    """
    Create separate entries for normal and overtime hours
    If overtime_hours > 0, creates two entries: normal and overtime
    If overtime_hours = 0, creates one normal entry
    """
```

### 2. Entry Creation Rules

| Scenario | Regular Hours | Overtime Hours | Entries Created |
|----------|---------------|----------------|-----------------|
| **Normal Only** | > 0 | 0 | 1 entry (Normal) |
| **Normal + Overtime** | > 0 | > 0 | 2 entries (Normal + Overtime) |
| **Overtime Only** | 0 | > 0 | 1 entry (Overtime) |
| **Zero Hours** | 0 | 0 | 1 entry (Normal, 0 hours) |

### 3. Transaction Type Selection

The system automatically selects the appropriate radio button for each entry:

- **Normal Entry**: `MainContent_rblOT_0` (Normal) radio button
- **Overtime Entry**: `MainContent_rblOT_1` (Overtime) radio button

## Implementation Details

### New Methods Added

#### `create_overtime_entries(record: Dict) -> List[Dict]`
Splits a single record into separate normal and overtime entries.

#### `select_transaction_type(driver, transaction_type: str) -> bool`
Selects the appropriate transaction type radio button using JavaScript.

#### `fill_hours_field(driver, hours_value: float) -> bool`
Fills the hours field with the specified value.

### Modified Methods

#### `process_single_record(driver, record: Dict) -> bool`
Now includes:
- Transaction type selection (Step 3)
- Hours field filling (Step 8)

#### `run_api_automation() -> bool`
Now processes records through `create_overtime_entries()` before form filling.

## Example Usage

### Sample Record Input
```json
{
  "employee_name": "Ade Prasetya",
  "date": "2025-05-18",
  "regular_hours": 7.0,
  "overtime_hours": 16.0,
  "raw_charge_job": "(OC7190) BOILER OPERATION / STN-BLR (STATION BOILER) / BLR00000 (LABOUR COST) / L (LABOUR)"
}
```

### Generated Entries
The system creates **2 entries** from this record:

#### Entry 1 (Normal)
- Transaction Type: **Normal** (radio button selected)
- Hours: **7.0**
- All other fields: Same as original record

#### Entry 2 (Overtime)
- Transaction Type: **Overtime** (radio button selected)
- Hours: **16.0**
- All other fields: Same as original record

## Form Fields Filled

For each entry, the system fills:

1. **Date Field**: `MainContent_txtTrxDate`
2. **Employee Field**: First autocomplete field
3. **Transaction Type**: Radio button selection
4. **Task Code**: From `raw_charge_job` part 1
5. **Station Code**: From `raw_charge_job` part 2
6. **Machine Code**: From `raw_charge_job` part 3
7. **Expense Code**: From `raw_charge_job` part 4
8. **Hours Field**: `MainContent_txtHours`

## HTML Elements Targeted

### Transaction Type Radio Buttons
```html
<table id="MainContent_rblOT">
  <tr>
    <td>
      <input id="MainContent_rblOT_0" type="radio" name="ctl00$MainContent$rblOT" value="1">
      <label for="MainContent_rblOT_0">Normal</label>
    </td>
    <td>
      <input id="MainContent_rblOT_1" type="radio" name="ctl00$MainContent$rblOT" value="2">
      <label for="MainContent_rblOT_1">Overtime</label>
    </td>
  </tr>
</table>
```

### Hours Field
```html
<input name="ctl00$MainContent$txtHours" type="text" id="MainContent_txtHours" />
```

## Testing

### Demo Script
Run `demo_overtime_automation.py` to test the overtime functionality:

```bash
python demo_overtime_automation.py
```

### Test Cases Included

1. **Mixed Hours**: Regular 7.0h + Overtime 16.0h → 2 entries
2. **Normal Only**: Regular 8.0h + Overtime 0.0h → 1 entry  
3. **Overtime Only**: Regular 0.0h + Overtime 4.0h → 1 entry

## Logging

The system provides detailed logging for overtime processing:

```
✅ Created normal entry: 7.0 hours
✅ Created overtime entry: 16.0 hours
📊 Created 2 entries from 1 records
🔘 Selecting transaction type: Normal
✅ Normal transaction type selected
⏰ Filling hours field with: 7.0
✅ Hours field filled: 7.0
```

## Error Handling

The system includes comprehensive error handling:

- Invalid transaction types
- Missing form fields
- Stale element references
- JavaScript execution failures

## Performance Impact

- **Entry Creation**: Minimal overhead (memory copy operations)
- **Form Filling**: Additional steps for transaction type and hours
- **Overall Impact**: ~20% increase in processing time per record due to additional form interactions

## Future Enhancements

1. **Shift Type Selection**: Automatically select shift based on hours
2. **Validation Rules**: Enforce maximum overtime hours per day
3. **Batch Processing**: Optimize for multiple entries from same employee
4. **Custom Transaction Types**: Support for additional transaction types beyond Normal/Overtime

---

*Last Updated: June 11, 2025*
*Version: 1.0.0* 