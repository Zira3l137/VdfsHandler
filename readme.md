# VdfsHandler

VdfsHandler is a CLI utility written in Python for managing VDF (Virtual Disk Files) archives, primarily used in the Gothic game series. It allows you to view, extract, add, and remove files from VDF archives, as well as create new archives.

## Features

- **View VDF structure**: Print the tree structure of the VDF archive.
- **Extract files**: Extract specific files or directories from the VDF archive.
- **Add files**: Insert new files or directories into the VDF archive.
- **Remove files**: Delete specific files or directories from the VDF archive.
- **Save changes**: Save the modified VDF archive to a specified location.

![image](https://github.com/user-attachments/assets/7a3c4276-d9a5-4815-a26c-9e0ec8308f30)


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

### Command-line Arguments

- `archive_path` (required): Path to the VDF archive.
- `-g, --game-version <g1|g2>`:  Specifies the game version (Gothic 1 or Gothic 2). Defaults to `g2`.
- `-o, --output-path <path>`: Specifies the output directory for unpack/extract/save operations. Defaults to the current working directory.  If not provided when adding/removing files, the original archive is overwritten if it exists, otherwise a new VDF is created in the current directory.
- `-u, --unpack`: Unpack the entire VDF archive.
- `-e, --extract <file_or_directory>`: Extract a specific file or directory (wildcards `*` supported).
- `-a, --add <source_path> <destination_path>`: Add a file or directory to the VDF.
- `-r, --remove <file_or_directory>`: Remove a file or directory (wildcards `*` supported).
- `-v, --view-vfs`: View the VDF file system tree.
- `-d, --debug`: Enable debug logging.
- `-f, --full-debug`: Enable full ZenKit debug logging.
- `-t, --timestamp <DD.MM.YYYY HH:MM:SS>`: Set a custom timestamp for the output VDF.

### Examples

**Unpack an archive:**

```bash
python VdfsHandler.py my_archive.vdf -u -o extracted_files
```

**Extract a specific directory:**

```bash
python VdfsHandler.py my_archive.vdf -e DATA -o extracted_data
```

**Extract files matching a pattern:**

```bash
python VdfsHandler.py my_archive.vdf -e '*.mds' -o extracted_mds_files
```

**Add a file:**

```bash
python VdfsHandler.py my_archive.vdf -a my_file.txt DATA/MyFile.TXT -o modified_archive.vdf
```

**Add a directory:**

```bash
python VdfsHandler.py my_archive.vdf -a my_directory DATA/MyDirectory -o modified_archive.vdf
```

**Remove a file:**

```bash
python VdfsHandler.py my_archive.vdf -r MyFile.TXT  -o modified_archive.vdf
```

**View the VFS:**

```bash
python VdfsHandler.py my_archive.vdf -v
```

**Wildcards are case insensitive.**

### Debugging

To enable debugging, use the `-d` or `-debug` flag. For more detailed internal debugging related to the ZenKit library, use the `-f` or `-full_debug` flag.

```sh
python VdfsHandler.py /path/to/archive.vdf -d
python VdfsHandler.py /path/to/archive.vdf -f
```

## License

This project is licensed under the GNU General Public License v3.0 (see [GPLv3](https://www.gnu.org/licenses/gpl-3.0.html)).
*This tool was made by modders for modders, for free and forever.*

## Acknowledgments

[ZenKit](https://github.com/GothicKit/ZenKit4Py) for the library used in handling VDF files.

## Credits

- Big thanks to [Luis Michaelis](https://github.com/lmichaelis) for his work on the [ZenKit library](https://github.com/GothicKit/ZenKit4Py) and for his patience.
- Big thanks to [Damianut](https://github.com/damianut) for his help in debugging and testing the tool (and for his endless enthusiasm).
