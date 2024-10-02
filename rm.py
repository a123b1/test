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



vless://ecd4054a-b635-402b-bd15-5d83bb606b89@102.67.99.50:443?flow=&encryption=none&security=tls&sni=gns1.gcdn.co&type=ws&host=sail.ocean.google&path=/download&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=true#1,美国,剩982G,昨18G.(1002) 
vless://ecd4054a-b635-402b-bd15-5d83bb606b89@kx-speedtest.tools.gcore.com:443?flow=&encryption=none&security=tls&sni=kx-speedtest.tools.gcore.com&type=ws&host=www.celebrate.cyou&path=/download&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=true#2,美国,剩987G,昨14G.(1002) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQHd3LXNwZWVkdGVzdC50b29scy5nY29yZS5jb206NDQzOndzOi9jbG91ZDpwcm9taXNlLnUubWUuY2M6bm9uZTp0bHM6d3ctc3BlZWR0ZXN0LnRvb2xzLmdjb3JlLmNvbTpbJ2h0dHAvMS4xJ106#22,波兰s12,剩990G,昨10G.(1002) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQGxhMi1zcGVlZHRlc3QudG9vbHMuZ2NvcmUuY29tOjQ0Mzp3czovY2xvdWQ6d3d3LndoZXRoZXIuc3BhY2UubW4uY2M6bm9uZTp0bHM6bGEyLXNwZWVkdGVzdC50b29scy5nY29yZS5jb206WydodHRwLzEuMSddOg==#19,波兰s7,剩973G,昨27G.(1002) 
vmess://eyJ2IjoiMiIsImFkZCI6IjIxMy4xNTYuMTQ0LjYxIiwicG9ydCI6NDQzLCJzY3kiOiJhdXRvIiwicHMiOiI0LOe+juWbvSzliak5NzdHLOaYqDI2Ry4oMTAwMikiLCJuZXQiOiJ3cyIsImlkIjoiNDlmZWI2OWEtNTE3MS00NWYwLTk1YjAtYjA0NTQ2ZTZjM2RkIiwiYWxwbiI6Imh0dHAvMS4xIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImhlLnNpLnQuYXRlLm1peC5jYyIsInBhdGgiOiIvcmVzb3VyY2VzIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoibGdzLXNwZWVkdGVzdC50b29scy5nY29yZS5jb20ifQ== 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQGthbC1zcGVlZHRlc3QudG9vbHMuZ2NvcmUuY29tOjQ0Mzp3czovY2xvdWQ6cmFpbi5kMy5zaGFyZXRveW91LnVzLmtnOm5vbmU6dGxzOmthbC1zcGVlZHRlc3QudG9vbHMuZ2NvcmUuY29tOlsnaHR0cC8xLjEnXTo=#11,德国d3,剩988G,昨12G.(1002) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQHRobjItc3BlZWR0ZXN0LnRvb2xzLmdjb3JlLmNvbTo0NDM6d3M6L2Nsb3VkOmFidGFpbi5kMS5zaGFyZXRveW91LnVzLmtnOm5vbmU6dGxzOnRobjItc3BlZWR0ZXN0LnRvb2xzLmdjb3JlLmNvbTpbJ2h0dHAvMS4xJ106#7,德国d1,剩986G,昨14G.(1002) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQDQ1LjgyLjEwMy44OjQ0Mzp3czovY2xvdWQ6Zm91bnRhaW4uZDQuc2hhcmV0b3lvdS51cy5rZzpub25lOnRsczpoazItc3BlZWR0ZXN0LnRvb2xzLmdjb3JlLmNvbTpbJ2h0dHAvMS4xJ106#15,德国d4,剩983G,昨17G.(1002) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQDUuMTAxLjIyMi4xMzo0NDM6d3M6L2Nsb3VkOnN0YWluLmQzLnNoYXJldG95b3UudXMua2c6bm9uZTp0bHM6bGdzLXNwZWVkdGVzdC50b29scy5nY29yZS5jb206WydodHRwLzEuMSddOg==#13,德国d3,剩991G,昨8G.(1002) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQGNjMS1zcGVlZHRlc3QudG9vbHMuZ2NvcmUuY29tOjQ0Mzp3czovY2xvdWQ6cGFpbi5kMi5zaGFyZXRveW91LnVzLmtnOm5vbmU6dGxzOmNjMS1zcGVlZHRlc3QudG9vbHMuZ2NvcmUuY29tOlsnaHR0cC8xLjEnXTo=#8,德国d2,剩990G,昨10G.(1002) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQGxncy1zcGVlZHRlc3QudG9vbHMuZ2NvcmUuY29tOjQ0Mzp3czovY2xvdWQ6c3RhaW4uZDMuc2hhcmV0b3lvdS51cy5rZzpub25lOnRsczpsZ3Mtc3BlZWR0ZXN0LnRvb2xzLmdjb3JlLmNvbTpbJ2h0dHAvMS4xJ106#13,德国d3,剩991G,昨8G.(1002) 
vless://ecd4054a-b635-402b-bd15-5d83bb606b89@95.85.92.5:443?flow=&encryption=none&security=tls&sni=kx-speedtest.tools.gcore.com&type=ws&host=www.celebrate.cyou&path=/download&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=true#2,美国,剩987G,昨14G.(1002) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQDExOC4xMDMuMTM2LjI0NTo0NDM6d3M6L2Nsb3VkOmdyYWluLmQyLnNoYXJldG95b3UudXMua2c6bm9uZTp0bHM6bnMyLmdjb3JlbGFicy5uZXQ6WydodHRwLzEuMSddOg==#10,德国d2,剩990G,昨10G.(1002) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQGRvY3MuZ2NvcmVsYWJzLmNvbTo0NDM6d3M6L2Nsb3VkOnd3dy5zZWN1cmUuc3BhY2UwMDcubW46bm9uZTp0bHM6ZG9jcy5nY29yZWxhYnMuY29tOlsnaHR0cC8xLjEnXTo=#21,波兰s12,剩990G,昨9G.(1002) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQGxhMi1zcGVlZHRlc3QudG9vbHMuZ2NvcmUuY29tOjQ0Mzp3czovY2xvdWQ6c3RhdGljLmNvcm5ib3JuLmlvOm5vbmU6dGxzOmxhMi1zcGVlZHRlc3QudG9vbHMuZ2NvcmUuY29tOlsnaHR0cC8xLjEnXTo=#17,波兰s6,剩971G,昨31G.(1002) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQHNwMy1zcGVlZHRlc3QudG9vbHMuZ2NvcmUuY29tOjQ0Mzp3czovY2xvdWQ6bW91bnRhaW4uZDEuc2hhcmV0b3lvdS51cy5rZzpub25lOnRsczpzcDMtc3BlZWR0ZXN0LnRvb2xzLmdjb3JlLmNvbTpbJ2h0dHAvMS4xJ106#6,德国d1,剩992G,昨8G.(1002) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQDQ1LjgwLjIxMy40OjQ0Mzp3czovY2xvdWQ6bWFpbnRhaW4uZDQuc2hhcmV0b3lvdS51cy5rZzpub25lOnRsczpsYTItc3BlZWR0ZXN0LnRvb2xzLmdjb3JlLmNvbTpbJ2h0dHAvMS4xJ106#16,德国d4,剩978G,昨22G.(1002) 
vless://ecd4054a-b635-402b-bd15-5d83bb606b89@gns1.gcdn.co:443?flow=&encryption=none&security=tls&sni=gns1.gcdn.co&type=ws&host=sail.ocean.google&path=/download&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=true#1,美国,剩982G,昨18G.(1002) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQDE4NS40OC4xMzYuMTUwOjQ0Mzp3czovY2xvdWQ6Z2Fpbi5kMi5zaGFyZXRveW91LnVzLmtnOm5vbmU6dGxzOmt4LXNwZWVkdGVzdC50b29scy5nY29yZS5jb206WydodHRwLzEuMSddOg==#9,德国d2,剩989G,昨11G.(1002) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQHRobjItc3BlZWR0ZXN0LnRvb2xzLmdjb3JlLmNvbTo0NDM6d3M6L2Nsb3VkOmNvbnRhaW4uZDQuc2hhcmV0b3lvdS51cy5rZzpub25lOnRsczp0aG4yLXNwZWVkdGVzdC50b29scy5nY29yZS5jb206WydodHRwLzEuMSddOg==#14,德国d4,剩992G,昨7G.(1002) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQGxncy1zcGVlZHRlc3QudG9vbHMuZ2NvcmUuY29tOjQ0Mzp3czovY2xvdWQ6bWVycnkuZDEuc2hhcmV0b3lvdS51cy5rZzpub25lOnRsczpsZ3Mtc3BlZWR0ZXN0LnRvb2xzLmdjb3JlLmNvbTpbJ2h0dHAvMS4xJ106#5,德国d1,剩990G,昨11G.(1002) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQDE5Ny4yMTUuMTQwLjIzNDo0NDM6d3M6L2Nsb3VkOmNvbnRhaW4uZDQuc2hhcmV0b3lvdS51cy5rZzpub25lOnRsczp0aG4yLXNwZWVkdGVzdC50b29scy5nY29yZS5jb206WydodHRwLzEuMSddOg==#14,德国d4,剩992G,昨7G.(1002) 

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
