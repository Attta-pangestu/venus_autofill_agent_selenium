#!/usr/bin/env python3
"""
Database Structure Analyzer for staging_attendance.db
Analyzes the structure and content of the staging database
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

class DatabaseStructureAnalyzer:
    """
    Analyzes SQLite database structure and provides detailed information
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.analysis_results = {}
        
    def analyze_database(self) -> Dict[str, Any]:
        """
        Perform comprehensive database analysis
        """
        try:
            if not os.path.exists(self.db_path):
                return {"error": f"Database file not found: {self.db_path}"}
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get database info
                self.analysis_results = {
                    "database_path": self.db_path,
                    "file_size_mb": round(os.path.getsize(self.db_path) / (1024 * 1024), 2),
                    "analysis_timestamp": datetime.now().isoformat(),
                    "tables": {},
                    "indexes": [],
                    "triggers": [],
                    "views": []
                }
                
                # Analyze tables
                self._analyze_tables(cursor)
                
                # Analyze indexes
                self._analyze_indexes(cursor)
                
                # Analyze triggers
                self._analyze_triggers(cursor)
                
                # Analyze views
                self._analyze_views(cursor)
                
                # Get sample data
                self._get_sample_data(cursor)
                
                return self.analysis_results
                
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    def _analyze_tables(self, cursor):
        """
        Analyze all tables in the database
        """
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table['name']
            if table_name.startswith('sqlite_'):
                continue  # Skip system tables
                
            self.analysis_results['tables'][table_name] = {
                'columns': [],
                'row_count': 0,
                'constraints': [],
                'sample_data': []
            }
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for col in columns:
                column_info = {
                    'name': col['name'],
                    'type': col['type'],
                    'not_null': bool(col['notnull']),
                    'default_value': col['dflt_value'],
                    'primary_key': bool(col['pk'])
                }
                self.analysis_results['tables'][table_name]['columns'].append(column_info)
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            row_count = cursor.fetchone()['count']
            self.analysis_results['tables'][table_name]['row_count'] = row_count
            
            # Get foreign keys
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            foreign_keys = cursor.fetchall()
            
            for fk in foreign_keys:
                constraint_info = {
                    'type': 'foreign_key',
                    'column': fk['from'],
                    'references_table': fk['table'],
                    'references_column': fk['to']
                }
                self.analysis_results['tables'][table_name]['constraints'].append(constraint_info)
    
    def _analyze_indexes(self, cursor):
        """
        Analyze database indexes
        """
        cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
        indexes = cursor.fetchall()
        
        for index in indexes:
            index_info = {
                'name': index['name'],
                'table': index['tbl_name'],
                'sql': index['sql']
            }
            self.analysis_results['indexes'].append(index_info)
    
    def _analyze_triggers(self, cursor):
        """
        Analyze database triggers
        """
        cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='trigger'")
        triggers = cursor.fetchall()
        
        for trigger in triggers:
            trigger_info = {
                'name': trigger['name'],
                'table': trigger['tbl_name'],
                'sql': trigger['sql']
            }
            self.analysis_results['triggers'].append(trigger_info)
    
    def _analyze_views(self, cursor):
        """
        Analyze database views
        """
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='view'")
        views = cursor.fetchall()
        
        for view in views:
            view_info = {
                'name': view['name'],
                'sql': view['sql']
            }
            self.analysis_results['views'].append(view_info)
    
    def _get_sample_data(self, cursor):
        """
        Get sample data from each table
        """
        for table_name in self.analysis_results['tables']:
            try:
                # Get first 5 rows as sample
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                rows = cursor.fetchall()
                
                sample_data = []
                for row in rows:
                    sample_data.append(dict(row))
                
                self.analysis_results['tables'][table_name]['sample_data'] = sample_data
                
            except Exception as e:
                self.analysis_results['tables'][table_name]['sample_data'] = f"Error: {str(e)}"
    
    def save_analysis_report(self, output_path: str = None):
        """
        Save analysis results to JSON file
        """
        if output_path is None:
            output_path = "database_analysis_report.json"
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_results, f, indent=4, ensure_ascii=False, default=str)
            
            print(f"✅ Analysis report saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save report: {e}")
            return False
    
    def print_summary(self):
        """
        Print a summary of the analysis
        """
        if 'error' in self.analysis_results:
            print(f"❌ Analysis Error: {self.analysis_results['error']}")
            return
        
        print("\n" + "="*60)
        print("📊 DATABASE STRUCTURE ANALYSIS SUMMARY")
        print("="*60)
        
        print(f"📁 Database: {self.analysis_results['database_path']}")
        print(f"📏 File Size: {self.analysis_results['file_size_mb']} MB")
        print(f"🕒 Analysis Time: {self.analysis_results['analysis_timestamp']}")
        
        print(f"\n📋 TABLES ({len(self.analysis_results['tables'])})")
        print("-" * 40)
        
        for table_name, table_info in self.analysis_results['tables'].items():
            print(f"\n🗂️  {table_name}")
            print(f"   📊 Rows: {table_info['row_count']:,}")
            print(f"   📝 Columns: {len(table_info['columns'])}")
            
            print("   📋 Column Details:")
            for col in table_info['columns']:
                pk_marker = " (PK)" if col['primary_key'] else ""
                null_marker = " NOT NULL" if col['not_null'] else ""
                default_marker = f" DEFAULT {col['default_value']}" if col['default_value'] else ""
                print(f"      • {col['name']}: {col['type']}{pk_marker}{null_marker}{default_marker}")
            
            if table_info['constraints']:
                print("   🔗 Constraints:")
                for constraint in table_info['constraints']:
                    if constraint['type'] == 'foreign_key':
                        print(f"      • FK: {constraint['column']} → {constraint['references_table']}.{constraint['references_column']}")
        
        if self.analysis_results['indexes']:
            print(f"\n🔍 INDEXES ({len(self.analysis_results['indexes'])})")
            print("-" * 40)
            for index in self.analysis_results['indexes']:
                print(f"   • {index['name']} on {index['table']}")
        
        if self.analysis_results['triggers']:
            print(f"\n⚡ TRIGGERS ({len(self.analysis_results['triggers'])})")
            print("-" * 40)
            for trigger in self.analysis_results['triggers']:
                print(f"   • {trigger['name']} on {trigger['table']}")
        
        if self.analysis_results['views']:
            print(f"\n👁️  VIEWS ({len(self.analysis_results['views'])})")
            print("-" * 40)
            for view in self.analysis_results['views']:
                print(f"   • {view['name']}")
        
        print("\n" + "="*60)

def main():
    """
    Main function to run the database analysis
    """
    # Database path
    db_path = r"D:\Gawean Rebinmas\Autofill Venus Millware\Selenium Auto Fill _Progress\Selenium Auto Fill\Selenium Auto Fill\data\staging_attendance.db"
    
    print("🔍 Starting Database Structure Analysis...")
    print(f"📁 Target Database: {db_path}")
    
    # Create analyzer
    analyzer = DatabaseStructureAnalyzer(db_path)
    
    # Perform analysis
    results = analyzer.analyze_database()
    
    # Print summary
    analyzer.print_summary()
    
    # Save detailed report
    report_path = "staging_database_analysis_report.json"
    analyzer.save_analysis_report(report_path)
    
    # Additional analysis for staging data compatibility
    print("\n" + "="*60)
    print("🔧 STAGING DATA COMPATIBILITY ANALYSIS")
    print("="*60)
    
    if 'error' not in results:
        analyze_staging_compatibility(results)
    
    print("\n✅ Analysis completed!")

def analyze_staging_compatibility(analysis_results):
    """
    Analyze compatibility with staging data requirements
    """
    tables = analysis_results.get('tables', {})
    
    # Check for staging_attendance table
    if 'staging_attendance' in tables:
        staging_table = tables['staging_attendance']
        print("\n✅ Found staging_attendance table")
        
        # Check required columns for Venus automation
        required_columns = [
            'id', 'employee_id', 'employee_name', 'date', 
            'check_in', 'check_out', 'total_hours', 'overtime_hours', 
            'status', 'created_at'
        ]
        
        existing_columns = [col['name'] for col in staging_table['columns']]
        
        print("\n📋 Column Compatibility Check:")
        for req_col in required_columns:
            if req_col in existing_columns:
                print(f"   ✅ {req_col} - Found")
            else:
                print(f"   ❌ {req_col} - Missing")
        
        # Additional columns in database
        additional_cols = set(existing_columns) - set(required_columns)
        if additional_cols:
            print("\n📝 Additional columns found:")
            for col in additional_cols:
                print(f"   • {col}")
        
        # Data volume analysis
        row_count = staging_table['row_count']
        print(f"\n📊 Data Volume: {row_count:,} records")
        
        if row_count > 0:
            print("\n📋 Sample Data Structure:")
            sample_data = staging_table.get('sample_data', [])
            if sample_data and len(sample_data) > 0:
                first_record = sample_data[0]
                for key, value in first_record.items():
                    value_type = type(value).__name__
                    value_preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                    print(f"   • {key}: {value_preview} ({value_type})")
        
    else:
        print("\n❌ staging_attendance table not found")
        print("Available tables:")
        for table_name in tables.keys():
            print(f"   • {table_name}")
    
    # Check for operations_log table
    if 'operations_log' in tables:
        print("\n✅ Found operations_log table")
        ops_table = tables['operations_log']
        print(f"   📊 Log entries: {ops_table['row_count']:,}")
    else:
        print("\n⚠️  operations_log table not found (optional)")

if __name__ == "__main__":
    main()