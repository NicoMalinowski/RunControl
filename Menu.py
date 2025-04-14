#!/usr/bin/env python
import click 
import Run
import time
import MqttCourier
from EnvironmentStates import *
from LowVoltageStates import *
from HighVoltageStates import *
import traceback
import run_Yarr as Yarr
import CUSEXP as CE
from threading import Timer
import MotorControl as MC
import logging
import sys

def setup_custom_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    named_tuple = time.localtime() # get struct_time
    time_string = time.strftime("%m-%d-%Y_%H:%M:%S", named_tuple)
    handler = logging.FileHandler(f'Logs/MENU_{time_string}.log', mode='w')
    handler.setFormatter(formatter)
    screen_handler = logging.StreamHandler(stream=sys.stdout)
    screen_handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.addHandler(screen_handler)
    return logger


logger = setup_custom_logger(__name__)

MenuList=["ENV","LV","HV","SOURCE","TEST","STATE","RELOAD","EXIT"]
MType=""

def MainMenu(run,courier,MType):
    f=True
    sel=click.prompt("Main Menu: Choose one of the following to proceed with testing",type=click.Choice(MenuList))
    if sel== "ENV":
        EnvMenu(run)
    elif sel== "LV":
        LVMenu(run)
    elif sel== "HV":
        HVMenu(run)
    elif sel== "SOURCE":
        MotorMenu()
    elif sel== "TEST":
        TestMenu(run,MType)
    elif sel== "STATE":
        StateMenu(run)
    elif sel== "RELOAD":
        Mod = run.get_active_modules()
        MType=type_select()
        for x in Mod:
            Yarr.config_POS(x[0],x[1],"warm")
            Yarr.config_POS(x[0],x[1],"cold")
            Yarr.config_POS(x[0],x[1],"LP")
    elif sel== "EXIT":
        f=False
        MC.to_position(0)
        #TURN HV
        run.switch_high_voltage_state(HVoff())
        run.switch_low_voltage_state(LVoff(LV_channels=None))
        run.switch_environment_state(Idle())
        run.switch_environment_state(Off())

    else:
        click.echo("Unprogrammed Input")
        return 
    return (f,MType)  

def EnvMenu(run):
    sel=click.prompt("Enviroment/Chiller Menu: Select Temperature State",type=click.Choice(["START","IDLE","WARM","COLD","VAR","OFF","EXIT"]))
    if sel== "IDLE":
        click.echo("Setting")
        run.switch_environment_state(Idle())
    elif sel== "START":
        click.echo("Setting")
        run.switch_environment_state(Start())
    elif sel== "WARM":
        click.echo("Setting")
        run.switch_environment_state(Warm())
    elif sel== "COLD":
        click.echo("Setting")
        run.switch_environment_state(Cold())
    elif sel== "VAR":
        click.echo("Setting")
    elif sel== "OFF":
        click.echo("Setting")
        run.switch_environment_state(Off())
    elif sel== "EXIT":
        return
    else:
        click.echo("Unprogrammed Input")
        return
    return

def HVMenu(run: Run):
    sel=click.prompt("HV Menu: Select HV State",type=click.Choice(["ON","OFF","DEFVAL","EXIT"]))
    if sel== "ON":
        click.echo("Setting")
        run.switch_high_voltage_state(HVonDefault())
    elif sel== "OFF":
        click.echo("Setting")
        run.switch_high_voltage_state(HVoff())
    elif sel== "DEFVAL":
        click.echo("Current default value: "+HighVoltageState.defaultHV)
        newval = input("New value (<ret> to keep current): ")
        if newval == "":
            pass
        else:
            try:
                newval = float(newval)
                if newval > 0 or newval < -200:
                    print("Only values between 0 and -200 allowed.")
                else:
                    HighVoltageState.defaultHV=str(newval)
                    print("Default HV value: "+str(newval))
            except ValueError:
                print("Only integer or float values allowed.")
    elif sel== "EXIT":
        return
    else:
        click.echo("Unprogrammed Input")
        return

def LVMenu(run,activeCH=[1]):
    sel=click.prompt("LV Menu: Select LV State",type=click.Choice(["ON","OFF","EXIT"]))
    if sel== "ON":
        click.echo("Setting")
        run.switch_low_voltage_state(LVonDefault(LV_channels=None))
    elif sel== "OFF":
        click.echo("Setting")
        run.switch_low_voltage_state(LVoff(LV_channels=None))
    elif sel== "EXIT":
        return
    else:
        click.echo("Unprogrammed Input")
        return

def MotorMenu():
    sel=click.prompt("Source Pos. Menu: Select Source Position",type=click.Choice(["SAFE","1","2","3","4","EXIT"]))
    if sel== "SAFE":
        click.echo("Setting")
        MC.to_position(0)
    elif sel== "1":
        click.echo("Setting")
        MC.to_position(1)
    elif sel== "2":
        click.echo("Setting")
        MC.to_position(2)
    elif sel== "3":
        click.echo("Setting")
        MC.to_position(3)
    elif sel== "4":
        click.echo("Setting")
        MC.to_position(4)
    elif sel== "EXIT":
        click.echo("Setting")
    else:
        click.echo("Unprogrammed Input")
        return

def TestMenu(run,MType):
    Mod=run.get_active_modules()
    logger.info(Mod)
    state=click.prompt("Select YARR Scan",type=click.Choice(["warm","cold"]))
    sel=click.prompt("Select YARR Scan",type=click.Choice(["ST","SOURCE","QC","FULL_QC","PFA","STAB","HW-SLOT","EXIT"]))
    if sel== "ST":
        click.echo(f"RUNNING Single TEST")
        SCAN=click.prompt("Select YARR Scan",type=click.Choice(Yarr.getScanDict()))
        if click.prompt("Need Target",type=click.Choice(["Y","N"]))=="Y":
            tar=click.prompt("Target?",type=str)
        else:
            tar=""    
        for x in Mod:
            Targs=Yarr.genargsdict(MSN=x[1],POS=x[0],MTYPE=MType,state=state,MPath="/data/Yarr_data/Configs/",sconf=f"/products/QC_CC/QTS_{MType}_{x[0]}.json")
            logger.info(x)
            Yarr.run_UNI(SCAN,Targs,target=tar)
    elif sel== "SOURCE":
        click.echo(f"RUNNING {sel}")
        for x in Mod:
            if x[0]=="1":
                run.send_data("HW_Slot","1")
            elif x[0]=="2":
                run.send_data("HW_Slot","2")
            elif x[0]=="3":
                run.send_data("HW_Slot","3")
            elif x[0]=="4":
                run.send_data("HW_Slot","4")
            else:
                raise ValueError
            run.switch_low_voltage_state(LVonDefault())
            run.switch_high_voltage_state(HVonDefault())
            Yarr.run_EYE(x[1],state)
            MC.to_position(int(x[0]))
            Yarr.run_Yarr("selftrigger_source",x[1],state,OPath="PFA",timeout=2400,ctype=MType)
            MC.to_position(0)
            run.switch_high_voltage_state(HVoff())
            run.switch_low_voltage_state(LVoff(LV_channels=None))
    elif sel== "QC":
        click.echo(f"RUNNING {sel}")
        for x in Mod:
            logger.info(x)
            try:
                run_QC(run,f"/products/QC_CC/QTS_{MType}_{x[0]}.json","/data/Yarr_data/Configs/",x[0],x[1],state,MType)
            except ValueError:
                logger.error("Some value out of range")
            except:
                logger.info("Unhandled exception")
        MC.to_position(0)
        #TURN HV
        run.switch_high_voltage_state(HVoff())
        run.switch_low_voltage_state(LVoff(LV_channels=None))
        run.switch_environment_state(Idle())
        run.switch_environment_state(Off())
    elif sel== "FULL_QC":
        click.echo(f"RUNNING {sel}")
        if check_COMS(run,Mod)=="False":
            logging.error("Comms Check failed")
            raise ValueError
        for x in Mod:
            logger.info(x)
            try:
                run_QC(run,f"/products/QC_CC/QTS_{MType}_{x[0]}.json","/data/Yarr_data/Configs/",x[0],x[1],"warm",MType)
            except ValueError:
                logger.error("Some value out of range")
            except:
                logger.info("Unhandled exception")
        for x in Mod:
            logger.info(x)
            try:
                run_QC(run,f"/products/QC_CC/QTS_{MType}_{x[0]}.json","/data/Yarr_data/Configs/",x[0],x[1],"cold",MType)
            except ValueError:
                logger.error("Some value out of range")
            except:
                logger.info("Unhandled exception")
        run.send_data("START", "0")
        MC.to_position(0)
        run.switch_high_voltage_state(HVoff())
        run.switch_low_voltage_state(LVoff(LV_channels=None))
        run.switch_environment_state(Idle())
        run.switch_environment_state(Off())
    elif sel== "PFA":
        click.echo("Setting")
        for x in Mod:
            logger.info(x)
            run_PFA(run,"/products/QC_CC/QTS_{MType}_{x[0]}.json","/data/Yarr_data/Configs/",x[0],x[1],state,MType)
    elif sel== "STAB":
        click.echo("Setting")
        for x in Mod:
            logger.info(x)
            run.switch_high_voltage_state(HVoff())
            run.switch_low_voltage_state(LVoff())
            logger.info(f"Initial powering state set, proceeding to {state} state")
            if state=="warm": 
                run.switch_environment_state(Idle())
            elif state=="cold":
                run.switch_environment_state(Cold()) 
            else:
                logger.info("wrong state set")
                return           
            time.sleep(60)
            run.switch_low_voltage_state(LVonDefault())
            run.switch_high_voltage_state(HVonDefault())
            T=Timer(300,run.send_data("START", "1"))
            T.start()
            logger.info("starting STAB Test for 8h")
            Yarr.run_Simple("LONG-TERM-STABILITY-DCS",False,"/products/QC_CC/QTS_{MType}_{x[0]}.json","/data/Yarr_data/Configs/",x[1],state,timeout=36000)
            logger.info("stab test finished")
            run.send_data("START", "0")
            MC.to_position(0)
            run.switch_high_voltage_state(HVoff())
            run.switch_low_voltage_state(LVoff(LV_channels=None))
            run.switch_environment_state(Idle())
            run.switch_environment_state(Off())
    elif sel== "HW-SLOT":
        click.echo("Setting")
        POS=click.prompt("Select HW_Slot",type=click.Choice(["1","2","3","4"]))
        if POS=="1":
            run.send_data("HW_Slot","1")
        elif POS=="2":
            run.send_data("HW_Slot","2")
        elif POS=="3":
            run.send_data("HW_Slot","3")
        elif POS=="4":
            run.send_data("HW_Slot","4")
        else:
            raise ValueError 
    elif sel== "EXIT":
        click.echo("Setting")
    else:
        click.echo("Unprogrammed Input")
        return
    
def StateMenu(run: Run):
    sel=click.prompt("Select test state for SWINE", type=click.Choice(["IDLE","STABILITY","SOURCE","WARM","COLD"]))
    if sel== "IDLE":
        click.echo(f"Setting SWINE state to IDLE")
        run.send_data("START", "0")
    if sel== "STABILITY":
        click.echo(f"Setting SWINE state to STABILITYTEST")
        run.send_data("START", "1")
    if sel== "SOURCE":
        click.echo(f"Setting SWINE state to SOURCETEST")
        run.send_data("START", "2")
    if sel== "WARM":
        click.echo(f"Setting SWINE state to WARMTEST")
        run.send_data("START", "3")
    if sel== "COLD":
        click.echo(f"Setting SWINE state to COLDTEST")
        run.send_data("START", "4")

def check_env(flag:bool,run:Run,state,POS):
    logger.info("Checking Enviroment and Interlock Parameters")
    time.sleep(5)
    T=float(run.get_data(f"TempNTC_{POS}"))
    Dew=float(run.get_data("Dewpoint"))
    RT=run.get_data("RelevantTrip")
    if flag == False:
        logger.error("TimeOut")
        raise CE.TimeOutError
    if RT!="00000000000000000000000":
        logger.error("HWTRIP")
        raise CE.HWTripError
    if Dew>= T-5:
            logger.error("DEWPOINT ERROR")
            raise CE.DewPointError
    if state=="warm":
        if float(T)<=13 or float(T)>=23 :
            logger.error(f" {T} = Temperature out of range")
            raise CE.TempError
    if state=="cold":
        if float(T)<=-24 or float(T)>=-12 :
            logger.error(f" {T} = Temperature out of range")
            raise CE.TempError
    logger.info("Passed")
    return

def check_COMS(run,MLIST:list):
    run.switch_high_voltage_state(HVoff())
    run.switch_low_voltage_state(LVoff())
    run.switch_environment_state(Warm())
    run.switch_low_voltage_state(LVonDefault())
    for x in MLIST:
        try:
            Yarr.run_EYE(x[1],"warm")
        except:
                logger.info("ERROR in EYE Diagram")  
    for x in MLIST:       
        try:
            print(x[1])
            #Yarr.run_Yarr("std_digitalscan",x[1],"warm",OPath="COMS",target="-m 1",timeout=120,ctype=MType)
        except:
                logger.info("ERROR in DIGITAL SCAN")  
    run.switch_low_voltage_state(LVoff())
    check=click.prompt("Did all Modules respond correctly in coms digital scans",type=click.Choice(["True","False"]))
    return check           
    

def run_QC(run,SimpleConf,ModulePath,POS,ModuleSN,state,MType):
    Targs=Yarr.genargsdict(MSN=ModuleSN,POS=POS,MTYPE=MType,state=state,MPath=ModulePath,sconf=SimpleConf)
    logger.info(f"Setting Peripherie states for full {state} QC")
    run.switch_high_voltage_state(HVoff())
    run.switch_low_voltage_state(LVoff())
    #logger.info(type(POS),POS)
    if POS=="1":
        run.send_data("HW_Slot","1")
    elif POS=="2":
        run.send_data("HW_Slot","2")
    elif POS=="3":
        run.send_data("HW_Slot","3")
    elif POS=="4":
        run.send_data("HW_Slot","4")
    else:
        raise ValueError    

    logger.info(f"Initial powering state set, proceeding to {state} state")
    if state=="warm": 
        run.switch_environment_state(Warm())
    elif state=="cold":
        run.switch_environment_state(Cold()) 
    else:
        logger.info("wrong state set")
        raise ValueError 
    time.sleep(60)
    run.switch_low_voltage_state(LVonDefault(LV_channels=[int(POS)]))
    run.switch_high_voltage_state(HVonDefault())
    if state=="warm": 
        run.send_data("START", "3")
    elif state=="cold":
        run.send_data("START", "4")
    else:
        logger.info("wrong state set")
        raise ValueError
    
    # MODULE QC TESTS
    # SCAN MAP for YARR.run_UNI to be found in YARR_MAP_json
    logger.info("Power state set to default ON, proceedding with Simple QC tests")
    #IV SCAN
    check_env(Yarr.run_UNI("IV",Targs),run,state,POS)
    run.switch_high_voltage_state(HVoff())
    run.send_data("HV_U","0") #Set HV Voltage to 0
    run.switch_high_voltage_state(HVonDefault())
    logger.info("IV Done")
    #EYE DIAGRAM for reliable coms
    check_env(Yarr.run_UNI("EYE",Targs),run,state,POS)
    logger.info("EYE Done")
    #ADC CAL
    check_env(Yarr.run_UNI("ADC",Targs),run,state,POS)
    logger.info("ADC Done")
    #ANALOG READBACK
    check_env(Yarr.run_UNI("ANAREAD",Targs),run,state,POS)
    logger.info("ANALOG Done")
    #SLDO
    check_env(Yarr.run_UNI("SLDO",Targs),run,state,POS)
    run.switch_low_voltage_state(LVonDefault(LV_channels=[int(POS)]))
    logger.info("SLDO Done")
    #VCAL CALIBRATION
    check_env(Yarr.run_UNI("VCAL",Targs),run,state,POS)
    logger.info("VCAL Done")
    #INJECTION CAPACITANCE
    check_env(Yarr.run_UNI("INJ",Targs),run,state,POS)
    logger.info("INJECTION Done")
    #LP_MODE disabled for V2
    if MType=="rd53b":
        check_env(Yarr.run_UNI("LPM",Targs),run,state,POS)
    else:
        print("\033[91m LP Mode Scan disabled for other module types \033[00m")
        logger.info("LP Mode Scan disabled for other module types")

    logger.info("LP Done")

    #check_env(Yarr.run_UNI("OVP",Targs),run,state,POS)
    #logger.info("OVP Done")
    #check_env(Yarr.run_UNI("USP",Targs),run,state,POS)
    #logger.info("USP Done")

    #DATATRANSMISION
    check_env(Yarr.run_UNI("DAT",Targs),run,state,POS)
    logger.info("DAT Done")
    #YARR Minimum Health Tests
    logger.info("Starting Yarr Scans")
    logger.info("Minimum Health Tests")
    print(Targs)
    
    Targs=Yarr.genargsdict(args=Targs,Opath="MHT")
    print(Targs)
    check_env(Yarr.run_UNI("DIG",Targs,target="-m 1"),run,state,POS)
    check_env(Yarr.run_UNI("ANA",Targs),run,state,POS)
    check_env(Yarr.run_UNI("THR",Targs),run,state,POS)
    check_env(Yarr.run_UNI("TOT",Targs,target="-t 6000"),run,state,POS)
    logger.info("MHT Finished")
    #YARR Tuning Procedure
    logger.info("Starting TUNing procedure")
    Targs=Yarr.genargsdict(args=Targs,Opath="TUN")
    check_env(Yarr.run_UNI("TUG",Targs,target="-t 2000"),run,state,POS)
    check_env(Yarr.run_UNI("THR",Targs),run,state,POS)
    check_env(Yarr.run_UNI("TUP",Targs,target="-t 2000"),run,state,POS)
    check_env(Yarr.run_UNI("RTG",Targs,target="-t 1500"),run,state,POS)
    check_env(Yarr.run_UNI("RTP",Targs,target="-t 1500"),run,state,POS)
    check_env(Yarr.run_UNI("THD",Targs),run,state,POS)
    check_env(Yarr.run_UNI("TOT",Targs,target="-t 6000"),run,state,POS)
    logger.info("TUN Finished")
    #YARR Pixel failure analysis
    logger.info("Starting Pixel Failure Analysis")
    Targs=Yarr.genargsdict(args=Targs,Opath="PFA")
    check_env(Yarr.run_UNI("DIG",Targs,target="-m 1"),run,state,POS)
    check_env(Yarr.run_UNI("ANA",Targs),run,state,POS)
    check_env(Yarr.run_UNI("THD",Targs),run,state,POS)
    check_env(Yarr.run_UNI("NOS",Targs),run,state,POS)
    check_env(Yarr.run_UNI("DIB",Targs),run,state,POS)
    check_env(Yarr.run_UNI("MER",Targs),run,state,POS)
    logger.info("switching HV Off for Zero bias scan")
    run.switch_high_voltage_state(HVoff())
    check_env(Yarr.run_UNI("RTP",Targs,target="-t 1500"),run,state,POS)
    check_env(Yarr.run_UNI("TZB",Targs),run,state,POS)
    logger.info("switching HV back on and retune to normal")
    run.switch_high_voltage_state(HVonDefault())
    check_env(Yarr.run_UNI("RTP",Targs,target="-t 1500"),run,state,POS)
    #YARR selftrigger source scan
    logger.info("Running Source scan--- DO NOT OPEN LEAD BOX")
    run.send_data("START", "2")
    MC.to_position(int(POS))
    check_env(Yarr.run_UNI("STS",Targs),run,state,POS)
    MC.to_position(0)
    logger.info("BOX SAFE Source scan Finished")
    logger.info(f"QC step {state} for {ModuleSN} finished")
    run.send_data("START", "0")

    return

def run_PFA(run,SimpleConf,ModulePath,POS,ModuleSN,state,MType):
    logger.info(f"Setting Peripherie states for full {state} QC")
    run.switch_high_voltage_state(HVoff())
    run.switch_low_voltage_state(LVoff())
    logger.info(f"Initial powering state set, proceeding to {state} state")
    if state=="warm": 
        run.switch_environment_state(Warm())
    elif state=="cold":
        run.switch_environment_state(Cold()) 
    else:
        logger.info("wrong state set")
        return           
    time.sleep(60)
    run.switch_low_voltage_state(LVonDefault())
    run.switch_high_voltage_state(HVonDefault())
    if state=="warm": 
        run.send_data("START", "3")
    elif state=="cold":
        run.send_data("START", "4")
    else:
        logger.info("wrong state set")
        return 

    Yarr.run_EYE(ModuleSN)
    logger.info("Starting Pixel Failure Analysis")
    Yarr.run_Yarr("std_digitalscan",ModuleSN,state,OPath="PFA",target="-m 1",ctype=MType)
    Yarr.run_Yarr("std_analogscan",ModuleSN,state,OPath="PFA",ctype=MType)
    Yarr.run_Yarr("std_thresholdscan_hd",ModuleSN,state,OPath="PFA",ctype=MType)
    Yarr.run_Yarr("std_noisescan",ModuleSN,state,OPath="PFA",ctype=MType)
    Yarr.run_Yarr("std_discbumpscan",ModuleSN,state,OPath="PFA",ctype=MType)
    Yarr.run_Yarr("std_mergedbumpscan",ModuleSN,state,OPath="PFA",target="-t 2000",ctype=MType)
    logger.info("switching HV Off for Zero bias scan")
    run.switch_high_voltage_state(HVoff())
    Yarr.run_Yarr("std_retune_pixelthreshold",ModuleSN,state,OPath="PFA",target="-t 1500",ctype=MType)
    Yarr.run_Yarr("std_thresholdscan_zerobias",ModuleSN,state,OPath="PFA",ctype=MType)
    logger.info("switching HV back on and retune to normal")
    #run.switch_high_voltage_state(HVonDefault())
    Yarr.run_Yarr("std_retune_pixelthreshold",ModuleSN,state,OPath="PFA",target="-t 1500",ctype=MType)
    logger.info("Running Source scan--- DO NOT OPEN LEAD BOX")
    run.send_data("START", "2")
    MC.to_position(int(POS))
    #Yarr.run_Yarr("selftrigger_source",ModuleSN,state,OPath="PFA",ctype=MType)
    MC.to_position(0)
    logger.info("BOX SAFE Source scan Finished")
    logger.info(f"QC step {state} for {ModuleSN} finished")
    run.send_data("START", "0")

def type_select():
    sel=click.prompt("Select Module type", type=click.Choice(["V1","V2"]))
    if sel=="V1":
        R="rd53b"
    elif sel=="V2":
        R="itkpixv2"  
    logger.info(f"Module Type:{R} selected") 
    return(R)     

def main() -> int:
    logger.info("Menu Startup")
    MType=type_select()
    try:
        courier = MqttCourier.MqttCourier("MqttCourier_config.json")    
    except Exception:
        logger.info(traceback.format_exc())
    time.sleep(10)
    run = Run.Run(courier)
    Mod = run.get_active_modules()
    for x in Mod:
        Yarr.config_POS(x[0],x[1],"warm")
        Yarr.config_POS(x[0],x[1],"cold")
        Yarr.config_POS(x[0],x[1],"LP") 
    f=True
    while f==True:
        try:
            x=MainMenu(run,courier,MType)
            f=x[0]
            MType=x[1]
        except KeyboardInterrupt:
            print("\033[91m Nein Luke EXIT beendet das Program :P \033[00m")
        except click.exceptions.Abort:
            print("\033[91m Nein Luke EXIT beendet das Program :P \033[00m")
    for x in Mod:
        Yarr.config_POS("1",x[1],"warm")
        Yarr.config_POS("1",x[1],"cold")
        Yarr.config_POS("1",x[1],"LP")
    logger.info("Menu Close")
    return 1
if __name__ == "__main__":
    main()
