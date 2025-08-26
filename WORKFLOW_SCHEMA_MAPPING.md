# Alur Kerja, Skema, dan Mapping Input Data

## Ringkasan Implementasi

Dokumen ini menjelaskan alur kerja, skema, dan mapping untuk penginputan setiap record data dalam sistem Enhanced User-Controlled Automation.

## Data Source

Sistem ini mengambil data langsung dari database SQLite `staging_attendance.db` yang berisi data presensi karyawan. Database ini diakses melalui `DatabaseManager` class yang menyediakan data yang sudah dikelompokkan berdasarkan employee_id.

### Database Structure

Data dari database SQLite memiliki struktur tabel `staging_attendance` sebagai berikut:

```sql
CREATE TABLE staging_attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT,
    employee_name TEXT,
    date TEXT,
    check_in TEXT,
    check_out TEXT,
    total_hours REAL,
    task_code TEXT,
    station_code TEXT,
    machine_code TEXT,
    expense_code TEXT,
    status TEXT DEFAULT 'staged',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_record_id TEXT,
    notes TEXT,
    raw_charge_job TEXT,
    leave_type_code TEXT,
    leave_type_description TEXT,
    leave_ref_number TEXT,
    is_alfa INTEGER DEFAULT 0,
    is_on_leave INTEGER DEFAULT 0,
    ptrj_employee_id TEXT
);
```

### Grouped Data Structure

Data yang dikelompokkan oleh `DatabaseManager.fetch_grouped_staging_data()` memiliki struktur:

```json
[
  {
    "employee_id": "PTRJ.250300212",
    "employee_name": "ALDI",
    "ptrj_employee_id": "POM00283",
    "data_presensi": [
      {
        "id": 1,
        "employee_id": "PTRJ.250300212",
        "employee_name": "ALDI",
        "date": "2025-08-14",
        "check_in": "07:08",
        "check_out": "18:02",
        "total_hours": 10.0,
        "task_code": "(OC7240) LABORATORY ANALYSIS",
        "station_code": null,
        "machine_code": null,
        "expense_code": null,
        "status": "staged",
        "ptrj_employee_id": "POM00283"
      }
    ]
  }
]
```

## Urutan Input Data

Sesuai dengan instruksi yang telah ditetapkan, urutan input data adalah sebagai berikut:

### 1. Document Date (Tanggal Dokumen)

**Implementasi:** `calculate_document_date_by_mode()`

**Logika berdasarkan mode:**
- **Mode Test:** Document date month disesuaikan dengan bulan dari Transaction Date
  - Menggunakan hari saat ini dengan bulan dan tahun dari Transaction Date
  - Menangani edge case jika hari saat ini tidak ada di bulan target (misal: 30 Februari)
- **Mode Real:** Document date harus sama dengan tanggal hari ini
  - Menggunakan tanggal lengkap hari ini (`datetime.now()`)

**Field Target:** `MainContent_txtDocDate`

**Format Output:** `dd/mm/yyyy`

### 2. Transaction Date (Tanggal Transaksi)

**Implementasi:** `calculate_transaction_date_by_mode()`

**Logika berdasarkan mode:**
- **Mode Test:** Tanggal presensi aktual dikurangi 1 bulan
- **Mode Real:** Tanggal presensi aktual (tanpa perubahan)

**Field Target:** `MainContent_txtTrxDate`

**Format Output:** `dd/mm/yyyy`

### 3. Employee Identification (Identifikasi Karyawan)

**Implementasi:** `smart_employee_autocomplete_input()`

**Prioritas Input:**
1. **PTRJ Employee ID** (Prioritas Utama)
   - Menggunakan `employee_id_ptrj` dari record data
   - Menambahkan prefix "POM" jika belum ada
   - Menggunakan fungsi `_try_employee_id_autocomplete_robust()`

2. **Employee Name** (Fallback)
   - Jika Employee ID tidak tersedia atau gagal
   - Menggunakan `employee_name` dari record data
   - Menggunakan fungsi `_try_employee_name_autocomplete_robust()`

**Field Target:** Autocomplete field pertama (`.ui-autocomplete-input`)

## Alur Kerja Lengkap

### Fungsi Utama: `process_single_record_enhanced()`

```
1. Ekstraksi data record:
   - employee_name
   - employee_id_ptrj
   - date_value (tanggal presensi)
   - transaction_type
   - raw_charge_job

2. Step 0: Fill Document Date
   - Hitung menggunakan calculate_document_date_by_mode()
   - Isi field MainContent_txtDocDate via JavaScript
   - Wait 1.5 detik

3. Step 1: Fill Transaction Date
   - Hitung menggunakan calculate_transaction_date_by_mode()
   - Isi field MainContent_txtTrxDate via JavaScript
   - Trigger ENTER key dan wait 2 detik

4. Step 2: Fill Employee Field
   - Gunakan smart_employee_autocomplete_input()
   - Prioritas: Employee ID PTRJ → Employee Name
   - Wait 2 detik setelah sukses

5. Step 3: Select Transaction Type
   - Gunakan processor.select_transaction_type()

6. Step 4: Fill Charge Job Components
   - Parse raw_charge_job
   - Gunakan fill_charge_job_smart_autocomplete()

7. Step 5: Fill Hours Field
   - Gunakan processor.fill_hours_field()

8. Step 6: Enhanced Button Click
   - Gunakan enhanced_button_click()
   - Logika berbeda untuk record terakhir
```

## Skema Data Record

### Input Data Structure
```json
{
  "employee_name": "string",
  "employee_id_ptrj": "string",
  "date_value": "string (dd/mm/yyyy atau yyyy-mm-dd)",
  "transaction_type": "string",
  "raw_charge_job": "string",
  "working_hours": "number"
}
```

### Field Mapping

| Data Field | Target UI Field | Processing Function | Priority |
|------------|----------------|-------------------|----------|
| `date_value` | `MainContent_txtDocDate` | `calculate_document_date_by_mode()` | 1 |
| `date_value` | `MainContent_txtTrxDate` | `calculate_transaction_date_by_mode()` | 2 |
| `employee_id_ptrj` | `.ui-autocomplete-input[0]` | `smart_employee_autocomplete_input()` | 3a |
| `employee_name` | `.ui-autocomplete-input[0]` | `smart_employee_autocomplete_input()` | 3b |
| `transaction_type` | Transaction Type Dropdown | `select_transaction_type()` | 4 |
| `raw_charge_job` | Charge Job Fields | `fill_charge_job_smart_autocomplete()` | 5 |
| `working_hours` | Hours Field | `fill_hours_field()` | 6 |

## Mode Operasi

### Testing Mode
- Document Date: Bulan sesuai Transaction Date, hari sesuai hari ini
- Transaction Date: Tanggal presensi - 1 bulan
- Digunakan untuk testing tanpa mempengaruhi data production

### Real Mode
- Document Date: Tanggal hari ini (lengkap)
- Transaction Date: Tanggal presensi aktual
- Digunakan untuk input data production

## Error Handling

### Employee Input
- Jika Employee ID PTRJ gagal → fallback ke Employee Name
- Jika kedua metode gagal → return False dan log error
- Robust error handling dengan retry mechanism

### Date Calculation
- Edge case handling untuk tanggal yang tidak valid
- Fallback ke tanggal saat ini jika terjadi error
- Logging detail untuk debugging

### Field Validation
- Driver responsiveness check
- Field validity verification
- Stale element recovery

## Logging dan Monitoring

- Automation step logging untuk setiap tahap
- Performance metrics untuk setiap operasi
- Driver state logging
- Element state logging
- Detailed error logging dengan context

## Kesimpulan

Implementasi ini memastikan:
1. ✅ Urutan input sesuai instruksi: Document Date → Transaction Date → Employee ID
2. ✅ Prioritas Employee ID PTRJ over Employee Name
3. ✅ Logika Document Date berbeda untuk mode test dan real
4. ✅ Transaction Date tetap menggunakan tanggal presensi aktual
5. ✅ Robust error handling dan logging
6. ✅ Komponen lainnya tetap mengikuti alur sebelumnya