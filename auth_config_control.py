#!/usr/bin/env python3
"""
Centralized Authentication Configuration Control Script

This script allows easy control of the entire authentication system.
Run this script to modify authentication behavior across the entire platform.

Usage:
    python auth_config_control.py --debug on
    python auth_config_control.py --session-validation off
    python auth_config_control.py --jwt-tokens off
    python auth_config_control.py --help
"""

import os
import sys
import argparse

# Add the current directory to Python path so we can import from utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.auth_manager import (
    set_auth_debug, 
    set_session_validation, 
    set_jwt_tokens, 
    set_session_duration, 
    set_jwt_expiry,
    AuthConfig
)

def show_current_config():
    """Display current authentication configuration"""
    print("=== Current Authentication Configuration ===")
    print(f"JWT Tokens Enabled: {AuthConfig.ENABLE_JWT_TOKENS}")
    print(f"Session Validation: {AuthConfig.REQUIRE_SESSION_VALIDATION}")
    print(f"Debug Logging: {AuthConfig.ENABLE_DEBUG_LOGGING}")
    print(f"Session Duration: {AuthConfig.SESSION_DURATION_HOURS} hours")
    print(f"JWT Expiry: {AuthConfig.JWT_EXPIRY_HOURS} hours")
    print(f"JWT Algorithm: {AuthConfig.JWT_ALGORITHM}")
    print("===============================================")

def main():
    parser = argparse.ArgumentParser(description="Control centralized authentication system")
    parser.add_argument("--debug", choices=["on", "off"], help="Enable/disable debug logging")
    parser.add_argument("--session-validation", choices=["on", "off"], help="Enable/disable session validation")
    parser.add_argument("--jwt-tokens", choices=["on", "off"], help="Enable/disable JWT token system")
    parser.add_argument("--session-duration", type=int, metavar="HOURS", help="Set session duration in hours")
    parser.add_argument("--jwt-expiry", type=int, metavar="HOURS", help="Set JWT expiry in hours")
    parser.add_argument("--show-config", action="store_true", help="Show current configuration")
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        # No arguments provided, show current config
        show_current_config()
        return
    
    # Apply configuration changes
    if args.debug:
        set_auth_debug(args.debug == "on")
        print(f"Debug logging: {'ENABLED' if args.debug == 'on' else 'DISABLED'}")
        
    if args.session_validation:
        set_session_validation(args.session_validation == "on")
        print(f"Session validation: {'ENABLED' if args.session_validation == 'on' else 'DISABLED'}")
        
    if args.jwt_tokens:
        set_jwt_tokens(args.jwt_tokens == "on")
        print(f"JWT tokens: {'ENABLED' if args.jwt_tokens == 'on' else 'DISABLED'}")
        
    if args.session_duration:
        set_session_duration(args.session_duration)
        print(f"Session duration set to: {args.session_duration} hours")
        
    if args.jwt_expiry:
        set_jwt_expiry(args.jwt_expiry)
        print(f"JWT expiry set to: {args.jwt_expiry} hours")
        
    if args.show_config:
        show_current_config()

if __name__ == "__main__":
    main()