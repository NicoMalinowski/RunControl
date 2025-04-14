from MqttCourier import MqttCourier
from EnvironmentStates import *
from LowVoltageStates import *
from HighVoltageStates import *
import traceback
from typing import List
from time import sleep


class Run:
    def __init__(self, courier: MqttCourier) -> None:
        
        self.courier = courier
        self.switch_high_voltage_state(HVoff())
        self.switch_low_voltage_state(LVoff())
        self.switch_environment_state(Idle())

    def send_data(self, topic_key: str, data: str) -> None:
        self.courier.send_data_by_topic(topic_key,data)
        
    def get_data(self, topic_key: str) -> str:
        return self.courier.get_data_by_topic(topic_key)
    
    def get_active_modules(self) -> List[str]:
        active_modules=[]
        for position in ["1","2","3","4"]:
            is_position_filled = self.get_data(f"Present_{position}")
            if is_position_filled=="1":
                ID = self.get_data(f"Serialnumber_{position}")
                active_modules.append([position,ID])
        return(active_modules)
    
    def switch_environment_state(self, environment_state: EnvironmentState, temperature: Optional[str] = None) -> None:
        try:

            if temperature is not None and environment_state != CustomEnv:
                raise ValueError("Temperature can only be set for CustomEnv EnvironmentState!")
            if temperature is None and environment_state == CustomEnv:
                raise ValueError("Temperature has to be set for CustomEnv EnvironmentState!")
        
            self.environment_state = environment_state
            self.environment_state.set_environment(self, temperature=temperature)

        except:
            print(traceback.format_exc())
            print(f"Setting the environment state {str(environment_state)} went wrong, going into Idle.")
            self.environment_state = Idle()
            self.environment_state.set_environment(self)
    
    def switch_low_voltage_state(self, low_voltage_state: LowVoltageState, LV_channels: List[str] = None,
                                 low_voltage_U: Optional[str] = None, low_voltage_I: Optional[str] = None) -> None:
        try:

            if (low_voltage_U is not None or low_voltage_I is not None) and low_voltage_state != LVonCustom:
                raise ValueError("LV voltage and current can only be set for LVonCustom LowVoltageState!")
            if (low_voltage_U is None or low_voltage_I is None) and low_voltage_state == LVonCustom:
                raise ValueError("LV voltage and current have to be set for LVonCustom LowVoltageState!")
            
            if LV_channels is None:
                LV_channels = [active_slot[0] for active_slot in self.get_active_modules()]

            low_voltage_state.LV_channels = LV_channels
            self.low_voltage_state = low_voltage_state
            self.low_voltage_state.set_low_voltage(self, low_voltage_U=low_voltage_U, low_voltage_I=low_voltage_I)
        
        except:
            print(traceback.format_exc())
            print(f"Setting the low voltage state {str(low_voltage_state)} went wrong, going into LVoff.")
            self.low_voltage_state = LVoff(["1","2","3","4"])
            self.low_voltage_state.set_low_voltage(self)
            
    def switch_high_voltage_state(self, high_voltage_state: HighVoltageState, high_voltage: Optional[str] = None) -> None:
        try:
            
            if high_voltage is not None and high_voltage_state != HVonCustom:
                raise ValueError("High voltage can obly be set for HVonCustom HighVoltageState.")
            if high_voltage is None and high_voltage_state == HVonCustom:
                raise ValueError("High voltage has to be set for HVonCustom HighVoltageState.")
            
            self.high_voltage_state = high_voltage_state
            self.high_voltage_state.set_high_voltage(self, high_voltage=high_voltage)
        
        except:
            print(traceback.format_exc())
            print(f"Setting the high voltage state {str(high_voltage_state)} went wrong, going into HVoff.")
            self.high_voltage_state = HVoff()
            self.high_voltage_state.set_high_voltage(self)
            
    def check_trip(self) -> str:
        print("Waiting 5 seconds to read out trip array")
        sleep(5)
        trip_array = self.get_data("RelevantTrip")
        if "1" not in trip_array:
            return "No trip"
        else:
            trip_dict = {
                0: "PT100 1", 1: "PT100 2", 2: "PT100 3", 3: "PT100 4", 
                4: "NTC 1", 5: "NTC 2", 6: "NTC 3", 7: "NTC 4",
                8: "Lid Switch", 9: "Dry Air", 10: "Vacuum",
                11: "NTC Ref", 12: "Humidity", 13: "Air Temp",
                14: "PT100 1 < DP", 15: "PT100 2 < DP", 16: "PT100 3 < DP", 17: "PT100 4 < DP",
                18: "NTC 1 < DP", 19: "NTC 2 < DP", 20: "NTC 3 < DP", 21: "NTC 4 < DP",
            }
            trips = [index for index, char in enumerate(trip_array) if char == "1"]
            trips_and_names = [(index,trip_dict[index]) for index in trips]
            raise ValueError(f"The test system is tripped, because of the following conditions:\n{trips_and_names}")
