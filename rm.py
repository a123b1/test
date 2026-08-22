import argparse
import os
import pathlib
import platform
import shutil
import sys
from typing import NamedTuple

import setuptools
from wheel.bdist_wheel import bdist_wheel

# Parse --build-option arguments meant for the bdist_wheel command. We have to parse these
# ourselves because when bdist_wheel runs it's too late to select a subset of libraries for package_data.
parser = argparse.ArgumentParser()
parser.add_argument("command")
parser.add_argument(
    "--platform", "-P", type=str, default="", help="Wheel platform: windows|linux|macos-x86_64|aarch64|universal"
)
args = parser.parse_known_args()[0]


# returns a canonical machine architecture string
# - "x86_64" for x86-64, aka. AMD64, aka. x64
# - "aarch64" for AArch64, aka. ARM64
def machine_architecture() -> str:
    machine = platform.machine()
    if machine == "x86_64" or machine == "AMD64":
        return "x86_64"
    if machine == "aarch64" or machine == "arm64":
        return "aarch64"
    raise RuntimeError(f"Unrecognized machine architecture {machine}")


def machine_os() -> str:
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "linux":
        return "linux"
    if sys.platform == "darwin":
        return "macos"
    raise RuntimeError(f"Unrecognized system platform {sys.platform}")


class Platform(NamedTuple):
    os: str
    arch: str
    fancy_name: str
    extension: str
    tag: str

    def name(self) -> str:
        return self.os + "-" + self.arch


platforms = [
    Platform("windows", "x86_64", "Windows x86-64", ".dll", "win_amd64"),
    Platform("linux", "x86_64", "Linux x86-64", ".so", "manylinux2014_x86_64"),
    Platform("linux", "aarch64", "Linux AArch64", ".so", "manylinux2014_aarch64"),
    Platform("macos", "universal", "macOS universal", ".dylib", "macosx_10_13_universal2"),
]


class Library(NamedTuple):
    """
trojan://humanity@104.18.152.77:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0821法国 
trojan://humanity@104.21.46.3:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=http/1.1%2Ch3%2Ch2&fp=chrome&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0821法国 
trojan://humanity@104.26.14.137:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0821法国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@papoosehhknossos.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=papoosehhknossos.oceanof.xyz&type=xhttp&host=papoosehhknossos.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.25.160.84:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@farcicalblcvirginian.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=farcicalblcvirginian.oceanof.xyz&type=xhttp&host=farcicalblcvirginian.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@190.93.244.167:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@spamyewfringed.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=spamyewfringed.oceanof.xyz&type=xhttp&host=spamyewfringed.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@103.21.244.114:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.25.199.206:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@162.159.130.238:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.18.24.219:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@198.41.196.128:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@103.21.244.203:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@103.21.244.86:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.18.248.218:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@173.245.59.242:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@anyjwtitillate.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=anyjwtitillate.oceanof.xyz&type=xhttp&host=anyjwtitillate.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@141.101.121.129:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@metrifynxlot.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=metrifynxlot.oceanof.xyz&type=xhttp&host=metrifynxlot.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@marattiagdcourtier.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=marattiagdcourtier.oceanof.xyz&type=xhttp&host=marattiagdcourtier.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@shimmyvtrepublish.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=shimmyvtrepublish.oceanof.xyz&type=xhttp&host=shimmyvtrepublish.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@musophobiafccdeadness.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=musophobiafccdeadness.oceanof.xyz&type=xhttp&host=musophobiafccdeadness.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@linnaeuscrebenaceae.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=linnaeuscrebenaceae.oceanof.xyz&type=xhttp&host=linnaeuscrebenaceae.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@188.114.96.253:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@passerbywzsqueezer.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=passerbywzsqueezer.oceanof.xyz&type=xhttp&host=passerbywzsqueezer.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@103.21.244.155:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@glendowernldsucking.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=glendowernldsucking.oceanof.xyz&type=xhttp&host=glendowernldsucking.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.24.205.235:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.25.18.25:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0821德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTc1LjIyMC4zOCIsInBvcnQiOjU5MDc2LCJzY3kiOiJhdXRvIiwicHMiOiIwODIx5b635Zu9IiwibmV0Ijoid3MiLCJpZCI6IjI1OWQ5YmQ0LTYwMDItNGM4Ny04ZjA0LTEwMDFlNDQ1ZjA1YyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoidXBkYXRlLm1pY3Jvc29mdC5jb20iLCJwYXRoIjoiLzAyQWRTcjRhbEd0P2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJleHRyYSI6IiIsInBjcyI6IiIsIm9zIjoiIn0= 
trojan://42766876-e2a4-44ff-8eea-93bbf39626e6@5.175.220.38:12017?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/4wGthwSQpk21lVcNJUEGTpZfO%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=&os=#0821德国 
hysteria2://LbdYnnDn1lBHEDel2lIx2RcKEQVf3A@5.175.220.38:35498?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=n6F6PmRAVU0grbFWf3p5GIfvs0hDtuq24L3b03Qj&mport=&os=#0821德国 
hysteria2://UahEnxNdQThvT5nQLEEWuYskSHE9fpzDs11@5.175.220.38:5711?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=EOtW2se1WQHKOgeCUSeu18owY&mport=&os=#0821德国 
anytls://fAYZD70TwutyD1KpFQntFEshYz65KbXH@5.175.220.38:27206?insecure=1&sni=update.microsoft.com&alpn=h2&fp=&os=#0821德国 
hysteria2://VAsXIvUldEJETOSEN8RxM51boOBxjbQdmCH@5.175.220.38:5002?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=huST6OmGllQ6AV17Z8Ahum8pQ4y&mport=&os=#0821德国 
hysteria2://9iAqkibgMUxuxRcNigdStlECTecoN2@5.175.220.38:7419?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=08j4v2jyikwtQ8t0ZVYco3v&mport=&os=#0821德国 
hysteria2://M8qcKfcprVTMErY9ld0oE2LHkQlulKe3c8Tu3o8V@5.175.220.38:42344?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=kSPBlTQGdlQwzxgnu9WGt2EcNZdQ64MLuaZZD&mport=&os=#0821德国 

"""
    file: str
    directory: str
    platform: Platform


# Enumerate warp/bin libraries
def detect_warp_libraries():
    detected_libraries = set()
    warp_bin = pathlib.Path("warp/bin")
    for file in warp_bin.rglob("*.*"):
        for p in platforms:
            if os.path.splitext(file.name)[1] == p.extension:
                # If this is a local build, assume we want a wheel for this machine's architecture
                if file.parent.name == "bin" and (p.arch == machine_architecture() or p.arch == "universal"):
                    detected_libraries.add(Library(file.name, "bin/", p))
                else:
                    # Expect libraries to be in a subdirectory named after the wheel platform
                    platform_name = p.name()
                    if file.parent.name == platform_name:
                        detected_libraries.add(Library(file.name, "bin/" + platform_name + "/", p))

    if len(detected_libraries) == 0:
        raise Exception("No libraries found in warp/bin. Please run build_lib.py first.")

    return detected_libraries


detected_libraries = detect_warp_libraries()
detected_platforms = {lib.platform for lib in detected_libraries}

wheel_platform = None  # The one platform for which we're building a wheel

if args.command == "bdist_wheel":
    if args.platform != "":
        for p in platforms:
            if args.platform == p.name():
                wheel_platform = p
                print(f"Platform argument specified for building {p.fancy_name} wheel")
                break

        if wheel_platform is None:
            print(f"Platform argument '{args.platform}' not recognized")
        elif wheel_platform not in detected_platforms:
            print(f"No libraries found for {wheel_platform.fancy_name}")
            print("Falling back to auto-detection")
            wheel_platform = None

    if wheel_platform is None:
        if len(detected_platforms) > 1:
            print("Libraries for multiple platforms were detected.")
            print(
                "Run `python -m build --wheel -C--build-option=-P[windows|linux|macos]-[x86_64|aarch64|universal]` to select a specific one."
            )
            # Select the libraries corresponding with the this machine's platform
            for p in platforms:
                if p.os == machine_os() and p.arch == machine_architecture():
                    wheel_platform = p
                    break

        if wheel_platform is None:
            # Just pick the first one
            wheel_platform = next(iter(detected_platforms))

    print("Creating Warp wheel for " + wheel_platform.fancy_name)


# Binary wheel distribution builds assume that the platform you're building on will be the platform
# of the package. This class overrides the platform tag.
# https://packaging.python.org/en/latest/specifications/platform-compatibility-tags
class WarpBDistWheel(bdist_wheel):
    # Even though we parse the platform argument ourselves, we need to declare it here as well so
    # setuptools.Command can validate the command line options.
    user_options = bdist_wheel.user_options + [
        ("platform=", "P", "Wheel platform: windows|linux|macos-x86_64|aarch64|universal"),
    ]

    def initialize_options(self):
        super().initialize_options()
        self.platform = ""

    def get_tag(self):
        if wheel_platform is not None:
            # The wheel's complete tag format is {python tag}-{abi tag}-{platform tag}.
            return "py3", "none", wheel_platform.tag
        else:
            # The target platform was not overridden. Fall back to base class behavior.
            return bdist_wheel.get_tag(self)

    def run(self):
        super().run()

        # Clean up so we can re-invoke `py -m build --wheel -C--build-option=--platform=...`
        # See https://github.com/pypa/setuptools/issues/1871 for details.
        shutil.rmtree("./build", ignore_errors=True)
        shutil.rmtree("./warp_lang.egg-info", ignore_errors=True)


# Distributions are identified as non-pure (i.e. containing non-Python code, or binaries) if the
# setuptools.setup() `ext_modules` parameter is not empty, but this assumes building extension
# modules from source through the Python build. This class provides an override for prebuilt binaries:
class BinaryDistribution(setuptools.Distribution):
    def has_ext_modules(self):
        return True


def get_warp_libraries(platform):
    libraries = []
    for library in detected_libraries:
        if library.platform == platform:
            src = "warp/" + library.directory + library.file
            dst = "warp/bin/" + library.file
            if src != dst:
                shutil.copyfile(src, dst)

            libraries.append("bin/" + library.file)

    return libraries


if wheel_platform is not None:
    warp_binary_libraries = get_warp_libraries(wheel_platform)
else:
    warp_binary_libraries = []  # Not needed during egg_info command

setuptools.setup(
    package_data={
        "": [
            "native/*.cpp",
            "native/*.cu",
            "native/*.h",
            "native/clang/*.cpp",
            "native/nanovdb/*.h",
            "tests/assets/*",
            "examples/assets/*",
        ]
        + warp_binary_libraries,
    },
    distclass=BinaryDistribution,
    cmdclass={
        "bdist_wheel": WarpBDistWheel,
    },
)
