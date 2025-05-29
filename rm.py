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


trojan://Aimer@108.165.152.67:2053?flow=&security=tls&sni=epmw.ambercc.filegear-sg.me&type=ws&header=none&host=epmw.ambercc.filegear-sg.me&path=/%3Fed%3D2560%26proxyip%3Dts.hpc.tw&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528美国 
hysteria2://kU9qTpqwsS95gh7DcunEKzVmAm4wthuSEC@109.71.253.175:29175?insecure=1&sni=ssca.irundns.net&alpn=&fp=&obfs=salamander&obfs-password=z5Fw8DRJvHmJDVHfPBT8x&mport=&os=#0528德国 
trojan://Aimer@141.11.203.191:8443?flow=&security=tls&sni=epmw.ambercc.filegear-sg.me&type=ws&header=none&host=epmw.ambercc.filegear-sg.me&path=/%3Fed%3D2560%26proxyip%3Dts.hpc.tw&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528英国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.24.213.255:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTc1IiwicG9ydCI6MzQzMCwic2N5IjoiYXV0byIsInBzIjoiMDUyOOW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI2NWE2ODkwNC0xMjFjLTQwNjMtYjdkMS00ODkzY2Y0OGZiNjYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InNzY2EuaXJ1bmRucy5uZXQiLCJwYXRoIjoiLz9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoic3NjYS5pcnVuZG5zLm5ldCIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://9faad253-384a-4ad0-8ce8-090bd10b1b7e@109.71.253.175:28725?flow=&security=tls&sni=ssca.irundns.net&type=ws&header=none&host=ssca.irundns.net&path=/fWZULiTelJhF%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528德国 
hysteria2://E7F0OeymeIbrSydhhbpqW@109.71.253.175:35387?insecure=1&sni=ssca.irundns.net&alpn=&fp=&obfs=salamander&obfs-password=yeI8UaAQBSiDK1bk8TeUJuEk2ZVz6fzV&mport=&os=#0528德国 
trojan://Aimer@108.165.152.58:2087?flow=&security=tls&sni=epmw.ambercc.filegear-sg.me&type=ws&header=none&host=epmw.ambercc.filegear-sg.me&path=/%3Fed%3D2560%26proxyip%3Dts.hpc.tw&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528美国 
vless://690ab90e-3f21-422b-8cb1-bc9845c7af1e@172.67.73.163:8080?flow=&encryption=none&security=&sni=IO.IhJtq0hklC.ZULAiR.OrG.&type=ws&host=IO.IhJtq0hklC.ZULAiR.OrG.&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528美国 
trojan://fa5bdcb7-118e-4be1-b940-a3946c0dc5df@109.71.253.175:44853?flow=&security=tls&sni=ssca.irundns.net&type=ws&header=none&host=ssca.irundns.net&path=/D7TVHDIE1l%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTc1IiwicG9ydCI6MzIyNzQsInNjeSI6ImF1dG8iLCJwcyI6IjA1Mjjlvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiNjZkNDg5YTEtMWNiNy00MTE1LWEzMWUtNTc0Mzk2YzRlMDU0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJzc2NhLmlydW5kbnMubmV0IiwicGF0aCI6Ii9zN0pEQnFmMkhhWDlwbTBrUzJRcm9IZFM0UmdWP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJzc2NhLmlydW5kbnMubmV0IiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NjVhNjg5MDQtMTIxYy00MDYzLWI3ZDEtNDg5M2NmNDhmYjY2QDEwOS43MS4yNTMuMTc1OjUwNzQ4OndzOi93VWlCNUl6Y2ZQT0trS2lSb1IlM0ZlZCUzRDI1NjA6c3NjYS5pcnVuZG5zLm5ldDpub25lOnRsczpzc2NhLmlydW5kbnMubmV0OltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0528德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.18.230.96:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.58.130:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTc1IiwicG9ydCI6MzM1MTksInNjeSI6ImF1dG8iLCJwcyI6IjA1Mjjlvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiNGE3YmIzYzgtNWZlNi00ZjU3LWFjZTktNzQ4YjFlMjM2ZmUyIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJzc2NhLmlydW5kbnMubmV0IiwicGF0aCI6Ii9pY0YyYlZZbFlpS3hIT2NhMUxiWTN2bzB2dz9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoic3NjYS5pcnVuZG5zLm5ldCIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@103.21.244.223:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528德国 
vmess://eyJ2IjoiMiIsImFkZCI6InY3LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA3LCJzY3kiOiJhdXRvIiwicHMiOiIwNTI4576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoidjcuaGVkdWlhbi5saW5rIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@198.41.209.156:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528德国 
hysteria2://WARHoqxf9E1XyFkz7i4ZjwwD3ua3@109.71.253.175:23617?insecure=1&sni=ssca.irundns.net&alpn=&fp=&obfs=salamander&obfs-password=OJkLyOZDzeNcDdS3472H02t&mport=&os=#0528德国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0528俄罗斯 
anytls://eCW5EH6YtRDzMGKMa4UoMv6e1qO@109.71.253.175:40313?insecure=1&sni=ssca.irundns.net&alpn=h2&fp=&os=#0528德国 
trojan://Aimer@188.164.159.18:443?flow=&security=tls&sni=epmw.ambercc.filegear-sg.me&type=ws&header=none&host=epmw.ambercc.filegear-sg.me&path=/%3Fed%3D2560%26proxyip%3Dts.hpc.tw&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528亚美尼亚 
hysteria2://2ed73747-3a59-4d3a-8c05-e9132e448e79@107.172.235.75:38834?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&mport=&os=#0528阿富汗 
anytls://oukzhs3SL3R1TNhQr550fMFPCpF5XUyiNZ6Uj@109.71.253.175:18550?insecure=1&sni=ssca.irundns.net&alpn=h2&fp=&os=#0528德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@103.21.244.215:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@103.21.244.170:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@162.159.8.51:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528德国 
trojan://66d489a1-1cb7-4115-a31e-574396c4e054@109.71.253.175:24364?flow=&security=tls&sni=ssca.irundns.net&type=ws&header=none&host=ssca.irundns.net&path=/SBtJP2Beba%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NGE3YmIzYzgtNWZlNi00ZjU3LWFjZTktNzQ4YjFlMjM2ZmUyQDEwOS43MS4yNTMuMTc1OjU5MzI2OndzOi9ZYmVXbXdUbm5MOHJyZnJzVnNYdXZnUHpCMHU1dDglM0ZlZCUzRDI1NjA6c3NjYS5pcnVuZG5zLm5ldDpub25lOnRsczpzc2NhLmlydW5kbnMubmV0OltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0528德国 
anytls://MDUzqvdhX3PfxVS16yWZ0CPZrcNL@109.71.253.175:56006?insecure=1&sni=ssca.irundns.net&alpn=h2&fp=&os=#0528德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.59.32:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528德国 
trojan://Aimer@108.165.152.18:2087?flow=&security=tls&sni=epme.ambercc.filegear-sg.me&type=ws&header=none&host=epme.ambercc.filegear-sg.me&path=/%3Fed%3D2560%26proxyip%3Dts.hpc.tw&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528美国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@141.101.121.246:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjExMS4yNi4xMDkuNzkiLCJwb3J0IjozMDgyOCwic2N5IjoiYXV0byIsInBzIjoiMDUyOOe+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQxIiwicG9ydCI6NDE1OTcsInNjeSI6ImF1dG8iLCJwcyI6IjA1Mjjnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
anytls://vjcM55AS721MTHFoEORlsr4Cpb@109.71.253.175:38916?insecure=1&sni=ssca.irundns.net&alpn=h2&fp=&os=#0528德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTc1IiwicG9ydCI6NjM5MDcsInNjeSI6ImF1dG8iLCJwcyI6IjA1Mjjlvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiMzE5Yzg5MzUtYTA2Mi00ZDhhLTlkZWMtODZhMDg1MzQ0ZmQ5IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJzc2NhLmlydW5kbnMubmV0IiwicGF0aCI6Ii9QVUtXRVZMSXl2cmw3M0F4RlpIVEZoQndqVFhzRDdiP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJzc2NhLmlydW5kbnMubmV0IiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://d68e148b-416e-47d5-8795-45a3c33d9504@109.71.253.175:47306?flow=&security=tls&sni=ssca.irundns.net&type=ws&header=none&host=ssca.irundns.net&path=/syEsdRtN%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528德国 
trojan://Aimer@103.116.7.248:443?flow=&security=tls&sni=epmw.ambercc.filegear-sg.me&type=ws&header=none&host=epmw.ambercc.filegear-sg.me&path=/%3Fed%3D2560%26proxyip%3Dts.hpc.tw&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528日本 
trojan://Aimer@59.29.143.247:12225?flow=&security=tls&sni=epme.ambercc.filegear-sg.me&type=ws&header=none&host=epme.ambercc.filegear-sg.me&path=/%3Fed%3D2560%26proxyip%3Dts.hpc.tw&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528韩国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.49.21:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528德国 
trojan://Aimer@192.210.207.89:20080?flow=&security=tls&sni=epme.ambercc.filegear-sg.me&type=ws&header=none&host=epme.ambercc.filegear-sg.me&path=/%3Fed%3D2560%26proxyip%3Dts.hpc.tw&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528美国 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMy5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzMywic2N5IjoiYXV0byIsInBzIjoiMDUyOCIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.22.35.167:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528德国 
trojan://Aimer@92.53.190.161:2087?flow=&security=tls&sni=epmw.ambercc.filegear-sg.me&type=ws&header=none&host=epmw.ambercc.filegear-sg.me&path=/%3Fed%3D2560%26proxyip%3Dts.hpc.tw&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528 
hysteria2://2ed73747-3a59-4d3a-8c05-e9132e448e79@185.126.255.78:21005?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&mport=&os=#0528阿富汗 
trojan://319c8935-a062-4d8a-9dec-86a085344fd9@109.71.253.175:58691?flow=&security=tls&sni=ssca.irundns.net&type=ws&header=none&host=ssca.irundns.net&path=/fdA6Jx9kq7ndZG5zBLHGFD%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjExMS4yNi4xMDkuNzkiLCJwb3J0IjozMDgyOCwic2N5IjoiYXV0byIsInBzIjoiMDUyOCIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://690ab90e-3f21-422b-8cb1-bc9845c7af1e@104.26.14.85:8080?flow=&encryption=none&security=&sni=IO.IhJtq0hklC.ZULAiR.OrG.&type=ws&host=IO.IhJtq0hklC.ZULAiR.OrG.&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528美国 
trojan://Aimer@23.95.215.205:8443?flow=&security=tls&sni=epme.ambercc.filegear-sg.me&type=ws&header=none&host=epme.ambercc.filegear-sg.me&path=/%3Fed%3D2560%26proxyip%3Dts.hpc.tw&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTc1IiwicG9ydCI6NDQ1NzUsInNjeSI6ImF1dG8iLCJwcyI6IjA1Mjjlvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiZGY2ZWMwN2MtMTE0Yy00ZTljLWIyZTYtY2E5NTc2YzgwNTkwIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJzc2NhLmlydW5kbnMubmV0IiwicGF0aCI6Ii9tV2U/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6InNzY2EuaXJ1bmRucy5uZXQiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
anytls://xp7zYQtBz3tCoogc4GUCEyqYtIA@109.71.253.175:38289?insecure=1&sni=ssca.irundns.net&alpn=h2&fp=&os=#0528德国 
trojan://Aimer@188.164.159.18:443?flow=&security=tls&sni=epme.ambercc.filegear-sg.me&type=ws&header=none&host=epme.ambercc.filegear-sg.me&path=/%3Fed%3D2560%26proxyip%3Dts.hpc.tw&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528亚美尼亚 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.19.254.193:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528德国 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMi5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzMiwic2N5IjoiYXV0byIsInBzIjoiMDUyOCIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZDY4ZTE0OGItNDE2ZS00N2Q1LTg3OTUtNDVhM2MzM2Q5NTA0QDEwOS43MS4yNTMuMTc1OjUwMzgxOndzOi9ma29LTzFPbUxWNWZ0dExpSTFYWjRhSWVLWEElM0ZlZCUzRDI1NjA6c3NjYS5pcnVuZG5zLm5ldDpub25lOnRsczpzc2NhLmlydW5kbnMubmV0OltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0528德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.25.154.175:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528德国 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMi5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzMiwic2N5IjoiYXV0byIsInBzIjoiMDUyOOe+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
hysteria2://LHjGjaSsRO2DBK1hOS58IV7@109.71.253.175:44081?insecure=1&sni=ssca.irundns.net&alpn=&fp=&obfs=salamander&obfs-password=lD8pDVVRIzDwtwlgyymFU2oY&mport=&os=#0528德国 
trojan://Aimer@192.3.127.231:443?flow=&security=tls&sni=epmw.ambercc.filegear-sg.me&type=ws&header=none&host=epmw.ambercc.filegear-sg.me&path=/%3Fed%3D2560%26proxyip%3Dts.hpc.tw&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528美国 
anytls://8m5G26mQaiM1qpdQM@109.71.253.175:46713?insecure=1&sni=ssca.irundns.net&alpn=h2&fp=&os=#0528德国 
anytls://9kE5Jn92Pl3pzcukl7Hv@109.71.253.175:46650?insecure=1&sni=ssca.irundns.net&alpn=h2&fp=&os=#0528德国 
ss://YWVzLTI1Ni1nY206ZG9uZ3RhaXdhbmcuY29t@195.154.54.171:13355?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0528法国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.25.209.113:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528德国 
trojan://Aimer@108.165.152.91:2083?flow=&security=tls&sni=epme.ambercc.filegear-sg.me&type=ws&header=none&host=epme.ambercc.filegear-sg.me&path=/%3Fed%3D2560%26proxyip%3Dts.hpc.tw&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528美国 
vless://65a68904-121c-4063-b7d1-4893cf48fb66@109.71.253.175:43067?flow=&encryption=none&security=tls&sni=ssca.irundns.net&type=ws&host=ssca.irundns.net&path=/uHwTYghNGH6P5n2GQl%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528德国 
trojan://Aimer@103.116.7.248:443?flow=&security=tls&sni=epme.ambercc.filegear-sg.me&type=ws&header=none&host=epme.ambercc.filegear-sg.me&path=/%3Fed%3D2560%26proxyip%3Dts.hpc.tw&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528日本 
anytls://1L8ds5bIgBsRWL4UuSFgE@109.71.253.175:32248?insecure=1&sni=ssca.irundns.net&alpn=h2&fp=&os=#0528德国 
hysteria2://3Ns3ZQP5syaC0WL28qOb7i8iOg@109.71.253.175:26265?insecure=1&sni=ssca.irundns.net&alpn=&fp=&obfs=salamander&obfs-password=oAl4yGSlVQZwREJhIJnpTUUadNjFit&mport=&os=#0528德国 
anytls://StlPLgoK4ZVD6NYmoB4Qtgwe@109.71.253.175:4536?insecure=1&sni=ssca.irundns.net&alpn=h2&fp=&os=#0528德国 
vless://1549e70f-dc57-45e3-ac7c-515f0161db72@172.67.155.140:443?flow=&encryption=none&security=tls&sni=XXSe.hUaNGsHaNg.DpdNS.org&type=ws&host=xxse.huangshang.dpdns.org&path=/IKLitbwX0RSt1mktNrT&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjYzIiwicG9ydCI6Mzc4MDUsInNjeSI6ImF1dG8iLCJwcyI6IjA1Mjjnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@172.66.216.95:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528德国 
anytls://w1gD7xfR2nQBWzkKDrDa@109.71.253.175:9952?insecure=1&sni=ssca.irundns.net&alpn=h2&fp=&os=#0528德国 
vless://4a7bb3c8-5fe6-4f57-ace9-748b1e236fe2@109.71.253.175:25537?flow=&encryption=none&security=tls&sni=ssca.irundns.net&type=ws&host=ssca.irundns.net&path=/58tgRFOLdyyy1qrl%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.18.154.3:443?flow=&encryption=none&security=tls&sni=www.vycodcx.dpdns.org&type=xhttp&host=www.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0528德国 

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
