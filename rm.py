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


trojan://tDW776HerJ07nbiT8Q6LPBu@103.211.151.21:443?flow=&security=tls&sni=hk2-speedtest.tools.gcore.com&type=ws&header=none&host=api.euzzz.ru&path=/msdownload&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=true#7,德国,剩999G,昨0G.(0901) 
trojan://tDW776HerJ07nbiT8Q6LPBu@hk2-speedtest.tools.gcore.com:443?flow=&security=tls&sni=hk2-speedtest.tools.gcore.com&type=ws&header=none&host=api.euzzz.ru&path=/msdownload&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=true#7,德国,剩999G,昨0G.(0901) 
trojan://tDW776HerJ07nbiT8Q6LPBu@202.129.236.162:443?flow=&security=tls&sni=kx-speedtest.tools.gcore.com&type=ws&header=none&host=www.thoughtstar.cc&path=/msdownload&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=true#6,德国,剩999G,昨0G.(0901) 
trojan://tDW776HerJ07nbiT8Q6LPBu@kx-speedtest.tools.gcore.com:443?flow=&security=tls&sni=kx-speedtest.tools.gcore.com&type=ws&header=none&host=www.thoughtstar.cc&path=/msdownload&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=true#6,德国,剩999G,昨0G.(0901) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQDIwMC4xMC4xNzcuNTQ6NDQzOndzOi9jbG91ZDpzb21lLnRoaW5ncy50by5kbzpub25lOnRsczpsZ3Mtc3BlZWR0ZXN0LnRvb2xzLmdjb3JlLmNvbTpbJ2h0dHAvMS4xJ106#11,德国,剩994G,昨18G.(0901) 
vless://ecd4054a-b635-402b-bd15-5d83bb606b89@meet.gcorelabs.com:443?flow=&encryption=none&security=tls&sni=meet.gcorelabs.com&type=ws&host=sail.ocean.google&path=/download&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=true#1,美国,剩991G,昨62G.(0901) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQDUuMTAxLjIxOS42OjQ0Mzp3czovY2xvdWQ6bXlhLm5vdGUzYy5kZXY6bm9uZTp0bHM6Y2RuLmdjb3JlLmNvbTpbJ2h0dHAvMS4xJ106#12,德国,剩999G,昨0G.(0901) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQDUuMTg4LjEzMi4xNDo0NDM6d3M6L2Nsb3VkOmNkbjM2NS5wZW5wZWVyLmlvOm5vbmU6dGxzOnRlZy1zcGVlZHRlc3QudG9vbHMuZ2NvcmUuY29tOlsnaHR0cC8xLjEnXTo=#17,波兰s6,剩999G,昨0G.(0901) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQDEzMC4xOTMuMTY2LjI6NDQzOndzOi9jbG91ZDp3d3cuZXdvb2RzLmdvb2dsZS5pdDpub25lOnRsczpzcDMtc3BlZWR0ZXN0LnRvb2xzLmdjb3JlLmNvbTpbJ2h0dHAvMS4xJ106#9,德国,剩990G,昨34G.(0901) 
trojan://tDW776HerJ07nbiT8Q6LPBu@197.225.145.26:443?flow=&security=tls&sni=la2-speedtest.tools.gcore.com&type=ws&header=none&host=cdn.starre.me.it&path=/msdownload&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=true#8,德国,剩999G,昨0G.(0901) 
trojan://tDW776HerJ07nbiT8Q6LPBu@la2-speedtest.tools.gcore.com:443?flow=&security=tls&sni=la2-speedtest.tools.gcore.com&type=ws&header=none&host=cdn.starre.me.it&path=/msdownload&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=true#8,德国,剩999G,昨0G.(0901) 
vless://ecd4054a-b635-402b-bd15-5d83bb606b89@92.38.159.14:443?flow=&encryption=none&security=tls&sni=meet.gcorelabs.com&type=ws&host=sail.ocean.google&path=/download&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=true#1,美国,剩991G,昨62G.(0901) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQDQ1LjgwLjIxMy42Mjo0NDM6d3M6L2Nsb3VkOmNyZS5kcmVhbS50b3A6bm9uZTp0bHM6dGhuMi1zcGVlZHRlc3QudG9vbHMuZ2NvcmUuY29tOlsnaHR0cC8xLjEnXTo=#10,德国,剩992G,昨38G.(0901) 
vless://ecd4054a-b635-402b-bd15-5d83bb606b89@meet.gcorelabs.com:443?flow=&encryption=none&security=tls&sni=meet.gcorelabs.com&type=ws&host=www.celebrate.cyou&path=/download&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=true#2,美国,剩997G,昨40G.(0901) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQGxncy1zcGVlZHRlc3QudG9vbHMuZ2NvcmUuY29tOjQ0Mzp3czovY2xvdWQ6c29tZS50aGluZ3MudG8uZG86bm9uZTp0bHM6bGdzLXNwZWVkdGVzdC50b29scy5nY29yZS5jb206WydodHRwLzEuMSddOg==#11,德国,剩994G,昨18G.(0901) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQDUuMTAxLjIyMi4xMzo0NDM6d3M6L2Nsb3VkOnd3dy53aGV0aGVyLnNwYWNlLm1uLmNjOm5vbmU6dGxzOmxhMi1zcGVlZHRlc3QudG9vbHMuZ2NvcmUuY29tOlsnaHR0cC8xLjEnXTo=#20,波兰s7,剩999G,昨0G.(0901) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQDEwMi42Ny45OS41MDo0NDM6d3M6L2Nsb3VkOnNlcnYueXVnb2N4LmRldjpub25lOnRsczprYWwtc3BlZWR0ZXN0LnRvb2xzLmdjb3JlLmNvbTpbJ2h0dHAvMS4xJ106#15,德国,剩983G,昨66G.(0901) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQGFjY291bnRzLmdjb3JlbGFicy5jb206NDQzOndzOi9jbG91ZDpjZG4uY2xvdWRvbmUuc3BhY2Uua3I6bm9uZTp0bHM6YWNjb3VudHMuZ2NvcmVsYWJzLmNvbTpbJ2h0dHAvMS4xJ106#16,德国,剩999G,昨0G.(0901) 
vmess://eyJ2IjoiMiIsImFkZCI6ImhrMi1zcGVlZHRlc3QudG9vbHMuZ2NvcmUuY29tIiwicG9ydCI6NDQzLCJzY3kiOiJhdXRvIiwicHMiOiI1LOe+juWbvSzliak5OTBHLOaYqDQ3Ry4oMDkwMSkiLCJuZXQiOiJ3cyIsImlkIjoiNDlmZWI2OWEtNTE3MS00NWYwLTk1YjAtYjA0NTQ2ZTZjM2RkIiwiYWxwbiI6Imh0dHAvMS4xIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Imd1ZXNzLndoYXQubG5rLnVzIiwicGF0aCI6Ii9yZXNvdXJjZXMiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJoazItc3BlZWR0ZXN0LnRvb2xzLmdjb3JlLmNvbSJ9 
vless://ecd4054a-b635-402b-bd15-5d83bb606b89@37.239.145.13:443?flow=&encryption=none&security=tls&sni=meet.gcorelabs.com&type=ws&host=www.celebrate.cyou&path=/download&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=true#2,美国,剩997G,昨40G.(0901) 


hysteria2://NjODAtMDNzViZTc1dlODY5WU5@91.185.187.49:3307?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=LhkMWI0Mzgz5t2OTNjES0&os=#21,波兰,s0.serv00.com. 
hysteria2://qRVQxTVdJTnRNVDFScVJWUXhUVm@85.194.242.89:8002?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=STlZERlNjVkpXVVho&os=#22,波兰,s6.serv00.com. 
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
