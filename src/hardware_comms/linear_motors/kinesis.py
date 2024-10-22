from .linear_motor import LinearMotor, StageOutOfBoundsException, StageNotCalibratedException

from pylablib.devices.Thorlabs import KinesisMotor
from pylablib.devices.Thorlabs.base import ThorlabsError
from pylablib.devices.Thorlabs.kinesis import list_kinesis_devices

'''
Class for all Thorlabs linear motors which 
use the Kinesis software stack
'''


class ThorlabsKinesisMotor(LinearMotor):
    '''
    Instantiate by the serial number of the control module
    '''

    def __init__(self, how='first', serial_no=None):
        # auto-detect stage step -> distance calibration
        if how == 'first':
            self._idn = list_kinesis_devices()[0][0]
        else:
            self._idn = serial_no
        self.motor = KinesisMotor(self._idn, scale="stage")
        self._position = None
        if self.motor.get_scale_units() != 'm':
            raise StageNotCalibratedException(
                "No step to distance calibration found. Input this manually.")
    @property
    def idn(self):
        return self._idn

    @property
    def position(self):
        # default units are (m)
        try:
            self._position = self.motor.get_position()
        except ThorlabsError:
            pass
        return self._position

    def is_in_motion(self) -> bool:
        try:
            return self.motor.is_moving()
        except ThorlabsError:
            return True

    def move_abs(self, loc: float):
        if not (self.travel_limits[0] <= loc <= self.travel_limits[1]):
            raise StageOutOfBoundsException(
                "Location would exceed software limits")
        else:
            # default units are (m)
            try:
                self.motor.move_to(loc, scale=True)
            except ThorlabsError:
                pass

    def move_by(self, dist):
        # move the motor to the new position and update the position in micron
        if not (self.travel_limits[0] <= (dist + self.position) <= self.travel_limits[1]):
            raise StageOutOfBoundsException(
                "Location would exceed software limits")
        else:
            try:
                self.motor.move_by(distance=dist)
            except ThorlabsError:
                pass
    # def wait_move_finish(self, interval):
        # self.motor.wait_move()

    def stop(self, blocking=True) -> None:
        try:
            self.motor.stop(sync=blocking)
        except ThorlabsError:
            pass

    def home(self, blocking=False) -> None:
        try:
            self.motor.home(sync=blocking)
        except ThorlabsError:
            pass

    def close(self) -> None:
        self.motor.close()
