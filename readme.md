# VdfsHandler

VdfsHandler is a CLI utility written in Python for managing VDF (Virtual Disk Files) archives, primarily used in the Gothic game series. It allows you to view, extract, add, and remove files from VDF archives, as well as create new archives. This version represents a complete rewrite of the original `VdfsHandler.py` functionality, now split into `Vdf.py` (core VDF manipulation) and `Cli.py` (command-line interface).

## Features

- **View VDF structure**: Print the tree structure of the VDF archive.
- **Extract files**: Extract specific files or directories from the VDF archive, with wildcard support.
- **Add files**: Insert new files or directories into the VDF archive, with wildcard support.
- **Remove files**: Delete specific files or directories from the VDF archive, with wildcard support.
- **Create new archives**: Generate new VDF archives.
- **Unpack archives**: Extract all files from a VDF archive into a directory structure.
- **Set game version**: Specify the game version (Gothic 1 or Gothic 2) for compatibility.
- **Set timestamp**: Set the creation date of the VDF archive.

## Requirements

- Python 3.7 or higher
- [ZenKit 1.3.0.1](https://github.com/GothicKit/ZenKit4Py) or higher

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/Zira3l137/VdfsHandler
    cd vdfshandler
    ```

2. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Usage


The command-line interface is now managed through `Cli.py`.  Here are the available options:

```
usage: cli.py [-h] [-i PATH_TO_VDF] [-n PATH_TO_NEW_VDF] [-o OUTPUT_PATH]
              [-gv INT 0 or 1] [-t %d.%m.%Y %H:%M:%S]
              [-e PATH_TO_ASSET_INSIDE_VDF] [-u] [-r PATH_TO_ASSET_INSIDE_VDF]
              [-a [PATH_TO_LOCAL_FILE_OR_DIRECTORY PATH_TO_ASSET_IN_VDF ...]]
              [-l] [-d]

options:
  -h, --help            show this help message and exit
  -i PATH_TO_VDF, --input PATH_TO_VDF
                        The path to the VDF archive
  -n PATH_TO_NEW_VDF, --new PATH_TO_NEW_VDF
                        The path to the new VDF archive that will be created
  -o OUTPUT_PATH, --output OUTPUT_PATH
                        The output path to save asset from VDF or VDF archive
                        itself
  -gv INT 0 or 1, --game-version INT 0 or 1
                        The game version of the saved VDF file, 0 for Gothic 1
                        and 1 for Gothic 2
  -t %d.%m.%Y %H:%M:%S, --timestamp %d.%m.%Y %H:%M:%S
                        The creation date of the VDF file in the format
                        %d.%m.%Y %H:%M:%S
  -e PATH_TO_ASSET_INSIDE_VDF, --extract PATH_TO_ASSET_INSIDE_VDF
                        The path to the asset to extract from VDF archive, used
                        with --output, wildcards are supported.Example:
                        `textures/ui/hud/healthbar_*`
  -u, --unpack         The path to the archive to unpack, used with --output
  -r PATH_TO_ASSET_INSIDE_VDF, --remove PATH_TO_ASSET_INSIDE_VDF
                        The name of the asset to remove from VDF archive,
                        wildcards are supported. Example:
                        `path/to/assets/in/vdf/OLDMINE_*`
  -a [PATH_TO_LOCAL_FILE_OR_DIRECTORY PATH_TO_ASSET_IN_VDF ...], --add [PATH_TO_LOCAL_FILE_OR_DIRECTORY PATH_TO_ASSET_IN_VDF ...]
                        The path to the asset to add to VDF archive and its
                        paht inside VDF archive, used with --output, wildcards
                        are supported. Example:
                        `path/to/local/files/*.tga`
  -l, --list           List all assets in the VDF archive
  -d, --debug          Display debug information
```

### Examples


**Create a new VDF:**

```bash
python Cli.py -n my_new_archive.vdf -o /path/to/output/
```

**Create a new VDF and add files to it in one go:**

```bash
python Cli.py -n my_new_archive.vdf -a "path/to/local/files/*.mrm" meshes/ -o new_archive.vdf
```

**Add files to an existing VDF:**

```bash
python Cli.py -i my_archive.vdf -a "path/to/local/files/*.tga" textures/ -o updated_archive.vdf
```

**Extract files with wildcards:**

```bash
python Cli.py -i my_archive.vdf -e "textures/*.tex" -o extracted_textures/
```

**Remove files with wildcards:**

```bash
python Cli.py -i my_archive.vdf -r "old_assets/ADDON_*" -o cleaned_archive.vdf
```

**Unpack a VDF:**

```bash
python Cli.py -i my_archive.vdf -u -o unpacked_archive/
```

**List contents of a VDF:**

```bash
python Cli.py -i my_archive.vdf -l
```



## License

This project is licensed under the GNU General Public License v3.0 (see [GPLv3](https://www.gnu.org/licenses/gpl-3.0.html)).
*This tool was made by modders for modders, for free and forever.*

## Acknowledgments

[ZenKit](https://github.com/GothicKit/ZenKit4Py) for the library used in handling VDF files.

## Credits

- Big thanks to [Luis Michaelis](https://github.com/lmichaelis) for his work on the [ZenKit library](https://github.com/GothicKit/ZenKit4Py) and for his patience.
- Big thanks to [Damianut](https://github.com/damianut) for his help in debugging and testing the tool (and for his endless enthusiasm).
