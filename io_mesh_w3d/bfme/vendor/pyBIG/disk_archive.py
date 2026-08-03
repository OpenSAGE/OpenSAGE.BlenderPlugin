import logging
import os
import shutil
import tempfile
from typing import IO, Type, TypeVar

from .base_archive import BaseArchive, FileList

T = TypeVar("T", bound="InDiskArchive")


class InDiskArchive(BaseArchive):
    """This implementation stores as few things possible in memory, preferring
    to use disk space in the temp folder instead. This allows loading large
    archives into memory with minimal impact on memory usage. Assume all changes made
    are directly applied to the data in the disk.

    Params
    -------
    file_path : str
        The path to the archive.
    """

    def __init__(self, file_path: str, *, entries=None, header: str = "BIG4"):
        self.file_path = file_path
        self.modified_entries = {}

        if not os.path.exists(file_path):
            raise ValueError(f"File {file_path} not found")

        if entries is None:
            with open(self.file_path, "rb") as f:
                self.entries, self.header = self._unpack(f)
        else:
            self.entries = entries
            self.header = header

    def __repr__(self):
        return f"< LargeArchive path={self.file_path} entries={len(self.entries)} dirty={bool(self.modified_entries)} >"

    def _pack(self, file_path=None):
        """Rewrite the archive with the modifications stores
        in self.modified_entries."""
        file_data = self._create_file_list()

        with tempfile.NamedTemporaryFile(delete=False) as fp:
            entries = self._pack_file_list(fp, *file_data, self.header)
            name = fp.name

            self._pack_files(fp, *file_data)

        path = file_path or self.file_path
        self.entries = entries
        shutil.move(name, path)
        self.modified_entries = {}

    def _pack_files(
        self, raw_data_file: IO, file_list: FileList, total_size: int, file_count: int
    ):
        """Combine all files into a single raw data bundle"""
        logging.info("packing files")

        # raw file data at the positions specified in the index
        with open(self.file_path, "rb") as existing_archive:
            for file in file_list:
                if file[0] in self.modified_entries:
                    file_entry = self.modified_entries[file[0]]
                    raw_data_file.write(file_entry.content)
                else:
                    file_entry = self.entries[file[0]]
                    existing_archive.seek(file_entry.position)
                    raw_data_file.write(existing_archive.read(file_entry.size))

        logging.info("finished packing files")

    def _get_file(self, name: str) -> bytes:
        """Get the contents of a specific file in the big based on file name"""
        entry = self.entries[name]
        with open(self.file_path, "rb") as f:
            f.seek(entry.position)
            return f.read(entry.size)

    def save(self, path: str = None):
        """Save the archive to a file.

        Params
        -------
        path : Optional[str]
            The new path to save to. Something like 'path/to/file/test.big'.
            Omit this if you just want to save in the same file.
        """
        self._pack(path)

    @classmethod
    def from_directory(
        cls: Type[T], path: str, header: str = "BIG4", *, file_path: str = None
    ) -> T:
        """Generate a BIG archive from a directory. This is useful for
        compiling an archive without adding each file manually. You simply
        give the top level directory and every file will be added recursively.

        Params
        -------
        path : str
            Path to the top level folder of the files you wish to compile
        header : str
            The type of the archive, either BIG4 or BIGF
        file_path : str
            Path to save the new archive

        Returns
        --------
        Archive
            Compiled archived
        """
        if file_path is None:
            raise ValueError("Please specify a file path")

        return cls._pack_archive_from_directory(cls.empty(header, file_path=file_path), path)

    @classmethod
    def empty(cls: Type[T], header: str = "BIG4", *, file_path: str = None) -> T:
        """Generate an empty archive.

        Params
        -------
        header : str
            The type of the archive, can either be BIG4 or BIGF. Defaults to BIG4
        file_path : str
            Path to save the new archive

        Returns
        --------
        Archive
            Empty archive
        """
        with open(file_path, "wb") as f:
            f.write(b"")

        return cls(file_path, entries={}, header=header)

    def bytes(self) -> bytes:
        """Returns the archive data as bytes

        Returns
        --------
        bytes
            The archive data
        """
        self._pack()

        with open(self.file_path, "rb") as f:
            return f.read()
