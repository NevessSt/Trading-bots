#!/usr/bin/env python3
"""
Machine ID Generator Tool

This tool generates a unique machine identifier for license binding.
Usage: python machine_id.py
"""

import hashlib
import json
import platform
import sys
import os

def get_system_info():
    """Collect system information for machine ID generation."""
    try:
        system_info = {
            'platform': platform.platform(),
            'processor': platform.processor(),
            'machine': platform.machine(),
            'node': platform.node(),
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version()
        }
        
        # Add additional identifiers if available
        try:
            import uuid
            system_info['mac_address'] = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                                                 for elements in range(0,2*6,2)][::-1])
        except:
            pass
            
        return system_info
    except Exception as e:
        print(f"Error collecting system info: {e}")
        return {}

def generate_machine_id(system_info=None):
    """Generate a unique machine identifier."""
    if system_info is None:
        system_info = get_system_info()
    
    # Create a consistent string representation
    info_string = json.dumps(system_info, sort_keys=True)
    
    # Generate hash
    machine_id = hashlib.sha256(info_string.encode()).hexdigest()[:16]
    return machine_id.upper()

def display_system_info():
    """Display system information used for machine ID."""
    print("=" * 50)
    print("SYSTEM INFORMATION")
    print("=" * 50)
    
    system_info = get_system_info()
    for key, value in system_info.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    
    print("\n" + "=" * 50)
    print("MACHINE ID")
    print("=" * 50)
    machine_id = generate_machine_id(system_info)
    print(f"Machine ID: {machine_id}")
    print("\nThis ID will be used for license binding.")
    print("Keep this ID secure and provide it when requesting a license.")
    
    return machine_id

def save_machine_id(output_file=None):
    """Save machine ID to a file."""
    if output_file is None:
        output_file = "machine_id.txt"
    
    machine_id = generate_machine_id()
    
    try:
        with open(output_file, 'w') as f:
            f.write(f"Machine ID: {machine_id}\n")
            f.write(f"Generated: {platform.node()} - {platform.platform()}\n")
            f.write(f"Timestamp: {json.dumps({'generated_at': str(platform.uname())}, indent=2)}\n")
        
        print(f"Machine ID saved to: {output_file}")
        return True
    except Exception as e:
        print(f"Error saving machine ID: {e}")
        return False

def main():
    """Main function for command line usage."""
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print(__doc__)
            print("\nOptions:")
            print("  -h, --help    Show this help message")
            print("  -s, --save    Save machine ID to file")
            print("  -q, --quiet   Only output machine ID")
            return
        elif sys.argv[1] in ['-s', '--save']:
            machine_id = display_system_info()
            save_machine_id()
            return
        elif sys.argv[1] in ['-q', '--quiet']:
            machine_id = generate_machine_id()
            print(machine_id)
            return
    
    # Default: display full information
    display_system_info()

if __name__ == "__main__":
    main()