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
- [ZenKit 1.2.3rc1](https://github.com/GothicKit/ZenKit4Py) or higher

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/Zira3l137/VdfsHandler
    cd vdfshandler
    ```

2. Install the required dependencies:
    ```sh
    pip install zenkit
    ```

## Usage

### Command-line Arguments

- `archive_path` (required): Path to the VDF archive.
- `-g1, --gothic1`: Set the game version to Gothic 1.
- `-o, --output_path`: Specify the output directory for extracted files.
- `-u, --unpack`: Unpack the entire VDF archive to the specified output directory.
- `-e, --extract`: Extract a specific file or directory from the VDF.
- `-a, --add`: Add a file or directory to the VDF.
- `-r, --remove`: Remove a file or directory from the VDF.
- `-v, --view_vfs_tree`: Print out the VDF tree structure.
- `-d, --debug`: Enable debug mode.
- `-f, --full_debug`: Enable full debug mode for ZenKit.

### Examples

1. **View VDF Tree Structure**:
    ```sh
    python VdfsHandler.py /path/to/archive.vdf -v
    ```

2. **Extract a File**:
    ```sh
    python VdfsHandler.py /path/to/archive.vdf -e filename -o /output/directory
    ```
      Wildcards with `*` symbol can be used in the filename argument.
    Example: `*HUM_HEAD` as filename will extract all files with `HUM_HEAD` in the filename.

3. **Add a File to the VDF**:
    ```sh
    python VdfsHandler.py /path/to/archive.vdf -a /path/to/file internal/path/in/vdf -o /output/directory/for/vdf/with/changes
    ```
      Wildcards with `*` symbol can be used instead of the path to the file.
    Example: `*ZOM` as a path to the file will add all files with `ZOM` in the filename into the archive to the specified internal path.

4. **Remove a File from the VDF**:
    ```sh
    python VdfsHandler.py /path/to/archive.vdf -r filename -o /output/directory
    ```
      Wildcards with `*` symbol can be used in the filename argument.
    Example: `*HUM_BODY` as filename will remove all files with `HUM_BODY` in the filename from the archive.

5. **Unpack the Entire Archive**:
    ```sh
    python VdfsHandler.py /path/to/archive.vdf -u -o /output/directory
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
