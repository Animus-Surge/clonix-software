# Scripts for `additional options` section

# Could be changed depending on the base image selected

options = {
        "Run puppet on boot": puppet_enable,
        "Install nvidia driver": nvidia_driver_install,
}

def get_options():
    return options

def puppet_enable():
    pass

def nvidia_driver_install():
    pass
