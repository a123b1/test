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

vless://9794d18f-9280-3553-a7a5-a23da75aca76@108.61.163.234:443?flow=xtls-rprx-vision&encryption=none&security=tls&sni=u691611u45517d37s7122.gogocs.xyz&type=tcp&host=45517d37s7122.gogocs.xyz&path=&headerType=none&alpn=http/1.1%2Ch2&fp=firefox&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0630日本 
vless://9794d18f-9280-3553-a7a5-a23da75aca76@45.76.96.98:443?flow=xtls-rprx-vision&encryption=none&security=tls&sni=u691611uee859f33s5969.wagahaha.xyz&type=tcp&host=ee859f33s5969.wagahaha.xyz&path=&headerType=none&alpn=http/1.1%2Ch2&fp=firefox&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0630日本 
vless://9794d18f-9280-3553-a7a5-a23da75aca76@s5975.okgg.top:443?flow=xtls-rprx-vision&encryption=none&security=tls&sni=u691611uee859f33s5969.wagahaha.xyz&type=tcp&host=ee859f33s5969.wagahaha.xyz&path=&headerType=none&alpn=http/1.1%2Ch2&fp=firefox&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0630日本 
vless://9794d18f-9280-3553-a7a5-a23da75aca76@s7123.uugfw.top:443?flow=xtls-rprx-vision&encryption=none&security=tls&sni=u691611u45517d37s7122.gogocs.xyz&type=tcp&host=45517d37s7122.gogocs.xyz&path=&headerType=none&alpn=http/1.1%2Ch2&fp=firefox&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0630日本 
vless://9794d18f-9280-3553-a7a5-a23da75aca76@s7124.ccgfw.online:443?flow=xtls-rprx-vision&encryption=none&security=tls&sni=u691611u45517d37s7122.gogocs.xyz&type=tcp&host=45517d37s7122.gogocs.xyz&path=&headerType=none&alpn=http/1.1%2Ch2&fp=firefox&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0630日本 
hysteria2://5CfpsOdQ9dEBVrfhAgruk9hNJb0qpBD@45.82.122.119:61987?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=ZUegWCg5kgsPhhDrMhPVK0ym0NYwoE&mport=&os=#0630德国 
hysteria2://dN1WsGf5Rd3VOgtiiDZfDksvwijrzII@45.82.122.119:22580?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=rCjOItOBRZm93rDwnn&mport=&os=#0630德国 
hysteria2://5sPsZH9jpL5fKfffWmLRpfcSJlJyIVpWm5@45.82.122.119:24015?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=HXJ41gy67i5BPyVOJqHRkTwPBvuHnZE&mport=&os=#0630德国 
hysteria2://zhe8WUI9wtG728U945B3@45.82.122.119:21214?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=ff8cBZ3TXtWiBgNvJm1fo7kvg&mport=&os=#0630德国 
hysteria2://7JnCZOKq2gwcqc38b@45.82.122.119:44802?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=E1iRsQ6UYWS2KXJYZCE41lEk7mKE&mport=&os=#0630德国 
hysteria2://X7QSUye3NKXxZ6LR76nqTuAGOvwgtqDjL1C1olH@45.82.122.119:62468?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=sHoHpfyJB6pyTATWJLCGaC3Nn3ua4SukqC1qh&mport=&os=#0630德国 
anytls://rGFGShFNUjJX5Iy2NT@45.82.122.119:13367?insecure=1&sni=update.microsoft.com&alpn=h2&fp=&os=#0630德国 
anytls://7HfZmJxgykC9bZ2iJA@45.82.122.119:27213?insecure=1&sni=update.microsoft.com&alpn=h2&fp=&os=#0630德国 
anytls://BGrdsC9im9IszkdizAij84X1N@45.82.122.119:21996?insecure=1&sni=update.microsoft.com&alpn=h2&fp=&os=#0630德国 
anytls://zxUhR0XkiFqatYB1GbdU@45.82.122.119:63771?insecure=1&sni=update.microsoft.com&alpn=h2&fp=&os=#0630德国 
anytls://C6zsCFGOwXNqQhB4WPkenAg1u0FYM@45.82.122.119:41067?insecure=1&sni=update.microsoft.com&alpn=h2&fp=&os=#0630德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@173.245.59.97:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0630德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@clinicallyry.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=clinicallyry.oceanof.xyz&type=xhttp&host=clinicallyry.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0630美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@atonementxi.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=atonementxi.oceanof.xyz&type=xhttp&host=atonementxi.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0630美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@188.114.98.101:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0630德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@profligacypr.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=profligacypr.oceanof.xyz&type=xhttp&host=profligacypr.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0630美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.27.113.190:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0630德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@macer.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=macer.oceanof.xyz&type=xhttp&host=macer.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0630美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@141.101.113.130:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0630德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.18.21.130:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0630德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@securefwo.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=securefwo.oceanof.xyz&type=xhttp&host=securefwo.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0630美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.18.248.218:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0630德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@162.159.252.125:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0630德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.19.133.213:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0630德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.16.228.174:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0630德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@198.41.202.17:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0630德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@crawfordx.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=crawfordx.oceanof.xyz&type=xhttp&host=crawfordx.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0630美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@141.101.121.129:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0630德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@carcinogent.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=carcinogent.oceanof.xyz&type=xhttp&host=carcinogent.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0630美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@173.245.59.70:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0630德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@lakevoltao.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=lakevoltao.oceanof.xyz&type=xhttp&host=lakevoltao.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0630美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.25.199.178:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0630德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@harridansv.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=harridansv.oceanof.xyz&type=xhttp&host=harridansv.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0630美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@textfilexmb.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=textfilexmb.oceanof.xyz&type=xhttp&host=textfilexmb.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0630美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.27.6.183:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0630德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.16.42.49:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0630德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@162.159.192.187:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0630德国 

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
