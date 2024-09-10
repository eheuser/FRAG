import json

from utils.utils import ts_to_utc


# Static Indicators
INTERESTING_PORTS = ( 20, 21, 22, 23, 445, 3128, 3389, 5900, 5901, 5985, 5986, 9000, 9001, 9030 )

LOL_BINS = [
    "appvlp.exe",
    "at.exe",
    "atbroker.exe",
    "bash.exe",
    "bginfo.exe",
    "bitsadmin.exe",
    "cdb.exe",
    "certutil.exe",
    "cmd.exe",
    "control.exe",
    "csc.exe",
    "cscript.exe",
    "csexec.exe",
    "csi.exe",
    "dfsvc.exe",
    "diskshadow.exe",
    "dnscmd.exe",
    "dnx.exe",
    "dxcap.exe",
    "esentutl.exe",
    "expand.exe",
    "explorer.exe",
    "extexport.exe",
    "extrac32.exe",
    "filezilla.exe",
    "findstr.exe",
    "forfiles.exe",
    "gpscript.exe",
    "gpup.exe",
    "hh.exe",
    "ie4uinit.exe",
    "ieexec.exe",
    "infdefaultinstall.exe",
    "installutil.exe",
    "jsc.exe",
    "makecab.exe",
    "mavinject.exe",
    "mftrace.exe",
    "microsoft.workflow.compiler.exe",
    "mmc.exe",
    "msbuild.exe",
    "msdeploy.exe",
    "msdt.exe",
    "mshta.exe",
    "msiexec.exe",
    "mstsc.exe",
    "msxsl.exe",
    "net.exe",
    "net1.exe",
    "netsh.exe",
    "nlnotes.exe",
    "nltest.exe",
    "notes.exe",
    "nps.exe",
    "nslookup.exe",
    "nvudisp.exe",
    "nvuhda6.exe",
    "odbcconf.exe",
    "openwith.exe",
    "paexec.exe",
    "pcalua.exe",
    "pcwrun.exe",
    "ping.exe",
    "plink.exe",
    "powershell.exe",
    "powershell_ise.exe",
    "presentationhost.exe",
    "print.exe",
    "pscp.exe",
    "psexec.exe",
    "psftp.exe",
    "psr.exe",
    "putty.exe",
    "puttytel.exe",
    "rcsi.exe",
    "reg.exe",
    "regasm.exe",
    "regedit.exe",
    "register-cimprovider.exe",
    "regsvcs.exe",
    "regsvr32.exe",
    "remcom.exe",
    "replace.exe",
    "robocopy.exe",
    "rpcping.exe",
    "rundll32.exe",
    "runonce.exe",
    "runscripthelper.exe",
    "sc.exe",
    "scp.exe",
    "scriptrunner.exe",
    "securecrt.exe",
    "sftp.exe",
    "sqldumper.exe",
    "sqlps.exe",
    "sqltoolsps.exe",
    "squirrel.exe",
    "syncappvpublishingserver.exe",
    "taskkill.exe",
    "te.exe",
    "telnet.exe",
    "tracker.exe",
    "tttracer.exe",
    "usbinst.exe",
    "vboxdrvinst.exe",
    "verclsid.exe",
    "vsjitdebugger.exe",
    "wab.exe",
    "winrm.exe",
    "winrs.exe",
    "winscp.exe",
    "winword.exe",
    "wmic.exe",
    "wscript.exe",
    "wsl.exe",
    "wsreset.exe",
    "xcmd.exe",
    "xwizard.exe",
    "pwsh.exe",
]

pa_targets = (
    "c:\\windows\\system32\\lsass.exe",
    "c:\\windows\\system32\\csrss.exe",
    "c:\\windows\\system32\\wininit.exe",
    "c:\\windows\\system32\\winlogon.exe",
    "c:\\windows\\system32\\services.exe",
)

pa_filter_source = (
    "google\\chrome\\application\\chrome.exe",
    "c:\\windows\\system32\\wbem\\wmiprvse.exe",
    "c:\\windows\\system32\\svchost.exe",
    "c:\\windows\\system32\\wininit.exe",
    "c:\\windows\\system32\\csrss.exe",
    "c:\\windows\\system32\\services.exe",
    "c:\\windows\\system32\\winlogon.exe",
    "c:\\windows\\system32\\audiodg.exe",
)

susp_file_ext = (
    ".zip",
    ".7z",
    ".rar",
    ".exe",
    ".scr",
    ".sys",
    ".ps1",
    ".vbs",
    ".vbe",
    ".py",
    ".bat",
    ".com",
)

def filter_mft_path(_filepath):
    """
    Filters $MFT entries by image path

    This function filters the 100k+ MFT entries going into the vector db. For now it
    looks for files in the Users, ProgramData or temp directories with interesting file extensions.

    Args:
        _filepath (str): The file path of the $MFT entry.
    Returns:
        bool: True if the entry is to be kept, False if it is meant to be discarded.
    """
    filepath = _filepath.casefold()
    # Too much uninteresting data
    if filepath.startswith("windows\\"):
        return False
    # Too much uninteresting data
    if filepath.startswith("program files\\") or filepath.startswith("program files (x86)\\"):
        return False
    # Too much uninteresting data
    if "winsxs" in filepath:
        return False
    
    if filepath.startswith("users\\") or filepath.startswith("programdata\\") or ("\\temp\\" in filepath) or ("\\tmp\\" in filepath):
        for ext in susp_file_ext:
            if filepath.endswith(ext):
                return True
    
    return False

def filter_evtx_event(data):
    """
    Filters EVTX entries by Channel, EventID and event attributes.

    Selectively add Sysmon events and other forensically interesting events.

    Args:
        data (dict): The parsed event in dictionary format.
    Returns:
        bool: True if the entry is to be kept, False if it is meant to be discarded.
    """
    try:
        event = data.get("Event")
        event_data = event.get("EventData")
        if event_data is None:
            return None, None
        
        system = event.get("System")
        if system is None:
            return None, None
        
        channel = system.get("Channel")
        event_id = int(system.get("EventID", 0))
        system_time = system["TimeCreated"]["#attributes"]["SystemTime"]
        utc = ts_to_utc(system_time)
    except Exception as e:
        print(e)
        return None, None

    match channel:
        # LOL bins are the glue for incidents, they're always in there somewhere
        case "Microsoft-Windows-Sysmon/Operational":
            match event_id:
                case 1:# Process Create
                    if is_lol_bin(event_data.get("Image")):
                        return data, utc
                    if is_lol_bin(event_data.get("OriginalFileName")):
                        return data, utc
                    if is_lol_bin(event_data.get("ParentImage")):
                        return data, utc
                case 3:# Network Connection
                    if event_data.get("DestinationPort") in INTERESTING_PORTS:
                        return data, utc
                    if event_data.get("SourcePort") in INTERESTING_PORTS:
                        return data, utc
                case 8:# Create Remote Thread
                    if is_lol_bin(event_data.get("SourceImage")):
                        return data, utc
                    if is_lol_bin(event_data.get("TargetImage")):
                        return data, utc
                    target_image = str(event_data.get("TargetImage"))
                    if target_image.casefold().endswith(pa_targets) and not target_image.casefold().endswith(pa_filter_source):
                        return data, utc
                case 10:# Process Access
                    if is_lol_bin(event_data.get("SourceImage")):
                        return data, utc
                    if is_lol_bin(event_data.get("TargetImage")):
                        return data, utc
                    target_image = str(event_data.get("TargetImage"))
                    if target_image.casefold().endswith(pa_targets) and not target_image.casefold().endswith(pa_filter_source):
                        return data, utc
                case 11:# File Create
                    target_filename = str(event_data.get("TargetFilename"))
                    if is_lol_bin(target_filename) or is_lol_bin(event_data.get("Image")):
                        if target_filename.endswith(susp_file_ext):
                            return data, utc
                case 12:# Registry create/delete
                    if event_data.get("EventType") == "CreateKey":
                        target_obj = event_data.get("TargetObject", "")
                        if is_windows_autorun(target_obj):
                            return data, utc
                case 13:# Registry value Set
                    if event_data.get("EventType") == "SetValue":
                        target_obj = event_data.get("Details", "")
                        if references_lol_bin(target_obj):
                            return data, utc
                case 19:# WmiEvent Filter
                    return data, utc
                case 20:# WmiEvent Consumer
                    return data, utc
                case 21:# WmiEvent Consumer to Filter
                    return data, utc
        case "Security":
            match event_id:
                case 4624:
                    if event_data.get("LogonType") in ( 5, 7, 10 ) and event_data.get("IpAddress") != "-":
                        return data, utc
                case 4625:
                    if not (event_data.get("IpAddress") in ( "0.0.0.0", "127.0.0.1" ) ) and not (event_data.get("IpAddress", "").startswith("fe")):
                        return data, utc
                case 4634:
                    return data, utc
                case 4647:
                    return data, utc
                case 4648:
                    return data, utc
                case 4779:
                    return data, utc
        case "Microsoft-Windows-PowerShell/Operational":
            match event_id:
                case 4103:
                    return data, utc
                case 4104:
                    return data, utc
                case 40961:
                    return data, utc
                case 40962:
                    return data, utc
                case 24577:
                    return data, utc
                case 8193:
                    return data, utc
                case 8194:
                    return data, utc
                case 8197:
                    return data, utc
        case "Microsoft-Windows-WinRM/Operational":
            match event_id:
                case 91:
                    return data, utc
                case 168:
                    return data, utc
                case 169:
                    return data, utc
                case 254:
                    return data, utc
        case "Microsoft-Windows-WMI-Activity/Operational":
            match event_id:
                case 5857:
                    return data, utc
                case 5858:
                    return data, utc
                case 5860:
                    return data, utc
                case 5861:
                    return data, utc
        case "Microsoft-Windows-Windows Defender/Operational":
            match event_id:
                case 1006:
                    return data, utc
                case 1007:
                    return data, utc
                case 1116:
                    return data, utc
                case 1117:
                    return data, utc
                case 1118:
                    return data, utc
                case 1119:
                    return data, utc
        case "Microsoft-Windows-TerminalServices-LocalSessionManager/Operational":
            match event_id:
                case 21:
                    return data, utc
                case 22:
                    return data, utc
                case 23:
                    return data, utc
                case 24:
                    return data, utc
                case 25:
                    return data, utc
        case "Microsoft-Windows-TerminalServices-RemoteConnectionManager/Operational":
            match event_id:
                case 1149:
                    return data, utc
        case "Microsoft-Windows-TerminalServices-RDPClient/Operational":
            match event_id:
                case 1024:
                    return data, utc
                case 1025:
                    return data, utc
                case 1102:
                    return data, utc
                case 1103:
                    return data, utc
        case "Microsoft-Windows-TaskScheduler/Operational":
            match event_id:
                case 106:
                    return data, utc
                case 129:
                    return data, utc
                case 140:
                    return data, utc
                case 141:
                    return data, utc
                case 200:
                    return data, utc
                case 201:
                    return data, utc
        case "Microsoft-Windows-RemoteDesktopServices-RdpCoreTS/Operational":
            match event_id:
                case 131:
                    return data, utc
                case 140:
                    return data, utc
    return None, None


def is_windows_autorun(_reg_key):
    """
    Checks if the provided Registry path is related to AutoRuns.

    Args:
        _reg_key (str): Registry Key path string.
    Returns:
        bool: True if the entry an AutoRun, False if not.
    """
    reg_key = str(_reg_key).casefold()
    
    autoruns = [
        "\\currentcontrolset\\control\\terminal server\\winstations\\rdp-tcp\\initialprogram",
        "\\currentcontrolset001\\control\\terminal server\\winstations\\rdp-tcp\\initialprogram",
        "\\microsoft\\windows nt\\currentversion\\winlogon\\gpextensions",
        "\\currentcontrolset\\services\\winsock",
        "\\currentcontrolset001\\services\\winsock",
        "\\microsoft\\windows\\currentversion\\explorer\\shelliconoverlayidentifiers",
        "\\microsoft\\wab\\dllpath",
        "\\microsoft\\windows\\currentversion\\controlpanel\\cpls",
        "\\currentcontrolset\\control\\session manager\\bootexecute",
        "\\currentcontrolset001\\control\\session manager\\bootexecute",
        "\\currentcontrolset\\control\\session manager\\appcertdlls",
        "\\currentcontrolset001\\control\\session manager\\appcertdlls",
        "\\wow6432node\\microsoft\\windows nt\\currentversion\\drivers32",
        "\\microsoft\\windows nt\\currentversion\\aedebug",
        "\\microsoft\\windows\\currentversion\\runservicesonce",
        "\\microsoft\\windows\\currentversion\\runservices",
        "\\microsoft\\windows nt\\currentversion\\winlogon",
        "\\microsoft\\windows\\currentversion\\shellserviceobjectdelayload",
        "\\microsoft\\windows\\currentversion\\runonce",
        "\\microsoft\\windows\\currentversion\\runonceex",
        "\\microsoft\\windows\\currentversion\\run",
        "\\microsoft\\windows\\currentversion\\runonce",
        "\\microsoft\\windows\\currentversion\\policies\\explorer\\run",
        "\\microsoft\\windows nt\\currentversion\\windows\\load",
        "\\microsoft\\windows nt\\currentversion\\windows\\run",
        "\\microsoft\\windows nt\\currentversion\\windows",
        "\\microsoft\\windows nt\\currentversion\\windows\\appinit_dlls",
        "\\microsoft\\windows nt\\currentversion\\windows\\loadappinit_dlls",
        "\\microsoft\\windows\\currentversion\\explorer\\user shell folders",
        "\\microsoft\\windows\\currentversion\\explorer\\shell folders",
        "\\microsoft\\windows nt\\currentversion\\winlogon\\userinit",
        "\\microsoft\\windows nt\\currentversion\\winlogon\\notify",
        "\\microsoft\\windows nt\\currentversion\\winlogon\\shell",
        "\\microsoft\\windows nt\\currentversion\\winlogon\\system",
        "\\microsoft\\windows\\currentversion\\explorer\\browser helper objects",
        "\\microsoft\\office test\\special\\perf",
        "\\microsoft\\windows nt\\currentversion\\appcompatflags\\installedsdb",
        "\\microsoft\\windows nt\\currentversion\\appcompatflags\\custom",
        "environment\\userinitmprlogonscript",
        "control panel\\desktop\\scrnsave.exe",
        "\\ms-settings\\shell\\open\\command\\delegateexecute",
        "shell\\open\\command\\(default)",
        "user shell folders\\startup",
    ]

    clsid_run = [
        "\\inprochandler",
        "\\inprocserver",
        "\\inprocserver32",
        "\\localserver",
        "\\localserver32\\shellex",
        "\\progid",
        "\\treatas",
        "\\scriptleturl",
    ]

    serv_run = ["\\imagepath", "\\binpath", "\\servicedll", "\\servicemanifest"]
    
    for a in autoruns:
        if a in reg_key:
            return True

    if "\\clsid\\" in reg_key:
        for c in clsid_run:
            if reg_key.endswith(c):
                return True
    
    if "\\currentcontrolset" in reg_key and "\\services\\" in reg_key:
        for s in serv_run:
            if reg_key.endswith(s):
                return True
    
    return False

def is_lol_bin(_image_or_filename):
    """
    Checks if the provided image or path is a LOLbins.

    Args:
        _image_or_filename (str): Image path or filename of file.
    Returns:
        bool: True if the entry an Lolbin, False if not.
    """
    image_or_filename = str(_image_or_filename).casefold()
    for bin in LOL_BINS:
        if bin == image_or_filename:
            return True
        if image_or_filename.endswith(f"\\{bin}"):
            return True
    return False

def references_lol_bin(_text):
    """
    Checks if the provided image or path is related to LOLbins.

    Args:
        _image_or_filename (str): Image path or filename of file.
    Returns:
        bool: True if the entry an Lolbin, False if not.
    """
    text = str(_text).casefold()
    for bin in LOL_BINS:
        if bin in text:
            return True
    return False