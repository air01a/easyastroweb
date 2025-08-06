from pyindi_client import PyIndi
from pydantic import BaseModel
from typing import List
from enum import Enum
import time
from enum import Enum
from pydantic import BaseModel
from typing import Optional


class INDIBaseClient:
    def __init__(self, device_name: str, host="localhost", port=7624):
        self.device_name = device_name
        self.client = PyIndi.IndiClient()
        self.client.setServer(host, port)
        self.client.connectServer()
        self.device = None
        self._wait_for_device()

    def _wait_for_device(self, timeout=5.0):
        start = time.time()
        while time.time() - start < timeout:
            self.device = self.client.getDevice(self.device_name)
            if self.device:
                break
            time.sleep(0.1)

    def _get_number(self, prop, elem):
        vector = self.device.getNumber(prop)
        return vector[elem].value if vector else None

    def _set_number(self, prop, values: dict):
        vector = self.device.getNumber(prop)
        if vector:
            for k, v in values.items():
                if k in vector:
                    vector[k].value = v
            self.client.sendNewNumber(vector)

    def _set_switch(self, prop, on_label):
        vector = self.device.getSwitch(prop)
        if vector:
            for k in vector:
                vector[k].s = PyIndi.ISS_OFF
            if on_label in vector:
                vector[on_label].s = PyIndi.ISS_ON
            self.client.sendNewSwitch(vector)



class AlignmentMode(int, Enum):
    ALT_AZ = 0
    POLAR = 1
    GERMAN_POLAR = 2


class TelescopePosition(BaseModel):
    right_ascension: float
    declination: float
    altitude: float
    azimuth: float
    side_of_pier: int = 0  # Non géré par INDI en standard
    tracking: bool
    slewing: bool


class INDITelescopeClient(INDIBaseClient):
    def __init__(self, device_name="Telescope Simulator", host="localhost", port=7624):
        super().__init__(device_name, host, port)

    def connect(self) -> bool:
        return self.device is not None

    def is_connected(self) -> bool:
        return self.device is not None and self.device.isConnected()

    def get_telescope_info(self) -> dict:
        return {
            "Name": self.device_name,
            "CanPark": self.device.getSwitch("TELESCOPE_PARK") is not None,
            "CanSync": self.device.getNumber("EQUATORIAL_EOD_COORD") is not None,
            "CanSlew": self.device.getNumber("EQUATORIAL_EOD_COORD") is not None,
            "AlignmentMode": AlignmentMode.ALT_AZ  # Non exposé directement par INDI
        }

    def get_position(self) -> Optional[TelescopePosition]:
        ra = self._get_number("EQUATORIAL_EOD_COORD", "RA")
        dec = self._get_number("EQUATORIAL_EOD_COORD", "DEC")
        alt = self._get_number("HORIZONTAL_COORD", "ALT")
        az = self._get_number("HORIZONTAL_COORD", "AZ")
        tracking = self._get_switch("TELESCOPE_TRACK_STATE", "TRACK_ON")
        slewing = self._get_switch("TELESCOPE_MOTION_NS", "MOTION_NORTH") or self._get_switch("TELESCOPE_MOTION_EW", "MOTION_EAST")

        if ra is None or dec is None:
            return None

        return TelescopePosition(
            right_ascension=ra,
            declination=dec,
            altitude=alt or 0.0,
            azimuth=az or 0.0,
            tracking=tracking,
            slewing=slewing
        )

    def slew_to_coordinates(self, ra: float, dec: float) -> None:
        self._set_number("EQUATORIAL_EOD_COORD", {
            "RA": ra,
            "DEC": dec
        })

    def sync_to_coordinates(self, ra: float, dec: float) -> None:
        self._set_number("EQUATORIAL_COORD", {
            "RA": ra,
            "DEC": dec
        })

    def abort_slew(self) -> None:
        self._set_switch("TELESCOPE_ABORT_MOTION", "ABORT")

    def set_tracking(self, enabled: bool) -> None:
        self._set_switch("TELESCOPE_TRACK_STATE", "TRACK_ON" if enabled else "TRACK_OFF")

    def is_tracking(self) -> bool:
        return self._get_switch("TELESCOPE_TRACK_STATE", "TRACK_ON")

    def is_slewing(self) -> bool:
        return self._get_switch("TELESCOPE_MOTION_NS", "MOTION_NORTH") or self._get_switch("TELESCOPE_MOTION_EW", "MOTION_EAST")

    def park(self) -> None:
        self._set_switch("TELESCOPE_PARK", "PARK")

    def unpark(self) -> None:
        self._set_switch("TELESCOPE_PARK", "UNPARK")

    def is_parked(self) -> bool:
        return self._get_switch("TELESCOPE_PARK", "PARK")


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
    light: bool = True


class ImageData(BaseModel):
    width: int
    height: int
    data: List[List[int]]
    exposure_duration: float
    timestamp: str





class INDICameraClient(INDIBaseClient):
    def start_exposure(self, settings: ExposureSettings):
        self._set_number("CCD_BINNING", {"HOR_BIN": settings.bin_x, "VER_BIN": settings.bin_y})
        self._set_number("CCD_EXPOSURE", {"CCD_EXPOSURE_VALUE": settings.duration})

    def is_image_ready(self) -> bool:
        blob = self.device.getBLOB("CCD1")
        return blob is not None

    def get_image_blob(self):
        blob = self.device.getBLOB("CCD1")
        if blob:
            return blob.getblobdata()
        return None


class INDIFocuserClient(INDIBaseClient):
    def move_absolute(self, position: int):
        self._set_number("FOCUS_ABSOLUTE_POSITION", {"FOCUS_ABSOLUTE_POSITION_VALUE": position})

    def move_relative(self, steps: int):
        current = self._get_number("FOCUS_ABSOLUTE_POSITION", "FOCUS_ABSOLUTE_POSITION_VALUE")
        if current is not None:
            self.move_absolute(current + steps)

    def get_position(self) -> Optional[int]:
        return self._get_number("FOCUS_ABSOLUTE_POSITION", "FOCUS_ABSOLUTE_POSITION_VALUE")

    def is_moving(self) -> bool:
        motion = self.device.getSwitch("FOCUS_MOTION")
        if motion:
            return motion.s == PyIndi.IPS_BUSY
        return False


class INDIFilterWheelClient(INDIBaseClient):
    def set_position(self, position: int):
        self._set_number("FILTER_SLOT", {"FILTER_SLOT_VALUE": position})

    def get_position(self) -> Optional[int]:
        return self._get_number("FILTER_SLOT", "FILTER_SLOT_VALUE")

    def get_names(self) -> List[str]:
        names_vector = self.device.getText("FILTER_NAME")
        if names_vector:
            return [names_vector[key].text for key in names_vector]
        return []
