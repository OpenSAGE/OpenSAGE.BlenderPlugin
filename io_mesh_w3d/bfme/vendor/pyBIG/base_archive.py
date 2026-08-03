import enum
import logging
import os
import struct
from collections import namedtuple
from typing import IO, Dict, List, Optional, Tuple, Type, TypeVar

Entry = namedtuple("Entry", "name position size")
EntryEdit = namedtuple("EntryEdit", "name action content size")
FileList = List[Tuple[str, int, Optional[int]]]
T = TypeVar("T", bound="BaseArchive")


class FileAction(enum.Enum):
    ADD = 0
    REMOVE = 1


class MaxSizeError(Exception):
    pass


class BaseArchive:
    modified_entries: Dict[str, EntryEdit]
    entries: Dict[str, Entry]

    @staticmethod
    def _unpack(file: IO) -> Tuple[List[Entry], str]:
        """Get a list of files in the big"""
        entries = {}
        file.seek(0)

        # header
        header = file.read(4).decode("utf-8")

        file_size = struct.unpack("<I", file.read(4))[0]
        logging.info(f"size: {file_size}")
        archive_count, index_size = struct.unpack(">II", file.read(8))
        logging.info(f"entry count: {archive_count}")
        logging.info(f"index size: {index_size}")

        index_data = file.read(index_size)
        buf = memoryview(index_data)
        offset = 0
        entry_struct = struct.Struct(">II")

        for _ in range(archive_count):
            position, entry_size = entry_struct.unpack_from(buf, offset)
            offset += entry_struct.size

            end = buf[offset:].tobytes().find(b"\x00")
            name = buf[offset : offset + end].tobytes().decode("latin-1")
            offset += end + 1

            logging.debug(f"name: {name}")
            logging.debug(f"position: {position}")
            logging.debug(f"file size: {entry_size}")

            entries[name] = Entry(name, position, entry_size)

        return entries, header

    def _create_file_list(self) -> Tuple[FileList, int, int]:
        """Re-gather the necessary information on each file in the archive
        while taking into account the modifications made by the user since
        then.
        """
        file_list = []
        file_count = 0
        total_size = 0

        for name in self.file_list():
            if name in self.modified_entries:
                entry = self.modified_entries[name]
                entry_size = len(entry.content)
                logging.info(f"applying change from modified entries for {name}")
            else:
                entry = self.entries[name]
                entry_size = entry.size

            file_list.append((entry.name, entry_size))
            file_count += 1
            total_size += entry_size

        file_list.sort(key=lambda x: x[0])
        return file_list, total_size, file_count

    def _pack_file_list(
        self,
        archive_file: IO,
        file_list: List[Tuple[str, int]],
        total_size: int,
        file_count: int,
        header: str,
    ):
        """Index the files and append the raw data to create a complete archive"""
        entries = {}

        # header, charstring, 4 bytes - always BIG4 or something similiar
        archive_file.write(header.encode("utf-8"))

        # https://github.com/chipgw/openbfme/blob/master/bigreader/bigarchive.cpp
        # /* 8 bytes for every entry, the entry, a blank bytes, and 20 at the start and end. */
        first_entry = 20
        for file in file_list:
            first_entry += len(file[0]) + 1 + 8

        # total file size, unsigned integer, 4 bytes, little endian byte order
        size = total_size + first_entry + 1
        logging.info(f"size: {size}")

        try:
            archive_file.write(struct.pack("<I", size))
        except struct.error as e:
            raise MaxSizeError("File bigger than supporter by BIG format") from e

        # number of embedded files, unsigned integer, 4 bytes, big endian byte order
        logging.info(f"entry count: {file_count}")
        archive_file.write(struct.pack(">I", file_count))

        # total size of index table in bytes, unsigned integer, 4 bytes, big endian byte order
        logging.info(f"index size: {first_entry}")
        archive_file.write(struct.pack(">I", first_entry))

        # Put the first file one byte after the end of the header.
        position = 1

        logging.info("packing file list...")
        entry_struct = struct.Struct(">II")
        for file in file_list:
            # position of embedded file within BIG-file, unsigned integer, 4 bytes, big endian byte order
            # size of embedded data, unsigned integer, 4 bytes, big endian byte order
            logging.debug("packing %s", file[0])
            pos_size = entry_struct.pack(first_entry + position, file[1])

            # file name, cstring, ends with null byte
            name = file[0].encode("latin-1") + b"\x00"
            archive_file.write(pos_size + name)

            entries[file[0]] = Entry(file[0], first_entry + position, file[1])

            position += file[1]

        # not sure what's this but I think we need it see:
        # https://github.com/chipgw/openbfme/blob/master/bigreader/bigarchive.cpp
        archive_file.write(b"L253")
        archive_file.write(b"\0")
        logging.info("DONE packing file list")

        return entries

    @staticmethod
    def _pack_archive_from_directory(archive: T, path: str) -> T:
        logging.info("building archive from folder")
        for dir_name, _, file_list in os.walk(path):
            for filename in file_list:
                file_path = os.path.join(dir_name, filename)
                name = file_path.replace(path, "")[1:].replace("/", "\\")

                with open(file_path, "rb") as f:
                    logging.debug("adding %s", name)
                    archive.add_file(name, f.read())

        archive._pack()
        logging.info("done building archive from folder")
        return archive

    def file_exists(self, name: str) -> bool:
        """Check if a file exists

        Params
        -------
        name : str
            Name of the file, usually something like data\\ini\\weapon.ini

        Returns
        --------
        bool
            True if the file exists, else false
        """
        if name in self.modified_entries:
            return self.modified_entries[name].action is not FileAction.REMOVE

        return name in self.entries

    def file_list(self) -> List[str]:
        """Return a list of file names, compiling both actual files
        currently in the archive and new/removed files waiting
        to be repacked.

        Returns
        --------
        List[str]
            The list of file names
        """
        file_list = list(
            {
                *[
                    name
                    for name in self.entries.keys()
                    if self.modified_entries.get(name, EntryEdit(name, None, None, 0)).action
                    is not FileAction.REMOVE
                ],
                *[
                    name
                    for name, file in self.modified_entries.items()
                    if file.action is not FileAction.REMOVE
                ],
            }
        )
        file_list.sort()

        return file_list

    def get_file_entry(self, name: str) -> Entry:
        """Get the file entry for a given file name.

        Params
        -------
        name : str
            Name of the file, usually something like data\\ini\\weapon.ini

        Returns
        -------
        Entry
            The file entry. If the file is part of the edited files
            position will be -1.
        """
        if not self.file_exists(name):
            raise KeyError(f"File '{name}' does not exist.")

        if name in self.modified_entries:
            entry = self.modified_entries[name]
            return Entry(name, -1, entry.size)

        return self.entries[name]

    def read_file(self, name: str) -> bytes:
        """Get the raw bytes of the file if the file exists. This method has
        the advantage over simply accessing Archive.entries that it will
        also check pending modified entries

        Params
        -------
        name : str
            Name of the file, usually something like data\\ini\\weapon.ini

        Returns
        -------
        bytes
            File bytes

        Raises
        ------
            KeyError
                File not found
        """
        if not self.file_exists(name):
            raise KeyError(f"File '{name}' does not exist.")

        if name in self.modified_entries:
            return self.modified_entries[name].content

        return self._get_file(name)

    def add_file(self, name: str, content: bytes):
        """Mark a file to be added. This does not modify the archive itself yet.
        You need to call Archive.repack for the archive to be actually modified.
        However, the get methods of the class take in account modified entries.

        The method will not permit adding a file that already exists.

        Params
        -------
        name : str
            Name of the file, usually something like data\\ini\\weapon.ini
        content : bytes
            File bytes to be added

        Raises
        ------
            KeyError
                File already exists
            ValueError
                File name contains forbidden characters
        """
        if self.file_exists(name):
            raise KeyError(f"File '{name}' already exists.")

        if "/" in name:
            raise ValueError(f"File '{name}' cannot contain '/', use '\\' instead.")

        self.modified_entries[name] = EntryEdit(name, FileAction.ADD, content, len(content))

    def edit_file(self, name: str, content: bytes):
        """Edit an existing file with new content. This does not actually modify
        the file yet. The method cannot edit a file that hasn't been added yet, either
        as a modified entry or already present in the archive.

        Params
        -------
        name : str
            Name of the file, usually something like data\\ini\\weapon.ini
        content : bytes
            File bytes

        Raises
        ------
            KeyError
                File not found
        """
        if not self.file_exists(name):
            raise KeyError(f"File '{name}' does not exist.")

        self.modified_entries[name] = EntryEdit(name, FileAction.ADD, content, len(content))

    def remove_file(self, name: str):
        """Mark as existing file for deletion. The deletion will only happen once
        the archive has been repacked.

        Params
        -------
        name : str
            Name of the file, usually something like data\\ini\\weapon.ini

        Raises
        ------
            KeyError
                File not found
        """
        if not self.file_exists(name):
            raise KeyError(f"File '{name}' does not exist.")

        self.modified_entries[name] = EntryEdit(name, FileAction.REMOVE, None, 0)

    def extract(self, output: str, *, files: List[str] = None):
        """Extract the contents of the archive to a folder.

        Params
        -------
        output : str
            The folder to extract everything to
        files : Optional[List[str]]
            The list of files to extract
        """
        if files is None:
            files = self.file_list()

        for name in files:
            file = self.read_file(name)
            path = os.path.normpath(os.path.join(output, name).replace("\\", "/"))

            # create the directories if they don't exist.
            file_dir = os.path.dirname(path)
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)

            with open(path, "wb") as f:
                f.write(file)

    def repack(self):
        """Update the archive to include all the modified entries. This clears
        the list and updates the archive with the new data.
        """
        self._pack()

    def archive_memory_size(self) -> int:
        """Get the current in memory size of all the modifies entries that
        have not yet been saved. You can use this to decide when you would
        like to save in relation to the capacities of your machine.
        """
        return sum(
            [
                len(entry.content)
                for entry in self.modified_entries.values()
                if entry.action is FileAction.ADD
            ]
        )

    def _get_file(self, name: str) -> bytes:
        """Archive specific method for retrieving file bytes from
        the archive.
        """

        raise NotImplementedError

    def _pack(self):
        """Rewrite the archive with the modifications stored
        in self.modified_entries.
        """

        raise NotImplementedError

    def _pack_files(
        self, raw_data_file: IO, file_list: FileList, total_size: int, file_count: int
    ):
        """Combine all files into a single raw data bundle"""

        raise NotImplementedError

    def save(self, path: str):
        """Save the archive to a file.

        Params
        -------
        path : str
            The path to save to. Something like 'path/to/file/test.big'
        """
        raise NotImplementedError

    @classmethod
    def from_directory(cls: Type[T], path: str, header: str = "BIG4", **kwargs) -> T:
        """Generate a BIG archive from a directory. This is useful for
        compiling an archive without adding each file manually. You simply
        give the top level directory and every file will be added recursively.

        Params
        -------
        path : str
            Path to the top level folder of the files you wish to compile
        header : str
            The type of the archive, either BIG4 or BIGF

        Returns
        --------
        Archive
            Compiled archived
        """
        raise NotImplementedError

    @classmethod
    def empty(cls: Type[T], header: str = "BIG4", **kwargs) -> T:
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

        raise NotImplementedError

    def bytes(self) -> bytes:
        """Returns the archive data as bytes

        Returns
        --------
        bytes
            The archive data
        """

        raise NotImplementedError
