#!/usr/bin/env python3
"""
Staging Data Server - Port 5173
Server terpisah untuk menyediakan staging data API di port 5173
"""

import json
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Sample staging data yang sesuai dengan format yang diharapkan
SAMPLE_STAGING_DATA = [
    {
        "check_in": "08:00",
        "check_out": "17:00",
        "created_at": "2025-06-10 04:43:03",
        "date": "2025-05-30",
        "day_of_week": "Sab",
        "employee_id": "PTRJ.241000001",
        "employee_name": "Ade Prasetya",
        "expense_code": "L (LABOUR)",
        "id": "c1e595b4-d498-4320-bce3-8d0f0cf52060",
        "machine_code": "BLR00000 (LABOUR COST)",
        "notes": "Transferred from Monthly Grid - May 2025",
        "overtime_hours": 0.0,
        "raw_charge_job": "(OC7190) BOILER OPERATION / STN-BLR (STATION BOILER) / BLR00000 (LABOUR COST) / L (LABOUR)",
        "regular_hours": 0.0,
        "shift": "Regular",
        "source_record_id": "",
        "station_code": "STN-BLR (STATION BOILER)",
        "status": "staged",
        "task_code": "(OC7190) BOILER OPERATION",
        "total_hours": 0.0,
        "transfer_status": "success",
        "updated_at": "2025-06-10 04:43:03"
    },
    {
        "check_in": "08:00",
        "check_out": "17:00",
        "created_at": "2025-06-10 04:43:03",
        "date": "2025-05-31",
        "day_of_week": "Min",
        "employee_id": "PTRJ.241000002",
        "employee_name": "Budi Santoso",
        "expense_code": "L (LABOUR)",
        "id": "d2f696c5-e599-5431-cdf4-9e1f1dg63171",
        "machine_code": "BLR00000 (LABOUR COST)",
        "notes": "Transferred from Monthly Grid - May 2025",
        "overtime_hours": 0.0,
        "raw_charge_job": "(OC7190) BOILER OPERATION / STN-BLR (STATION BOILER) / BLR00000 (LABOUR COST) / L (LABOUR)",
        "regular_hours": 8.0,
        "shift": "Regular",
        "source_record_id": "",
        "station_code": "STN-BLR (STATION BOILER)",
        "status": "staged",
        "task_code": "(OC7190) BOILER OPERATION",
        "total_hours": 8.0,
        "transfer_status": "success",
        "updated_at": "2025-06-10 04:43:03"
    },
    {
        "check_in": "08:00",
        "check_out": "17:00",
        "created_at": "2025-06-10 04:43:03",
        "date": "2025-06-01",
        "day_of_week": "Sen",
        "employee_id": "PTRJ.241000003",
        "employee_name": "Citra Dewi",
        "expense_code": "L (LABOUR)",
        "id": "e3g7a7d6-f6aa-6542-deg5-af2g2eh74282",
        "machine_code": "BLR00000 (LABOUR COST)",
        "notes": "Transferred from Monthly Grid - June 2025",
        "overtime_hours": 2.0,
        "raw_charge_job": "(OC7190) BOILER OPERATION / STN-BLR (STATION BOILER) / BLR00000 (LABOUR COST) / L (LABOUR)",
        "regular_hours": 8.0,
        "shift": "Regular",
        "source_record_id": "",
        "station_code": "STN-BLR (STATION BOILER)",
        "status": "staged",
        "task_code": "(OC7190) BOILER OPERATION",
        "total_hours": 10.0,
        "transfer_status": "success",
        "updated_at": "2025-06-10 04:43:03"
    }
]

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Staging Data Server is running',
        'timestamp': datetime.now().isoformat(),
        'port': 5173
    })

@app.route('/api/staging/data')
def get_staging_data():
    """Staging data endpoint - format yang sesuai dengan ekspektasi aplikasi"""
    try:
        # Filter berdasarkan parameter query jika ada
        employee_name = request.args.get('employee_name')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        status = request.args.get('status', 'staged')
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int, default=0)
        
        # Filter data berdasarkan parameter
        filtered_data = SAMPLE_STAGING_DATA.copy()
        
        if employee_name:
            filtered_data = [d for d in filtered_data if employee_name.lower() in d['employee_name'].lower()]
        
        if date_from:
            filtered_data = [d for d in filtered_data if d['date'] >= date_from]
            
        if date_to:
            filtered_data = [d for d in filtered_data if d['date'] <= date_to]
            
        if status:
            filtered_data = [d for d in filtered_data if d['status'] == status]
        
        # Apply pagination
        total_records = len(filtered_data)
        
        if limit:
            end_index = offset + limit
            filtered_data = filtered_data[offset:end_index]
        
        logger.info(f"Returning {len(filtered_data)} staging records (total: {total_records})")
        
        return jsonify({
            'success': True,
            'data': filtered_data,
            'total': total_records,
            'count': len(filtered_data),
            'offset': offset,
            'limit': limit
        })
        
    except Exception as e:
        logger.error(f"Error fetching staging data: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': [],
            'total': 0
        }), 500

@app.route('/api/staging/data-grouped')
def get_staging_data_grouped():
    """Get staging data in grouped format for desktop app"""
    try:
        # Group data by employee for the grouped endpoint
        grouped_data = []
        employees = {}
        
        # Group records by employee
        for record in SAMPLE_STAGING_DATA:
            emp_id = record.get('employee_id', '')
            if emp_id not in employees:
                employees[emp_id] = {
                    'identitas_karyawan': {
                        'employee_id_venus': record.get('employee_id', ''),
                        'employee_id_ptrj': record.get('employee_id', ''),
                        'employee_name': record.get('employee_name', ''),
                        'task_code': record.get('task_code', ''),
                        'station_code': record.get('station_code', ''),
                        'machine_code': record.get('machine_code', ''),
                        'expense_code': record.get('expense_code', ''),
                        'raw_charge_job': record.get('raw_charge_job', '')
                    },
                    'data_presensi': []
                }
            
            # Add attendance record
            employees[emp_id]['data_presensi'].append({
                'id': record.get('id', ''),
                'date': record.get('date', ''),
                'day_of_week': record.get('day_of_week', ''),
                'shift': record.get('shift', ''),
                'check_in': record.get('check_in', ''),
                'check_out': record.get('check_out', ''),
                'regular_hours': record.get('regular_hours', 0),
                'overtime_hours': record.get('overtime_hours', 0),
                'total_hours': record.get('total_hours', 0),
                'status': record.get('status', 'staged'),
                'created_at': record.get('created_at', ''),
                'updated_at': record.get('updated_at', '')
            })
        
        # Convert to list
        grouped_data = list(employees.values())
        
        response_data = {
            'success': True,
            'data': grouped_data,
            'total': len(grouped_data),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"📊 Returning grouped data: {len(grouped_data)} employee groups")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"❌ Error getting grouped staging data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/staging/stats')
def get_staging_stats():
    """Get staging data statistics"""
    try:
        total_records = len(SAMPLE_STAGING_DATA)
        processed = sum(1 for record in SAMPLE_STAGING_DATA if record.get('status') == 'processed')
        staged = sum(1 for record in SAMPLE_STAGING_DATA if record.get('status') == 'staged')
        failed = sum(1 for record in SAMPLE_STAGING_DATA if record.get('status') == 'failed')
        
        stats = {
            'total_records': total_records,
            'processed': processed,
            'staged': staged,
            'failed': failed,
            'last_updated': datetime.now().isoformat()
        }
        
        logger.info(f"📊 Returning stats: {stats}")
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"❌ Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def root():
    """Root endpoint"""
    return jsonify({
        'message': 'Staging Data Server',
        'version': '1.0.0',
        'endpoints': {
            'health': '/health',
            'staging_data': '/api/staging/data',
            'staging_stats': '/api/staging/stats'
        },
        'port': 5173
    })

if __name__ == '__main__':
    logger.info("🚀 Starting Staging Data Server on port 5173...")
    logger.info(f"📊 Loaded {len(SAMPLE_STAGING_DATA)} sample staging records")
    logger.info("🌐 Available endpoints:")
    logger.info("   - GET /health")
    logger.info("   - GET /api/staging/data")
    logger.info("   - GET /api/staging/data-grouped")
    logger.info("   - GET /api/staging/stats")
    logger.info("   - GET /")
    
    app.run(host='0.0.0.0', port=5173, debug=True)