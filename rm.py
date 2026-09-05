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

trojan://humanity@104.16.174.101:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.16.174.109:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.16.174.117:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.16.174.12:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.16.174.121:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.16.174.124:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.16.174.14:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.16.174.143:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.16.174.148:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.16.174.185:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.16.174.22:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=//assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.16.174.34:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.16.174.36:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.16.174.37:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.16.174.44:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.16.174.46:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.16.174.6:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.16.174.71:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.16.174.72:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.16.7.70:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.16.73.213:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.17.111.1:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.17.111.3:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.17.111.4:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.17.111.8:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.17.177.143:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.103:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.108:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.133:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.140:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.143:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.144:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.149:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.152:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.155:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.159:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.161:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.175:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.179:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.187:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.204:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.207:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.208:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.210:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.219:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.225:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.229:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.230:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.233:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.244:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.246:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.50:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.73:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.152.77:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0904法国 
trojan://humanity@104.18.152.97:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.22.63:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.18.23.63:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=http/1.1&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.19.229.21:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.20.6.134:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@104.21.46.3:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=http/1.1%2Ch3%2Ch2&fp=chrome&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0904法国 
trojan://humanity@104.26.14.137:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0904法国 
trojan://humanity@104.26.15.137:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@130.250.137.171:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@141.101.90.101:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@165.215.250.14:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@172.67.149.60:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@172.67.221.242:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@172.67.74.2:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@176.97.66.175:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@188.114.97.7:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@198.41.223.96:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@216.24.57.1:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@216.24.57.7:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=/assignment&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@45.130.125.158:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@8.6.112.0:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@86.38.214.205:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@ip.myip2.qzz.io:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@join-telegram-channel-tirexnet.trex.kdns.fr:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=http/1.1%2Ch3%2Ch2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@join-telegram-channel.tirexnet.kdns.fr:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=www.ignitelimit.com&path=/assignment&alpn=http/1.1%2Ch3%2Ch2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@render.com:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@www.ignitelimit.com:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
trojan://humanity@www.speedtest.org:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&os=#0904法国 
anytls://mDqQW6l54gk0sxixbdDrOh40@45.82.121.192:41317?insecure=1&sni=swdist.apple.com&alpn=h2&fp=&os=#0904德国 
anytls://wnDS4KblxZzTNYaoBgXYLlZcLBxPstdnpHaWUqQ@45.82.121.192:32753?insecure=1&sni=swdist.apple.com&alpn=h2&fp=&os=#0904德国 
hysteria2://RX2axG9jZ7i91CpWotJzQy9TrRuvqZ0yqw@45.82.121.192:37523?insecure=1&sni=swdist.apple.com&alpn=&fp=&obfs=salamander&obfs-password=wFIMRgAX9pPfJVM2edFdU1O&mport=&os=#0904德国 
anytls://xejfOfLFUajZ4yjnolamQ4dX6WZbL6h@45.82.121.192:55299?insecure=1&sni=swdist.apple.com&alpn=h2&fp=&os=#0904德国 
hysteria2://hsy5TNXvoffqB9GQAqg@45.82.121.192:5913?insecure=1&sni=swdist.apple.com&alpn=&fp=&obfs=salamander&obfs-password=rwLz6IXB8Cbfb0iNPOCeiZ27hqdercs&mport=&os=#0904德国 
hysteria2://fqqwADyrxdmvFjQjwlbHBH0MpdE15a8LeU@45.82.121.192:58606?insecure=1&sni=swdist.apple.com&alpn=&fp=&obfs=salamander&obfs-password=7qGkpDBhrZmm4604spqd9xu9qbiGBi&mport=&os=#0904德国 
anytls://f8tt392ZjWx6wBDvUJMbgjDpZv@45.82.121.192:21211?insecure=1&sni=swdist.apple.com&alpn=h2&fp=&os=#0904德国 
hysteria2://Dj2IzqEeUoRO3eiCSEF4K7PrWiCnB0BBNr9fd8vV@45.82.121.192:35159?insecure=1&sni=swdist.apple.com&alpn=&fp=&obfs=salamander&obfs-password=veSLL09gcUy66LN3&mport=&os=#0904德国 
trojan://f4a6bcdc-3088-437d-9952-1081e84e5f35@45.82.121.192:16168?flow=&security=tls&sni=swdist.apple.com&type=ws&header=none&host=swdist.apple.com&path=/G4Obh0CbCBG3gwmVoX2zzD%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=&os=#0904德国 
hysteria2://wg6x4zDC33FZ9TWIbngRy2lf9HQum0IG@45.82.121.192:37653?insecure=1&sni=swdist.apple.com&alpn=&fp=&obfs=salamander&obfs-password=l1nWhfgW2FoMkFjQDKP29qLes&mport=&os=#0904德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.19.133.213:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@pulloutbv.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=pulloutbv.oceanof.xyz&type=xhttp&host=pulloutbv.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.27.87.206:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.27.6.183:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@hurryinglzpterazosin.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=hurryinglzpterazosin.oceanof.xyz&type=xhttp&host=hurryinglzpterazosin.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@141.101.113.130:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.16.139.79:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@198.41.201.41:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@rwandabbfollies.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=rwandabbfollies.oceanof.xyz&type=xhttp&host=rwandabbfollies.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@rictuscroquefort.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=rictuscroquefort.oceanof.xyz&type=xhttp&host=rictuscroquefort.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@laffiteos.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=laffiteos.oceanof.xyz&type=xhttp&host=laffiteos.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@exertzt.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=exertzt.oceanof.xyz&type=xhttp&host=exertzt.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@phocidaewfzrichweed.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=phocidaewfzrichweed.oceanof.xyz&type=xhttp&host=phocidaewfzrichweed.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@162.159.130.238:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@kameezpdu.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=kameezpdu.oceanof.xyz&type=xhttp&host=kameezpdu.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.17.107.191:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@190.93.244.167:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@knockoutkuqpostexilic.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=knockoutkuqpostexilic.oceanof.xyz&type=xhttp&host=knockoutkuqpostexilic.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@162.159.252.125:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.19.135.80:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@188.114.98.101:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@duckingpd.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=duckingpd.oceanof.xyz&type=xhttp&host=duckingpd.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@applerustxm.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=applerustxm.oceanof.xyz&type=xhttp&host=applerustxm.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@woodcutw.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=woodcutw.oceanof.xyz&type=xhttp&host=woodcutw.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@fricativeypbutcher.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=fricativeypbutcher.oceanof.xyz&type=xhttp&host=fricativeypbutcher.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@fryingpanamleap.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=fryingpanamleap.oceanof.xyz&type=xhttp&host=fryingpanamleap.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@fundedgpnuthatch.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=fundedgpnuthatch.oceanof.xyz&type=xhttp&host=fundedgpnuthatch.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@162.159.192.187:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.27.104.179:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@103.21.244.164:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.27.27.86:443?flow=&encryption=none&security=tls&sni=du.ryalol.qzz.io&type=xhttp&host=du.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@neritidrl.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=neritidrl.oceanof.xyz&type=xhttp&host=neritidrl.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0904美国 



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
