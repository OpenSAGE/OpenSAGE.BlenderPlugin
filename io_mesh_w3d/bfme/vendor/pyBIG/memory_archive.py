import io
import logging
from typing import IO, Type, TypeVar

from .base_archive import BaseArchive, FileList

T = TypeVar("T", bound="InMemoryArchive")


class InMemoryArchive(BaseArchive):
    """The core of the library, represents a BIG file and allows
    the user to mainpulate it programatically.

    This implementation stores as much as possible in memory to avoid
    creating unecessary clutter that needs to be cleaned up. All
    disk action need to be explicit through .save

    Params
    -------
    content : Optional[bytes]
        Raw bytes of the original big file

    """

    def __init__(self, content: bytes = b"", **kwargs):
        self.archive = io.BytesIO(content)
        self.entries = kwargs.get("entries")
        self.modified_entries = {}
        self.header = kwargs.get("header", "BIG4")

        if self.entries is None:
            self.entries, self.header = self._unpack(self.archive)

    def __repr__(self):
        return f"< Archive entries={len(self.entries)} dirty={bool(self.modified_entries)} >"

    def _pack(self):
        """Rewrite the archive with the modifications stored
        in self.modified_entries."""
        new_archive = io.BytesIO()

        file_data = self._create_file_list()
        entries = self._pack_file_list(new_archive, *file_data, self.header)

        self._pack_files(new_archive, *file_data)

        self.archive = new_archive
        self.entries = entries
        self.archive.seek(0)
        self.modified_entries = {}

    def _pack_files(
        self, raw_data_file: IO, file_list: FileList, total_size: int, file_count: int
    ):
        """Combine all files into a single raw data bundle"""

        logging.info("packing files")
        for file in file_list:
            if file[0] in self.modified_entries:
                file_entry = self.modified_entries[file[0]]
                raw_data_file.write(file_entry.content)
            else:
                raw_data_file.write(self._get_file(file[0]))
        logging.info("finished packing files")

    def _get_file(self, name: str) -> bytes:
        """Get the contents of a specific file in the big based on file name"""
        entry = self.entries[name]
        self.archive.seek(entry.position)
        return self.archive.read(entry.size)

    def save(self, path: str):
        """Save the archive to a file.

        Params
        -------
        path : str
            The path to save to. Something like 'path/to/file/test.big'
        """
        self._pack()
        with open(path, "wb") as f:
            f.write(self.archive.getvalue())

    @classmethod
    def from_directory(cls: Type[T], path: str, header: str = "BIG4") -> T:
        """Generate a BIG archive from a directory. This is useful for
        compiling an archive without adding each file manually. You simply
        give the top level directory and every file will be added recursively.

        Params
        -------
        path : str
            Path to the top level folder of the files you wish to compile
        header : str
            The type of archive, either BIG4 or BIGF. Defaults to BIG4

        Returns
        --------
        Archive
            Compiled archived
        """
        return cls._pack_archive_from_directory(cls.empty(header), path)

    @classmethod
    def empty(cls: Type[T], header: str = "BIG4") -> T:
        """Generate an empty archive.

        Params
        -------
        header : str
            The type of the archive, can either be BIG4 or BIGF. Defaults to BIG4

        Returns
        --------
        Archive
            Empty archive
        """
        return cls(entries={}, header=header)

    def bytes(self) -> bytes:
        """Returns the archive data as bytes

        Returns
        --------
        bytes
            The archive data
        """
        self._pack()

        return self.archive.getvalue()
