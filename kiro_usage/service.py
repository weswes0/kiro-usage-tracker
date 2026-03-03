"""Service installer — register/unregister the archiver as a background service.

macOS: ~/Library/LaunchAgents/dev.kiro.usage-archiver.plist  (launchctl)
Linux: ~/.config/systemd/user/kiro-usage-archiver.service    (systemd --user)
"""

import os, platform, shutil, subprocess, textwrap
from pathlib import Path

LABEL = "dev.kiro.usage-archiver"

def _find_archiver_bin():
    """Find the kiro-usage-archiver binary on PATH."""
    p = shutil.which("kiro-usage-archiver")
    if p:
        return p
    # Fallback: same directory as the current Python interpreter
    d = Path(os.sys.executable).parent / "kiro-usage-archiver"
    if d.exists():
        return str(d)
    return None

# ── macOS (launchd) ───────────────────────────────────────────────────────────
def _launchd_plist_path():
    return Path.home() / "Library/LaunchAgents/{}.plist".format(LABEL)

def _launchd_install():
    bin_path = _find_archiver_bin()
    if not bin_path:
        print("Error: kiro-usage-archiver not found on PATH")
        return False
    plist = textwrap.dedent("""\
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
          "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
            <key>Label</key>
            <string>{label}</string>
            <key>ProgramArguments</key>
            <array>
                <string>{bin}</string>
            </array>
            <key>RunAtLoad</key>
            <true/>
            <key>KeepAlive</key>
            <true/>
            <key>StandardErrorPath</key>
            <string>{log}</string>
            <key>StandardOutPath</key>
            <string>{log}</string>
        </dict>
        </plist>
    """).format(
        label=LABEL,
        bin=bin_path,
        log=str(Path.home() / ".kiro_sessions/archiver.log"),
    )
    path = _launchd_plist_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Unload first if already loaded
    if path.exists():
        subprocess.run(["launchctl", "bootout", "gui/{}".format(os.getuid()), str(path)],
                       capture_output=True)
    path.write_text(plist)
    r = subprocess.run(["launchctl", "bootstrap", "gui/{}".format(os.getuid()), str(path)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("Warning: launchctl bootstrap: {}".format(r.stderr.strip()))
    return True

def _launchd_uninstall():
    path = _launchd_plist_path()
    if not path.exists():
        print("Not installed.")
        return False
    subprocess.run(["launchctl", "bootout", "gui/{}".format(os.getuid()), str(path)],
                   capture_output=True)
    path.unlink()
    return True

# ── Linux (systemd --user) ────────────────────────────────────────────────────
def _systemd_unit_path():
    return Path.home() / ".config/systemd/user/kiro-usage-archiver.service"

def _systemd_install():
    bin_path = _find_archiver_bin()
    if not bin_path:
        print("Error: kiro-usage-archiver not found on PATH")
        return False
    unit = textwrap.dedent("""\
        [Unit]
        Description=Kiro Usage Session Archiver

        [Service]
        ExecStart={bin}
        Restart=on-failure
        RestartSec=5

        [Install]
        WantedBy=default.target
    """).format(bin=bin_path)
    path = _systemd_unit_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(unit)
    subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
    subprocess.run(["systemctl", "--user", "enable", "--now", "kiro-usage-archiver"],
                   capture_output=True)
    return True

def _systemd_uninstall():
    path = _systemd_unit_path()
    if not path.exists():
        print("Not installed.")
        return False
    subprocess.run(["systemctl", "--user", "disable", "--now", "kiro-usage-archiver"],
                   capture_output=True)
    path.unlink()
    subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
    return True

# ── Public API ────────────────────────────────────────────────────────────────
def install():
    if platform.system() == "Darwin":
        ok = _launchd_install()
    else:
        ok = _systemd_install()
    if ok:
        print("✅ Archiver installed and running.")
        print("   Sessions will be archived to ~/.kiro_sessions/")
    return ok

def uninstall():
    if platform.system() == "Darwin":
        ok = _launchd_uninstall()
    else:
        ok = _systemd_uninstall()
    if ok:
        print("✅ Archiver uninstalled.")
    return ok

def status():
    if platform.system() == "Darwin":
        path = _launchd_plist_path()
        if not path.exists():
            print("Archiver: not installed")
            return
        r = subprocess.run(
            ["launchctl", "print", "gui/{}/{}".format(os.getuid(), LABEL)],
            capture_output=True, text=True)
        if r.returncode == 0:
            # Extract state line
            for line in r.stdout.splitlines():
                if "state" in line.lower():
                    print("Archiver: {}".format(line.strip()))
                    return
            print("Archiver: loaded")
        else:
            print("Archiver: installed but not running")
    else:
        r = subprocess.run(
            ["systemctl", "--user", "is-active", "kiro-usage-archiver"],
            capture_output=True, text=True)
        print("Archiver: {}".format(r.stdout.strip() or "not installed"))
