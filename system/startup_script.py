# CloNIX system/startup_script.py
# Startup script generator
# Generates the script that runs on first boot

# action: function
MASTER_SCRIPT_PARTS = {
        "enable_puppet": enable_puppet,
        "install_nvidia_driver": install_nvidia_driver
}

# Generates the first_run.sh script; takes in a list of strings as an argument
def generate_script(parts):
    for part in parts:
        MASTER_SCRIPT_PARTS.get(part)()

def enable_puppet():
    pass

def install_nvidia_driver():
    pass


