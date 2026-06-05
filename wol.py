import socket
import re

def send_wol(mac_address: str, ip_address: str = '255.255.255.255', port: int = 9) -> None:
    """
    Sends a Wake-on-LAN (WOL) magic packet to the specified MAC address.
    
    :param mac_address: The target MAC address (e.g. '00:11:22:33:44:55' or '00-11-22-33-44-55')
    :param ip_address: The broadcast IP address (default '255.255.255.255')
    :param port: The target UDP port (default 9, sometimes 7)
    """
    # Remove common delimiters: colons, hyphens, spaces, and periods
    clean_mac = re.sub(r'[:\-\s.]', '', mac_address)
    
    # Verify length and hex format
    if len(clean_mac) != 12:
        raise ValueError(f"Invalid MAC address length: '{mac_address}' should be 12 hexadecimal characters.")
    
    try:
        # Check if the cleaned MAC contains only hexadecimal characters
        mac_bytes = bytes.fromhex(clean_mac)
    except ValueError as e:
        raise ValueError(f"Invalid characters in MAC address: '{mac_address}'. Must be hexadecimal.") from e
        
    # Magic Packet format:
    # 6 bytes of 0xFF followed by 16 repetitions of the 6-byte MAC address.
    # Total payload: 6 + (16 * 6) = 102 bytes.
    packet = b'\xff' * 6 + mac_bytes * 16
    
    # Send the magic packet as a UDP broadcast
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(packet, (ip_address, port))
