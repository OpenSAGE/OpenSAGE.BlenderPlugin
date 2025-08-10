import os
import sys
import ctypes
import subprocess

def run_as_admin():
    """Run script with admin privileges"""
    if ctypes.windll.shell32.IsUserAnAdmin():
        return True
    
    # Re-run with admin privileges
    script = os.path.abspath(sys.argv[0])
    params = ' '.join([script] + sys.argv[1:])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    sys.exit()

def find_blender_addons_path():
    """Find Blender's addons directory"""
    username = os.getenv('USERNAME')
    if not username:
        print("Failed to get current username")
        return None
    
    # Try to locate Blender's addons path
    base_path = f"C:\\Users\\{username}\\AppData\\Roaming\\Blender Foundation\\Blender"
    if not os.path.exists(base_path):
        print(f"Blender config directory not found: {base_path}")
        return None
    
    # Find the latest Blender version
    versions = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
    if not versions:
        print("No Blender version directories found")
        return None
    
    # Sort versions and pick the newest
    versions.sort(reverse=True)
    latest_version = versions[0]
    
    addons_path = os.path.join(base_path, latest_version, "scripts", "addons")
    if not os.path.exists(addons_path):
        print(f"Addons directory not found: {addons_path}")
        return None
    
    return addons_path

def create_symbolic_link():
    """Create symbolic link with user confirmation"""
    # Get current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    source_folder = os.path.join(current_dir, "io_mesh_w3d")
    
    if not os.path.exists(source_folder):
        print(f"Source folder not found: {source_folder}")
        return False
    
    # Get Blender addons path
    addons_path = find_blender_addons_path()
    if not addons_path:
        return False
    
    target_path = os.path.join(addons_path, "io_mesh_w3d")
    
    # Check if target already exists
    if os.path.exists(target_path):
        print(f"Target path already exists: {target_path}")
        return False
    
    # Prepare command and display for confirmation
    cmd = f'mklink /D "{target_path}" "{source_folder}"'
    print("\nAbout to execute the following command:")
    print(f"  {cmd}\n")
    
    # Get user confirmation
    confirm = input("Do you want to proceed? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Operation cancelled by user")
        return False
    
    # Create symbolic link
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"\nSuccessfully created symbolic link: {target_path} -> {source_folder}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nFailed to create symbolic link: {e}")
        return False

if __name__ == "__main__":
    # Request admin privileges
    run_as_admin()
    
    # Execute main logic
    print("\nBlender Addon Symbolic Link Creator")
    print("----------------------------------")
    
    if create_symbolic_link():
        print("\nOperation completed successfully!")
    else:
        print("\nOperation failed")
    
    # Keep window open
    input("\nPress Enter to exit...")