// ==========================================
// 🟢 FILE TYPE DETECTION RULES (SAFE)
// ==========================================

rule FileType_PHP
{
    meta:
        description = "Detect PHP file (strong)"

    strings:
        $php1 = "<?php"
        $php2 = "<?="
        $php3 = "$_GET"
        $php4 = "$_POST"
        $php5 = "$_REQUEST"

    condition:
        any of ($php1,$php2) or 2 of ($php3,$php4,$php5)
}

rule FileType_Python
{
    meta:
        description = "Detect Python file (strict)"

    strings:
        $py1 = "def "
        $py2 = "import "
        $py3 = "__name__"
        $py4 = "print("
        $py5 = "self"

    condition:
        3 of ($py*)
}

rule FileType_Ruby
{
    meta:
        description = "Detect Ruby file (strict)"

    strings:
        $rb1 = "puts "
        $rb2 = "require '"
        $rb3 = "end\n"
        $rb4 = "do |"

    condition:
        2 of ($rb*)
}

rule FileType_Perl
{
    meta:
        description = "Detect Perl file"

    strings:
        $pl1 = "use strict"
        $pl2 = "my $"
        $pl3 = "print "

    condition:
        2 of ($pl*)
}

rule FileType_Bash
{
    meta:
        description = "Detect Bash script (strict)"

    strings:
        $sh1 = "#!/bin/bash"
        $sh2 = "#!/bin/sh"
        $sh3 = "echo "
        $sh4 = "read "

    condition:
        any of ($sh1,$sh2) or 2 of ($sh3,$sh4)
}

// Detect via shebang (VERY IMPORTANT)
rule FileType_Shebang
{
    meta:
        description = "Detect script via shebang"

    strings:
        $s1 = "#!/usr/bin/python"
        $s2 = "#!/usr/bin/perl"
        $s3 = "#!/usr/bin/ruby"
        $s4 = "#!/bin/bash"

    condition:
        any of them
}


// ==========================================
// 🔴 SUSPICIOUS / MALICIOUS RULES
// ==========================================

rule Suspicious_Powershell
{
    meta:
        description = "PowerShell suspicious usage"

    strings:
        $ps1 = "powershell"
        $ps2 = "Invoke-Expression"
        $ps3 = "IEX"
        $ps4 = "-NoP"
        $ps5 = "-NonI"
        $ps6 = "System.Net.Sockets.TCPClient"

    condition:
        any of ($ps*)
}

rule Suspicious_Python
{
    meta:
        description = "Python reverse shell"

    strings:
        $py1 = "socket.socket"
        $py2 = "AF_INET"
        $py3 = "SOCK_STREAM"
        $py4 = "os.dup2"
        $py5 = "pty.spawn"
        $py6 = "subprocess.Popen"
        $py7 = "connect(("

    condition:
        3 of ($py*) and $py1
}

rule Suspicious_PHP_ReverseShell
{
    meta:
        description = "PHP reverse shell (strong detection)"

    strings:
        $s1 = "fsockopen"
        $s2 = "proc_open"
        $s3 = "stream_select"
        $s4 = "fwrite"
        $s5 = "fread"
        $s6 = "/bin/sh"
        $s7 = "shell"
        $s8 = "$sock"
        $s9 = "$pipes"

    condition:
        4 of ($s*)
}

rule Suspicious_Ruby
{
    meta:
        description = "Ruby reverse shell"

    strings:
        $rb1 = "TCPSocket.new"
        $rb2 = "require 'socket'"
        $rb3 = "exec sprintf"
        $rb4 = "fork"

    condition:
        2 of ($rb*) and $rb1
}

rule Suspicious_Perl
{
    meta:
        description = "Perl reverse shell"

    strings:
        $pl1 = "IO::Socket::INET"
        $pl2 = "exec(\"/bin/sh\")"
        $pl3 = "system("
        $pl4 = "fork"

    condition:
        2 of ($pl*) and $pl1
}

rule Suspicious_Bash
{
    meta:
        description = "Bash reverse shell"

    strings:
        $bash1 = "/dev/tcp/"
        $bash2 = "bash -i"
        $bash3 = "sh -i"
        $bash4 = ">&"
        $bash5 = "0>&1"

    condition:
        2 of ($bash*)
}

rule Suspicious_Network_Connection
{
    meta:
        description = "Generic network behavior"

    strings:
        $net1 = "socket"
        $net2 = "connect("
        $net3 = "TcpClient"
        $net4 = "net.Dial"

    condition:
        3 of ($net*)
}

// 🔥 Detect encoded payload execution
rule Suspicious_Encoded_Execution
{
    meta:
        description = "Encoded execution (obfuscation)"

    strings:
        $e1 = "base64_decode"
        $e2 = "eval("
        $e3 = "exec("
        $e4 = "system("

    condition:
        2 of ($e*)
}

// Detect long base64 blobs
rule Base64_Payload
{
    meta:
        description = "Base64 encoded payload"

    strings:
        $b64 = /[A-Za-z0-9+\/]{80,}={0,2}/

    condition:
        $b64
}


// ==========================================
// 🧬 BINARY TYPE DETECTION (MAGIC BASED)
// ==========================================

rule FileType_PE
{
    meta:
        description = "Windows EXE"

    condition:
        uint16(0) == 0x5A4D
}

rule FileType_ZIP
{
    meta:
        description = "ZIP archive"

    condition:
        uint32(0) == 0x04034b50
}

rule FileType_ELF
{
    meta:
        description = "Linux ELF"

    condition:
        uint32(0) == 0x464c457f
}