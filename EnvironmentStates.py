import time
from abc import ABC, abstractmethod
from Wrapper import state_wrapper
from typing import Optional

import Run

class EnvironmentState(ABC):
    
    def get_average_chuck_temperature(self, run: Run) -> float:
        sum_temperatures = 0
        for module in [1,2,3,4]:
            sum_temperatures=sum_temperatures+float(run.get_data("TempPT100_"+str(module)))
        return sum_temperatures/4
    
    def set_and_wait_on_chiller(self, run: Run, set_temperature: str, temperature_tolerance: float = 3) -> None:
        run.send_data("CL_T", set_temperature)
        run.send_data("CL_P", "4")
        
        average_chuck_temperature = self.get_average_chuck_temperature(run)
        if abs(average_chuck_temperature-float(set_temperature))>temperature_tolerance:
            run.send_data("CL_SS", "1")
        time.sleep(1)
        
        print("Waiting for system to reach close to desired temperature")
        
        while abs(average_chuck_temperature-float(set_temperature))>temperature_tolerance:
            time.sleep(5)
            average_chuck_temperature = self.get_average_chuck_temperature(run)
        print(f"Chiller is now at {average_chuck_temperature}, waiting ceased.")
    
    @abstractmethod
    def set_environment(self, run: Run, temperature: Optional[str] = None) -> None:
        pass
    
class Idle(EnvironmentState):
    @state_wrapper
    def set_environment(self, run: Run, temperature: Optional[str] = None):
        self.set_and_wait_on_chiller(run, "21")

class Start(EnvironmentState):
    @state_wrapper
    def set_environment(self, run: Run, temperature: Optional[str] = None):
        self.set_and_wait_on_chiller(run, "21")
        run.send_data("CL_SS", "1")
    
class Off(EnvironmentState):
    @state_wrapper
    def set_environment(self, run: Run, temperature: Optional[str] = None):
        self.set_and_wait_on_chiller(run, "21")
        run.send_data("CL_SS", "0")
            
class Warm(EnvironmentState):
    @state_wrapper
    def set_environment(self, run: Run, temperature: Optional[str] = None):
        self.set_and_wait_on_chiller(run, "14")
        
class Cold(EnvironmentState):
    @state_wrapper
    def set_environment(self, run: Run, temperature: Optional[str] = None):
        self.set_and_wait_on_chiller(run, "-24")
        
class CustomEnv(EnvironmentState):
    @state_wrapper
    def set_environment(self, run: Run, temperature: Optional[str] = None):
        self.set_and_wait_on_chiller(run, temperature)
