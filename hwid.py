import sys
import uuid
import hashlib
import subprocess
import json
import wmi

def get_system_info():
    """Collect system information to generate a unique HWID"""
    try:
        c = wmi.WMI()
        
        # Get CPU information
        cpu_info = c.Win32_Processor()[0]
        processor_id = cpu_info.ProcessorId.strip() if cpu_info.ProcessorId else ""
        
        # Get motherboard serial
        board = c.Win32_BaseBoard()[0]
        board_serial = board.SerialNumber.strip() if board.SerialNumber else ""
        
        # Get primary disk serial
        disk = c.Win32_DiskDrive()[0]
        disk_serial = disk.SerialNumber.strip() if disk.SerialNumber else ""
        
        # Get BIOS serial
        bios = c.Win32_BIOS()[0]
        bios_serial = bios.SerialNumber.strip() if bios.SerialNumber else ""
        
        # Combine all identifiers
        system_id = f"{processor_id}:{board_serial}:{disk_serial}:{bios_serial}"
        
        return system_id
    except Exception as e:
        print(f"Error collecting system info: {e}")
        # Fallback to MAC address if WMI fails
        return str(uuid.getnode())

def generate_hwid():
    """Generate a unique hardware ID based on system components"""
    system_id = get_system_info()
    
    # Create SHA-256 hash of the system ID
    hwid = hashlib.sha256(system_id.encode()).hexdigest()
    
    # Format HWID in groups for better readability
    formatted_hwid = '-'.join(hwid[i:i+6] for i in range(0, len(hwid), 6))
    
    return formatted_hwid

if __name__ == "__main__":
    hwid = generate_hwid()
    print(f"Your system's HWID: {hwid}")