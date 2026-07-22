from aicage.errors import AicageError


class DockerError(AicageError):
    pass


class _RegistryDiscoveryError(DockerError):
    """Raised when registry discovery fails."""
