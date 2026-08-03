from .disk_archive import InDiskArchive
from .memory_archive import InMemoryArchive

Archive = InMemoryArchive
LargeArchive = InDiskArchive

__version__ = "0.6.6"

__all__ = ["InMemoryArchive", "InDiskArchive", "Archive", "LargeArchive"]
