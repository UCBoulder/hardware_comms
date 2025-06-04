from ..devices import Device 


from abc import abstractmethod
from time import sleep


class LinearMotor(Device):
    '''
    Abstract class for linear motors. Implement this with a subclass for
    new motor devices.
    '''
    @property
    def travel_limits(self) -> tuple[float]:
        '''
        Software limits for the stage

        returns: (lower bound, upper bound), in meters 
        raises: StageLimitsNotSetException if limits are not
        set
        '''
        try:
            return self._travel_limits
        except AttributeError:
            raise StageLimitsNotSetException(
                "Motor software limits not initialized")


    @travel_limits.setter
    def travel_limits(self, limits: tuple[float]) -> None:
        '''
        Sets software limits of the stage. Should be initialized in 
        .connect_devices.connect_devices() or the constructor for the
        subclass.

        limits: listlike containing (lower bound, upper bound), in meters 
        '''
        self._travel_limits = limits[:2]

    @property
    @abstractmethod
    def position(self) -> float:
        '''
        Get stage position in microns

        returns: location of the stage, in microns
        '''
        pass

    @abstractmethod
    def move_by(self, value: float) -> None:
        '''
        Move the relative position of the stage (micron units).

        value_um: distance of relative move (positive or negative), in meters
        raises: StageOutOfBoundException if the move would exceed
        the software limits of the stage.
        '''
        pass


    @abstractmethod
    def move_abs(self, value: float) -> None:
        '''
        Move to an absolute location (micron units).

        value: desired stage location, in meters
        raises: StageOutOfBoundException if the move would exceed
        the software limits of the stage.
        '''
        pass


    @abstractmethod
    def home(self, blocking=False) -> None:
        '''
        Home the stage. 

        blocking: True if program should pause until the stage is homed.
        False otherwise.
        '''
        pass

    @abstractmethod
    def is_in_motion(self) -> bool:
        '''
        Checks if the stage is in motion.

        returns: True if stage is in motion. False otherwise.
        '''
        pass

    def wait_move_finish(self, interval):
        '''override this if there is a built-in method'''
        while self.is_in_motion():
            sleep(interval)

    @abstractmethod
    def stop(self, blocking=True) -> None:
        '''
        Stops the stage, interrupting any current operations.

        blocking: True if program should pause until the stage is homed.
        False otherwise.
        '''
        pass


class StageOutOfBoundsException(Exception):
    def __init__(self, message):
        self.message = message


class StageLimitsNotSetException(Exception):
    def __init__(self, message):
        self.message = message


class StageNotCalibratedException(Exception):
    def __init__(self, message):
        self.message = message