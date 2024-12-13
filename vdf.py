from datetime import datetime
from os.path import sep as PATH_SEP
from pathlib import Path
from traceback import format_exc
from typing import Self, override

from zenkit import GameVersion, Vfs, VfsNode, LogLevel, set_logger_default

EXTENSION = ".vdf"


def enable_logging() -> None:
    set_logger_default(LogLevel.TRACE)


class VdfSaveError(Exception):
    """
    Exception raised if an error occurs during VDF saving.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class VdfLoadError(Exception):
    """
    Exception raised if an error occurs during VDF loading.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class VdfParseError(Exception):
    """
    Exception raised if an error occurs during VDF loading.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class VdfCreateNodeError(Exception):
    """
    Exception raised if an error occurs during VDF loading.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class Asset:
    def __init__(self, node: VfsNode, parent: Self | None = None) -> None:
        self.node: VfsNode = node
        self.parent: Self | None = parent

    @override
    def __str__(self) -> str:
        if self.parent and self.parent.node.name == "":
            return self.node.name

        def trackback(asset_: Asset) -> str:
            if not asset_.parent:
                return ""
            return f"{trackback(asset_.parent)}{PATH_SEP}{asset_.node.name}"

        return trackback(self)[1:]

    def is_dir(self) -> bool:
        return self.node.is_dir()

    def data(self) -> bytes:
        return self.node.data

    def save(self, destination: str) -> None:
        if self.is_dir():
            return
        destination_ = Path(destination)
        if "." not in destination_.name:
            destination_.mkdir(parents=True, exist_ok=True)
            (destination_ / self.node.name).write_bytes(self.data())
        else:
            destination_.parent.mkdir(parents=True, exist_ok=True)
            destination_.write_bytes(self.data())


class Vdf:
    def __init__(self, name: str, version: GameVersion = GameVersion.GOTHIC2) -> None:
        self._name: str = name
        self._version: GameVersion = version
        self._path: str = ""
        self._vfs = Vfs()
        self._cache = []

    def __len__(self) -> int:
        def __traverse_tree(current: VfsNode) -> int:
            count = 0
            for child in current:
                if child.is_dir():
                    count += 1
                    __traverse_tree(child)
                else:
                    count += 1
            return count

        return __traverse_tree(self._vfs.root)

    @property
    def name(self) -> str:
        """
        The name of the VDF file.
        """
        return self._name

    @property
    def path(self) -> str:
        """
        The path of the VDF file.

        Raises `FileNotFoundError` if the VDF file is not loaded.
        """
        return self._path

    @property
    def game_version(self) -> GameVersion:
        """
        The game version of the VDF file.
        """
        return self._version

    @game_version.setter
    def game_version(self, version: GameVersion) -> None:
        self._version = version

    def print_vfs(self) -> None:
        """
        Outputs the VFS tree of the VDF file, listing all files and directories.
        """

        def __traverse_tree(
            current: VfsNode, buffer: str = "", indent: str = ""
        ) -> None:
            children = current.children
            last_child_index = len(children) - 1
            for index, node in enumerate(children):
                is_last = index == last_child_index
                current_indent = indent + ("└── " if is_last else "├── ")
                if node.is_dir():
                    extension = "    " if is_last else "│   "
                    print(f"{current_indent}[{node.name}]")
                    __traverse_tree(node, buffer, indent + extension)
                else:
                    print(f"{current_indent}{node.name}")

        root = self._vfs.root
        __traverse_tree(root)

    def save(self, destination: str, creation_date: str | None = None) -> None:
        """
        Saves the VDF file to the specified location and sets the creation date.

        If `creation_date` is not specified, the current date and time will be used.

        Parameters
        ----------
        `destination : str`
            The path to save the VDF file to.
        `creation_date : str`
            The creation date of the VDF file in the format `%d.%m.%Y %H:%M:%S`.

        Raises
        ------
        VdfSaveError
            If an error occurs during saving.
            Includes details about the underlying error.
        """
        try:
            destination_ = Path(destination)
            destination_.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise VdfSaveError(
                f"Could not create parent directories for {destination}: {e}"
            ) from e

        if not creation_date:
            creation_date = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        try:
            unix_timestamp = datetime.strptime(
                creation_date, "%d.%m.%Y %H:%M:%S"
            ).timestamp()
        except ValueError as e:
            raise VdfSaveError(f"Invalid creation_date format: {e}") from e

        save_path = (
            (destination_ / self.name).with_suffix(EXTENSION)
            if destination_.is_dir()
            else destination_.with_suffix(EXTENSION)
        )

        try:
            self._vfs.save(str(save_path), self.game_version, int(unix_timestamp))
            self._path = str(save_path)
        except Exception as e:
            detailed_error = f"Error saving VDF to {save_path}: {e}\n{format_exc()}"
            raise VdfSaveError(detailed_error) from e

    def load(self, file: str) -> None:
        """
        Loads the VDF file from the specified location.

        Parameters
        ----------
        `file : str`
            The path to the VDF file.

        Raises
        ------
        VdfLoadError
            If an error occurs during loading.
            Includes details about the underlying error.
        """
        try:
            file_ = Path(file)
            if not file_.exists():
                raise FileNotFoundError(file)
            if file_.is_dir():
                raise IsADirectoryError(file)
        except (FileNotFoundError, IsADirectoryError) as e:
            raise VdfLoadError(f"Could not find VDF file: {e}") from e

        try:
            self._vfs.mount_disk(file_)
        except (Exception, OSError) as e:
            detailed_error = f"Error loading VDF file: {e}\n{format_exc()}"
            raise VdfLoadError(detailed_error) from e
        self._path = file

    def fetch_assets(self) -> list[Asset]:
        """
        Parses the VDF file and returns a list of `Asset` objects.

        Returns
        -------
        `list[Asset]`
            A list of `Asset` objects representing the assets in the VDF file.

        Raises
        ------
        VdfParseError
            If an error occurs during parsing.  Includes details about the underlying error.
        """
        root = self._vfs.root
        assets = []

        try:

            def __traverse_tree(current: VfsNode, parent: Asset | None = None):
                for child in current:
                    try:
                        current_asset = Asset(current, parent)
                        next_asset = Asset(child, current_asset)
                        if current == root:
                            assets.append(Asset(child, None))
                        else:
                            assets.append(next_asset)
                        if child.is_dir():
                            __traverse_tree(next_asset.node, current_asset)
                    except Exception as e:
                        child_name = child.name if child.name else "root"
                        parent_name = parent.node.name if parent else "root"
                        raise VdfParseError(
                            f"Error parsing asset '{child_name}' under parent '{parent}': {e}\n{format_exc()}"
                        ) from e

            __traverse_tree(root)
            return assets

        except VdfParseError:
            raise
        except Exception as e:
            raise VdfParseError(
                f"An unexpected error occurred during VDF parsing: {e}\n{format_exc()}"
            ) from e

    def get_asset(self, name: str) -> Asset | None:
        """
        Returns VDF node from the VFS wrapped in `Asset` object with the specified name.

        Parameters
        ----------
        `name : str`
            The name of the asset to retrieve.

        Returns
        -------
        `Asset | None`
            The `Asset` object with the specified name, or `None` if not found.

        Raises
        ------
        VdfParseError
            If an error occurs during parsing.
        """
        if not self._cache:
            try:
                self._cache = self.fetch_assets()
            except VdfParseError as e:
                raise VdfParseError(f"Failed to update cache: {e}") from e

        if PATH_SEP in name:
            name = name.rsplit(PATH_SEP, 1)[-1]

        asset = next(
            (a for a in self._cache if a.node.name.lower() == name.lower()), None
        )
        if asset is None:
            try:
                self._cache = self.fetch_assets()  # Refresh cache
                asset = next(
                    (a for a in self._cache if a.node.name.lower() == name.lower()),
                    None,
                )
            except VdfParseError as e:
                raise VdfParseError(f"Failed to update cache: {e}") from e

        return asset

    def remove_asset(self, name: str) -> None:
        """
        Removes the VDF node from the VFS with the specified name.

        Parameters
        ----------
        `name : str`
            The name of the asset to remove.

        Raise
        -----
        VdfParseError
            If an error occurs during parsing.
        """

        try:
            self._cache = self.fetch_assets()
        except VdfParseError as e:
            raise VdfParseError(f"Failed to update cache: {e}") from e

        for asset in list(self._cache):
            if asset.node.name.lower() == name.lower():
                try:
                    if asset.parent:
                        print(asset.parent.node.name)
                        print(asset.node.name)
                        parent_node = self._vfs.find(asset.parent.node.name)
                        parent_node.remove(asset.node.name)
                    else:
                        self._vfs.remove(asset.node.name)

                    self._cache.remove(asset)
                    return

                except (KeyError, ValueError) as e:
                    raise VdfParseError(f"Error removing asset '{name}': {e}") from e

    def insert_asset(
        self, file_path: str, in_vdf_path: str | None = None
    ) -> Asset | None:
        """
        Inserts an asset into the VFS at the specified path.
        If the asset already exists, aborts and returns None.
        Automatically creates parents of the specified path.

        Args:
            file_path: The path to the asset file.
            in_vdf_path: The path to the VDF file that contains the asset.

        Returns:
            The inserted asset.
        """
        file_path_ = Path(file_path)
        if not file_path_.exists():
            raise FileNotFoundError(file_path)
        if self._vfs.find(file_path_.name) is not None:
            return

        timestamp_ = file_path_.stat().st_ctime
        parent_, asset_name_ = self._create_parents(in_vdf_path)
        if not asset_name_:
            asset_name_ = file_path_.name

        try:
            new_node = self.create_node(
                name=asset_name_,
                data=file_path_.read_bytes(),
                parent=parent_.name,
                timestamp=timestamp_,
            )
        except (VdfCreateNodeError, ValueError):
            raise

        return self.get_asset(new_node.name) if new_node else None

    def create_node(
        self,
        name: str,
        data: bytes | None = None,
        parent: str | None = None,
        timestamp: int | float | None = None,
        create_parent: bool = False,
    ) -> VfsNode | None:
        """
        Creates a new node in the VFS with the specified name and parent.

        Parameters
        ----------
        `name : str`
            The name of the directory to create.
        `parent : str`
            The name of the parent directory. If not specified, the root directory will be used.
        `timestamp : int | float`
            The timestamp of the directory. If not specified, the current timestamp will be used.
        `create_parent : bool`
            Whether to create the parent directory if it doesn't exist. Default is `False`.

        Returns
        -------
        `VfsNode | None`
            The `VfsNode` object representing the created directory, or `None` if the directory could not be created.

        Raises
        ------
        VdfCreateNodeError
            If an error occurs during creating the node.
            Includes details about the underlying error.
        ValueError
            If the parent node is not found.

        """
        result = None
        parent_node = (
            self._vfs.root if (not parent or parent == "/") else self._vfs.find(parent)
        )
        if not parent_node and create_parent:
            parent_node = self.create_node(parent)
        elif not parent_node:
            raise ValueError(f"Parent node {parent} not found")
        try:
            if data:
                result = parent_node.create(name, data, timestamp=timestamp)
            else:
                result = parent_node.create(name, timestamp=timestamp)
        except (Exception, OSError) as e:
            detailed_error = f"Error while creating a node: {name}\n{e}\n{format_exc()}"
            raise VdfCreateNodeError(detailed_error) from e
        if result:
            try:
                self._cache = self.fetch_assets()
                return result
            except VdfParseError as e:
                raise VdfParseError(f"Failed to update cache: {e}") from e

    def _create_parents(self, path: str | None = None) -> tuple[VfsNode, str | None]:
        if not path:
            return self._vfs.root, None
        parent = None
        asset_name = None

        parts = path.replace("\\", "/").split("/")
        if len(parts) == 1:
            if "." in parts[0]:
                return self._vfs.root, None
        for index, part in enumerate(parts):
            if found := self._vfs.find(part):
                parent = found
                continue
            if "." in part:
                asset_name = part
                continue
            if index == 0:
                parent = self.create_node(part)
                continue
            parent = self.create_node(part, parent=parts[index - 1], create_parent=True)

        return parent, asset_name
