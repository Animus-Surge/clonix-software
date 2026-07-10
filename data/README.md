# Data directory

Here lies test data for Clonix. This is where the example profiles and snippets will be stored.

## Profiles

This directory contains default profiles for how things are handled. Below is the layout of a profile:

```
{
    "label": <optional, str; default 'gpt'>,
    "partitions": [
        {
            "fstype": <str>,
            "start": <str>,
            "end": <str>,
            "flags": <optional, list[str]; default `[]`>,
            "mountpoint": <optional, str; default ''>,
            "label": <optional, str; default ''>,
            "encrypted": <optional, bool; default `false`>,
            "passphrase": <optional, str; default ''>
        },
        <...>
    ],
    "extra_fstab": [
        {
            "device": <str>,
            "mountpoint": <str>,
            "fstype": <str>,
            "mountopts": <list[str]>,
            "freq": <int>,
            "passno": <int>
        },
        <...>
    ]
}
```

### Fields

- `partitions`: The list of partitions on the drive
- `label`: Optional, defaults to `gpt`. Can be one of `gpt`, `msdos`. Represents the partition table.
- `extra_fstab`: Optional, defaults to `[]`. Additional entries to add to the end of `/target/etc/fstab`

#### Partitions - `partitions`

These objects represent a single partition to add to the device.

- `fstype`: The filesystem to format the partition as. See `supported filesystems` for more information.
- `start`: The start point of the partition to directly pass to `parted`
- `end`: The end point of the partition to directly pass to `parted`
- `flags`: Optional, defaults to `[]`. The flags to use in `parted`.
- `mountpoint`: Optional, defaults to `""`. The mountpoint of this partition.
- `label`: Optional, defaults to `""`. The filesystem label to set when formatting.
- `encrypted`: Optional, defaults to `false`. Whether or not to run `cryptsetup luksFormat` on this partition
- `passphrase`: Optional, defaults to `""`. The obfuscated passphrase to pass to `cryptsetup`.

#### Extra `fstab` entries - `extra_fstab`

These objects represent an extra entry to put into `/target/etc/fstab`. Each field name roughly
matches their names in the manpage.
