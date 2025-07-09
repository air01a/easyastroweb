import win32com.client
from pydantic import BaseModel
from typing import List
from enum import Enum
from utils.logger import logger



# Les enums que tu avais
class AlignmentMode(int, Enum):
    ALT_AZ = 0
    POLAR = 1
    GERMAN_POLAR = 2

class TelescopePosition(BaseModel):
    right_ascension: float
    declination: float
    altitude: float
    azimuth: float
    side_of_pier: int
    tracking: bool
    slewing: bool

class ASCOMComTelescopeClient:
    """Client ASCOM COM pour télescope avec la même API que la version Alpaca."""

    def __init__(self, prog_id="ASCOM.Simulator.Telescope"):
        self.device = win32com.client.Dispatch(prog_id)

    def connect(self) -> bool:
        self.device.Connected = True
        return self.device.Connected

    def disconnect(self) -> bool:
        self.device.Connected = False
        return not self.device.Connected

    def is_connected(self) -> bool:
        return self.device.Connected

    def get_telescope_info(self):
        """Retourne un dict simplifié, tu peux créer un Pydantic si tu veux."""
        return {
            "Name": self.device.Name,
            "Description": self.device.Description,
            "DriverVersion": self.device.DriverVersion,
            "InterfaceVersion": self.device.InterfaceVersion,
            "CanPark": self.device.CanPark,
            "CanSlew": self.device.CanSlew,
            "CanSync": self.device.CanSync,
            "AlignmentMode": self.device.AlignmentMode,
        }

    def get_position(self) -> TelescopePosition:
        return TelescopePosition(
            right_ascension=self.device.RightAscension,
            declination=self.device.Declination,
            altitude=self.device.Altitude,
            azimuth=self.device.Azimuth,
            side_of_pier=int(self.device.SideOfPier),
            tracking=self.device.Tracking,
            slewing=self.device.Slewing
        )

    def slew_to_coordinates(self, ra: float, dec: float) -> None:
        self.device.SlewToCoordinates(ra, dec)

    def slew_to_coordinates_async(self, ra: float, dec: float) -> None:
        self.device.SlewToCoordinatesAsync(ra, dec)

    def sync_to_coordinates(self, ra: float, dec: float) -> None:
        self.device.SyncToCoordinates(ra, dec)

    def set_utc_date(self, date: str) -> None:
        # ASCOM COM n'a pas UTCDate en settable sur tous les drivers
        raise NotImplementedError("Setting UTC date is not supported via COM in standard ASCOM.")

    def get_utc_date(self) -> str:
        return str(self.device.UTCDate)

    def abort_slew(self) -> None:
        self.device.AbortSlew()

    def set_tracking(self, enabled: bool) -> None:
        self.device.Tracking = enabled

    def is_tracking(self) -> bool:
        return self.device.Tracking

    def park(self) -> None:
        self.device.Park()

    def unpark(self) -> None:
        self.device.Unpark()

    def is_parked(self) -> bool:
        return self.device.AtPark

    def is_slewing(self) -> bool:
        return self.device.Slewing

    def move_axis(self, axis: int, rate: float) -> None:
        self.device.MoveAxis(axis, rate)

    def set_latitude(self, latitude: float) -> None:
        self.device.SiteLatitude = latitude

    def set_longitude(self, longitude: float) -> None:
        self.device.SiteLongitude = longitude

    def set_elevation(self, elevation: float) -> None:
        self.device.SiteElevation = elevation

    def get_altitude(self) -> float:
        return self.device.Altitude


class CameraState(int, Enum):
    IDLE = 0
    WAITING = 1
    EXPOSING = 2
    READING = 3
    DOWNLOAD = 4
    ERROR = 5

class ExposureSettings(BaseModel):
    duration: float = 1.0
    bin_x: int = 1
    bin_y: int = 1
    start_x: int = 0
    start_y: int = 0
    num_x: int = None
    num_y: int = None
    light: bool = True

class ImageData(BaseModel):
    width: int
    height: int
    data: List[List[int]]
    exposure_duration: float
    timestamp: str

class ASCOMComCameraClient:
    """Client ASCOM COM pour caméra"""
    def __init__(self, prog_id="ASCOM.Simulator.Camera"):
        self.device = win32com.client.Dispatch(prog_id)

    def connect(self) -> bool:
        self.device.Connected = True
        return self.device.Connected

    def disconnect(self) -> bool:
        self.device.Connected = False
        return not self.device.Connected

    def is_connected(self) -> bool:
        return self.device.Connected

    def get_camera_info(self):
        return {
            "CameraXSize": self.device.CameraXSize,
            "CameraYSize": self.device.CameraYSize,
            "MaxBinX": self.device.MaxBinX,
            "MaxBinY": self.device.MaxBinY,
            "PixelSizeX": self.device.PixelSizeX,
            "PixelSizeY": self.device.PixelSizeY,
            "HasShutter": self.device.HasShutter,
            "CanAbortExposure": self.device.CanAbortExposure,
            "CanStopExposure": self.device.CanStopExposure
        }

    def start_exposure(self, settings: ExposureSettings) -> None:
        self.device.BinX = settings.bin_x
        self.device.BinY = settings.bin_y
        self.device.StartX = settings.start_x
        self.device.StartY = settings.start_y
        self.device.NumX = settings.num_x or self.device.CameraXSize
        self.device.NumY = settings.num_y or self.device.CameraYSize
        self.device.StartExposure(settings.duration, settings.light)

    def abort_exposure(self) -> None:
        self.device.AbortExposure()

    def stop_exposure(self) -> None:
        self.device.StopExposure()

    def get_camera_state(self) -> CameraState:
        return CameraState(self.device.CameraState)

    def is_image_ready(self) -> bool:
        return self.device.ImageReady

    def get_image_array(self) -> ImageData:
        img_array = self.device.ImageArray
        return ImageData(
            width=len(img_array[0]),
            height=len(img_array),
            data=img_array,
            exposure_duration=self.device.LastExposureDuration,
            timestamp=str(self.device.LastExposureStartTime)
        )

    def set_ccd_temperature(self, temperature: float) -> None:
        self.device.SetCCDTemperature = temperature

    def get_ccd_temperature(self) -> float:
        return self.device.CCDTemperature

    def set_cooler_on(self, enabled: bool) -> None:
        self.device.CoolerOn = enabled

    def is_cooler_on(self) -> bool:
        return self.device.CoolerOn


class ASCOMComFocuserClient:
    """Client ASCOM COM pour focuser"""
    def __init__(self, prog_id="ASCOM.Simulator.Focuser"):
        self.device = win32com.client.Dispatch(prog_id)

    def connect(self) -> bool:
        self.device.Connected = True
        return self.device.Connected

    def disconnect(self) -> bool:
        self.device.Connected = False
        return not self.device.Connected

    def is_connected(self) -> bool:
        return self.device.Connected

    def get_focuser_info(self):
        return {
            "Absolute": self.device.Absolute,
            "MaxIncrement": self.device.MaxIncrement,
            "MaxStep": self.device.MaxStep,
            "StepSize": self.device.StepSize,
            "TempCompAvailable": self.device.TempCompAvailable
        }

    def move_absolute(self, position: int) -> None:
        self.device.Move(position)

    def move_relative(self, steps: int) -> None:
        current = self.device.Position
        self.device.Move(current + steps)

    def halt(self) -> None:
        self.device.Halt()

    def get_position(self) -> int:
        return self.device.Position

    def is_moving(self) -> bool:
        return self.device.IsMoving

    def get_temperature(self) -> float:
        return self.device.Temperature

    def set_temp_compensation(self, enabled: bool) -> None:
        self.device.TempComp = enabled

    def is_temp_compensation_enabled(self) -> bool:
        return self.device.TempComp

    def wait_for_movement_complete(self, timeout=60.0) -> bool:
        import time
        start = time.time()
        while time.time() - start < timeout:
            if not self.is_moving():
                return True
            time.sleep(0.1)
        return False


class ASCOMComFilterWheelClient:
    """Client ASCOM COM pour roue à filtres"""
    def __init__(self, prog_id="ASCOM.Simulator.FilterWheel"):
        self.device = win32com.client.Dispatch(prog_id)

    def connect(self) -> bool:
        self.device.Connected = True
        return self.device.Connected

    def disconnect(self) -> bool:
        self.device.Connected = False
        return not self.device.Connected

    def is_connected(self) -> bool:
        return self.device.Connected

    def get_position(self) -> int:
        return self.device.Position

    def set_position(self, position: int) -> None:
        self.device.Position = position

    def get_names(self) -> List[str]:
        return list(self.device.Names)

    def get_filterwheel_info(self):
        return {
            "Names": list(self.device.Names),
            "FocusOffsets": list(self.device.FocusOffsets),
            "Position": self.device.Position
        }


focuser = ASCOMComFocuserClient("ASCOM.Simulator.Focuser")
focuser.connect()
print("Position:", focuser.get_position())
focuser.move_absolute(1000)
focuser.disconnect()