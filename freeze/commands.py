# freeze/commands.py
# Command constants and run functions

import subprocess
import threading

import httpx
from loguru import logger

import util.gvars as gvars
from util import log_error

TAR_EXCLUDES = [
        "dev/*",
        "proc/*",
        "run/*",
        "sys/*",
        "tmp/*",
        "home/*",
        "var/cache/apt/*",
        "var/log/journal/*",
        "etc/puppetlabs/puppet/ssl",
        "etc/ssh/ssh_host_*",
]

TAR_CMD = [
        "/bin/tar",
        "--create", "--file=-",
        "--absolute-names",
        "--preserve-permissions",
        "--sparse",
        "--xattrs", "--xattrs-include=*",
        "--acls",
        "--ignore-failed-read",
        "--directory", "{TEMPLATE:source}",
]
PV_CMD = [
        "/bin/pv", "-n", "-s", "{TEMPLATE:source_usage}",
]
PZSTD_CMD = [
        "/bin/pzstd",
        "-c",
]

def do_freeze(image_name: str, source_usage: float, destination: str, source: str = "/source", to_file = False):
    # Create local copies of the commands
    cmd_a = TAR_CMD
    cmd_b = PV_CMD
    cmd_c = PZSTD_CMD

    gvars.g_pv_freeze_progress = {
        "latest": 0,
        "history": []
    }


    # Progress update thread function
    def _update_progress(pv_pipe):
        buffer = ""
        while True:
            char = pv_pipe.read(1)
            if not char: break

            if char in ('\r', '\n'):
                if buffer.strip():
                    gvars.g_pv_freeze_progress["latest"] = buffer.strip()
                    gvars.g_pv_freeze_progress["history"].append(buffer.strip())
                buffer = ""
            else:
                buffer += char
    # End progress update thread function

    try:
        # Replace placeholders with actual data
        cmd_a[cmd_a.index("{TEMPLATE:source}")] = source
        cmd_b[cmd_b.index("{TEMPLATE:source_usage}")] = str(source_usage)

        # Local file handling
        file=None
        if to_file:
            file = open(destination, 'wb')

        # Start subprocesses
        proc_a = subprocess.Popen(cmd_a, stdout=subprocess.PIPE)
        proc_b = subprocess.Popen(cmd_b, stdin=proc_a.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        pv_thread = threading.Thread(target=_update_progress, args=(proc_b.stderr,), daemon=True)
        pv_thread.start()

        proc_c = subprocess.Popen(cmd_c, stdin=proc_b.stdout, stdout=file if to_file else subprocess.PIPE)

        if proc_a.stdout:
            proc_a.stdout.close()
        if proc_b.stdout:
            proc_b.stdout.close()
        
        # Local file
        # `destination` will be an absolute file path
        if to_file:
            proc_c.wait()
        
        # Store to file endpoint
        # `destination` will be a URL
        else:
            headers = {
                "Content-Type": "application/octet-stream"
            }

            with httpx.Client(timeout=None) as client: 
                response = client.post(destination, content=proc_c.stdout, headers=headers)
                response.raise_for_status()
            proc_c.wait()

        # Cleanups
        proc_b.wait()
        proc_a.wait()

        pv_thread.join()

        # Handle any subprocess errors
        for proc in (proc_a, proc_b, proc_c):
            if proc.returncode != 0:
                raise subprocess.CalledProcessError(proc.returncode, proc.args)

        logger.success("Freeze complete.")
        return True

    except subprocess.CalledProcessError as e:
        log_error(e, "One or more subprocesses failed.")

    except httpx.HTTPStatusError as e:
        log_error(e, f"Error while trying to write to {destination}")

    except IndexError as e:
        log_error(e, "Could not find placeholders. Cannot complete required commands.")

    return False
