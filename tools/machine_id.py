#!/usr/bin/env python3
"""
Machine ID generation for license binding
"""

import hashlib
import platform
import uuid
import os

def generate_machine_id():
    """Generate a unique machine identifier.
    
    Returns:
        str: Unique machine identifier
    """
    try:
        # Collect system information
        system_info = {
            'platform': platform.platform(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'system': platform.system(),
            'node': platform.node(),
        }
        
        # Try to get MAC address
        try:
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                           for elements in range(0,2*6,2)][::-1])
            system_info['mac'] = mac
        except:
            system_info['mac'] = 'unknown'
        
        # Try to get disk serial (Windows)
        try:
            if platform.system() == 'Windows':
                import subprocess
                result = subprocess.run(['wmic', 'diskdrive', 'get', 'serialnumber'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        serial = lines[1].strip()
                        if serial and serial != 'SerialNumber':
                            system_info['disk_serial'] = serial
        except:
            pass
        
        # Create a consistent string from system info
        info_string = '|'.join([f"{k}:{v}" for k, v in sorted(system_info.items())])
        
        # Generate SHA-256 hash
        machine_id = hashlib.sha256(info_string.encode()).hexdigest()[:32]
        
        return machine_id
        
    except Exception as e:
        # Fallback to a simple hash of available info
        fallback_info = f"{platform.system()}|{platform.machine()}|{uuid.getnode()}"
        return hashlib.sha256(fallback_info.encode()).hexdigest()[:32]

if __name__ == "__main__":
    print(f"Machine ID: {generate_machine_id()}")