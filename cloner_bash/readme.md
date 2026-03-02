# cloner

### Old version; bash based

Linux deployment tools

## scripts

- `deploy`: Deploy a system
- `freeze`: Freeze a source filesystem to a compressed tarball (zstd)
- `activate_source.sh`: Mount a source partition (NOT DRIVE)
- `deactivate_source.sh`: Unmount what's mounted at `/source` (gets run as part of deploy)
- `deactivate_target.sh`: Unmount what's mounted at `/target` (gets run as part of deploy)

## Requirements

```
# apt install pv
```

## directories

- `config/`: Contains production and example configurations for extra packages (wip)
- `device/`: Configuration files for the live ssd systems

