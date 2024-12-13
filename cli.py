from datetime import datetime
from typing import NamedTuple
from vdf import Vdf, enable_logging, EXTENSION
from argparse import ArgumentParser, Namespace
from pathlib import Path
from os.path import sep as PATH_SEP
from traceback import format_exc


class ArgInfo(NamedTuple):
    short: str
    long: str
    help: str
    type: type
    metavar: str | tuple[str, str] | None = None
    nargs: str | int | None = None
    default: str | int | bool | None = None
    action: str = "store"
    choices: list[str] | list[int] | None = None


ARGS = {
    "input": ArgInfo(
        short="-i",
        long="--input",
        help="The path to the VDF archive",
        type=str,
        metavar="PATH_TO_VDF",
        default=None,
    ),
    "new": ArgInfo(
        short="-n",
        long="--new",
        help="The path to the new VDF archive that will be created",
        type=str,
        metavar="PATH_TO_NEW_VDF",
    ),
    "output": ArgInfo(
        short="-o",
        long="--output",
        help="The output path to save asset from VDF or VDF archive itself",
        type=str,
        metavar="OUTPUT_PATH",
    ),
    "game_version": ArgInfo(
        short="-gv",
        long="--game-version",
        help="The game version of the saved VDF file, 0 for Gothic 1 and 1 for Gothic 2",
        type=int,
        default=1,
        choices=[0, 1],
        metavar="INT 0 or 1",
    ),
    "timestamp": ArgInfo(
        short="-t",
        long="--timestamp",
        help="The creation date of the VDF file in the format %d.%m.%Y %H:%M:%S",
        type=str,
        default=None,
        metavar="%d.%m.%Y %H:%M:%S",
    ),
    "extract": ArgInfo(
        short="-e",
        long="--extract",
        help=(
            "The path to the asset to extract from VDF archive, "
            "used with --output, wildcards are supported."
            "Example: `textures/ui/hud/healthbar_*`"
        ),
        type=str,
        metavar="PATH_TO_ASSET_INSIDE_VDF",
    ),
    "unpack": ArgInfo(
        short="-u",
        long="--unpack",
        help="The path to the archive to unpack, used with --output",
        type=bool,
        default=None,
        action="store_true",
    ),
    "remove": ArgInfo(
        short="-r",
        long="--remove",
        help=(
            "The name of the asset to remove from VDF archive, "
            "wildcards are supported. Example: `path/to/assets/in/vdf/OLDMINE_*`"
        ),
        type=str,
        metavar="PATH_TO_ASSET_INSIDE_VDF",
    ),
    "add": ArgInfo(
        short="-a",
        long="--add",
        help=(
            "The path to the asset to add to VDF archive and its paht inside VDF archive, "
            "used with --output, wildcards are supported. "
            "Example: `path/to/local/files/*.tga`"
        ),
        type=str,
        nargs="+",
        metavar=("PATH_TO_LOCAL_FILE_OR_DIRECTORY", "PATH_TO_ASSET_IN_VDF"),
    ),
    "list": ArgInfo(
        short="-l",
        long="--list",
        help="List all assets in the VDF archive",
        type=bool,
        default=False,
        action="store_true",
    ),
    "debug": ArgInfo(
        short="-d",
        long="--debug",
        help="Display debug information",
        type=bool,
        default=False,
        action="store_true",
    ),
}


def parse_args() -> Namespace:
    parser = ArgumentParser()
    for _, info in ARGS.items():
        if info.type == bool:
            _ = parser.add_argument(
                info.short,
                info.long,
                help=info.help,
                action=info.action,
                default=info.default,
            )
            continue
        _ = parser.add_argument(
            info.short,
            info.long,
            help=info.help,
            type=info.type,
            default=info.default,
            nargs=info.nargs,
            action=info.action,
            metavar=info.metavar,
        )
    return parser.parse_args()


def get_input(input: str | None = None, new: str | None = None) -> Vdf:
    if input and not new:
        vdf_path = Path(input)
        if not vdf_path.exists():
            raise FileNotFoundError(f"VDF file {vdf_path} does not exist")
        if not vdf_path.is_file():
            raise FileNotFoundError(f"VDF file {vdf_path} is not a file")
        vdf = Vdf(vdf_path.stem)
        vdf.load(str(vdf_path))
        return vdf
    elif new and not input:
        vdf_path = Path(new)
        vdf = Vdf(vdf_path.stem)
        return vdf
    else:
        raise ValueError("Please specify either --input or --new")


def unpack(vdf: Vdf, output_path_: str) -> None:
    if vdf.path == "":
        raise Exception("Nothing to unpack yet, VDF archive is empty")
    output_path = Path.cwd()
    if output_path_:
        output_path = Path(output_path_)
    output_path.mkdir(parents=True, exist_ok=True)
    for asset in vdf.fetch_assets():
        final_path = str(output_path / vdf.name / str(asset))
        asset.save(final_path)


def extract(vdf: Vdf, extract: str, output_path_: str | None = None) -> None:
    if vdf.path == "":
        raise Exception("Nothing to extract yet, VDF archive is empty")
    output_path = Path.cwd()
    if output_path_:
        output_path = Path(output_path_)
    output_path.mkdir(parents=True, exist_ok=True)
    last_part = extract
    if PATH_SEP in extract:
        last_part = extract.rsplit(PATH_SEP, 1)[1]
    if last_part.startswith("*"):
        for asset in vdf.fetch_assets():
            if asset.node.name.lower().endswith(last_part[1:].lower()):
                final_path = str(output_path / vdf.name / str(asset))
                asset.save(final_path)
    elif last_part.endswith("*"):
        for asset in vdf.fetch_assets():
            if asset.node.name.lower().startswith(last_part[:-1].lower()):
                final_path = str(output_path / vdf.name / str(asset))
                asset.save(final_path)
    else:
        asset = vdf.get_asset(last_part)
        if asset:
            final_path = str(output_path / vdf.name / str(asset))
            asset.save(final_path)


def remove(
    vdf: Vdf, timestamp: str, remove: str, output_path_: str | None = None
) -> None:
    if vdf.path == "":
        raise Exception("Nothing to remove yet, VDF archive is empty")
    output_path = vdf.path
    if output_path_:
        output_path = Path(output_path_)
        if not "." in output_path.name:
            output_path = Path(output_path_) / Path(vdf.path).name
        output_path.parent.mkdir(parents=True, exist_ok=True)
    last_part = remove
    if PATH_SEP in remove:
        last_part = remove.rsplit(PATH_SEP, 1)[1]
    if last_part.startswith("*"):
        for asset in vdf.fetch_assets():
            if asset.node.name.lower().endswith(last_part[1:].lower()):
                vdf.remove_asset(asset.node.name)
    elif last_part.endswith("*"):
        for asset in vdf.fetch_assets():
            if asset.node.name.lower().startswith(last_part[:-1].lower()):
                vdf.remove_asset(asset.node.name)
    else:
        asset = vdf.get_asset(last_part)
        if asset:
            vdf.remove_asset(asset.node.name)
    vdf.save(str(output_path), timestamp)


def add(
    vdf: Vdf, timestamp: str, add_args: list[str], output_path_: str | None = None
) -> None:
    if not add_args:
        raise ValueError("No files or directories specified for adding.")
    source_path = Path(add_args[0])
    vdf_destination = None
    if len(add_args) == 2:
        vdf_destination = add_args[1]
    if not source_path.exists() and not source_path.parent.exists():
        raise FileNotFoundError(f"Source path '{source_path}' does not exist.")

    def add_file(file_path: Path, vdf_path: str) -> None:
        try:
            if vdf.insert_asset(str(file_path), vdf_path) is None:
                print(
                    f"Warning: Asset '{vdf_path}' already exists in the VDF. Skipping."
                )
        except FileNotFoundError as e:
            raise
        except Exception as e:
            raise

    def add_directory(dir_path: Path, vdf_path: str) -> None:
        parent_name = (
            vdf_path + PATH_SEP + Path(dir_path).name
            if vdf_path
            else Path(dir_path).name
        )
        for item in dir_path.iterdir():
            if item.is_file():
                add_file(item, parent_name)
            elif item.is_dir():
                add_directory(item, parent_name)

    source_path_name = source_path.name
    if source_path.is_file():
        add_file(source_path, vdf_destination)
    elif source_path.is_dir():
        add_directory(source_path, vdf_destination)
    elif "*" in source_path_name:
        if source_path_name.startswith("*"):
            for file in source_path.parent.iterdir():
                if file.name.lower().endswith(source_path_name[1:].lower()):
                    add_file(file, vdf_destination)
        elif source_path_name.endswith("*"):
            for file in source_path.parent.iterdir():
                if file.name.lower().startswith(source_path_name[:-1].lower()):
                    add_file(file, vdf_destination)

    output_path = vdf.path
    if vdf.path == "":
        output_path = (Path.cwd() / vdf.name).with_suffix(EXTENSION)
    if output_path_:
        output_path = Path(output_path_)
        if not "." in output_path.name:
            output_path = Path(output_path_) / Path(vdf.name).with_suffix(EXTENSION)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Saving to {output_path}")
    vdf.save(str(output_path), timestamp)


def main():
    args = parse_args()

    try:
        vdf = get_input(args.input, args.new)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error while getting input: {e}")
        return

    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    if args.timestamp:
        timestamp = args.timestamp

    if args.debug:
        enable_logging()
    if args.list:
        vdf.print_vfs()

    if [
        args.unpack != None,
        args.extract != None,
        args.remove != None,
        args.add != None,
    ].count(True) > 1:
        print("Please specify only one of --unpack, --extract, --remove or --add")
        return

    if args.unpack:
        try:
            unpack(vdf, args.output)
        except Exception as e:
            print(f"Error while unpacking: {e}")
            print(f"{format_exc()}")
        return

    if args.extract:
        try:
            extract(vdf, args.output, args.extract)
        except Exception as e:
            print(f"Error while extracting: {e}")
            print(f"{format_exc()}")
        return

    if args.remove:
        try:
            remove(vdf, timestamp, args.remove, args.output)
        except Exception as e:
            print(f"Error while removing: {e}")
            print(f"{format_exc()}")
            return

    if args.add:
        try:
            add(vdf, timestamp, args.add, args.output)
        except (FileNotFoundError, ValueError) as e:
            print(f"Error while adding: {e}")
            print(f"{format_exc()}")
        except Exception as e:
            print(f"Error while adding: {e}")
            print(f"{format_exc()}")


if __name__ == "__main__":
    main()
