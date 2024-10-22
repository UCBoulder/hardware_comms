from abc import ABC, abstractmethod
class Device(ABC):

    @abstractmethod
    def idn(self):
        '''Returns an identifying characteristic of the device'''
        pass

    @abstractmethod
    def close(self) -> None:
        '''Closes the backend to avoid hanging processes.'''
        pass


class DeviceCommsException(Exception):
    def __init__(self, message):
        self.message = message
