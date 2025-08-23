# Attendance Report System - API Documentation

## Overview

This document provides comprehensive documentation for all API endpoints available in the Attendance Report System. The system provides both health monitoring endpoints and comprehensive staging data management capabilities.

## Base URL
```
http://localhost:5173
```

## Health and Status Endpoints

### Basic Health Check
```http
GET /health
```

**Description:** Basic health check endpoint for monitoring systems.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-13T20:00:00.000Z",
  "version": "1.0.0",
  "uptime": "running",
  "service": "attendance-report-system"
}
```

### Comprehensive API Health Check
```http
GET /api/health
```

**Description:** Comprehensive API health check with system status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-13T20:00:00.000Z",
  "version": "1.0.0",
  "components": {
    "database": {
      "status": "healthy",
      "current_mode": "local",
      "local_connected": true,
      "remote_connected": false
    },
    "staging_database": {
      "status": "healthy",
      "path": "data/staging_attendance.db"
    },
    "attendance_reporter": {
      "status": "healthy",
      "initialized": true
    }
  },
  "metrics": {
    "fallback_enabled": true
  }
}
```

### System Status
```http
GET /status
```

**Description:** Detailed system status endpoint.

**Response:**
```json
{
  "system": {
    "status": "operational",
    "timestamp": "2025-01-13T20:00:00.000Z",
    "version": "1.0.0",
    "environment": "production"
  },
  "database": {
    "connection_manager": {
      "current_mode": "local",
      "fallback_enabled": true
    },
    "connections": {
      "local": {
        "connected": true,
        "last_test": "2025-01-13T20:00:00.000Z"
      },
      "remote": {
        "connected": false,
        "last_test": "2025-01-13T20:00:00.000Z"
      }
    }
  },
  "staging": {
    "database_health": true,
    "statistics": {
      "total_attendance_records": 1500,
      "total_log_entries": 45,
      "unique_employees": 120
    }
  }
}
```

## Database Management Endpoints

### Get Database Status
```http
GET /api/database/status
```

**Description:** Retrieves current database connection status.

### Test Database Connection
```http
POST /api/database/test-connection
```

**Body:**
```json
{
  "mode": "local|remote|all",
  "config": {
    "server": "localhost",
    "database": "attendance_db",
    "username": "user",
    "password": "pass"
  }
}
```

### Switch Database Mode
```http
POST /api/database/switch-mode
```

**Body:**
```json
{
  "mode": "local|remote"
}
```

### Initial Database Scan
```http
POST /api/database/initial-scan
```

**Description:** Performs initial scan of both local and remote database connections.

## Staging Data Management Endpoints

### Staging Health Check
```http
GET /api/staging/health
```

**Description:** Get staging database health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-13T20:00:00.000Z",
  "database_accessible": true,
  "statistics": {
    "total_attendance_records": 1500,
    "total_log_entries": 45,
    "unique_employees": 120,
    "database_size_mb": 2.5
  }
}
```

### Get Staging Data
```http
GET /api/staging/data
```

**Query Parameters:**
- `limit` (int): Number of records to return (default: 100)
- `offset` (int): Number of records to skip (default: 0)
- `employee_id` (string): Filter by employee ID
- `status` (string): Filter by status
- `date_from` (string): Start date filter (YYYY-MM-DD)
- `date_to` (string): End date filter (YYYY-MM-DD)

**Response:**
```json
{
  "data": [
    {
      "id": "unique_id",
      "employee_id": "EMP001",
      "employee_name": "John Doe",
      "date": "2025-01-13",
      "check_in": "08:00:00",
      "check_out": "17:00:00",
      "total_hours": 8.0,
      "status": "staged"
    }
  ],
  "pagination": {
    "total": 1500,
    "limit": 100,
    "offset": 0,
    "has_more": true
  }
}
```

### Get Grouped Staging Data
```http
GET /api/staging/data-grouped
```

**Description:** Get staging data grouped by employee for optimized structure.

### Create Staging Record
```http
POST /api/staging/data
```

**Body:**
```json
{
  "employee_id": "EMP001",
  "employee_name": "John Doe",
  "date": "2025-01-13",
  "check_in": "08:00:00",
  "check_out": "17:00:00",
  "total_hours": 8.0,
  "status": "staged"
}
```

### Update Staging Record
```http
PUT /api/staging/data/{staging_id}
```

**Body:** Same as create staging record

### Delete Staging Record
```http
DELETE /api/staging/data/{staging_id}
```

### Upload Staging Data
```http
POST /api/staging/upload
```

**Content-Type:** `multipart/form-data`

**Form Data:**
- `file`: CSV file containing attendance data

### Get Staging Statistics
```http
GET /api/staging/stats
```

**Response:**
```json
{
  "total_records": 1500,
  "unique_employees": 120,
  "date_range": {
    "earliest": "2025-01-01",
    "latest": "2025-01-13"
  },
  "status_distribution": {
    "staged": 1200,
    "processed": 300
  }
}
```

### Delete All Staging Data
```http
DELETE /api/staging/delete-all
```

**Description:** Deletes all records from staging database.

### Get Staging Employees
```http
GET /api/staging/employees
```

**Description:** Get list of employees in staging data.

### Selective Copy to Production
```http
POST /api/staging/selective-copy
```

**Body:**
```json
{
  "employee_ids": ["EMP001", "EMP002"],
  "date_from": "2025-01-01",
  "date_to": "2025-01-13",
  "target_table": "production_attendance"
}
```

### Cleanup Duplicate Records
```http
POST /api/staging/cleanup-duplicates
```

**Description:** Removes duplicate records from staging database.

### Check for Duplicates
```http
GET /api/staging/check-duplicates
```

**Description:** Check for duplicate records without removing them.

### Test Staging Operations
```http
POST /api/staging/test
```

**Description:** Test staging database operations.

### Move Data to Staging
```http
POST /api/staging/move-to-staging
```

**Body:**
```json
{
  "source_table": "production_attendance",
  "date_from": "2025-01-01",
  "date_to": "2025-01-13",
  "employee_ids": ["EMP001", "EMP002"]
}
```

### Get Operations Log
```http
GET /api/staging/operations-log
```

**Query Parameters:**
- `limit` (int): Number of log entries to return (default: 50)
- `offset` (int): Number of entries to skip (default: 0)
- `operation_type` (string): Filter by operation type
- `status` (string): Filter by result status
- `hours_back` (int): Show operations from last N hours

**Response:**
```json
{
  "logs": [
    {
      "id": 1,
      "timestamp": "2025-01-13T20:00:00.000Z",
      "operation_type": "upload",
      "operation_details": "CSV file upload",
      "affected_record_ids": "1,2,3",
      "data_volume": 3,
      "result_status": "success",
      "error_details": null
    }
  ],
  "pagination": {
    "total": 45,
    "limit": 50,
    "offset": 0,
    "has_more": false
  }
}
```

### Get Staging Summary
```http
GET /api/staging/summary
```

**Description:** Get comprehensive staging area summary including health, statistics, and recent activity.

**Response:**
```json
{
  "health": {
    "status": "healthy",
    "database_accessible": true
  },
  "statistics": {
    "total_attendance_records": 1500,
    "total_log_entries": 45,
    "unique_employees": 120,
    "database_size_mb": 2.5
  },
  "recent_activity": {
    "operations_24h": [
      {
        "operation_type": "upload",
        "result_status": "success",
        "count": 5
      }
    ]
  },
  "data_distribution": {
    "status_counts": [
      {
        "status": "staged",
        "count": 1200
      },
      {
        "status": "processed",
        "count": 300
      }
    ]
  }
}
```

## Attendance Report Endpoints

### Get Attendance Data
```http
GET /api/attendance
```

**Query Parameters:**
- `year` (int): Year filter
- `month` (int): Month filter (1-12)
- `employee_id` (string): Filter by employee ID

### Get Employees List
```http
GET /api/employees
```

**Description:** Get list of all employees.

### Get Available Months
```http
GET /api/months
```

**Description:** Get list of available months with data.

### Get Monthly Summary
```http
GET /api/summary
```

**Query Parameters:**
- `year` (int): Year
- `month` (int): Month (1-12)
- `employee_id` (string): Employee ID

### Export Data
```http
GET /api/export
```

**Query Parameters:**
- `format` (string): Export format (csv, excel)
- `year` (int): Year
- `month` (int): Month
- `employee_id` (string): Employee ID

### Get Shift Information
```http
GET /api/shifts
```

**Description:** Get shift information and schedules.

### Get Monthly Report
```http
GET /api/monthly-report
```

**Query Parameters:**
- `year` (int): Year
- `month` (int): Month (1-12)

### Get Leave Data
```http
GET /api/leave-data
```

**Query Parameters:**
- `year` (int): Year
- `month` (int): Month
- `employee_id` (string): Employee ID

### Get Monthly Grid
```http
GET /api/monthly-grid
```

**Description:** Get monthly attendance data in grid format.

### Get Monthly Grid by Station
```http
GET /api/monthly-grid-by-station
```

**Description:** Get monthly attendance data grouped by station.

### Get Employee Charge Jobs
```http
GET /api/employee-charge-jobs
```

**Query Parameters:**
- `employee_id` (string): Employee ID
- `date` (string): Date (YYYY-MM-DD)

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "Invalid request parameters",
  "details": "Specific error message"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found",
  "details": "The requested resource was not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "details": "Specific error message"
}
```

### 503 Service Unavailable
```json
{
  "error": "Service unavailable",
  "details": "Database connection failed"
}
```

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

## Rate Limiting

No rate limiting is currently implemented.

## CORS

CORS is enabled for all origins in development mode.

## Notes

1. All timestamps are in ISO 8601 format
2. Date parameters should be in YYYY-MM-DD format
3. The system supports both local SQLite and remote SQL Server databases with automatic failover
4. Staging operations are logged for audit purposes
5. The system includes comprehensive health monitoring for production deployments

## Support

For technical support or questions about the API, please refer to the system logs or contact the development team.