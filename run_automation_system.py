#!/usr/bin/env python3
"""
Automated Data Entry System - Main Startup Script
Runs both the data interface web application and automation service
"""

import os
import sys
import json
import logging
import argparse
import subprocess
import threading
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('automation_system.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_config():
    """Load configuration from config files"""
    config_dir = Path(__file__).parent / "config"
    
    # Default configuration
    default_config = {
        "browser": {
            "headless": False,
            "window_size": [1280, 720],
            "disable_notifications": True,
            "event_delay": 0.5
        },
        "automation": {
            "implicit_wait": 10,
            "page_load_timeout": 30,
            "script_timeout": 30,
            "max_retries": 3
        },
        "credentials": {
            "username": "adm075",
            "password": "adm075"
        },
        "urls": {
            "login": "http://millwarep3:8004/",
            "taskRegister": "http://millwarep3:8004/en/PR/trx/frmPrTrxTaskRegisterDet.aspx"
        },
        "api": {
            "staging_data_url": "http://localhost:5173/api/staging/data"
        },
        "web_interface": {
            "host": "0.0.0.0",
            "port": 5000,
            "debug": False
        }
    }
    
    # Load user configuration if exists
    config_file = config_dir / "app_config.json"
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                # Deep merge configurations
                for key, value in user_config.items():
                    if isinstance(value, dict) and key in default_config:
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
        except Exception as e:
            print(f"Error loading config file: {e}, using defaults")
    
    return default_config

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'selenium',
        'webdriver-manager',
        'flask',
        'flask-cors',
        'requests',
        'pandas'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nPlease install missing packages using:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def run_web_interface(config):
    """Run the Flask web interface"""
    try:
        from data_interface.app import app
        
        web_config = config.get('web_interface', {})
        host = web_config.get('host', '0.0.0.0')
        port = web_config.get('port', 5000)
        debug = web_config.get('debug', False)
        
        print(f"🌐 Starting web interface on http://{host}:{port}")
        
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True,
            use_reloader=False  # Disable reloader to avoid issues with threading
        )
        
    except Exception as e:
        print(f"❌ Failed to start web interface: {e}")
        raise

def run_automation_service(config):
    """Initialize the enhanced automation service with persistent browser"""
    try:
        from automation_service import get_automation_service
        
        print("🤖 Initializing enhanced automation service...")
        print("⚡ Pre-initializing WebDriver and browser session for optimal performance...")
        
        automation_service = get_automation_service(config)
        
        print("✅ Enhanced automation service initialized successfully")
        print("🚀 WebDriver will be pre-initialized in background for instant automation!")
        
        # Keep the service running
        while True:
            time.sleep(10)
            # Cleanup old jobs periodically
            automation_service.cleanup_old_jobs()
            
            # Log engine status every few minutes
            engine_status = automation_service.get_engine_status()
            if not engine_status['initialized']:
                print("⚠️ Warning: Automation engine not yet ready")
            
    except Exception as e:
        print(f"❌ Failed to initialize automation service: {e}")
        raise

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Automated Data Entry System')
    parser.add_argument('--mode', choices=['web', 'automation', 'both'], default='both',
                       help='Run mode: web interface only, automation only, or both')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🚀 AUTOMATED DATA ENTRY SYSTEM")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Load configuration
    config = load_config()
    
    # Apply command line overrides
    if args.headless:
        config['browser']['headless'] = True
    if args.debug:
        config['web_interface']['debug'] = True
    
    logger.info("Configuration loaded successfully")
    
    try:
        if args.mode == 'web':
            # Run only web interface
            print("🌐 Starting web interface only...")
            run_web_interface(config)
            
        elif args.mode == 'automation':
            # Run only automation service
            print("🤖 Starting automation service only...")
            run_automation_service(config)
            
        else:
            # Run both (default)
            print("🔄 Starting both web interface and automation service...")
            
            # Start automation service in background thread
            automation_thread = threading.Thread(
                target=run_automation_service,
                args=(config,),
                daemon=True
            )
            automation_thread.start()
            
            # Give automation service time to initialize
            time.sleep(2)
            
            # Start web interface (this will block)
            run_web_interface(config)
    
    except KeyboardInterrupt:
        print("\n🛑 System interrupted by user")
        logger.info("System shutdown requested by user")
    except Exception as e:
        print(f"\n❌ System error: {e}")
        logger.error(f"System error: {e}")
        sys.exit(1)
    finally:
        # Clean up automation service resources
        try:
            from automation_service import cleanup_automation_service
            print("🧹 Cleaning up automation service...")
            cleanup_automation_service()
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")
        
        print("🔚 System shutdown complete")
        logger.info("System shutdown complete")

def create_sample_config():
    """Create sample configuration files"""
    config_dir = Path(__file__).parent / "config"
    config_dir.mkdir(exist_ok=True)
    
    # Create app_config.json
    app_config_file = config_dir / "app_config.json"
    if not app_config_file.exists():
        sample_config = {
            "browser": {
                "headless": False,
                "window_size": [1280, 720],
                "disable_notifications": True,
                "event_delay": 0.5
            },
            "automation": {
                "implicit_wait": 10,
                "page_load_timeout": 30,
                "script_timeout": 30,
                "max_retries": 3
            },
            "credentials": {
                "username": "adm075",
                "password": "adm075"
            },
            "urls": {
                "login": "http://millwarep3:8004/",
                "taskRegister": "http://millwarep3:8004/en/PR/trx/frmPrTrxTaskRegisterDet.aspx"
            },
            "api": {
                "staging_data_url": "http://localhost:5173/api/staging/data"
            },
            "web_interface": {
                "host": "0.0.0.0",
                "port": 5000,
                "debug": False
            }
        }
        
        with open(app_config_file, 'w', encoding='utf-8') as f:
            json.dump(sample_config, f, indent=2)
        
        print(f"📝 Created sample configuration: {app_config_file}")

def show_usage():
    """Show usage examples"""
    print("\n📖 USAGE EXAMPLES:")
    print("=" * 30)
    print("# Run complete system (web interface + automation)")
    print("python run_automation_system.py")
    print()
    print("# Run only web interface")
    print("python run_automation_system.py --mode web")
    print()
    print("# Run only automation service")
    print("python run_automation_system.py --mode automation")
    print()
    print("# Run in headless mode (no browser window)")
    print("python run_automation_system.py --headless")
    print()
    print("# Run with debug enabled")
    print("python run_automation_system.py --debug")
    print()
    print("🌐 Web Interface: http://localhost:5000")
    print("📊 API Endpoints:")
    print("   - GET  /api/staging-data")
    print("   - POST /api/process-selected")
    print("   - GET  /api/job-status/<job_id>")
    print("   - GET  /api/current-job")

if __name__ == "__main__":
    # Create sample config if it doesn't exist
    create_sample_config()
    
    # Show usage if no arguments
    if len(sys.argv) == 1:
        show_usage()
        print("\nPress Enter to start the system, or Ctrl+C to exit...")
        try:
            input()
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)
    
    main()
