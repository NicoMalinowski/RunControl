import time
from abc import ABC, abstractmethod
from Wrapper import state_wrapper
from typing import Optional
import Run

class HighVoltageState(ABC):

    # static variable
    defaultHV = "-120"
    
    def ramp_high_voltage_to(self, run: Run, high_voltage_value: str) -> None:
        run.send_data("HV_SO", "1")
        run.send_data("HV_RT", high_voltage_value)
        
        time.sleep(1)
        ramp_to_state = run.get_data("GetHighVoltageState")
        print(f"High voltage in state '{ramp_to_state}'")
        
        while ramp_to_state == "Ramp_To":
            time.sleep(1)
            ramp_to_state = run.get_data("GetHighVoltageState")
        
        if ramp_to_state == "Ramp_To_Failed":
            raise ValueError(f"High voltage in state '{ramp_to_state}', aborting")
        
        print(f"High voltage in state '{ramp_to_state}', proceeding")
    
    def ramp_high_voltage_down(self, run: Run) -> None:
        run.send_data("HV_RD", "1")
        
        time.sleep(3)
        rampdown_state = run.get_data("GetHighVoltageState")
        print(f"High voltage in state '{rampdown_state}'")
        
        while rampdown_state == "Rampdown":
            time.sleep(1)
            rampdown_state = run.get_data("GetHighVoltageState")
        
        if rampdown_state == "Rampdown_Failed":
            HVV=run.get_data("GetHighVoltage")
            print(f"HV:{HVV} V")
            if HVV!=0 or HVV!="0":
                print("ramp down failed setting voltage to 0")
                run.send_data("HV_U",0)
                time.sleep(2)
                run.send_data("HV_SO", "0")
                time.sleep(1)
                run.send_data("HV_U",0)
                time.sleep(1)
                run.send_data("HV_SO", "1")
            time.sleep(1)
            HVV=run.get_data("GetHighVoltage")
            rampdown_state = run.get_data("GetHighVoltageState")
            print(f"HV:{HVV} V")
            if HVV>=1 and rampdown_state=="Running":
               raise ValueError(f"High voltage in state '{rampdown_state}', aborting") 

        
        print(f"High voltage in state '{rampdown_state}', proceeding")
        
    @abstractmethod
    def set_high_voltage(self, run: Run, high_voltage: Optional[str] = None) -> None:
        pass
    
class HVoff(HighVoltageState):    
    @state_wrapper
    def set_high_voltage(self, run: Run, high_voltage: Optional[str] = None) -> None:
        self.ramp_high_voltage_down(run)
        
class HVonDefault(HighVoltageState):    
    @state_wrapper
    def set_high_voltage(self, run: Run, high_voltage: Optional[str] = None) -> None:
        # w.w. lower default value for testing
        # self.ramp_high_voltage_to(run, high_voltage_value="-120")
        self.ramp_high_voltage_to(run, high_voltage_value=HighVoltageState.defaultHV)
        
class HVonCustom(HighVoltageState):    
    @state_wrapper
    def set_high_voltage(self, run: Run, high_voltage: Optional[str] = None) -> None:
        self.ramp_high_voltage_to(run, high_voltage_value=high_voltage)
