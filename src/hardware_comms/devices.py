from abc import ABC, abstractmethod

from pyvisa import ResourceManager 
from pyvisa.resources import MessageBasedResource
import numpy as np

class Device(ABC):

    @property
    @abstractmethod
    def idn(self):
        '''Returns an identifying characteristic of the device'''
        pass

    @abstractmethod
    def close(self) -> None:
        '''Closes the backend to avoid hanging processes.'''
        pass


class PyvisaDevice(Device):
    def __init__(self, resource_address):
        self.resource: MessageBasedResource = ResourceManager().open_resource(resource_address)
    
    def idn(self):
        return self.query("*IDN?")

    def query(self, message) -> str:
        return self.resource.query(message) 
    
    def query_list(self,message) -> np.ndarray:
        response = self.query(message)
        return np.array([float(x.strip()) for x in response.split(',')])

    def read(self) -> str:
        return self.resource.read()

    def write(self, message) -> str:
        self.resource.write(message) 

    def close(self):
        self.resource.close() 
        

class DeviceCommsException(Exception):
    def __init__(self, message):
        self.message = message
