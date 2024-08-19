from argparse import ArgumentParser
from datetime import datetime
from logging import DEBUG, ERROR, basicConfig, error, info
from pathlib import Path

from zenkit import GameVersion, LogLevel, Vfs, VfsNode, set_logger_default

from printColored import print_colored, print_mixed

DESKTOP = Path.home() / "Desktop"


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
                result = self.vfs.root.create(internal_path.upper(), content)
                return result
            internal_parent = self._insert_dir(Path(internal_path).parent)
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
            result = self.vfs.root.create(
                Path(source_path).name.upper(), Path(source_path).read_bytes()
            )
            return result
        internal_parent = self._insert_dir(internal_path)
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

    def save_vdf(self, destination: str | Path) -> None:
        if not destination:
            if not self.path:
                destination = Path.cwd() / self.archive_name
            else:
                destination = self.path
        if "." not in Path(destination).name:
            destination = Path(destination) / self.archive_name
        try:
            info(f"Saving VDF archive as {destination}...")
            self.vfs.save(destination, self.game_version)
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


def parse_args() -> dict:
    parser = ArgumentParser()
    # Game version switch
    parser.add_argument(
        "-g1",
        "--gothic1",
        action="store_true",
        help="Set game version for packed VDF archives to Gothic 1",
        required=False,
    )
    # Input directory for unpacking
    parser.add_argument("archive_path", type=str, help="Path to the VDF archive")
    # Output directory for unpacking
    parser.add_argument(
        "-o",
        "--output_path",
        type=str,
        help=(
            "If provided, the VDF archive will be unpacked into"
            " this directory instead"
        ),
        required=False,
    )
    # Unpack to cwd or output dir
    parser.add_argument(
        "-u",
        "--unpack",
        help=(
            "Unpack VDF archive to the current working directory or into a directory specified with -o. "
            "Usage: -u -o (optional)[path]"
        ),
        action="store_true",
        required=False,
    )
    # Extract node by name
    parser.add_argument(
        "-e",
        "--extract",
        help=(
            "Extract a file or a directory tree from the VDF archive to the "
            "provided output path. Usage: -e [file_or_directory_name] -o [path]"
        ),
        type=str,
        required=False,
    )
    # Insert file or a directory tree into VFS and save modified VDF
    parser.add_argument(
        "-a",
        "--add",
        type=tuple[str],
        help=(
            "Add a file or a directory with files to the VDF archive. "
            "Usage: -a [path to input file or directory]"
            "[path to destination inside VDF] -o (optional)[path to the resulted VDF] "
            "If not provided, the resulted VDF will be unpacked to the current directory, replacing the original archive"
        ),
        required=False,
    )
    # Remove node by name or number of them with wildcards
    parser.add_argument(
        "-r",
        "--remove",
        type=str,
        help=(
            "Remove a file or a directory tree or number of them using wildcards "
            "from the VDF tree. "
            "Usage: -r [file_or_directory_name] -o (optional)[path_to_the_output_VDF]"
        ),
        required=False,
    )
    # Print out VFS structure tree
    parser.add_argument(
        "-v",
        "--view_vfs_tree",
        action="store_true",
        help="View the VDF tree",
        required=False,
    )
    # Enable debug mode
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug mode", required=False
    )
    # Enable internal debug mode for ZenKit
    parser.add_argument(
        "-f",
        "--full_debug",
        action="store_true",
        help="Enable full debug mode, with deeper debug messages",
        required=False,
    )

    return vars(parser.parse_args())


def main() -> None:
    args = parse_args()
    if args["archive_path"][-4:] != ".vdf" or not Path(args["archive_path"]).exists():
        print_colored(
            "red", f"Aborting: {args['archive_path']} is not a valid VDF archive."
        )
        exit()
    vfs = VdfsHandler(args["archive_path"])

    if args["gothic1"]:
        vfs.game_version = "g1"
    if args["view_vfs_tree"]:
        if vfs.is_existing_file:
            vfs.print_vfs()
        else:
            print_colored("red", f"Aborting: {vfs.archive_name} is empty.")
    if args["debug"]:
        vfs._toggle_debugging(args["debug"], False)
    if args["full_debug"]:
        vfs._toggle_debugging(args["full_debug"], True)

    if args["unpack"]:
        if vfs.is_existing_file:
            vfs.export_all(args["output_path"])
            exit()
        print_colored("red", f"Aborting: {vfs.archive_name} is empty.")
        exit()
    elif args["extract"]:
        if vfs.is_existing_file:
            node = args["extract"]
            path = args["output_path"]
            if "*" not in node:
                vfs.export_file(node, path)
                exit()
            wildcard = node.split("*")[1]
            vfs.export_file(wildcard, path, all_with_name=True)
            exit()
        print_colored("red", f"Aborting: {vfs.archive_name} is empty.")
        exit()
    elif args["add"]:
        input_path, vdf_path = args["add"]
        output_path = args["output_path"]
        if True not in [input_path, vdf_path]:
            print_colored("red", "Aborting: No input file for insertion was provided.")
            exit()
        if not "*" in input_path:
            vfs.insert_file(vdf_path, input_path)
            vfs.save_vdf(output_path)
            exit()
        parent_directory, wildcard = input_path.split("*")
        if parent_directory:
            if Path(parent_directory).exists():
                for file in Path(parent_directory).iterdir():
                    if wildcard.lower() in file.name.lower():
                        vfs.insert_file(vdf_path, file)
                vfs.save_vdf(output_path)
                exit()
            else:
                print_colored("red", f"Aborting: {parent_directory} was not found.")
                exit()
        else:
            for file in Path().iterdir():
                if wildcard.lower() in file.name.lower():
                    vfs.insert_file(vdf_path, file)
            vfs.save_vdf(output_path)
            exit()
    elif args["remove"]:
        if vfs.is_existing_file:
            node = args["remove"]
            output_path = args["output_path"]
            if "*" not in node:
                vfs.remove_file(node)
                vfs.save_vdf(output_path)
                exit()
            wildcard = node.split("*")[1]
            vfs.remove_file(wildcard, all_with_name=True)
            vfs.save_vdf(output_path)
            exit()
        print_colored("red", f"Aborting: {vfs.archive_name} is empty.")
        exit()

    exit()


if __name__ == "__main__":
    main()
