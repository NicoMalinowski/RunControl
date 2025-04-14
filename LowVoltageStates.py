import time
from abc import ABC, abstractmethod
from Wrapper import state_wrapper
from typing import Optional
from typing import List
import Run

class LowVoltageState(ABC):
    def __init__(self, LV_channels: List[str] = ["1","2","3","4"]) -> None:
         super().__init__()
         self.LV_channels = LV_channels
    
    def low_voltage_on(self, run: Run) -> None:
        for module in self.LV_channels:
                run.send_data("CH_S"+module, "1")
                time.sleep(1)
        print("Low voltage channels turned off.")
        run.send_data("M_S", "1")
        print(f"Low voltage master switch turned on.")
    
    def low_voltage_off(self, run: Run) -> None:
        for module in ["1","2","3","4"]:
                run.send_data("CH_S"+module, "0")
                time.sleep(1)
        print("Low voltage channels turned off.")
        run.send_data("M_S", "0")
        print(f"Low voltage master switch turned off.")
    
    def set_low_voltage_U(self, run: Run, low_voltage_U_value: str) -> None:
        for module in self.LV_channels:
                run.send_data("LV_U"+module, low_voltage_U_value)
                time.sleep(1)
        print(f"Low voltage set to {low_voltage_U_value}V.")
    
    def set_low_voltage_I(self, run: Run, low_voltage_I_value: str) -> None:
        for module in self.LV_channels:
                run.send_data("LV_I"+module, low_voltage_I_value)
                time.sleep(1)
        print(f"Low voltage current set to {low_voltage_I_value}A.")
        
    @abstractmethod
    def set_low_voltage(self, run: Run, low_voltage_U: Optional[str] = None, low_voltage_I: Optional[str] = None) -> None:
        pass
    
class LVoff(LowVoltageState):
    @state_wrapper
    def set_low_voltage(self, run: Run, low_voltage_U: Optional[str] = None, low_voltage_I: Optional[str] = None) -> None:
        self.low_voltage_off(run)
        self.set_low_voltage_U(run, "0")
        self.set_low_voltage_I(run, "0")
        
class LVonDefault(LowVoltageState):
    @state_wrapper
    def set_low_voltage(self, run: Run, low_voltage_U: Optional[str] = None, low_voltage_I: Optional[str] = None) -> None:
        self.set_low_voltage_U(run, "3")
        self.set_low_voltage_I(run, "5.88")
        self.low_voltage_on(run)
        
class LVonCustom(LowVoltageState):
    @state_wrapper  
    def set_low_voltage(self, run: Run, low_voltage_U: Optional[str] = None, low_voltage_I: Optional[str] = None) -> None:
        self.set_low_voltage_U(run, low_voltage_U)
        self.set_low_voltage_I(run, low_voltage_I)
        self.low_voltage_on(run)