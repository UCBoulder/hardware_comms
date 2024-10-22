from ..device import Device

from abc import abstractmethod
import numpy as np

class Spectrometer(Device):

    '''
    Abstract class for spectrometers
    '''
    @abstractmethod
    def intensities(self) -> np.ndarray[np.float64]:
        '''
        The intensities read by each pixel in the spectrometer (in arbitrary units).

        returns: NDArray of floats corresponding to the intensity in arbitrary units
        '''
        pass

    @abstractmethod
    def wavelengths(self) -> np.ndarray[np.float64]:
        '''
        Returns the wavelength bins (in meters).

        returns: NDArray of floats enumerating the wavelength bins in meters
        '''
        pass

    @abstractmethod
    def spectrum(self) -> np.ndarray[np.float64]:
        '''
        Returns a 2-D list of the wavelengths (0) and intensities (1)

        returns: 2DArray where,
                [0] = wavelengths
                [1] = intensities
        '''
        pass
    @property

    @property
    @abstractmethod
    def integration_time(self) -> int:
        '''
        Reads the integration time in seconds.

        return: hardware integration time, in seconds
        '''
        pass

    @integration_time.setter
    @abstractmethod
    def integration_time(self, value) -> None:
        '''
        Sets the integration time in microseconds

        value: integration time, in microseconds
        '''
        pass

    @property
    @abstractmethod
    def scans_to_avg(self) -> int:
        '''
        Reads the number of scans averaged together in each
        spectrum.

        returns: number of averages per spectrum
        '''
        pass

    @scans_to_avg.setter
    @abstractmethod
    def scans_to_avg(self, N) -> None:
        '''
        Sets the number of scans averaged together in each spectrum.

        N: number of averages per spectrum
        '''
        pass

    @property
    @abstractmethod
    def integration_time_limits(self) -> tuple[int, int]:
        '''
        Returns the integration time in seconds.

        return: listlike of (lower bound, upper bound) in seconds
        '''
        pass

    @integration_time_limits.setter
    @abstractmethod
    def integration_time_limits(self) -> tuple[int, int]:
        '''
        Returns the integration time in seconds.

        return: listlike of (lower bound, upper bound) in seconds
        '''
        pass

    @abstractmethod
    def close(self) -> None:
        '''
        Closes the backend to avoid hanging processes.
        '''
        pass

class SpectrometerIntegrationException(Exception):
    def __init__(self, message):
        self.message = message


class SpectrometerAverageException(Exception):
    def __init__(self, message):
        self.message = message