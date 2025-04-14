import subprocess as sp
import traceback
import json as js
import os
from threading import Timer

f=open("YARR_MAP.json","r")
MAP=js.load(f)

def run_SP(com,timeout):
    f=True
    arg=com.split(" ")
    try:
        with sp.Popen(arg,stdout=sp.PIPE) as p:
            timer = Timer(timeout, p.kill)
            timer.start()
            while p.poll()==None:
                    text= p.stdout.read1().decode("utf-8")
                    print(text,end='',flush=True) 
                    #print(p.poll()) 
            f=timer.is_alive()
            timer.cancel()  
    except Exception:
        print(traceback.format_exc())
    #print(temp.stdout)
    #print(f)
    return f

def run_Yarr(SCAN,ModuleSN,state,target = "", PathYarr="/products/YARR/pro",PathConf="/data/Yarr_data",OPath="ADV",timeout=1800,ctype="rd53b"):
    com=f"{PathYarr}/bin/scanConsole -r {PathYarr}/configs/controller/specCfg-rd53b-16x1.json -c {PathConf}/Configs/{ModuleSN}/{ModuleSN}_L2_{state}.json -s {PathYarr}/configs/scans/{ctype}/{SCAN}.json {target} -p -o {PathConf}/Configs/{ModuleSN}/{state}/{OPath}" 
    f=run_SP(com,timeout)
    Path=f"{PathConf}/Configs/{ModuleSN}/{state}/{OPath}"
    Path=max([os.path.join(Path,d) for d in os.listdir(Path)], key=os.path.getmtime)
    f=checkYScan(Path)
    return f

def run_EYE(ModuleSN,state,PathYarr="/products/YARR/pro",PathConf="/data/Yarr_data",timeout=1800):
    com=f"{PathYarr}/bin/eyeDiagram -r {PathYarr}/configs/controller/specCfg-rd53b-16x1.json -c {PathConf}/Configs/{ModuleSN}/{ModuleSN}_L2_{state}.json" 
    f=run_SP(com,timeout)
    return f

def config_POS(POS,ModuleSN,state="warm",PathConf="/data/Yarr_data/Configs"):
    P=int(POS)-1
    temp=js.load(open(f"{PathConf}/{ModuleSN}/{ModuleSN}_L2_{state}.json"))
    #print(temp["chips"])
    for x in range(4):
        #print(temp["chips"][x])
        temp["chips"][x]["tx"]=P
        temp["chips"][x]["rx"]=int(temp["chips"][x]["rx"])%4 +P*4
        #print(temp["chips"][x])
    with open(f"{PathConf}/{ModuleSN}/{ModuleSN}_L2_{state}.json", 'w') as f:
        js.dump(temp,f,ensure_ascii=False, indent=4)

def run_Simple(Scan,Analys,Conf,MPath,MSN,state,timeout=1800):
    com=f"measurement-{Scan} -c {Conf} -m {MPath}/{MSN}/{MSN}_L2_{state}.json -o {MPath}/{MSN}/{state}/Simple --site Universitaet_Siegen" 
    f=run_SP(com,timeout)
    if f==False:
        return f
    if Analys==True:
        SC=Scan.replace("-","_")
        Path=f"{MPath}/{MSN}/{state}/Simple/Measurements/{SC}"
        Path=max([os.path.join(Path,d) for d in os.listdir(Path)], key=os.path.getmtime)
        #print(Path)
        
        com=f"analysis-{Scan} -i {Path} -o {MPath}/{MSN}/{state}/Simple/Results"
        f=run_SP(com,timeout)
        if f==False:
            return f
        SC=Scan.replace("-","_")
        Path=f"{MPath}/{MSN}/{state}/Simple/Results/{SC}"
        Path=max([os.path.join(Path,d) for d in os.listdir(Path)], key=os.path.getmtime)
        com=f"analysis-update-chip-config -i {Path} -c {MPath}/{MSN}/L2_{state} --override"
        f=run_SP(com,timeout)
        if f==False:
            return f
    return f

def run_Simple_LP(Scan,Analys,Conf,MPath,MSN,state,timeout=1800):
    com=f"measurement-{Scan} -c {Conf} -m {MPath}/{MSN}/{MSN}_L2_LP.json -o {MPath}/{MSN}/{state}/Simple --site Universitaet_Siegen" 
    #print(com)
    f=run_SP(com,timeout)
    if f==False:
        return f
    if Analys==True:
        SC=Scan.replace("-","_")
        Path=f"{MPath}/{MSN}/{state}/Simple/Measurements/{SC}"
        Path=max([os.path.join(Path,d) for d in os.listdir(Path)], key=os.path.getmtime)
        #print(Path)
        
        com=f"analysis-{Scan} -i {Path} -o {MPath}/{MSN}/{state}/Simple/Results"
        f=run_SP(com,timeout)
        if f==False:
            return f

        SC=Scan.replace("-","_")
        Path=f"{MPath}/{MSN}/{state}/Simple/Results/{SC}"
        Path=max([os.path.join(Path,d) for d in os.listdir(Path)], key=os.path.getmtime)
        com=f"analysis-update-chip-config -i {Path} -c {MPath}/{MSN}/L2_{state} --override"
        f=run_SP(com,timeout)
        if f==False:
            return f
    return f

def checkYScan(Path):
    f=False
    for x in os.listdir(Path):
        if x=="scanLog.json":
            f=True
            print("Scan success")   
    return f  

def run_UNI(scankey,args,target=""):
    scp=MAP["SCANS"][scankey]
    SN=scp[0]
    TO=int(scp[2])
    if len(scp)==4:
        if scp[3]=="True":
            ANA=True
        else:
            ANA=False
    else:
        ANA=False    
    print(SN,scp[1],TO,ANA)    
    if scp[1]=="simple":
        f=run_Simple(SN,ANA,args["SimpleConfPath"],args["MPath"],args["MSN"],args["STATE"],timeout=TO)
    elif scp[1]=="simple_LP":
        f=run_Simple_LP(SN,ANA,args["SimpleConfPath"],args["MPath"],args["MSN"],args["STATE"],timeout=TO)
    elif scp[1]=="yarr":
        f=run_Yarr(SN,args["MSN"],args["STATE"],target,OPath=args["OPath"],timeout=TO,ctype=args["MTYPE"])
    elif scp[1]=="eye":
        f=run_EYE(args["MSN"],args["STATE"],timeout=TO)
    else:
        print("Undefined subprocess selected")    
        f=False
    return(f)

def genargsdict(args={},MSN="20UPGxxxxxxxx",POS="1",MTYPE="itkpixv2",state="warm",MPath="/data/Yarr_data",Opath="ADV",sconf="/products/QC_CC"):
    if args=={}:
        args={"MSN":"20UPGM23210355",
            "POS":"1",
            "MTYPE":"itkpixv2",
            "STATE":"warm",
            "MPath":"/data/Yarr_data",
            "OPath":"ADV",
            "SimpleConfPath":"/products/QC_CC"}
        args["MSN"]=MSN
        args["POS"]=POS
        args["MTYPE"]=MTYPE
        args["STATE"]=state
        args["MPath"]=MPath
        args["OPath"]=Opath
        args["SimpleConfPath"]=sconf
    else:
        if MSN!="20UPGxxxxxxxx":
            args["MSN"]=MSN
        elif POS!="1":
            args["POS"]=POS
        elif MTYPE!="itkpixv2":
            args["MTYPE"]=MTYPE
        elif state!="warm":    
            args["STATE"]=state
        elif MPath!="/data/Yarr_data":
            args["MPath"]=MPath
        elif Opath!="ADV":    
            args["OPath"]=Opath
        elif sconf!="/products/QC_CC":
            args["SimpleConfPath"]=sconf
    return(args)
def getScanDict():
    f=MAP["SCANS"].keys()
    return(f)


if __name__ == "__main__":

    Targs={"MSN":"20UPGM23210355",
          "POS":"1",
          "MTYPE":"itkpixv2",
          "STATE":"warm",
          "MPath":"/data/Yarr_data/Configs/",
          "OPath":"ADV",
          "SimpleConfPath":"/products/QC_CC/QTS_itkpixv2_1.json"}
    #run_Yarr("std_digitalscan","20UPGM23210355","warm",OPath="COMS",target="-m 1",timeout=120,ctype="itkpixv2")
    #run_Yarr("std_digitalscan","20UPGM22110181","warm",OPath="ADV",target="",timeout=3600)
    #config_POS("1","20UPGM22110181","warm")
    #run_Simple("LONG-TERM-STABILITY-DCS",False,"/data/QTS_merged_vmux.json","/data/Yarr_data/Configs/","20UPGM22110182","warm",timeout=3600)
    #run_EYE("20UPGM22211250")
    #checkYScan("/data/Yarr_data/Configs/20UPGM22110181/post_parylene_cold_05.12.2024/MHT/001333_std_digitalscan")
    #run_UNI("DIG",args,target="")
    #print(Targs)
    #Targs=genargsdict(args=Targs,Opath="MHT")
    #print(Targs)
    print(getScanDict())
    print("DONE")

