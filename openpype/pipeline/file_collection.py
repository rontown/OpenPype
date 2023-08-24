"""Utility functions for file sequences and collections
"""
import os
import re
import clique
from openpype.lib import Logger
from openpype.pipeline import frames


def collect_filepaths_from_sequential_path(
    file_path,
    frame_start=None,
    frame_end=None,
    only_existing=False,
):
    """Generate expected files from path

    Args:
        file_path (str): Path to generate expected files from
        frame_start (Optional[int]): Start frame of the sequence
        frame_end (Optional[int]): End frame of the sequence
        only_existing (Optional[bool]): Ensure that files exists.

    Returns:
        Any[list[str], str]: List of absolute paths to files
            (frames of a sequence) or path if single file
    """

    dirpath = os.path.dirname(file_path)
    filename = os.path.basename(file_path)

    formattable_string = convert_filename_to_formattable_string(
        filename)

    if (
        not formattable_string
        or frame_start is None
        or frame_end is None
    ):
        return file_path

    expected_files = []
    for frame in range(int(frame_start), (int(frame_end) + 1)):
        frame_file_path = os.path.join(
            dirpath, formattable_string.format(frame)
        )
        # normalize path
        frame_file_path = os.path.normpath(frame_file_path)

        # make sure file exists if ensure_exists is enabled
        if only_existing and not os.path.exists(frame_file_path):
            continue

        # add to expected files
        expected_files.append(
            # add normalized path
            frame_file_path
        )

    return expected_files


def generate_expected_filepaths(
    frame_start,
    frame_end,
    path,
):
    """Generate expected files from path

    Args:
        frame_start (int): Start frame of the sequence
        frame_end (int): End frame of the sequence
        path (str): Path to generate expected files from

    Returns:
        Any[list[str], str]: List of expected absolute paths to files
            (frames of a sequence) or path if single file
    """
    return collect_filepaths_from_sequential_path(
        frame_start,
        frame_end,
        path,
        only_existing=False,
    )


def collect_basenames_from_sequential_path(
    file_path,
    frame_start=None,
    frame_end=None,
    only_existing=False,
):
    """Collect files from sequential path

    Args:
        file_path (str): Absolute path with any sequential pattern (##, %02d)
        frame_start (Optional[int]): Start frame of the sequence
        frame_end (Optional[int]): End frame of the sequence
        only_existing (Optional[bool]): Ensure that files exists.

    Returns:
        list[str]: List of collected file names
            (frames of a sequence) or path if single file
    """

    collected_abs_filepaths = collect_filepaths_from_sequential_path(
        file_path,
        frame_start,
        frame_end,
        only_existing,
    )

    if isinstance(collected_abs_filepaths, list):
        return [os.path.basename(f_) for f_ in collected_abs_filepaths]

    # return single file in list
    return [os.path.basename(collected_abs_filepaths)]


def convert_filename_to_formattable_string(filename):
    """Convert filename to formattable string

    Args:
        filename (str): Filename to convert

    Returns:
        Any[str, None]: Formattable string or None if not possible
                        to convert
    """
    new_filename = None

    if "#" in filename:
        # use regex to convert #### to {:0>4}
        def replace(match):
            return "{{:0>{}}}".format(len(match.group()))
        new_filename = re.sub("#+", replace, filename)

    elif "%" in filename:
        # use regex to convert %04d to {:0>4}
        def replace(match):
            return "{{:0>{}}}".format(match.group()[1:])
        new_filename = re.sub("%\\d+d", replace, filename)

    return new_filename


def prepare_publishing_representation(
    instance,
    file_paths,
    frame_start=None,
    frame_end=None,
    reviewable=False,
    log=None,
):
    """Get representation with expected files.

    Args:
        instance (pyblish.Instance): instance
        file_paths (list): list of absolute file paths or single file path
        frame_start (Optional[int]): first frame
        frame_end (Optional[int]): last frame
        log (Optional[Logger]): logger
        only_existing (Optional[bool]): Ensure that files exists.
        reviewable (Optional[bool]): reviewable


    Returns:
        dict[str, Any]: representation
    """
    log = log or Logger.get_logger(__name__)
    file_ext = os.path.splitext(file_paths[0])[-1].lstrip(".")
    output_dir = os.path.dirname(file_paths[0])

    tags = []
    if reviewable:
        tags.append("review")

    # prepare base representation data
    representation = {
        "name": file_ext,
        "ext": file_ext,
        "stagingDir": output_dir,
        # QUESTION: should we use persistent staging dir always?
        "stagingDir_persistent": True,
        "tags": tags,
    }

    # getting frame range from files
    if (
        len(file_paths) > 1
        and frame_start is None
        and frame_end is None
    ):
        frame_start, frame_end = frames.get_frame_range_from_list_of_files(
            file_paths)

    # add frame range data
    if frame_start is not None:
        representation["frameStart"] = frame_start
    if frame_end is not None:
        representation["frameEnd"] = frame_end

    # collect file frames
    collected_file_frames = [
        os.path.basename(filepath)
        for filepath in file_paths
    ]

    # get families from instance and add family from data
    families = set(
        instance.data.get("families", []) + [instance.data["family"]]
    )
    # set slate frame
    if (
        "slate" in families
        # make sure frame range is set
        and _add_slate_frame_to_collected_frames(
            collected_file_frames, frame_start, frame_end)
    ):
        log.info("Slate frame added to collected frames.")
        representation["frameStart"] = frame_start - 1

    if len(collected_file_frames) == 1:
        representation["files"] = collected_file_frames.pop()
    else:
        representation["files"] = collected_file_frames

    return representation


def _add_slate_frame_to_collected_frames(
    collected_file_frames,
    frame_start=None,
    frame_end=None,
):
    """Add slate frame to collected frames.

    Args:
        collected_file_frames (list[str]): collected file frames
        frame_start (Optional[int]): first frame
        frame_end (Optional[int]): last frame

    Returns:
        Bool: True if slate frame was added
    """
    if (
        frame_start is None
        and frame_end is None
    ):
        return False

    frame_start_str = frames.get_frame_start_str(
        frame_start, frame_end)
    frame_length = int(frame_end - frame_start + 1)

    # add slate frame only if it is not already in collected frames
    if frame_length == len(collected_file_frames):
        frame_slate_str = frames.get_frame_start_str(
            frame_start - 1,
            frame_end
        )

        slate_frame = collected_file_frames[0].replace(
            frame_start_str, frame_slate_str)
        collected_file_frames.insert(0, slate_frame)

        return True


def get_single_filepath_from_list_of_files(collected_files):
    """Get single filepath from list of files.

    Args:
        collected_files (list[str]): list of files

    Returns:
        Any[str, None]: single filepath or None if not possible
    """
    collections, reminders = clique.assemble(collected_files)
    if collections:
        return collections[0].format("{head}{padding}{tail}")
    elif reminders:
        return reminders[0]
