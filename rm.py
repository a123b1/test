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

vless://ecd4054a-b635-402b-bd15-5d83bb606b89@kal-speedtest.tools.gcore.com:443?flow=&encryption=none&security=tls&sni=kal-speedtest.tools.gcore.com&type=ws&host=sail.ocean.google&path=/download&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=true#21,美国,165G,63G.(1122) 
vless://ecd4054a-b635-402b-bd15-5d83bb606b89@213.156.156.62:443?flow=&encryption=none&security=tls&sni=ns1.gcdn.services&type=ws&host=www.celebrate.cyou&path=/download&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=true#1,美国,275G,59G.(1122) 
vless://ecd4054a-b635-402b-bd15-5d83bb606b89@92.38.159.7:443?flow=&encryption=none&security=tls&sni=kal-speedtest.tools.gcore.com&type=ws&host=sail.ocean.google&path=/download&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=true#21,美国,165G,63G.(1122) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQDIwMi43OC4xNjIuNDo0NDM6d3M6L2Nsb3VkOm1vdW50YWluLmQxLnNoYXJldG95b3UudXMua2c6bm9uZTp0bHM6d3ctc3BlZWR0ZXN0LnRvb2xzLmdjb3JlLmNvbTpbJ2h0dHAvMS4xJ106#4,德国d1,656G,26G.(1122) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQGRucy5nY29yZS5jb206NDQzOndzOi9jbG91ZDptZXJyeS5kMS5zaGFyZXRveW91LnVzLmtnOm5vbmU6dGxzOmRucy5nY29yZS5jb206WydodHRwLzEuMSddOg==#3,德国d1,696G,28G.(1122) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQDE4NS4yNDQuMjA5LjYyOjQ0Mzp3czovY2xvdWQ6bWFpbnRhaW4uZDQuc2hhcmV0b3lvdS51cy5rZzpub25lOnRsczpuczIuZ2NvcmVsYWJzLm5ldDpbJ2h0dHAvMS4xJ106#14,德国d4,753G,0G.(1122) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQG55Mi1zcGVlZHRlc3QudG9vbHMuZ2NvcmUuY29tOjQ0Mzp3czovY2xvdWQ6YWJ0YWluLmQxLnNoYXJldG95b3UudXMua2c6bm9uZTp0bHM6bnkyLXNwZWVkdGVzdC50b29scy5nY29yZS5jb206WydodHRwLzEuMSddOg==#5,德国d1,717G,19G.(1122) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQDg5LjIyMy45MC40OjQ0Mzp3czovY2xvdWQ6cGFpbi5kMi5zaGFyZXRveW91LnVzLmtnOm5vbmU6dGxzOm5zMS5nY29yZWxhYnMubmV0OlsnaHR0cC8xLjEnXTo=#6,德国d2,612G,21G.(1122) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQDE5My4xNjkuMjUwLjk6NDQzOndzOi9jbG91ZDp3d3cubm9ueS5tZS51czpub25lOnRsczpsYTItc3BlZWR0ZXN0LnRvb2xzLmdjb3JlLmNvbTpbJ2h0dHAvMS4xJ106#18,波兰s13,999G,0G.(1122) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQDQ2LjQ5LjEwLjIzMTo0NDM6d3M6L2Nsb3VkOmZpZWxkLmZhaWwuZmlsZS5pczpub25lOnRsczpjZG4uZ2NvcmVsYWJzLmNvbTpbJ2h0dHAvMS4xJ106#22,波兰s12,758G,19G.(1122) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQDQ1LjY1LjguNDo0NDM6d3M6L2Nsb3VkOmZvdW50YWluLmQ0LnNoYXJldG95b3UudXMua2c6bm9uZTp0bHM6bWluNC1zcGVlZHRlc3QudG9vbHMuZ2NvcmUuY29tOlsnaHR0cC8xLjEnXTo=#13,德国d4,701G,0G.(1122) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQDUuMTAxLjIyMi4xNDo0NDM6d3M6L2Nsb3VkOnByb21pc2UudS5tZS5jYzpub25lOnRsczpnbnMyLmdjZG4uY286WydodHRwLzEuMSddOg==#20,波兰s12,597G,14G.(1122) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQDk1Ljg1LjkyLjQ6NDQzOndzOi9jbG91ZDp3d3cud2hldGhlci5zcGFjZS5tbi5jYzpub25lOnRsczpreC1zcGVlZHRlc3QudG9vbHMuZ2NvcmUuY29tOlsnaHR0cC8xLjEnXTo=#17,波兰s13,999G,0G.(1122) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQDk0LjQzLjIwNi4yMDI6NDQzOndzOi9jbG91ZDpnYWluLmQyLnNoYXJldG95b3UudXMua2c6bm9uZTp0bHM6d3ctc3BlZWR0ZXN0LnRvb2xzLmdjb3JlLmNvbTpbJ2h0dHAvMS4xJ106#7,德国d2,557G,28G.(1122) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQGt4LXNwZWVkdGVzdC50b29scy5nY29yZS5jb206NDQzOndzOi9jbG91ZDp3d3cud2hldGhlci5zcGFjZS5tbi5jYzpub25lOnRsczpreC1zcGVlZHRlc3QudG9vbHMuZ2NvcmUuY29tOlsnaHR0cC8xLjEnXTo=#17,波兰s13,999G,0G.(1122) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQDgwLjkzLjIyMy42MTo0NDM6d3M6L2Nsb3VkOnd3dy5zZWN1cmUuc3BhY2UwMDcubW46bm9uZTp0bHM6bnkyLXNwZWVkdGVzdC50b29scy5nY29yZS5jb206WydodHRwLzEuMSddOg==#19,波兰s12,464G,10G.(1122) 
vless://ecd4054a-b635-402b-bd15-5d83bb606b89@ns1.gcdn.services:443?flow=&encryption=none&security=tls&sni=ns1.gcdn.services&type=ws&host=www.celebrate.cyou&path=/download&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=true#1,美国,275G,59G.(1122) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQHd3LXNwZWVkdGVzdC50b29scy5nY29yZS5jb206NDQzOndzOi9jbG91ZDpnYWluLmQyLnNoYXJldG95b3UudXMua2c6bm9uZTp0bHM6d3ctc3BlZWR0ZXN0LnRvb2xzLmdjb3JlLmNvbTpbJ2h0dHAvMS4xJ106#7,德国d2,557G,28G.(1122) 
ss://Y2hhY2hhMjAtcG9seTEzMDU6WkdoVkhxbVUxVHBYWlgyOVlDVTBOblJIQGdjZG4uY286NDQzOndzOi9jbG91ZDpzdGFpbi5kMy5zaGFyZXRveW91LnVzLmtnOm5vbmU6dGxzOmdjZG4uY286WydodHRwLzEuMSddOg==#11,德国d3,625G,17G.(1122) 

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
