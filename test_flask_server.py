#!/usr/bin/env python3
"""
Simple Flask server for testing desktop app browser initialization
"""

import asyncio
import json
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Mock automation service for testing
class MockAutomationService:
    def __init__(self):
        self.browser_initialized = False
        
    async def initialize_browser(self):
        """Mock browser initialization"""
        logger.info("🚀 Mock browser initialization started...")
        
        # Simulate initialization time
        await asyncio.sleep(2)
        
        self.browser_initialized = True
        logger.info("✅ Mock browser initialization completed")
        
        return {
            'success': True,
            'message': 'Browser initialized and logged in successfully (MOCK)',
            'status': 'ready'
        }
    
    def is_automation_running(self):
        return False
    
    def start_automation_job(self, selected_ids):
        return "mock-job-123"

# Initialize mock service
mock_service = MockAutomationService()

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Test Flask server is running',
        'timestamp': '2025-01-09T10:00:00'
    })

@app.route('/api/health')
def api_health_check():
    """API Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Test Flask API is running',
        'timestamp': '2025-01-09T10:00:00'
    })

@app.route('/api/initialize-browser', methods=['POST'])
def initialize_browser():
    """Initialize browser endpoint for testing"""
    try:
        logger.info("🚀 Browser initialization requested from desktop app")
        
        # Run the async initialization
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(mock_service.initialize_browser())
            return jsonify(result)
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"❌ Error in browser initialization endpoint: {e}")
        return jsonify({
            'success': False,
            'message': f'Browser initialization failed: {str(e)}',
            'status': 'error'
        }), 500

@app.route('/api/staging-data')
def get_staging_data():
    """Mock staging data endpoint"""
    return jsonify({
        'data': [
            {
                'id': 'test-001',
                'employee_name': 'Test Employee',
                'date': '2025-01-09',
                'hours': 8.0,
                'status': 'staged'
            }
        ],
        'total': 1
    })

@app.route('/api/process-selected', methods=['POST'])
def process_selected():
    """Mock process selected endpoint"""
    data = request.get_json()
    selected_ids = data.get('selected_ids', [])
    
    if not mock_service.browser_initialized:
        return jsonify({
            'error': 'Browser not initialized. Please initialize browser first.'
        }), 400
    
    return jsonify({
        'success': True,
        'message': f'Mock automation started for {len(selected_ids)} records',
        'automation_id': 'mock-job-123'
    })

if __name__ == '__main__':
    logger.info("Starting test Flask server for desktop app...")
    app.run(host='0.0.0.0', port=5000, debug=True)