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
vless://c897facf-2836-4538-be6e-25386fb49284@159.195.60.65:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=free1.anotherboring.top&type=tcp&host=&path=&headerType=none&alpn=&fp=firefox&pbk=vTtRZ_FeFQoAigFr_pmVc_O85RaE9H8aVL0SitFYcmI&sid=53cd45d26d7b53fe&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0612丹麦 
ss://YWVzLTI1Ni1nY206N2UxZGQ0YzU1YmY4NWRhNQ==@212.192.15.177:12091?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=0&fragment=,100-200,10-60&os=#0612香港 
ss://YWVzLTEyOC1nY206SlZyc0xMTjF0a044b1haTw==@chengbai02.ascwt179.com:13223?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=0&fragment=,100-200,10-60&os=#0612英国 
vless://ad356e93-cc14-417d-9f4e-32376d03f5b7@newyorkcity.instasup.ir:1004?flow=&encryption=none&security=reality&sni=yahoo.com&type=tcp&host=&path=&headerType=none&alpn=&fp=firefox&pbk=437UW8qHz_L4qlOZ_AgufdsA9me_uS5MWM-eptxM3w4&sid=998ad2ef2d977802&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0612美国 
vless://95e118b4-4352-4218-8493-f20cc7fc467a@nl08.abvpn.ru:443?flow=&encryption=none&security=tls&sni=nl08.abvpn.ru&type=ws&host=&path=/websocket&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0612荷兰 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMC5oZGFjZC5jb20iLCJwb3J0IjozMDgwNywic2N5IjoiYXV0byIsInBzIjoiMDYxMummmea4ryIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJleHRyYSI6IiIsInBjcyI6IiIsIm9zIjoiIn0= 
hysteria2://eq5hIPpZEoCPhBPihxPORcv0edrbkL6zQnc978@89.106.64.79:2003?insecure=1&sni=swdist.apple.com&alpn=&fp=&obfs=salamander&obfs-password=ZAyUlcFO1yNA0IQciAoi8iO0gb3vY&mport=&os=#0612德国 
hysteria2://eHCXYWGmEvkam8Z3IfxhhKs5Eae@89.106.64.79:12429?insecure=1&sni=swdist.apple.com&alpn=&fp=&obfs=salamander&obfs-password=XL0TWMsbwKBI8Dfr8GYJ5Raj&mport=&os=#0612德国 
anytls://NaykhEyUZ4mCbHrm01G1ZHx@89.106.64.79:47520?insecure=1&sni=swdist.apple.com&alpn=h2&fp=&os=#0612德国 
hysteria2://WIBE9ULdGLpIDZKih4UoI@89.106.64.79:49744?insecure=1&sni=swdist.apple.com&alpn=&fp=&obfs=salamander&obfs-password=gqqOMGndki6f3C0i1t973xJlA&mport=&os=#0612德国 
anytls://iOD99Mjjk3INd5qfyvIJwX4t99tNU2rB8oep@89.106.64.79:37219?insecure=1&sni=swdist.apple.com&alpn=h2&fp=&os=#0612德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@qqitouchily.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=qqitouchily.oceanof.xyz&type=xhttp&host=qqitouchily.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0612美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@brbplantpart.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=brbplantpart.oceanof.xyz&type=xhttp&host=brbplantpart.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0612美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@ileeward.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=ileeward.oceanof.xyz&type=xhttp&host=ileeward.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0612美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@nlegatee.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=nlegatee.oceanof.xyz&type=xhttp&host=nlegatee.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0612美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@dflicker.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=dflicker.oceanof.xyz&type=xhttp&host=dflicker.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0612美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@ljdegrease.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=ljdegrease.oceanof.xyz&type=xhttp&host=ljdegrease.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0612美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@szbulbaceous.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=szbulbaceous.oceanof.xyz&type=xhttp&host=szbulbaceous.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0612美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@yaslongas.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=yaslongas.oceanof.xyz&type=xhttp&host=yaslongas.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0612美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@yqmoline.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=yqmoline.oceanof.xyz&type=xhttp&host=yqmoline.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0612美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.24.91.33:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0612德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@162.159.62.219:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0612德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.25.225.87:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0612德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.27.65.243:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0612德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.24.179.138:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0612德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.21.115.63:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0612德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@103.21.244.235:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0612德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@162.159.3.7:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0612德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@162.159.192.187:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0612德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.20.31.41:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0612德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@103.21.244.78:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0612德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@198.41.223.174:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0612德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.27.87.206:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0612德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@162.159.252.125:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0612德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@162.159.8.239:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0612德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.27.6.183:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0612德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.27.27.86:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0612德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@190.93.245.63:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0612德国 

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
