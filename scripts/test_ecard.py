"""Test script for ECard electricity fee retrieval."""
import sys
from loguru import logger
from zzupy.app import CASClient, ECardClient

# Remove default logger and add custom one
logger.remove()
logger.add(sys.stderr, level="TRACE")
logger.enable("zzupy")

# Credentials from password.h
ACCOUNT = "202407010202"
PASSWORD = "sNmcc$0506"

def main():
    """Main test function."""
    print(f"Testing ZZU.Py ECard electricity fee retrieval...")
    print(f"Account: {ACCOUNT}")
    
    try:
        # Create CAS client
        cas = CASClient(ACCOUNT, PASSWORD)
        print("Logging in to CAS...")
        cas.login()
        print("CAS login successful!")
        
        # Create ECard client
        with ECardClient(cas) as ecard:
            print("Logging in to ECard system...")
            ecard.login()
            print("ECard login successful!")
            
            # Get default room
            print("Getting default room...")
            room = ecard.get_default_room()
            print(f"Default room: {room}")
            
            # Get remaining energy (electricity)
            print("Getting remaining energy...")
            energy = ecard.get_remaining_energy()
            print(f"Remaining energy: {energy} degrees")
            
            # Also get balance
            print("Getting card balance...")
            balance = ecard.get_balance()
            print(f"Card balance: {balance} yuan")
            
            return True
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)