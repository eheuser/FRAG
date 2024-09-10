class IOC:

    def __init__(self):
        self.ioc = {
            "TA0001": self.TA0001(),
            "TA0002": self.TA0002(),
            "TA0003": self.TA0003(),
            "TA0004": self.TA0004(),
            "TA0005": self.TA0005(),
            "TA0006": self.TA0006(),
            "TA0007": self.TA0007(),
            "TA0008": self.TA0008(),
            "TA0008": self.TA0009(),
            "TA0010": self.TA0010(),
            "TA0011": self.TA0011(),
        }

    def get_ioc_dict(self):
        """
        Returns a dictionary of indicators of compromise (IOC).

        This method retrieves and returns the IOC dictionary associated with the instance.

        Returns:
            dict: The IOC dictionary containing various indicators of compromise.
        """
        return self.ioc

    def get_tactic_ioc(self, tactic):
        """
        Retrieves IOC strings for a given tactic from the IOC dictionary.

        This function looks up the specified tactic in the IOC dictionary and returns any
        associated IOC strings if they exist. If no IOC strings are found, an empty list is
        returned.

        Args:
            tactic (str): The tactic for which to retrieve IOC strings.

        Returns:
            list: A list of IOC strings associated with the specified tactic or an empty list if
                no IOC strings are found.
        """
        entry = self.ioc.get(tactic, {})
        if entry and "ioc_strings" in entry:
            return entry["ioc_strings"]
        return []

    def TA0001(self):
        """
        Returns a dictionary containing information about initial access techniques used by adversaries to gain a
        foothold within a network. The dictionary includes the name of the technique, a description of the technique,
        and a list of Indicators of Compromise (IOC) strings that may be associated with this technique.

        Args:
            self: The instance of the class containing this method.

        Returns:
            dict: A dictionary with keys 'name', 'description', and 'ioc_strings'. The value for 'name' is a string
            representing the name of the technique, 'description' contains a detailed description of the technique,
            and 'ioc_strings' is a list of strings that are potential IOCs associated with this technique.
        """
        return {
            "name": "Initial Access",
            "description": """The adversary is trying to get into your network.

Initial Access consists of techniques that use various entry vectors to gain their initial foothold within a network. Techniques used to gain a foothold include targeted spearphishing and exploiting weaknesses on public-facing web servers. Footholds gained through initial access may allow for continued access, like valid accounts and use of external remote services, or may be limited-use due to changing passwords.""",
            "ioc_strings": [
                "java.exe",
                "javaw.exe",
                "javaws.exe",
                "powershell.exe",
                "powershell_ise.exe",
                "rundll32.exe",
                "\\microsoft\\office\\outlook\\addins",
                ".scf",
                ".pptx",
                ".ppt",
                ".doc",
                ".docx",
                ".rtf",
                ".pdf",
                ".cmd",
                ".bat",
                ".jar",
                ".lnk",
                ".vbs",
                ".vbe",
                "winword.exe",
                "powerpnt.exe",
                "excel.exe",
                "outlook.exe",
                "\\downloads\\",
                "temp\\7z",
            ],
        }

    def TA0002(self):
        """
        Returns a dictionary containing information about an adversary's execution tactics.

        This function provides details on how an adversary might execute malicious code on a
        local or remote system. It includes a description of the execution tactic and a list
        of Indicator of Compromise (IOC) strings that may be associated with such activities.

        Returns:
            dict: A dictionary with keys 'name', 'description', and 'ioc_strings'. The 'name' key
                contains the string 'Execution', the 'description' key provides a detailed
                explanation of the execution tactic, and the 'ioc_strings' key lists various
                strings that may indicate malicious activity.
        """
        return {
            "name": "Execution",
            "description": """The adversary is trying to run malicious code.

Execution consists of techniques that result in adversary-controlled code running on a local or remote system. Techniques that run malicious code are often paired with techniques from all other tactics to achieve broader goals, like exploring a network or stealing data. For example, an adversary might use a remote access tool to run a PowerShell script that does Remote System Discovery. """,
            "ioc_strings": [
                "CreateRemoteThread",
                "CreateThread",
                "CreateUserThread",
                "DllImport",
                "powershell.exe",
                "powershell_ise.exe",
                "pwsh.exe",
                "nps.exe",
                "rundll32.exe",
                "cmd.exe",
                "taskkill.exe",
                "wmic.exe",
                "wscript.exe",
                "wsl.exe",
                "bitsadmin.exe",
                "cscript.exe",
                "wcscript.exe",
                "encodedcommand",
                "-enc",
                "-e",
                "bypass",
                "iex",
                "-command",
            ],
        }

    def TA0003(self):
        """
        Returns a dictionary containing information about the 'Persistence' tactic.

        This function provides details on the 'Persistence' tactic used by adversaries to maintain
        their foothold in systems across restarts, changed credentials, and other interruptions.
        The returned dictionary includes a name, description, and a list of IOC (Indicators of
        Compromise) strings related to this tactic.

        Returns:
            dict: A dictionary with the following keys:
            'name' (str): The name of the tactic ('Persistence').
            'description' (str): A detailed description of the tactic.
            'ioc_strings' (list): A list of IOC strings related to the tactic.
        """
        return {
            "name": "Persistence",
            "description": """The adversary is trying to maintain their foothold.

Persistence consists of techniques that adversaries use to keep access to systems across restarts, changed credentials, and other interruptions that could cut off their access. Techniques used for persistence include any access, action, or configuration changes that let them maintain their foothold on systems, such as replacing or hijacking legitimate code or adding startup code. """,
            "ioc_strings": [
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
                "\\inprochandler",
                "\\inprocserver",
                "\\inprocserver32",
                "\\localserver",
                "\\localserver32\\shellex",
                "\\progid",
                "\\treatas",
                "\\scriptleturl",
                "\\imagepath",
                "\\binpath",
                "\\servicedll",
                "\\servicemanifest",
                "\\Start Menu",
                "\\Startup",
                "reg.exe",
            ],
        }

    def TA0004(self):
        """
        Returns a dictionary containing information about privilege escalation techniques used by adversaries.

        This function provides details on how adversaries attempt to gain higher-level permissions
        on a system or network. It includes a description of the technique and a list of indicators
        of compromise (IOC) strings that may be associated with such activities. The IOC strings
        include various executables, commands, and functions that could indicate privilege escalation
        attempts by adversaries.

        Returns:
            dict: A dictionary containing the name, description, and IOC strings related to
                 privilege escalation techniques.
        """
        return {
            "name": "Privilege Escalation",
            "description": """The adversary is trying to gain higher-level permissions.

Privilege Escalation consists of techniques that adversaries use to gain higher-level permissions on a system or network. Adversaries can often enter and explore a network with unprivileged access but require elevated permissions to follow through on their objectives. Common approaches are to take advantage of system weaknesses, misconfigurations, and vulnerabilities. Examples of elevated access include: 

* SYSTEM/root level
* local administrator
* user account with admin-like access 
* user accounts with access to specific system or perform specific function

These techniques often overlap with Persistence techniques, as OS features that let an adversary persist can execute in an elevated context.  """,
            "ioc_strings": [
                "C:\\Windows\\system32\\lsass.exe",
                "mimikatz",
                "delpy",
                "wce.exe",
                "windows credential editor",
                "gsecdump.exe",
                "adfind.exe",
                "powershell.exe",
                "powershell_ise.exe",
                "pwsh.exe",
                "nps.exe",
                "rundll32.exe",
                "cmd.exe",
                "taskkill.exe",
                "wmic.exe",
                "wscript.exe",
                "wsl.exe",
                "bitsadmin.exe",
                "cscript.exe",
                "wcscript.exe",
                "AddSecurityPackage",
                "AdjustTokenPrivileges",
                "CreateProcessWithToken",
                "GetLogonSessionData",
                "GetMember",
                "GetMembers",
                "GetMethod",
                "GetMethods",
                "GetModuleHandle",
                "GetTokenInformation",
                "ImpersonateLoggedOnUser",
                "VirtualAlloc",
                "VirtualFree",
                "VirtualProtect",
                "WriteByte",
                "WriteInt32",
                "WriteProcessMemory",
                "ZeroFreeGlobalAllocUnicode",
                "OpenProcess",
                "ReadProcessMemory",
                "ReflectedType",
                "PtrToString",
                "PtrToStructure",
            ],
        }

    def TA0005(self):
        """
        Returns a dictionary containing information about the Defense Evasion tactic.

        This function returns a dictionary with details about the 'Defense Evasion' tactic,
        including its name, description, and IOC (Indicators of Compromise) strings. The
        description provides an overview of defense evasion techniques used by adversaries to
        avoid detection during their compromise. The IOC strings include various commands and
        functions that may be indicative of such activities.

        Returns:
            dict: A dictionary with keys 'name', 'description', and 'ioc_strings'. The value for
                'name' is the string 'Defense Evasion', the value for 'description' is a detailed
                explanation of defense evasion tactics, and the value for 'ioc_strings' is a list
                of strings that are potential indicators of compromise.
        """
        return {
            "name": "Defense Evasion",
            "description": """The adversary is trying to avoid being detected.

Defense Evasion consists of techniques that adversaries use to avoid detection throughout their compromise. Techniques used for defense evasion include uninstalling/disabling security software or obfuscating/encrypting data and scripts. Adversaries also leverage and abuse trusted processes to hide and masquerade their malware. Other tactics’ techniques are cross-listed here when those techniques include the added benefit of subverting defenses. """,
            "ioc_strings": [
                "certutil.exe",
                "expand.exe",
                "makecab.exe",
                "\\eulaaccepted",
                "CreateDecryptor",
                "CreateEncryptor",
                "Cryptography",
                "CryptoServiceProvider",
                "CryptoStream",
                "EncodedCommand",
                "ExpandString",
                "FromBase64String",
                "ToBase64String",
                "EnumerateSecurityPackages",
            ],
        }

    def TA0006(self):
        """
        Returns a dictionary containing information about the 'Credential Access' tactic.

        This function provides details on the 'Credential Access' tactic, including its name,
        description, and associated indicators of compromise (IOC) strings. The description
        explains that adversaries may attempt to steal account names and passwords through
        techniques such as keylogging or credential dumping. IOC strings include various
        executables and functions commonly used in credential access attacks.

        Returns:
            dict: A dictionary with keys 'name', 'description', and 'ioc_strings'. The value of
                'name' is the string 'Credential Access', 'description' provides a detailed
                explanation of the tactic, and 'ioc_strings' contains a list of strings that may
                indicate credential access activity.
        """
        return {
            "name": "Credential Access",
            "description": """The adversary is trying to steal account names and passwords.

Credential Access consists of techniques for stealing credentials like account names and passwords. Techniques used to get credentials include keylogging or credential dumping. Using legitimate credentials can give adversaries access to systems, make them harder to detect, and provide the opportunity to create more accounts to help achieve their goals.""",
            "ioc_strings": [
                "C:\\Windows\\system32\\lsass.exe",
                "mimikatz",
                "delpy",
                "wce.exe",
                "windows credential editor",
                "gsecdump.exe",
                "adfind.exe",
                "powershell.exe",
                "powershell_ise.exe",
                "pwsh.exe",
                "nps.exe",
                "rundll32.exe",
                "cmd.exe",
                "taskkill.exe",
                "wmic.exe",
                "wscript.exe",
                "wsl.exe",
                "bitsadmin.exe",
                "cscript.exe",
                "wcscript.exe",
                "Cryptography",
                "CryptoServiceProvider",
                "CryptoStream",
                "GetAsyncKeyState",
                "GetKeyboardState",
                "memcpy",
                "MemoryStream",
                "Methods",
                "MiniDumpWriteDump",
                "PasswordDeriveBytes",
            ],
        }

    def TA0007(self):
        """
        Returns a dictionary containing information about the 'Discovery' tactic.

        This function provides details on the 'Discovery' tactic used by adversaries to gain
        knowledge about the system and internal network. The returned dictionary includes a
        name, description, and a list of IOC (Indicators of Compromise) strings that may be
        associated with this tactic. These techniques help adversaries observe the environment
        and orient themselves before deciding how to act. They also allow adversaries to explore
        what they can control and what’s around their entry point in order to discover how it could
        benefit their current objective. Native operating system tools are often used toward this
        post-compromise information-gathering objective.

        Returns:
            dict: A dictionary with keys 'name', 'description', and 'ioc_strings'. The 'name' key
                  contains the string 'Discovery', the 'description' key provides a detailed explanation
                  of the tactic, and the 'ioc_strings' key lists various strings that may be indicators
                  of compromise related to this tactic.
        """
        return {
            "name": "Discovery",
            "description": """The adversary is trying to figure out your environment.

Discovery consists of techniques an adversary may use to gain knowledge about the system and internal network. These techniques help adversaries observe the environment and orient themselves before deciding how to act. They also allow adversaries to explore what they can control and what’s around their entry point in order to discover how it could benefit their current objective. Native operating system tools are often used toward this post-compromise information-gathering objective. """,
            "ioc_strings": [
                "AccessChk.exe",
                "AccessEnum.exe",
                "LoadOrder.exe",
                "LogonSessions.exe",
                "PipeList.exe",
                "PsGetSID.exe",
                "PsInfo.exe",
                "PsList.exe",
                "PsService.exe",
                "ipconfig.exe",
                "netstat.exe",
                "qprocess.exe",
                "query.exe",
                "quser.exe",
                "GetAssemblies",
                "GetAsyncKeyState",
                "GetConstructor",
                "GetConstructors",
                "GetDefaultMembers",
                "GetDelegateForFunctionPointer",
                "GetEvent",
                "GetEvents",
                "GetField",
                "GetFields",
                "GetForegroundWindow",
                "GetInterface",
                "GetInterfaceMap",
                "GetInterfaces",
                "GetKeyboardState",
                "GetLogonSessionData",
                "GetMember",
                "GetMembers",
                "GetMethod",
                "GetMethods",
                "GetModuleHandle",
                "GetNestedType",
                "GetNestedTypes",
                "GetPowerShell",
                "GetProcAddress",
                "GetProcessHandle",
                "GetProperties",
                "GetProperty",
                "GetTokenInformation",
                "GetTypes",
            ],
        }

    def TA0008(self):
        """
        Returns a dictionary containing information about lateral movement techniques used by adversaries.

        This function provides details on how adversaries move through an environment to reach their target. It includes a description of the Lateral Movement tactic and a list of Indicators of Compromise (IoC) strings that may be associated with this activity. The IoC strings include various executables, commands, and ports that could indicate lateral movement attempts by adversaries.

        Returns:
            dict: A dictionary containing the name, description, and IoC strings related to Lateral Movement techniques.
        """
        return {
            "name": "Lateral Movement",
            "description": """The adversary is trying to move through your environment.

Lateral Movement consists of techniques that adversaries use to enter and control remote systems on a network. Following through on their primary objective often requires exploring the network to find their target and subsequently gaining access to it. Reaching their objective often involves pivoting through multiple systems and accounts to gain. Adversaries might install their own remote access tools to accomplish Lateral Movement or use legitimate credentials with native network and operating system tools, which may be stealthier. """,
            "ioc_strings": [
                "\\eulaaccepted",
                "powershell.exe",
                "powershell_ise.exe",
                "pwsh.exe",
                "nps.exe",
                "rundll32.exe",
                "cmd.exe",
                "wmic.exe",
                "wscript.exe",
                "wsl.exe",
                "bitsadmin.exe",
                "cscript.exe",
                "wcscript.exe",
                "robocopy.exe",
                "psexec.exe",
                "psexesvc.exe",
                "remcomvsvc.exe",
                "remcom.exe",
                "paexec.exe",
                "csexec.exe",
                "csexecsvc.exe",
                "net.exe",
                "net use",
                "mstsc.exe",
                "3389",
                "5985",
                "5986",
                "schtasks.exe",
                "at.exe",
                "vncviewer.exe",
                "vnc.exe",
                "winexesvc.exe",
                "ftp.exe",
                "telnet.exe",
            ],
        }

    def TA0009(self):
        """
            Returns a dictionary containing information about the Collection tactic.

            This function provides details on the 'Collection' tactic used by adversaries to gather
            data relevant to their objectives. The returned dictionary includes a name, description,
            and indicators of compromise (IOC) strings associated with this tactic.

            Returns:
                dict: A dictionary containing the following keys:
        'name': The name of the tactic ('Collection').
        'description': A detailed description of the Collection tactic.
        'ioc_strings': A list of IOC strings related to this tactic, such as executable
                                     names and file extensions that may be used in collection activities.
        """
        return {
            "name": "Collection",
            "description": """The adversary is trying to gather data of interest to their goal.

Collection consists of techniques adversaries may use to gather information and the sources information is collected from that are relevant to following through on the adversary's objectives. Frequently, the next goal after collecting data is to steal (exfiltrate) the data. Common target sources include various drive types, browsers, audio, video, and email. Common collection methods include capturing screenshots and keyboard input.""",
            "ioc_strings": [
                "powershell.exe",
                "powershell_ise.exe",
                "pwsh.exe",
                "nps.exe",
                "rundll32.exe",
                "cmd.exe",
                "wmic.exe",
                "cscript.exe",
                "wcscript.exe",
                "wsl.exe",
                ".zip",
                ".rar",
                ".7z",
                ".cab",
                "rar.exe",
                "-hp",
                "7z.exe",
            ],
        }

    def TA0010(self):
        """
        Returns a dictionary containing information about exfiltration techniques used by adversaries to steal data from your network.

        The returned dictionary includes the name of the technique, a description of how it is used, and a list of IOC (Indicators of Compromise) strings that may be associated with this type of activity. These IOCs include executables and file extensions commonly used in exfiltration attempts.

        Returns:
            dict: A dictionary containing the name, description, and IOC strings related to exfiltration techniques.
        """
        return {
            "name": "Exfiltration",
            "description": """The adversary is trying to steal data.

Exfiltration consists of techniques that adversaries may use to steal data from your network. Once they’ve collected data, adversaries often package it to avoid detection while removing it. This can include compression and encryption. Techniques for getting data out of a target network typically include transferring it over their command and control channel or an alternate channel and may also include putting size limits on the transmission.""",
            "ioc_strings": [
                "powershell.exe",
                "powershell_ise.exe",
                "pwsh.exe",
                "nps.exe",
                "rundll32.exe",
                "cmd.exe",
                "wmic.exe",
                "cscript.exe",
                "wcscript.exe",
                "wsl.exe",
                ".zip",
                ".rar",
                ".7z",
                ".cab",
                "rar.exe",
                "-hp",
                "7z.exe",
                "bitsadmin.exe",
                "robocopy.exe",
            ],
        }

    def TA0011(self):
        """
        Returns a dictionary containing information about the 'Command and Control' tactic.

        This function provides details on the adversary's attempt to communicate with compromised systems within a victim network. It includes a description of the Command and Control techniques used by adversaries, which often involve mimicking normal traffic to avoid detection. The dictionary also contains indicators of compromise (IOC) strings that may be associated with this tactic.

        Returns:
            dict: A dictionary containing the name, description, and IOC strings related to the 'Command and Control' tactic.
        """
        return {
            "name": "Command and Control",
            "description": """The adversary is trying to communicate with compromised systems to control them.

Command and Control consists of techniques that adversaries may use to communicate with systems under their control within a victim network. Adversaries commonly attempt to mimic normal, expected traffic to avoid detection. There are many ways an adversary can establish command and control with various levels of stealth depending on the victim’s network structure and defenses.""",
            "ioc_strings": ["9000", "9001", "9030", "tor.exe"],
        }
