from argparse import ArgumentParser, Namespace
from datetime import datetime
from logging import DEBUG, ERROR, basicConfig, error, info
from pathlib import Path

from zenkit import GameVersion, LogLevel, Vfs, VfsNode, set_logger_default

from printColored import enable_ansi_escape_sequences, print_colored, print_mixed

enable_ansi_escape_sequences()


class NodeNotFound(Exception):
    def __init__(self, message: str = "") -> None:
        super().__init__(message)


class InvalidData(Exception):
    def __init__(self, message: str = "") -> None:
        super().__init__(message)


class InvalidGameVersion(Exception):
    def __init__(self, message: str = "") -> None:
        super().__init__(message)


class VdfNotLoaded(Exception):
    def __init__(self, message: str = "") -> None:
        super().__init__(message)


class VdfsHandler:

    def __init__(
        self,
        vdf_archive: str | Path | None = None,
        debugging=None,
        internal_debugging=None,
    ):
        self.path = Path(vdf_archive) if Path(vdf_archive).exists() else None
        self.vdf_name = self._vdf_name(vdf_archive)
        self._toggle_debugging(debugging, internal_debugging)

        self.version_ = GameVersion.GOTHIC2
        self._node_count = 0
        self.vfs = self._initialize_vfs()

    @property
    def game_version(self) -> GameVersion:
        return self.version_

    @game_version.setter
    def game_version(self, version: str) -> None:
        match version.lower():
            case "g1":
                self.version_ = GameVersion.GOTHIC1
            case "g2":
                self.version_ = GameVersion.GOTHIC2
            case _:
                raise InvalidGameVersion(f"Invalid game version: {version}")

    @property
    def node_count(self) -> int:
        return self._node_count

    @property
    def archive_name(self) -> str:
        return self.vdf_name

    @property
    def is_existing_file(self) -> bool:
        return self.path.exists()

    def _vdf_name(self, vdf_archive: str | Path | None) -> str | Path | None:
        if self.path:
            return self.path.name
        if vdf_archive:
            return vdf_archive
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"Unnamed_{date}.vdf"

    def _toggle_debugging(
        self, condition: bool | None, condition2: bool | None
    ) -> None:
        logging_format = (
            "[%(asctime)s - %(levelname)s]"
            " [%(filename)s -> %(funcName)s -> %(lineno)d]"
            " - %(message)s"
        )
        level = DEBUG if condition else ERROR
        inner_level = LogLevel.TRACE if condition2 else LogLevel.WARNING
        basicConfig(level=level, format=logging_format)
        set_logger_default(inner_level)

    def _initialize_vfs(self) -> Vfs:
        def count_nodes(node: VfsNode) -> int:
            for child in node:
                if child.is_dir():
                    self._node_count += count_nodes(child)
                else:
                    self._node_count += 1
            return self._node_count

        vfs = Vfs()
        if self.path:
            if not self.path.is_file():
                raise FileNotFoundError(f"{self.path.name} was not found!")
            vfs.mount_disk(self.path)
        count_nodes(vfs.root)
        return vfs

    def _print_recursive(self, node: VfsNode, indent: str = "") -> None:
        contents = [child for child in node]
        contents.sort(key=lambda x: (not x.is_dir(), x.name))
        total_children = len(contents)

        for index, child in enumerate(contents, start=1):
            is_last = index == total_children
            if indent == "":
                current_indent = "└── " if is_last else "├── "
            else:
                current_indent = indent + ("└── " if is_last else "├── ")
            child_name = (
                f"[{child.name.title()}]" if child.is_dir() else child.name.title()
            )
            if not child.is_dir():
                print_mixed(
                    "green", text=f"{current_indent}", colored_text=f"{child_name}"
                )
            else:
                print_mixed(
                    "yellow", text=f"{current_indent}", colored_text=f"{child_name}"
                )
            if child.is_dir():
                extension = "    " if is_last else "│   "
                self._print_recursive(child, indent + extension)

    def _build_file_tree(self, directory: str | Path) -> dict:
        def add_to_tree(item, tree):
            if item.is_dir():
                sub_tree = []
                for sub_item in item.iterdir():
                    add_to_tree(sub_item, sub_tree)
                tree.append({item.name: sub_tree})
            else:
                tree.append(str(item))

        root_path = Path(directory)
        tree = []
        for item in root_path.iterdir():
            add_to_tree(item, tree)

        return {root_path.name: tree}

    def _export_recursive(self, node: VfsNode, destination: str | Path):
        for item in node:
            if item.is_dir():
                (Path(destination) / item.name).mkdir(exist_ok=True, parents=True)
                self._export_recursive(item, Path(destination) / item.name)
            else:
                (Path(destination) / item.name).write_bytes(item.data)

    def _insert_recursive(
        self,
        source: str | Path | None = None,
        node_tree: dict[str, dict | str] | None = None,
        parent_node: VfsNode | None = None,
    ) -> None:
        if not node_tree:
            node_tree = self._build_file_tree(str(source))
        for parent_name, children in node_tree.items():
            parent = self.vfs.find(parent_name)
            if not parent:
                if not parent_node:
                    parent_node = self.vfs.root
                parent = parent_node.create(parent_name)
            for child in children:
                if isinstance(child, dict):
                    sub_parent_name, sub_children = list(child.items())[0]
                    new_tree = {sub_parent_name: sub_children}
                    self._insert_recursive(node_tree=new_tree, parent_node=parent)
                else:
                    if not self.vfs.find(Path(child).name):
                        parent.create(Path(child).name, Path(child).read_bytes())

    def _insert_dir(
        self, internal_path: str | Path, parent: VfsNode | None = None
    ) -> VfsNode | None:
        path_tail = self.vfs.find(Path(internal_path).name)
        if path_tail:
            if len(Path(internal_path).parts) == 1:
                if self.vfs.root.get_child(path_tail.name):
                    return path_tail
                else:
                    return self.vfs.root.create(path_tail.name)
            exists = 1
            internal_path_parts = enumerate(Path(internal_path).parts)
            for index, part in internal_path_parts:
                if index == len(Path(internal_path).parts) - 1:
                    node = self.vfs.find(part)
                    if not node:
                        exists -= 1
                        break
                    else:
                        break
                node = self.vfs.find(part)
                matching = node.get_child(Path(internal_path).parts[index + 1])
                if not matching:
                    exists -= 1
                    break
            if exists == 1:
                return path_tail
        internal_path_parts = enumerate(Path(internal_path).parts)
        for index, part in internal_path_parts:
            if index == len(Path(internal_path).parts) - 1:
                node = self.vfs.find(part)
                new_parent = None
                if not node:
                    if not parent:
                        new_parent = self.vfs.root.create(part)
                        return new_parent
                    else:
                        new_parent = parent.create(part)
                        return new_parent
                else:
                    return node
            node = self.vfs.find(part)
            new_parent = None
            if not node:
                if not parent:
                    new_parent = self.vfs.root.create(part)
                else:
                    new_parent = parent.create(part)
                self._insert_dir(
                    "/".join(Path(internal_path).parts[index + 1 : :]), new_parent
                )
            else:
                self._insert_dir(
                    "/".join(Path(internal_path).parts[index + 1 : :]), node
                )

    def get_file(self, file_name: str) -> VfsNode | None:
        info(f"Loading {file_name}...")
        file = self.vfs.find(file_name)
        if file:
            return file
        info(f"Failed to load {file_name}!")

    def insert_file(
        self,
        internal_path: str | None = None,
        source_path: str | Path | None = None,
        content: bytes | None = None,
    ) -> VfsNode | None:
        if not source_path:
            if not internal_path:
                raise ValueError(
                    "Nor the source path or the internal path was provided"
                )
            info(f"Inserting to {internal_path}...")
            if "." not in internal_path:
                result = self._insert_dir(internal_path)
                return result
            if not content:
                raise ValueError(
                    "Nor the source path or content for the file was provided"
                )
            if not len(Path(internal_path).parts) > 1:
                if found := self.vfs.find(internal_path.upper()):
                    return found
                result = self.vfs.root.create(internal_path.upper(), content)
                return result
            internal_parent = self._insert_dir(Path(internal_path).parent)
            if found := self.vfs.find(Path(internal_path).name.upper()):
                return found
            result = internal_parent.create(Path(internal_path).name.upper(), content)
            return result
        info(f"Inserting from {source_path}...")
        if Path(source_path).is_dir():
            if not internal_path or internal_path in [".", "\\", "/", ".\\", "./"]:
                self._insert_recursive(source_path)
                return
            internal_parent = self._insert_dir(internal_path)
            self._insert_recursive(source_path, parent_node=internal_parent)
            return
        if not internal_path or internal_path in [".", "\\", "/", ".\\", "./"]:
            if found := self.vfs.find(Path(source_path).name.upper()):
                return found
            result = self.vfs.root.create(
                Path(source_path).name.upper(), Path(source_path).read_bytes()
            )
            return result
        internal_parent = self._insert_dir(internal_path)
        if found := self.vfs.find(Path(source_path).name.upper()):
            return found
        result = internal_parent.create(
            Path(source_path).name.upper(), Path(source_path).read_bytes()
        )
        return result

    def export_file(
        self, node_name: str, destination: str | Path, all_with_name: bool = False
    ) -> None:
        def traverse(node: VfsNode, target: str, export_dir: str | Path):
            for child in node:
                if child.is_dir():
                    traverse(child, target, export_dir)
                else:
                    if target.lower() in child.name.lower():
                        (Path(export_dir) / child.name).write_bytes(child.data)

        if not destination:
            destination = Path.cwd()
        Path(destination).mkdir(parents=True, exist_ok=True)
        node = self.vfs.find(node_name)
        if not all_with_name:
            if not node:
                raise NodeNotFound(f"{node_name} not found")
            if node.is_dir():
                self._export_recursive(node, destination)
            else:
                (Path(destination) / node.name).write_bytes(node.data)
        else:
            traverse(self.vfs.root, node_name, destination)

    def export_all(self, destination: str | Path) -> None:
        info(f"Exporting all files from {self.archive_name}...")
        if not destination:
            destination = Path.cwd()
        Path(destination).mkdir(parents=True, exist_ok=True)
        try:
            self._export_recursive(self.vfs.root, destination)
        except Exception as err:
            error(f"Failed to export all files due to an unhandled exception: {err}")
        else:
            info(f"Exctracted {self.node_count} files to {destination}")

    def remove_file(
        self, file_name: str, parent: VfsNode | None = None, all_with_name: bool = False
    ):
        if not parent:
            parent = self.vfs.root
        if not all_with_name:
            if not self.vfs.find(file_name):
                raise NodeNotFound(f"{file_name} not found")
        info(f"Removing {file_name}...")
        try:
            for node in parent:
                if not all_with_name:
                    if node.is_dir():
                        if node.name.lower() == file_name:
                            parent.remove(node.name)
                        else:
                            self.remove_file(file_name, node)
                    else:
                        if node.name.lower() == file_name:
                            parent.remove(node.name)
                else:
                    if node.is_dir():
                        self.remove_file(file_name, node, True)
                    else:
                        if file_name.lower() in node.name.lower():
                            parent.remove(node.name)
        except Exception as err:
            error(f"Failed to remove {file_name} due to an unhandled exception: {err}")
        else:
            info(f"Succesfully removed {file_name}")

    def save_vdf(self, destination: str | Path, timestamp: int = 0) -> None:
        if not destination:
            if not self.path:
                destination = Path.cwd() / self.archive_name
            else:
                destination = self.path
        if "." not in Path(destination).name:
            destination = Path(destination) / self.archive_name
        try:
            info(f"Saving VDF archive as {destination}...")
            self.vfs.save(destination, self.game_version, timestamp)
        except Exception as err:
            error(f"Failed to save VDF archive due to an unhandled exception: {err}")
        else:
            info(f"Succesfully saved {destination}")

    def print_vfs(self) -> None:
        info(f"Printing VFS structure tree of {self.archive_name}")
        try:
            self._print_recursive(self.vfs.root)
        except Exception as err:
            error(f"Failed to print VFS due to an unhandled exception: {err}")


def parse_args() -> Namespace:
    """Parses command-line arguments using argparse."""
    parser = ArgumentParser(description="VDF Archive Manager")
    parser.add_argument("archive_path", type=Path, help="Path to the VDF archive")
    parser.add_argument(
        "-g",
        "--game-version",
        choices=["g1", "g2"],
        default="g2",
        help="Game version (g1 or g2, default: g2)",
    )
    parser.add_argument(
        "-t",
        "--timestamp",
        type=lambda s: datetime.strptime(s, "%d.%m.%Y %H:%M:%S").timestamp(),
        help="Timestamp for output VDF (format: DD.MM.YYYY HH:MM:SS)",
    )
    parser.add_argument(
        "-o",
        "--output-path",
        type=Path,
        help="Output path for unpack/extract/save operations",
    )
    parser.add_argument(
        "-u", "--unpack", action="store_true", help="Unpack the VDF archive"
    )
    parser.add_argument(
        "-e",
        "--extract",
        type=str,
        help="Extract a file or directory (supports wildcards: *).  Example: -e 'DATA/*.txt'",
    )
    parser.add_argument(
        "-a",
        "--add",
        nargs="?",
        const=None,
        metavar=("SOURCE", "DESTINATION"),
        help="Add a file/dir to the archive. If only SOURCE is provided, the filename will be used inside the VDF. Ex: -a myfile.txt DATA/myfile.txt  or -a myfile.txt",
    )
    parser.add_argument(
        "-r",
        "--remove",
        type=str,
        help="Remove a file or directory (supports wildcards: *). Example: -r '*.tmp'",
    )
    parser.add_argument(
        "-v", "--view-vfs", action="store_true", help="View the VDF file system tree"
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug logging"
    )
    parser.add_argument(
        "-f",
        "--full-debug",
        action="store_true",
        help="Enable full debug logging (ZenKit)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Validate archive path
    if not Path(args.archive_path).exists():
        print_colored("red", f"Error: Archive file not found: {args.archive_path}")
        return

    # Validate game version (although zenkit likely handles this internally)
    try:
        vfs_handler = VdfsHandler(args.archive_path, args.debug, args.full_debug)
        vfs_handler.game_version = args.game_version
    except InvalidGameVersion as e:
        print_colored("red", f"Error: Invalid game version: {e}")
        return

    timestamp = int(args.timestamp) if args.timestamp else 0

    try:  # Wrap operations in try-except to catch potential exceptions from VdfsHandler
        if args.view_vfs:
            vfs_handler.print_vfs()
        elif args.unpack:
            vfs_handler.export_all(args.output_path)
        elif args.extract:
            extract_target = (
                args.extract.split("*")[1] if "*" in args.extract else args.extract
            )
            vfs_handler.export_file(
                extract_target, args.output_path, all_with_name="*" in args.extract
            )
        elif args.add:
            source_path = args.add[0]
            dest_path = args.add[1] if len(args.add) > 1 else None
            if not Path(source_path).exists():
                print_colored(
                    "red", f"Error: Source file/directory not found: {source_path}"
                )
                return
            vfs_handler.insert_file(dest_path, source_path=source_path)
            vfs_handler.save_vdf(args.output_path, timestamp)
        elif args.remove:
            remove_target = (
                args.remove.split("*")[1] if "*" in args.remove else args.remove
            )
            vfs_handler.remove_file(remove_target, all_with_name="*" in args.remove)
            vfs_handler.save_vdf(args.output_path, timestamp)
    except (
        NodeNotFound,
        InvalidData,
        FileNotFoundError,
        Exception,
    ) as e:  # Catch specific and generic exceptions
        print_colored("red", f"Error during operation: {e}")
        return


if __name__ == "__main__":
    main()
