# Millware Task Register Automation

## 🎯 Overview

Sistem otomasi untuk Task Register di Millware yang sudah diperbaiki dan terstruktur. Flow ini akan:

1. **Login otomatis** ke sistem Millware
2. **Input tanggal transaksi** di field `MainContent_txtTrxDate`
3. **Handle page reload** setelah input tanggal
4. **Input employee** dengan autocomplete
5. **Input activity** dengan autocomplete  
6. **Input labour** dengan autocomplete

## 🚀 Cara Penggunaan

### Quick Start
```bash
cd "Selenium Auto Fill"
python src/main.py
# Pilih option 1: AUTO RUN (Complete Login + Task Register)
```

### Test Script
```bash
python test_task_register.py
```

## ⚙️ Konfigurasi

### 1. Main Config (`config/app_config.json`)
```json
{
  "credentials": {
    "username": "adm075",
    "password": "adm075"
  },
  "urls": {
    "login": "http://millwarep3.rebinmas.com:8003/",
    "taskRegister": "http://millwarep3.rebinmas.com:8003/en/PR/trx/frmPrTrxTaskRegisterDet.aspx"
  }
}
```

### 2. Form Data (`config/form_data.json`)
```json
{
  "taskRegister": {
    "transactionDate": "03/06/2025",
    "employee": {
      "name": "Septian Pratama"
    },
    "activity": {
      "code": "(OC7240) LABORATORY ANALYSIS"
    },
    "labour": {
      "code": "LAB00000 (LABOUR COST)"
    }
  }
}
```

## 📋 Flow Sequence

### Pre-Login Flow (`flows/pre_login_flow.json`)
1. Navigate to Millware login page
2. Input username (`adm075`)
3. Input password (`adm075`)
4. Click login button
5. Handle location setting popup
6. Navigate to Task Register page

### Post-Login Flow (`flows/post_login_flow.json`)
1. **Wait for date field** (`#MainContent_txtTrxDate`)
2. **Input transaction date** (`03/06/2025`)
3. **Unfocus field** (trigger page reload)
4. **Wait for page reload** (5 seconds)
5. **Wait for autocomplete fields** to be ready
6. **Input employee name** (`Septian Pratama`)
7. **Trigger autocomplete** with Space key
8. **Select employee** with ArrowDown + Enter
9. **Input activity code** (`(OC7240) LABORATORY ANALYSIS`)
10. **Select activity** with ArrowDown + Enter
11. **Input labour code** (`LAB00000 (LABOUR COST)`)
12. **Select labour** with ArrowDown + Enter

## 🔧 Selectors Yang Digunakan

### Date Field
```css
#MainContent_txtTrxDate, input[name='ctl00$MainContent$txtTrxDate']
```

### Autocomplete Fields
```css
input.ui-autocomplete-input.ui-widget.CBOBox, input[class*='ui-autocomplete-input']
```

### Autocomplete Dropdown
```css
.ui-autocomplete.ui-widget.ui-widget-content.ui-corner-all:not([style*='display: none'])
```

## 🛠️ Customization

### Mengubah Data Input
Edit file `config/form_data.json`:

```json
{
  "taskRegister": {
    "transactionDate": "04/06/2025",  // Ubah tanggal
    "employee": {
      "name": "Nama Employee Lain"    // Ubah nama employee
    },
    "activity": {
      "code": "(CODE123) ACTIVITY BARU"  // Ubah activity
    },
    "labour": {
      "code": "LAB123 (LABOUR BARU)"     // Ubah labour
    }
  }
}
```

### Mengubah Timing
Edit `timings` section di `form_data.json`:

```json
{
  "timings": {
    "pageLoadWait": 5000,      // Wait setelah reload
    "autocompleteWait": 2000,  // Wait untuk autocomplete
    "dropdownWait": 1500,      // Wait untuk dropdown
    "selectionWait": 2000,     // Wait setelah selection
    "formStabilizeWait": 3000  // Wait final form
  }
}
```

## 🚨 Troubleshooting

### Element Not Found
- Pastikan halaman sudah fully loaded
- Check selector di `config/form_data.json`
- Increase timeout di flow file

### Autocomplete Tidak Muncul
- Pastikan field sudah focused
- Coba ganti trigger key (Space/Tab/ArrowDown)
- Check timing wait

### Page Reload Issues
- Pastikan unfocus dari date field
- Wait cukup lama setelah reload
- Check network connection

## 📊 Status Flow

### ✅ Yang Sudah Berfungsi
- ✅ Login otomatis ke Millware
- ✅ Popup handling setelah login  
- ✅ Navigasi ke Task Register
- ✅ Input tanggal dengan selector yang benar
- ✅ Struktur flow yang terpisah dan modular

### 🔄 Yang Perlu Ditest
- 🔄 Page reload setelah input tanggal
- 🔄 Autocomplete employee interaction
- 🔄 Autocomplete activity interaction  
- 🔄 Autocomplete labour interaction

## 📞 Support

Jika mengalami masalah:

1. **Check browser console** untuk error JavaScript
2. **Lihat log file** `selenium_autofill.log`
3. **Test manual** di browser untuk verify selector
4. **Adjust timing** jika halaman load lambat

## 🔄 Updates

**Version 2.0.0**
- ✨ Restructured flow dengan date input pertama
- ✨ Modular configuration dengan `form_data.json`
- ✨ Better selector targeting
- ✨ Improved page reload handling 