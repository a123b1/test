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

vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@103.127.248.51:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@103.21.244.112:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@103.21.244.144:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@103.21.244.174:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@103.21.244.86:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@103.21.244.89:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.16.155.114:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.16.244.36:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.20.192.155:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.20.251.171:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.20.51.130:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
trojan://15b24b56-d667-4fa8-b548-f3dc942fb461@104.21.15.232:443?flow=&security=tls&sni=ab2c7f0b-bf1b-4eb3-9884-256f4de3d.2030.pp.ua&type=ws&header=none&host=&path=/4p35eUnmGxQ8YJFJxz&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
trojan://f0f6e76e-e5fe-4e2c-9faf-34832e021eae@104.21.25.95:443?flow=&security=tls&sni=DDd.890604.FIlEGear-sG.Me&type=ws&header=none&host=&path=/mZr1mA5hub7QHHkQBzYO&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
trojan://c8eac4b7-95ba-4ce0-920d-c3279eb3b391@104.21.35.247:443?flow=&security=tls&sni=ff.HuangSHANg2030.DPDnS.oRg&type=ws&header=none&host=ff.huangshang2030.dpdns.org&path=/ptGwaGzcA4KNAXX&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
trojan://c8eac4b7-95ba-4ce0-920d-c3279eb3b391@104.21.35.247:443?flow=&security=tls&sni=ff.HuangSHANg2030.DPDnS.oRg&type=ws&header=none&host=&path=/ptGwaGzcA4KNAXX&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
trojan://895552fa-6284-4c1d-ba00-3944e0c7c626@104.21.71.112:443?flow=&security=tls&sni=CFR56ty7890.288288.sHOP&type=ws&header=none&host=&path=/By7cEmOrNRS58yeduy9AOG&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
trojan://895552fa-6284-4c1d-ba00-3944e0c7c626@104.21.71.112:443?flow=&security=tls&sni=CFR56ty7890.288288.sHOP&type=ws&header=none&host=cfr56ty7890.288288.shop&path=/By7cEmOrNRS58yeduy9AOG&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
trojan://4a3ee276-f50f-46f6-ba4d-13571732ab70@104.21.83.113:443?flow=&security=tls&sni=SxcDe3.859886.XYz&type=ws&header=none&host=sxcde3.859886.xyz&path=/COp52Dbu3dvwvDWUxOqxq&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
trojan://4a3ee276-f50f-46f6-ba4d-13571732ab70@104.21.83.113:443?flow=&security=tls&sni=SxcDe3.859886.XYz&type=ws&header=none&host=&path=/COp52Dbu3dvwvDWUxOqxq&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.23.117.19:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.23.99.41:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.24.46.117:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.25.94.26:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.26.13.81:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.27.3.204:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@109.120.150.79:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
trojan://319c8935-a062-4d8a-9dec-86a085344fd9@109.71.253.175:58691?flow=&security=tls&sni=ssca.irundns.net&type=ws&header=none&host=ssca.irundns.net&path=/fdA6Jx9kq7ndZG5zBLHGFD%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
anytls://8m5G26mQaiM1qpdQM@109.71.253.175:46713?insecure=1&sni=ssca.irundns.net&alpn=h2&fp=&os=#0603德国 
trojan://fa5bdcb7-118e-4be1-b940-a3946c0dc5df@109.71.253.175:44853?flow=&security=tls&sni=ssca.irundns.net&type=ws&header=none&host=ssca.irundns.net&path=/D7TVHDIE1l%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
trojan://d68e148b-416e-47d5-8795-45a3c33d9504@109.71.253.175:47306?flow=&security=tls&sni=ssca.irundns.net&type=ws&header=none&host=ssca.irundns.net&path=/syEsdRtN%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
anytls://9kE5Jn92Pl3pzcukl7Hv@109.71.253.175:46650?insecure=1&sni=ssca.irundns.net&alpn=h2&fp=&os=#0603德国 
vless://4a7bb3c8-5fe6-4f57-ace9-748b1e236fe2@109.71.253.175:25537?flow=&encryption=none&security=tls&sni=ssca.irundns.net&type=ws&host=ssca.irundns.net&path=/58tgRFOLdyyy1qrl%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
anytls://MDUzqvdhX3PfxVS16yWZ0CPZrcNL@109.71.253.175:56006?insecure=1&sni=ssca.irundns.net&alpn=h2&fp=&os=#0603德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NjVhNjg5MDQtMTIxYy00MDYzLWI3ZDEtNDg5M2NmNDhmYjY2QDEwOS43MS4yNTMuMTc1OjUwNzQ4OndzOi93VWlCNUl6Y2ZQT0trS2lSb1IlM0ZlZCUzRDI1NjA6c3NjYS5pcnVuZG5zLm5ldDpub25lOnRsczpzc2NhLmlydW5kbnMubmV0OltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0603德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTc1IiwicG9ydCI6MzQzMCwic2N5IjoiYXV0byIsInBzIjoiMDYwM+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI2NWE2ODkwNC0xMjFjLTQwNjMtYjdkMS00ODkzY2Y0OGZiNjYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InNzY2EuaXJ1bmRucy5uZXQiLCJwYXRoIjoiLz9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoic3NjYS5pcnVuZG5zLm5ldCIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTc1IiwicG9ydCI6NDQ1NzUsInNjeSI6ImF1dG8iLCJwcyI6IjA2MDPlvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiZGY2ZWMwN2MtMTE0Yy00ZTljLWIyZTYtY2E5NTc2YzgwNTkwIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJzc2NhLmlydW5kbnMubmV0IiwicGF0aCI6Ii9tV2U/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6InNzY2EuaXJ1bmRucy5uZXQiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
anytls://StlPLgoK4ZVD6NYmoB4Qtgwe@109.71.253.175:4536?insecure=1&sni=ssca.irundns.net&alpn=h2&fp=&os=#0603德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTc1IiwicG9ydCI6MzIyNzQsInNjeSI6ImF1dG8iLCJwcyI6IjA2MDPlvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiNjZkNDg5YTEtMWNiNy00MTE1LWEzMWUtNTc0Mzk2YzRlMDU0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJzc2NhLmlydW5kbnMubmV0IiwicGF0aCI6Ii9zN0pEQnFmMkhhWDlwbTBrUzJRcm9IZFM0UmdWP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJzc2NhLmlydW5kbnMubmV0IiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://9faad253-384a-4ad0-8ce8-090bd10b1b7e@109.71.253.175:28725?flow=&security=tls&sni=ssca.irundns.net&type=ws&header=none&host=ssca.irundns.net&path=/fWZULiTelJhF%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
anytls://oukzhs3SL3R1TNhQr550fMFPCpF5XUyiNZ6Uj@109.71.253.175:18550?insecure=1&sni=ssca.irundns.net&alpn=h2&fp=&os=#0603德国 
hysteria2://LHjGjaSsRO2DBK1hOS58IV7@109.71.253.175:44081?insecure=1&sni=ssca.irundns.net&alpn=&fp=&obfs=salamander&obfs-password=lD8pDVVRIzDwtwlgyymFU2oY&mport=&os=#0603德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTc1IiwicG9ydCI6MzM1MTksInNjeSI6ImF1dG8iLCJwcyI6IjA2MDPlvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiNGE3YmIzYzgtNWZlNi00ZjU3LWFjZTktNzQ4YjFlMjM2ZmUyIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJzc2NhLmlydW5kbnMubmV0IiwicGF0aCI6Ii9pY0YyYlZZbFlpS3hIT2NhMUxiWTN2bzB2dz9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoic3NjYS5pcnVuZG5zLm5ldCIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZDY4ZTE0OGItNDE2ZS00N2Q1LTg3OTUtNDVhM2MzM2Q5NTA0QDEwOS43MS4yNTMuMTc1OjUwMzgxOndzOi9ma29LTzFPbUxWNWZ0dExpSTFYWjRhSWVLWEElM0ZlZCUzRDI1NjA6c3NjYS5pcnVuZG5zLm5ldDpub25lOnRsczpzc2NhLmlydW5kbnMubmV0OltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0603德国 
hysteria2://kU9qTpqwsS95gh7DcunEKzVmAm4wthuSEC@109.71.253.175:29175?insecure=1&sni=ssca.irundns.net&alpn=&fp=&obfs=salamander&obfs-password=z5Fw8DRJvHmJDVHfPBT8x&mport=&os=#0603德国 
hysteria2://E7F0OeymeIbrSydhhbpqW@109.71.253.175:35387?insecure=1&sni=ssca.irundns.net&alpn=&fp=&obfs=salamander&obfs-password=yeI8UaAQBSiDK1bk8TeUJuEk2ZVz6fzV&mport=&os=#0603德国 
anytls://vjcM55AS721MTHFoEORlsr4Cpb@109.71.253.175:38916?insecure=1&sni=ssca.irundns.net&alpn=h2&fp=&os=#0603德国 
vless://65a68904-121c-4063-b7d1-4893cf48fb66@109.71.253.175:43067?flow=&encryption=none&security=tls&sni=ssca.irundns.net&type=ws&host=ssca.irundns.net&path=/uHwTYghNGH6P5n2GQl%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
anytls://1L8ds5bIgBsRWL4UuSFgE@109.71.253.175:32248?insecure=1&sni=ssca.irundns.net&alpn=h2&fp=&os=#0603德国 
hysteria2://3Ns3ZQP5syaC0WL28qOb7i8iOg@109.71.253.175:26265?insecure=1&sni=ssca.irundns.net&alpn=&fp=&obfs=salamander&obfs-password=oAl4yGSlVQZwREJhIJnpTUUadNjFit&mport=&os=#0603德国 
hysteria2://WARHoqxf9E1XyFkz7i4ZjwwD3ua3@109.71.253.175:23617?insecure=1&sni=ssca.irundns.net&alpn=&fp=&obfs=salamander&obfs-password=OJkLyOZDzeNcDdS3472H02t&mport=&os=#0603德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NGE3YmIzYzgtNWZlNi00ZjU3LWFjZTktNzQ4YjFlMjM2ZmUyQDEwOS43MS4yNTMuMTc1OjU5MzI2OndzOi9ZYmVXbXdUbm5MOHJyZnJzVnNYdXZnUHpCMHU1dDglM0ZlZCUzRDI1NjA6c3NjYS5pcnVuZG5zLm5ldDpub25lOnRsczpzc2NhLmlydW5kbnMubmV0OltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0603德国 
anytls://xp7zYQtBz3tCoogc4GUCEyqYtIA@109.71.253.175:38289?insecure=1&sni=ssca.irundns.net&alpn=h2&fp=&os=#0603德国 
anytls://w1gD7xfR2nQBWzkKDrDa@109.71.253.175:9952?insecure=1&sni=ssca.irundns.net&alpn=h2&fp=&os=#0603德国 
anytls://eCW5EH6YtRDzMGKMa4UoMv6e1qO@109.71.253.175:40313?insecure=1&sni=ssca.irundns.net&alpn=h2&fp=&os=#0603德国 
trojan://66d489a1-1cb7-4115-a31e-574396c4e054@109.71.253.175:24364?flow=&security=tls&sni=ssca.irundns.net&type=ws&header=none&host=ssca.irundns.net&path=/SBtJP2Beba%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjExMS4yNi4xMDkuNzkiLCJwb3J0IjozMDgyOCwic2N5IjoiYXV0byIsInBzIjoiMDYwM+e+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjExMS4yNi4xMDkuNzkiLCJwb3J0IjozMDgyOCwic2N5IjoiYXV0byIsInBzIjoiMDYwM+e+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNDQuMTI2IiwicG9ydCI6NDc4ODMsInNjeSI6ImF1dG8iLCJwcyI6IjA2MDPmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNDQuMTI2IiwicG9ydCI6NDc4ODMsInNjeSI6ImF1dG8iLCJwcyI6IjA2MDPmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE2IiwicG9ydCI6MzU5MjEsInNjeSI6ImF1dG8iLCJwcyI6IjA2MDPnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE2IiwicG9ydCI6MzU5MjEsInNjeSI6ImF1dG8iLCJwcyI6IjA2MDPnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE5IiwicG9ydCI6NDkzNTUsInNjeSI6ImF1dG8iLCJwcyI6IjA2MDPnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjYzIiwicG9ydCI6Mzc4MDUsInNjeSI6ImF1dG8iLCJwcyI6IjA2MDPnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzQuMTAyLjIyOSIsInBvcnQiOjQ5MTc0LCJzY3kiOiJhdXRvIiwicHMiOiIwNjAz576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@125.141.26.12:4857?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0603韩国 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@150.241.64.164:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@150.241.96.32:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603印度 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@162.159.251.147:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
trojan://f0f6e76e-e5fe-4e2c-9faf-34832e021eae@172.67.133.248:443?flow=&security=tls&sni=DDd.890604.FIlEGear-sG.Me&type=ws&header=none&host=ddd.890604.filegear-sg.me&path=/mZr1mA5hub7QHHkQBzYO&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
trojan://f0f6e76e-e5fe-4e2c-9faf-34832e021eae@172.67.133.248:443?flow=&security=tls&sni=DDd.890604.FIlEGear-sG.Me&type=ws&header=none&host=&path=/mZr1mA5hub7QHHkQBzYO&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
trojan://44ed7a37-af89-4cd1-8680-83a7207810d9@172.67.135.37:443?flow=&security=tls&sni=cCtv4.459.pp.uA&type=ws&header=none&host=cctv4.459.pp.ua&path=/HpYP4foAlpTKtfYnjLYhU30U&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
trojan://44ed7a37-af89-4cd1-8680-83a7207810d9@172.67.135.37:443?flow=&security=tls&sni=cCtv4.459.pp.uA&type=ws&header=none&host=&path=/HpYP4foAlpTKtfYnjLYhU30U&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
trojan://895552fa-6284-4c1d-ba00-3944e0c7c626@172.67.144.126:443?flow=&security=tls&sni=CFR56ty7890.288288.sHOP&type=ws&header=none&host=cfr56ty7890.288288.shop&path=/By7cEmOrNRS58yeduy9AOG&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
trojan://895552fa-6284-4c1d-ba00-3944e0c7c626@172.67.144.126:443?flow=&security=tls&sni=CFR56ty7890.288288.sHOP&type=ws&header=none&host=&path=/By7cEmOrNRS58yeduy9AOG&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
vless://1549e70f-dc57-45e3-ac7c-515f0161db72@172.67.155.140:443?flow=&encryption=none&security=tls&sni=XXSe.hUaNGsHaNg.DpdNS.org&type=ws&host=xxse.huangshang.dpdns.org&path=/IKLitbwX0RSt1mktNrT&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
trojan://15153c1d-fc81-4b2a-9689-7b4e4a72dce5@172.67.188.77:443?flow=&security=tls&sni=edfr4.890604.dpdns.org&type=ws&header=none&host=edfr4.890604.dpdns.org&path=/l6lvY4hFZriQDBimbKYmPIggy&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
trojan://15153c1d-fc81-4b2a-9689-7b4e4a72dce5@172.67.188.77:443?flow=&security=tls&sni=edfr4.890604.dpdns.org&type=ws&header=none&host=&path=/l6lvY4hFZriQDBimbKYmPIggy&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.49.233:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.58.158:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.59.110:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.59.153:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.59.50:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@178.236.244.195:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603芬兰 
trojan://2c605663-b89a-5734-a9d6-97d4743d72cf@183.232.235.2:8313?flow=&security=tls&sni=hk-13-568.flztjc.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603香港 
trojan://2c605663-b89a-5734-a9d6-97d4743d72cf@183.232.235.2:8313?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603香港 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo1OTY1Miwic2N5IjoiYXV0byIsInBzIjoiMDYwM+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0OTMwMiwic2N5IjoiYXV0byIsInBzIjoiMDYwM+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0OTU1NCwic2N5IjoiYXV0byIsInBzIjoiMDYwM+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0OTU1NCwic2N5IjoiYXV0byIsInBzIjoiMDYwM+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0OTMwMiwic2N5IjoiYXV0byIsInBzIjoiMDYwM+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo1OTY1Miwic2N5IjoiYXV0byIsInBzIjoiMDYwM+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0IjozMzkxOSwic2N5IjoiYXV0byIsInBzIjoiMDYwM+mmmea4ryIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0MTAyNCwic2N5IjoiYXV0byIsInBzIjoiMDYwM+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0IjozMDA1Miwic2N5IjoiYXV0byIsInBzIjoiMDYwM+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0OTMwMiwic2N5IjoiYXV0byIsInBzIjoiMDYwM+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJvY2JjLmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo1OTY1Miwic2N5IjoiYXV0byIsInBzIjoiMDYwM+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJkZGQwOTc3Zi1zeGFmNDAtdDNiNHczLXl3bXMuY201LmNua3VhaXNob3UuY29tIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo1OTY1Miwic2N5IjoiYXV0byIsInBzIjoiMDYwM+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzcuODQuNTMiLCJwb3J0Ijo1NTAwMiwic2N5IjoiYXV0byIsInBzIjoiMDYwM+aXpeacrCIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzcuODQuNTMiLCJwb3J0Ijo1NTAwMiwic2N5IjoiYXV0byIsInBzIjoiMDYwM+aXpeacrCIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzguOTAuOCIsInBvcnQiOjQxNzY2LCJzY3kiOiJhdXRvIiwicHMiOiIwNjAz576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzguOTAuOCIsInBvcnQiOjM5MDc2LCJzY3kiOiJhdXRvIiwicHMiOiIwNjAz576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzguOTAuOCIsInBvcnQiOjQ2OTIwLCJzY3kiOiJhdXRvIiwicHMiOiIwNjAz576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjY0LCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzguOTAuOCIsInBvcnQiOjQ2OTIwLCJzY3kiOiJhdXRvIiwicHMiOiIwNjAz576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0603波兰 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@185.232.170.240:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@188.114.96.253:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603德国 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@212.113.103.4:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@221.150.109.89:11389?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0603韩国 
trojan://1a17b19d-4896-4531-af79-6e91d8ef8228@3.115.106.126:6668?flow=&security=tls&sni=baidu.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603日本 
ss://YWVzLTI1Ni1jZmI6eWlqaWFuMDUwMw==@3.34.131.22:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0603韩国 
trojan://1a17b19d-4896-4531-af79-6e91d8ef8228@3.38.218.140:6668?flow=&security=tls&sni=baidu.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603韩国 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@45.112.195.46:2053?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@45.14.247.108:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603芬兰 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@45.14.247.108:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603芬兰 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@5.39.249.146:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
vless://64bb8ea6-f39a-4f9a-bc0e-5a1313540aca@5.42.223.147:15319?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603爱尔兰 
trojan://1a17b19d-4896-4531-af79-6e91d8ef8228@52.198.188.173:6668?flow=&security=tls&sni=baidu.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603日本 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@62.60.159.113:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@74.48.58.171:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603加拿大 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@77.105.167.95:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@77.221.137.52:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@77.221.138.68:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@77.221.142.75:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@77.221.159.70:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603阿拉伯酋长国 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@77.232.143.245:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@77.232.143.85:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@77.91.87.204:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603香港 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@79.137.248.211:2053?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjgwZWM5YWJiLXN2c3BzMC10NmZsMGMtMXI3b2QuY201LnA1cHYuY29tIiwicG9ydCI6MTcyMzIsInNjeSI6ImF1dG8iLCJwcyI6IjA2MDPpn6nlm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjZkNTY0MzZjLTE1MGQtMTFmMC1iMGM4LWYyM2M5MTNjOGQyYiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgxZjZiZjM3LXN1dGo0MC1zdmdweHUteTJncy5jbTUucDVwdi5jb20iLCJwb3J0IjoxNzIzMywic2N5IjoiYXV0byIsInBzIjoiMDYwM+e+juWbvSIsIm5ldCI6InRjcCIsImlkIjoiYjgwNmIzODgtNWY5Ny0xMWVlLTgwMTQtZjIzYzkxM2M4ZDJiIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@89.22.232.231:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@89.22.235.166:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603阿拉伯酋长国 
ss://YWVzLTI1Ni1nY206NEtHSFdLQ0tRQUpPVlBITw==@8tv68qhq.slashdevslashnetslashtun.net:15003?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0603香港 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpvamNQMzZuMVNvdURjbkJnOUVPWlA4@9.163.232.180:1490?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0603荷兰 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@91.103.140.206:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0603斯洛文尼亚共和国 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@91.201.113.193:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@94.159.98.123:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603印度 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@95.182.99.23:8443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=telegram%40wangcai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
vmess://eyJ2IjoiMiIsImFkZCI6ImExOTRhYjNlLXN1cm9nMC1zeTBnOHgtMWNjOHMuY201LnA1cHYuY29tIiwicG9ydCI6MTcyMzUsInNjeSI6ImF1dG8iLCJwcyI6IjA2MDPms5Xlm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjdlNjQyMjRjLTRjMTAtMTFlYy1iZDdjLWYyM2M5MTNjOGQyYiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://ac5b2e52-435b-4461-a99c-1317ab0e2889@dddfcvg.freevpnatm.dpdns.org:443?flow=&encryption=none&security=tls&sni=dDDfcvG.fReEVPnatm.dPdNS.OrG&type=ws&host=dddfcvg.freevpnatm.dpdns.org&path=/KMeBwp0RuivA5B99DmZDo0oju2st1&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0603美国 
vmess://eyJ2IjoiMiIsImFkZCI6ImRmYjg4M2YxLXN1cm9nMC1zenhmc20tdjNjMi5jbTUucDVwdi5jb20iLCJwb3J0IjoxNzIzNCwic2N5IjoiYXV0byIsInBzIjoiMDYwM+WNsOW6puWwvOilv+S6miIsIm5ldCI6InRjcCIsImlkIjoiNWYwOTFjYmUtZmIzNC0xMWVhLTk3NzctZjIzYzkxNjRjYTVkIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@p080.panda001.net:36379?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0603韩国 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@p231.panda004.net:11389?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0603韩国 
ss://YWVzLTI1Ni1nY206NkVaNVFLRlg2MEFWU1VZVA==@ti3hyra4.slashdevslashnetslashtun.net:18008?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0603日本 
vmess://eyJ2IjoiMiIsImFkZCI6InRrLmh6bHQudGtkZG5zLnh5eiIsInBvcnQiOjIyNjQxLCJzY3kiOiJhdXRvIiwicHMiOiIwNjAz576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6Ijk4ZTk2YzlmLTRiYjMtMzlkNC05YTJjLWZhYzA0MjU3ZjdjNyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoienhqcC1hLnRrb25nLmNjIiwicGF0aCI6Ii8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InRrLmh6bHQudGtkZG5zLnh5eiIsInBvcnQiOjIyNjQyLCJzY3kiOiJhdXRvIiwicHMiOiIwNjAz576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6Ijk4ZTk2YzlmLTRiYjMtMzlkNC05YTJjLWZhYzA0MjU3ZjdjNyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoienhqcC1iLnRrb25nLmNjIiwicGF0aCI6Ii8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InRrLmh6bHQudGtkZG5zLnh5eiIsInBvcnQiOjIyNjQzLCJzY3kiOiJhdXRvIiwicHMiOiIwNjAz576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6Ijk4ZTk2YzlmLTRiYjMtMzlkNC05YTJjLWZhYzA0MjU3ZjdjNyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoienhqcC1jLnRrb25nLmNjIiwicGF0aCI6Ii8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoienhqcC1jLnRrb25nLmNjIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMi5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzMiwic2N5IjoiYXV0byIsInBzIjoiMDYwM+e+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMi5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzMiwic2N5IjoiYXV0byIsInBzIjoiMDYwM+e+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMy5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzMywic2N5IjoiYXV0byIsInBzIjoiMDYwM+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InY0MC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDg0MCwic2N5IjoiYXV0byIsInBzIjoiMDYwM+e+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaTEwMC1jb3JlLXF1aWMtbGYuYW1lbXYuY29tIiwicGF0aCI6Ii9pbmRleCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InY2LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA2LCJzY3kiOiJhdXRvIiwicHMiOiIwNjAz5pel5pysIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0Ijoib2NiYy5jb20iLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InY3LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA3LCJzY3kiOiJhdXRvIiwicHMiOiIwNjAz576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoidjcuaGVkdWlhbi5saW5rIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InY3LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA3LCJzY3kiOiJhdXRvIiwicHMiOiIwNjAz576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InY5LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA5LCJzY3kiOiJhdXRvIiwicHMiOiIwNjAz6aaZ5rivIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoiYmFpZHUuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
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
