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

vmess://eyJ2IjoiMiIsImFkZCI6IjUuMjMxLjI2LjE1MSIsInBvcnQiOjcxMTEsInNjeSI6ImF1dG8iLCJwcyI6IuW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI3MDQ4ZTBhZC0wNGEwLTQ0MWMtODVlZS00NjEyZGM2NWFlNWUiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy55YWhvby5jb20iLCJwYXRoIjoiL0REcVhzbEtkREd0NXhSRHZITmxqRGROP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ3d3cueWFob28uY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsImV4dHJhIjoiIiwicGNzIjoiIiwib3MiOiIifQ== 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@audiogramotmarche.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=audiogramotmarche.oceanof.xyz&type=xhttp&host=audiogramotmarche.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@bluepointradopalize.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=bluepointradopalize.oceanof.xyz&type=xhttp&host=bluepointradopalize.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#美国 
trojan://e1241ee8-f866-4afc-97e7-387fa537fdf6@5.231.26.151:62907?flow=&security=tls&sni=www.yahoo.com&type=ws&header=none&host=www.yahoo.com&path=/%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=&os=#德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@103.21.244.164:443?flow=&encryption=none&security=tls&sni=4372.34892.qzz.io&type=xhttp&host=4372.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#德国 
vless://fc63367a-39d4-4f68-ae0d-e58cada00ead@5.231.26.151:17480?flow=&encryption=none&security=tls&sni=www.yahoo.com&type=ws&host=www.yahoo.com&path=/UR5883ZzW1WNAytObWgww7k1M%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=&os=#德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.27.104.179:443?flow=&encryption=none&security=tls&sni=4372.34892.qzz.io&type=xhttp&host=4372.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@storiedwswarner.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=storiedwswarner.oceanof.xyz&type=xhttp&host=storiedwswarner.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#美国 
hysteria2://I5iRXp6TOCbgMMmnivnE4Q7t0Gvo4XSRfr59vV@5.231.26.151:23877?insecure=1&sni=www.yahoo.com&alpn=&fp=&obfs=salamander&obfs-password=Oo0t92XhHMwM2V4T57e2rcZQBK8PokRR5XZAIm&mport=&os=#德国 
hysteria2://Hnoko0uETj7WbjwQQ2gPuUJc5uGMCD@5.231.26.151:53435?insecure=1&sni=www.yahoo.com&alpn=&fp=&obfs=salamander&obfs-password=WSlRk9uwkiMQWaJKRDKaRg0VT03&mport=&os=#德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@peakedmptoneless.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=peakedmptoneless.oceanof.xyz&type=xhttp&host=peakedmptoneless.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@nolongervclabber.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=nolongervclabber.oceanof.xyz&type=xhttp&host=nolongervclabber.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.27.87.206:443?flow=&encryption=none&security=tls&sni=4372.34892.qzz.io&type=xhttp&host=4372.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMjMxLjI2LjE1MSIsInBvcnQiOjE4Nzc5LCJzY3kiOiJhdXRvIiwicHMiOiLlvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiNzY2ZGI0ZTYtYWQ5ZC00YmIyLWExOTUtZjE0MzFlNDIwZmFkIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ3d3cueWFob28uY29tIiwicGF0aCI6Ii9md2N0RExIdDJOP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ3d3cueWFob28uY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsImV4dHJhIjoiIiwicGNzIjoiIiwib3MiOiIifQ== 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.17.107.191:443?flow=&encryption=none&security=tls&sni=4372.34892.qzz.io&type=xhttp&host=4372.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#德国 
anytls://RZRZoiP8Ucmq3T1oIVP0OBcP9R@5.231.26.151:27496?insecure=1&sni=www.yahoo.com&alpn=h2&fp=&os=#德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@firesalelihammett.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=firesalelihammett.oceanof.xyz&type=xhttp&host=firesalelihammett.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.25.135.240:443?flow=&encryption=none&security=tls&sni=4372.34892.qzz.io&type=xhttp&host=4372.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@pockmarkwschmeer.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=pockmarkwschmeer.oceanof.xyz&type=xhttp&host=pockmarkwschmeer.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.27.27.86:443?flow=&encryption=none&security=tls&sni=4372.34892.qzz.io&type=xhttp&host=4372.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@webbedperistic.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=webbedperistic.oceanof.xyz&type=xhttp&host=webbedperistic.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#美国 
hysteria2://2t4XGpgwlm2nCwsolCQCdVs@5.231.26.151:12752?insecure=1&sni=www.yahoo.com&alpn=&fp=&obfs=salamander&obfs-password=72IMp43RCn0670ezEMmbKAGkBZv4sKTgVTaJ8BSn&mport=&os=#德国 
hysteria2://7dY0n9qZEvE7qSjhD6cfU1U99c@5.231.26.151:42121?insecure=1&sni=www.yahoo.com&alpn=&fp=&obfs=salamander&obfs-password=Lah5vfjH2iEwyKZWYodsTvSU3F&mport=&os=#德国 
vless://5912c24d-672b-4aa2-8221-3c99d99cf209@5.231.26.151:22587?flow=&encryption=none&security=tls&sni=www.yahoo.com&type=ws&host=www.yahoo.com&path=/IHbHojooIr0IpbzZWuQE3Jby2WK%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=&os=#德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@162.159.192.187:443?flow=&encryption=none&security=tls&sni=4372.34892.qzz.io&type=xhttp&host=4372.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.27.65.243:443?flow=&encryption=none&security=tls&sni=4372.34892.qzz.io&type=xhttp&host=4372.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@qophsragdoll.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=qophsragdoll.oceanof.xyz&type=xhttp&host=qophsragdoll.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@varnaxhemline.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=varnaxhemline.oceanof.xyz&type=xhttp&host=varnaxhemline.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.27.11.25:443?flow=&encryption=none&security=tls&sni=4372.34892.qzz.io&type=xhttp&host=4372.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@auriculateidastride.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=auriculateidastride.oceanof.xyz&type=xhttp&host=auriculateidastride.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@foveanuhcardia.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=foveanuhcardia.oceanof.xyz&type=xhttp&host=foveanuhcardia.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@198.41.201.41:443?flow=&encryption=none&security=tls&sni=4372.34892.qzz.io&type=xhttp&host=4372.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.23.105.86:443?flow=&encryption=none&security=tls&sni=4372.34892.qzz.io&type=xhttp&host=4372.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.21.115.63:443?flow=&encryption=none&security=tls&sni=4372.34892.qzz.io&type=xhttp&host=4372.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@172.67.17.135:443?flow=&encryption=none&security=tls&sni=4372.34892.qzz.io&type=xhttp&host=4372.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#德国 
hysteria2://Rwdn7JRn575Y6YS2MgUSlc0Yp2rBo7zcOcYx@5.231.26.151:17806?insecure=1&sni=www.yahoo.com&alpn=&fp=&obfs=salamander&obfs-password=m0APtLrcdmYZ7t0QBrDGEUp7F&mport=&os=#德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.25.129.36:443?flow=&encryption=none&security=tls&sni=4372.34892.qzz.io&type=xhttp&host=4372.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#德国 
trojan://54b4beab-0eff-4aa6-92a6-6cbd75d2ad52@5.231.26.151:19969?flow=&security=tls&sni=www.yahoo.com&type=ws&header=none&host=www.yahoo.com&path=/1H8yLHoEEMgnIwdzHt0dK%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=&os=#德国 


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
