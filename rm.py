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

ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@103.163.218.2:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0625越南 
vless://288124da-0d68-42f4-9f48-70dc4dcc55a6@104.21.21.190:443?flow=&encryption=none&security=tls&sni=EerfgT6.890606.XYZ&type=ws&host=eerfgt6.890606.xyz&path=/e49RZLgIb0TdfgF5HdHEIupMZeK&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625加拿大 
vless://c8eac4b7-95ba-4ce0-920d-c3279eb3b391@104.21.23.210:443?flow=&encryption=none&security=tls&sni=OOO0987654.932.pp.uA&type=ws&host=ooo0987654.932.pp.ua&path=/6r23FpdcA4KNAXX&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625美国 
vless://cf8c791e-9d0b-4e90-aaf6-41ac62468416@104.21.26.17:443?flow=&encryption=none&security=tls&sni=IiIIIiiIIIiiO.459.pp.uA&type=ws&host=iiiiiiiiiiiio.459.pp.ua&path=/dtBdvnoJO8180gomOew3d&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625美国 
vless://3ed60fc0-f13d-490a-a244-c827a8a8b1e5@104.21.57.206:443?flow=&encryption=none&security=tls&sni=WwwWWwS.4444926.xyZ&type=ws&host=wwwwwws.4444926.xyz&path=/j4Wxk3KUHJho91NIJLrX&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625美国 
vless://cb1d2f45-1af3-4bab-a308-7c0c27bac24a@104.21.63.135:443?flow=&encryption=none&security=tls&sni=444fg.8906004.XYz&type=ws&host=444fg.8906004.xyz&path=/YkFQqkZ9vqpDooparWRe5wKJ0R&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625美国 
vless://a96cb093-b164-4bc6-bd27-deb0e385de07@104.21.68.76:443?flow=&encryption=none&security=tls&sni=DDDDdddD.222769.xYZ&type=ws&host=dddddddd.222769.xyz&path=/3zsSOohi9huFfjEPpIlRig3qizHXb&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625美国 
vless://4b33b482-25bc-49e4-b866-878c914d945a@104.21.7.147:443?flow=&encryption=none&security=tls&sni=iIiiIiiIiIIO.HuanGsHaNg.dpDns.ORG&type=ws&host=iiiiiiiiiiio.huangshang.dpdns.org&path=/CpMgWdnDWahQyyQCjn8kmnN0ehd&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625美国 
vless://c226ac5d-65e9-4379-95c3-fb542bc242d8@104.21.9.71:443?flow=&encryption=none&security=tls&sni=eEeEeEEEEe.777198.xyz&type=ws&host=eEeEeEEEEe.777198.xyz&path=/OjdW89Bpg4ykd4O&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjExMS4yNi4xMDkuNzkiLCJwb3J0IjozMDgwNywic2N5IjoiYXV0byIsInBzIjoiMDYyNee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjExMS4yNi4xMDkuNzkiLCJwb3J0IjozMDgzNSwic2N5IjoiYXV0byIsInBzIjoiMDYyNea+s+Wkp+WIqeS6miIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6InYzNS5oZWR1aWFuLmxpbmsiLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ2MzUuaGVkdWlhbi5saW5rIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjExMS4yNi4xMDkuNzkiLCJwb3J0IjozMDg0MCwic2N5IjoiYXV0byIsInBzIjoiMDYyNee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaTEwMC1jb3JlLXF1aWMtbGYuYW1lbXYuY29tIiwicGF0aCI6Ii9pbmRleCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://a7c9c017-db10-4d15-b01b-0634db498b57@1111111q.0890604.xyz:443?flow=&encryption=none&security=tls&sni=1111111Q.0890604.XYZ&type=ws&host=1111111q.0890604.xyz&path=/xZjr7v1DqrYyamxeTh7sLJtI1&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625美国 
vless://948f6596-66f9-4707-aa92-3107a214ce53@112.223.212.219:10543?flow=&encryption=none&security=tls&sni=oops.shalamshorba.dpdns.org&type=ws&host=oops.shalamshorba.dpdns.org&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625美国 
trojan://85f133142f04dbf6547da33895cfabb3@113.99.140.184:39001?flow=&security=tls&sni=www.yrtok.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625香港 
trojan://85f133142f04dbf6547da33895cfabb3@116.31.75.150:39001?flow=&security=tls&sni=www.yrtok.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625香港 
vless://948f6596-66f9-4707-aa92-3107a214ce53@118.163.37.32:81?flow=&encryption=none&security=tls&sni=oops.shalamshorba.dpdns.org&type=ws&host=oops.shalamshorba.dpdns.org&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625美国 
vless://948f6596-66f9-4707-aa92-3107a214ce53@119.199.206.40:11166?flow=&encryption=none&security=tls&sni=oops.shalamshorba.dpdns.org&type=ws&host=oops.shalamshorba.dpdns.org&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625韩国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE0IiwicG9ydCI6MzExODAsInNjeSI6ImF1dG8iLCJwcyI6IjA2MjXml6XmnKwiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE0IiwicG9ydCI6NDAxNzUsInNjeSI6ImF1dG8iLCJwcyI6IjA2MjXmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjEyMyIsInBvcnQiOjUyOTUyLCJzY3kiOiJhdXRvIiwicHMiOiIwNjI1576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjY0LCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQwIiwicG9ydCI6MzEyMDksInNjeSI6ImF1dG8iLCJwcyI6IjA2MjXmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQwIiwicG9ydCI6NDMyOTIsInNjeSI6ImF1dG8iLCJwcyI6IjA2MjXmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQxIiwicG9ydCI6NDk1OTcsInNjeSI6ImF1dG8iLCJwcyI6IjA2MjXnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjYzIiwicG9ydCI6Mzc4MDUsInNjeSI6ImF1dG8iLCJwcyI6IjA2MjXnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://85f133142f04dbf6547da33895cfabb3@120.233.128.68:39001?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625美国 
ss://YWVzLTI1Ni1nY206ZHd6MUd0Rjc=@120.233.128.98:30015?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0625台湾 
trojan://2b1ed981-6547-4094-998b-06a3323d6f6c@120.233.44.201:21003?flow=&security=tls&sni=k15.tudou211.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625韩国 
trojan://2b1ed981-6547-4094-998b-06a3323d6f6c@120.233.44.201:21017?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625韩国 
trojan://2b1ed981-6547-4094-998b-06a3323d6f6c@120.233.44.201:21031?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625马来西亚 
trojan://2b1ed981-6547-4094-998b-06a3323d6f6c@120.233.44.201:21056?flow=&security=tls&sni=k14.tudou211.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625韩国 
trojan://2b1ed981-6547-4094-998b-06a3323d6f6c@120.233.44.201:21079?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625马来西亚 
trojan://2b1ed981-6547-4094-998b-06a3323d6f6c@120.233.44.201:21118?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625韩国 
trojan://2b1ed981-6547-4094-998b-06a3323d6f6c@120.233.44.201:21181?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625马来西亚 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzQuMTAyLjIyOSIsInBvcnQiOjQxMTc0LCJzY3kiOiJhdXRvIiwicHMiOiIwNjI1576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy55cnRvay5jb20iLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://948f6596-66f9-4707-aa92-3107a214ce53@121.167.145.40:10843?flow=&encryption=none&security=tls&sni=oops.shalamshorba.dpdns.org&type=ws&host=oops.shalamshorba.dpdns.org&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625美国 
ss://YWVzLTI1Ni1jZmI6cWF3c3p4YzEyMw==@13.250.125.114:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0625新加坡 
vless://948f6596-66f9-4707-aa92-3107a214ce53@152.67.201.16:11002?flow=&encryption=none&security=tls&sni=oops.shalamshorba.dpdns.org&type=ws&host=oops.shalamshorba.dpdns.org&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625韩国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE3Mi42Ny4xMzEuMjciLCJwb3J0IjoyMDg3LCJzY3kiOiJhdXRvIiwicHMiOiIwNjI1576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjM1MGUyYjAxLWQ0MTAtNDRhNi05MGJhLTY0ODNmMTA2Mjk3MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoicmFrMmQzLjg5MDYwMDA0Lnh5eiIsInBhdGgiOiIvIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoicmFrMmQzLjg5MDYwMDA0Lnh5eiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://c8eac4b7-95ba-4ce0-920d-c3279eb3b391@172.67.138.187:443?flow=&encryption=none&security=tls&sni=19U.7282728.xyz&type=ws&host=19u.7282728.xyz&path=/6r23FpdcA4KNAXX&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625美国 
vless://4b33b482-25bc-49e4-b866-878c914d945a@172.67.155.140:443?flow=&encryption=none&security=tls&sni=iIiiIiiIiIIO.HuanGsHaNg.dpDns.ORG&type=ws&host=iiiiiiiiiiio.huangshang.dpdns.org&path=/CpMgWdnDWahQyyQCjn8kmnN0ehd&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625美国 
vless://a96cb093-b164-4bc6-bd27-deb0e385de07@172.67.191.174:443?flow=&encryption=none&security=tls&sni=DDDDdddD.222769.xYZ&type=ws&host=dddddddd.222769.xyz&path=/3zsSOohi9huFfjEPpIlRig3qizHXb&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625美国 
trojan://2c605663-b89a-5734-a9d6-97d4743d72cf@183.232.235.2:8313?flow=&security=tls&sni=hk-13-568.flztjc.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0625香港 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0IjozNzcxOSwic2N5IjoiYXV0byIsInBzIjoiMDYyNemmmea4ryIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0MTAyNCwic2N5IjoiYXV0byIsInBzIjoiMDYyNeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0MTE5MSwic2N5IjoiYXV0byIsInBzIjoiMDYyNeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0NjkyMSwic2N5IjoiYXV0byIsInBzIjoiMDYyNeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0OTE1NCwic2N5IjoiYXV0byIsInBzIjoiMDYyNeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ3d3cueXJ0b2suY29tIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo1MTY1Miwic2N5IjoiYXV0byIsInBzIjoiMDYyNeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzguOTAuOCIsInBvcnQiOjM5MDc2LCJzY3kiOiJhdXRvIiwicHMiOiIwNjI1576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.153.197.5:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0625摩尔多瓦 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0625波兰 
trojan://85f133142f04dbf6547da33895cfabb3@203.156.253.11:39001?flow=&security=tls&sni=www.yrtok.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625日本 
trojan://85f133142f04dbf6547da33895cfabb3@203.156.253.12:39001?flow=&security=tls&sni=www.yrtok.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625韩国 
ss://YWVzLTI1Ni1nY206NzgxYmI1NGMtZjA4OS00OGRmLTgxMDItMDEyODhhODFlYjEw@218.204.188.10:44721?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0625日本 
trojan://VdWBGFmg@36.151.251.62:23770?flow=&security=tls&sni=36.151.251.62&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625美国 
trojan://2b1ed981-6547-4094-998b-06a3323d6f6c@36.156.184.33:21332?flow=&security=tls&sni=k65.tudou211.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625美国 
trojan://2b1ed981-6547-4094-998b-06a3323d6f6c@36.156.184.33:21603?flow=&security=tls&sni=k61.tudou211.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625美国 
vless://03e92910-34b1-4245-ac63-04a865f43cd5@3er4.4444916.xyz:443?flow=&encryption=none&security=tls&sni=3Er4.4444916.xYz&type=ws&host=3er4.4444916.xyz&path=/f7vKDX2UecxmlPhIJoo2wcE6Q&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625美国 
trojan://1b4c16925f934c57b954a9f0f23dea33@42.240.152.238:8842?flow=&security=tls&sni=brwx.spvpv.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625巴西 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTU5LjQ5LjI4IiwicG9ydCI6NzYwMCwic2N5IjoiYXV0byIsInBzIjoiMDYyNeW+t+WbvSIsIm5ldCI6InRjcCIsImlkIjoiY2U2M2Q3Y2UtYmM4NS00NTVhLWExMmItNGU1NGViMzlhMTRmIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://bcc58e88-e147-11ec-b286-f23c91cfbbc9@83242d49-sy41s0-szh3gf-ggww.cm5.cnkuaishou.com:21233?flow=&security=tls&sni=83242d49-sy41s0-szh3gf-ggww.cm5.cnkuaishou.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625马来西亚 
vmess://eyJ2IjoiMiIsImFkZCI6Ijg5LjQ0LjExMi4zNCIsInBvcnQiOjI1MzUsInNjeSI6ImFlcy0xMjgtZ2NtIiwicHMiOiIwNjI15b635Zu9IiwibmV0IjoidGNwIiwiaWQiOiIwNGQ3YzA4OS1iYmM1LTRlZjItODBlZi1hMDk4MmNmMzM3MDgiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0625斯洛文尼亚共和国 
vless://ce921385-2b31-45fe-84c5-1843e8ae845b@cccccccf.222769.xyz:443?flow=&encryption=none&security=tls&sni=ccCcCcCf.222769.Xyz&type=ws&host=cccccccf.222769.xyz&path=/1xrOld7e5RpK3I98dxLkez&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625美国 
trojan://2c605663-b89a-5734-a9d6-97d4743d72cf@dozo01.flztjc.top:8313?flow=&security=tls&sni=hk-13-568.flztjc.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625香港 
vless://a96cb093-b164-4bc6-bd27-deb0e385de07@eeeeeeeeed.999864.xyz:443?flow=&encryption=none&security=tls&sni=EEeeeEeEEd.999864.xyZ&type=ws&host=eeeeeeeeed.999864.xyz&path=/3zsSOohi9huFfjEPpIlRig3qizHXb&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625美国 
vless://4b33b482-25bc-49e4-b866-878c914d945a@iiiiiiiiiiio.huangshang.dpdns.org:443?flow=&encryption=none&security=tls&sni=iIiiIiiIiIIO.HuanGsHaNg.dpDns.ORG&type=ws&host=iiiiiiiiiiio.huangshang.dpdns.org&path=/CpMgWdnDWahQyyQCjn8kmnN0ehd&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625美国 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMi5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgxMiwic2N5IjoiYXV0byIsInBzIjoiMDYyNeaWsOWKoOWdoSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYyOC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyOCwic2N5IjoiYXV0byIsInBzIjoiMDYyNemfqeWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzMCwic2N5IjoiYXV0byIsInBzIjoiMDYyNeiNt+WFsCIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoib2NiYy5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMi5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzMiwic2N5IjoiYXV0byIsInBzIjoiMDYyNee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMy5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzMywic2N5IjoiYXV0byIsInBzIjoiMDYyNeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYzNS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzNSwic2N5IjoiYXV0byIsInBzIjoiMDYyNea+s+Wkp+WIqeS6miIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6InYzNS5oZWR1aWFuLmxpbmsiLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ2MzUuaGVkdWlhbi5saW5rIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InY0MC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDg0MCwic2N5IjoiYXV0byIsInBzIjoiMDYyNee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaTEwMC1jb3JlLXF1aWMtbGYuYW1lbXYuY29tIiwicGF0aCI6Ii9pbmRleCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InY2LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA2LCJzY3kiOiJhdXRvIiwicHMiOiIwNjI15pel5pysIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0Ijoib2NiYy5jb20iLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InY5LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA5LCJzY3kiOiJhdXRvIiwicHMiOiIwNjI16aaZ5rivIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoiYmFpZHUuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://2b1ed981-6547-4094-998b-06a3323d6f6c@xd-js.timiwc.com:21332?flow=&security=tls&sni=k65.tudou211.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625美国 
trojan://2b1ed981-6547-4094-998b-06a3323d6f6c@xd-js.timiwc.com:21603?flow=&security=tls&sni=k61.tudou211.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625美国 
trojan://2b1ed981-6547-4094-998b-06a3323d6f6c@xd-js.timiwc.com:59599?flow=&security=tls&sni=k62.tudou211.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625美国 
ss://YWVzLTI1Ni1nY206M2VlOTBhYTktODgzMS00ZWEzLTk0MjUtYzM2MTA5MGE5Mzhk@zf1.10101251.xyz:55175?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0625孟加拉国 
ss://YWVzLTI1Ni1nY206M2VlOTBhYTktODgzMS00ZWEzLTk0MjUtYzM2MTA5MGE5Mzhk@zf2.10101251.xyz:30725?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0625意大利 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@162.159.11.119:443?flow=&encryption=none&security=tls&sni=user.strosoa.dpdns.org&type=xhttp&host=user.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZDZiMTExM2QtZGM3MC00YjY4LTkzNTEtMmQ1OTAyNWQwNmI1QDQ1LjgyLjEyMS4yMzc6MjY1NjE6d3M6LzNLM0ltRlVJajA4eSUzRmVkJTNEMjU2MDp3d3cuYW1lYmxvLmpwOm5vbmU6dGxzOnd3dy5hbWVibG8uanA6W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0625德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@198.41.196.144:443?flow=&encryption=none&security=tls&sni=user.strosoa.dpdns.org&type=xhttp&host=user.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NzdiNWQzYzktMDBiOS00MDlmLTgwNDMtMTQzMjE5MzJlNThjQDQ1LjgyLjEyMS4yMzc6NjE3OTE6d3M6L0JHRCUzRmVkJTNEMjU2MDp3d3cuYW1lYmxvLmpwOm5vbmU6dGxzOnd3dy5hbWVibG8uanA6W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0625德国 
anytls://U6DucafFx4fsyGqSVJEwsK9PR6YSA6LYj@45.82.121.237:23166?insecure=1&sni=www.ameblo.jp&alpn=h2&fp=&os=#0625德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.27.27.86:443?flow=&encryption=none&security=tls&sni=user.strosoa.dpdns.org&type=xhttp&host=user.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.19.166.209:443?flow=&encryption=none&security=tls&sni=user.strosoa.dpdns.org&type=xhttp&host=user.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625德国 
anytls://kWDE9sRvbLC9rKlgQI5AO88Zz1KQu0DD8u2CYP@45.82.121.237:28050?insecure=1&sni=www.ameblo.jp&alpn=h2&fp=&os=#0625德国 
hysteria2://jHxp3bUBL0d1vfTRqjCtjB9K8jOQP69sj6dIzhQE@45.82.121.237:27606?insecure=1&sni=www.ameblo.jp&alpn=&fp=&obfs=salamander&obfs-password=kyiJB2qdcqCbyxQPLxcJhOR6WwLuj&mport=&os=#0625德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4yMzciLCJwb3J0IjozNTYxNSwic2N5IjoiYXV0byIsInBzIjoiMDYyNeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIwYTY4ZjIxZi1mMmNlLTQ5ZjEtYjkyZS0yNjY3Nzg4YWVjNTciLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5hbWVibG8uanAiLCJwYXRoIjoiL3MwYnRPM3ZIMHp4WDF0ZjZMRkhmWVY5NHc/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6Ind3dy5hbWVibG8uanAiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://50cc0a85-91d2-421b-a886-322493d2d1af@45.82.121.237:43316?flow=&encryption=none&security=tls&sni=www.ameblo.jp&type=ws&host=www.ameblo.jp&path=/erHfuMVA3E6cu%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4yMzciLCJwb3J0IjoyNjM0Mywic2N5IjoiYXV0byIsInBzIjoiMDYyNeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI3YTg4NGMwZi1jNDNhLTQ2NjYtYjNjZS04YmRhOTYxNTRjNjEiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5hbWVibG8uanAiLCJwYXRoIjoiL1d6WjVGVVpIVFZHWlZsb1BROW50UEUyR0o0P2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ3d3cuYW1lYmxvLmpwIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
anytls://7x3MCpPvVr6JcLAgF67TqVu5cYk26njx4a2EEv@45.82.121.237:64027?insecure=1&sni=www.ameblo.jp&alpn=h2&fp=&os=#0625德国 
hysteria2://NUrwoYB05b8aqDPMY@45.82.121.237:15266?insecure=1&sni=www.ameblo.jp&alpn=&fp=&obfs=salamander&obfs-password=UyZwPCfJU5LAPnyKFA7mOVKS69FS1&mport=&os=#0625德国 
hysteria2://rG92kTv73HBKOTynwyg2X1lIMf5Omq5RcHS9K58@45.82.121.237:48826?insecure=1&sni=www.ameblo.jp&alpn=&fp=&obfs=salamander&obfs-password=axcMhh8x2QP3sSZkHNbzBZFr3&mport=&os=#0625德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@141.101.123.23:443?flow=&encryption=none&security=tls&sni=user.strosoa.dpdns.org&type=xhttp&host=user.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4yMzciLCJwb3J0Ijo2MTczOSwic2N5IjoiYXV0byIsInBzIjoiMDYyNeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIwMTExMzMxMS1hMzBjLTRiOTUtYjFiZC03NzEzYzM2YmU3MTAiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5hbWVibG8uanAiLCJwYXRoIjoiL1E5dzRxZUh0ekdER2JmP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ3d3cuYW1lYmxvLmpwIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.21.110.201:443?flow=&encryption=none&security=tls&sni=user.strosoa.dpdns.org&type=xhttp&host=user.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625德国 
anytls://ihcYAp7k2Vgvrd9FT@45.82.121.237:41334?insecure=1&sni=www.ameblo.jp&alpn=h2&fp=&os=#0625德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@190.93.247.3:443?flow=&encryption=none&security=tls&sni=user.strosoa.dpdns.org&type=xhttp&host=user.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625德国 
vless://3de085ee-1986-4592-957a-7fbe455992cc@45.82.121.237:8016?flow=&encryption=none&security=tls&sni=www.ameblo.jp&type=ws&host=www.ameblo.jp&path=/LeZMTdlB%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4yMzciLCJwb3J0IjoxODg0Nywic2N5IjoiYXV0byIsInBzIjoiMDYyNeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI3N2I1ZDNjOS0wMGI5LTQwOWYtODA0My0xNDMyMTkzMmU1OGMiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5hbWVibG8uanAiLCJwYXRoIjoiL2J5P2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ3d3cuYW1lYmxvLmpwIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
anytls://CaT3yMmeziCviescWitdnGUMHVjuagfgUOI@45.82.121.237:46984?insecure=1&sni=www.ameblo.jp&alpn=h2&fp=&os=#0625德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.27.65.243:443?flow=&encryption=none&security=tls&sni=user.strosoa.dpdns.org&type=xhttp&host=user.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.16.109.184:443?flow=&encryption=none&security=tls&sni=user.strosoa.dpdns.org&type=xhttp&host=user.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625德国 
anytls://zRkA5PJV8JlCkeSIzrWG6cDtdV4yINN6MIApM@45.82.121.237:56418?insecure=1&sni=www.ameblo.jp&alpn=h2&fp=&os=#0625德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@172.66.45.147:443?flow=&encryption=none&security=tls&sni=user.strosoa.dpdns.org&type=xhttp&host=user.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625德国 
hysteria2://10V0hPWFQ6o99N1tiBINIh7YXXau@45.82.121.237:12906?insecure=1&sni=www.ameblo.jp&alpn=&fp=&obfs=salamander&obfs-password=Wbc7UbNMFGkUrAtcH38Ut2SO0op1qJVIVlG&mport=&os=#0625德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@190.93.246.68:443?flow=&encryption=none&security=tls&sni=user.strosoa.dpdns.org&type=xhttp&host=user.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625德国 
vless://7584d697-9089-4281-ae0c-f95ea3b6ba2d@45.82.121.237:60393?flow=&encryption=none&security=tls&sni=www.ameblo.jp&type=ws&host=www.ameblo.jp&path=/598Kc9LU8FBOp0spXQkT3pdoIX%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4yMzciLCJwb3J0Ijo0MzQwNiwic2N5IjoiYXV0byIsInBzIjoiMDYyNeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIzZGNiZDY5NS1mMjkyLTQwZDMtYWEzNi1iYzEzNGFmMTE1ZTAiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5hbWVibG8uanAiLCJwYXRoIjoiL3ZmUXVPRXFuSjZobXNJNT9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoid3d3LmFtZWJsby5qcCIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
anytls://YbXHfLKsIHsuiXgwYQYuS@45.82.121.237:19069?insecure=1&sni=www.ameblo.jp&alpn=h2&fp=&os=#0625德国 
hysteria2://hF0FfEaRBX5We1JnQEn54sReQ@45.82.121.237:14904?insecure=1&sni=www.ameblo.jp&alpn=&fp=&obfs=salamander&obfs-password=F5mYJiYLPMOYhp3bfm3VGj8aUpMyXO7cu8cs0J87&mport=&os=#0625德国 
hysteria2://ftg8hDewhhi2sl8ZJCTcLxAJ4kXVraAKk0LF4@45.82.121.237:26976?insecure=1&sni=www.ameblo.jp&alpn=&fp=&obfs=salamander&obfs-password=4rtRX0AacktTeyvVk&mport=&os=#0625德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@188.114.98.202:443?flow=&encryption=none&security=tls&sni=user.strosoa.dpdns.org&type=xhttp&host=user.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.27.29.71:443?flow=&encryption=none&security=tls&sni=user.strosoa.dpdns.org&type=xhttp&host=user.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4yMzciLCJwb3J0Ijo0ODM0MCwic2N5IjoiYXV0byIsInBzIjoiMDYyNeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIyYzI4YmMxNC03MmM2LTQ0YzUtYjQ4NC1jOTA3MzliN2UwZTMiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5hbWVibG8uanAiLCJwYXRoIjoiL0V6aGEzZFFjUkhlU3o/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6Ind3dy5hbWVibG8uanAiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
anytls://q2mNODfwD8GRZPM9CcC@45.82.121.237:45022?insecure=1&sni=www.ameblo.jp&alpn=h2&fp=&os=#0625德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.58.127:443?flow=&encryption=none&security=tls&sni=user.strosoa.dpdns.org&type=xhttp&host=user.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625德国 
hysteria2://UJ8zXekmJRaaZLJvVJaFUWblpj@45.82.121.237:34192?insecure=1&sni=www.ameblo.jp&alpn=&fp=&obfs=salamander&obfs-password=JGEi1YLZv21TDlDdrg0JbLMotvtN&mport=&os=#0625德国 
hysteria2://sFDvxgQqrXJu04aM6i2xxn1BUp97oYXNmkv1S6o@45.82.121.237:53831?insecure=1&sni=www.ameblo.jp&alpn=&fp=&obfs=salamander&obfs-password=VCMMhYs7WKor5Ah4lzLFopyn6jk&mport=&os=#0625德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4yMzciLCJwb3J0IjoxMTI4NCwic2N5IjoiYXV0byIsInBzIjoiMDYyNeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJhNGRjMzgwMS05ZWUwLTQzYTItOTUzMS02NGQ0MGM4OTQ1YjYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5hbWVibG8uanAiLCJwYXRoIjoiL1cxN3VJeXpWYjFtOWNUWTFBU1h1MzhKWTc/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6Ind3dy5hbWVibG8uanAiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@162.159.254.11:443?flow=&encryption=none&security=tls&sni=user.strosoa.dpdns.org&type=xhttp&host=user.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.59.98:443?flow=&encryption=none&security=tls&sni=user.strosoa.dpdns.org&type=xhttp&host=user.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.27.4.50:443?flow=&encryption=none&security=tls&sni=user.strosoa.dpdns.org&type=xhttp&host=user.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.21.115.63:443?flow=&encryption=none&security=tls&sni=user.strosoa.dpdns.org&type=xhttp&host=user.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@198.41.214.162:443?flow=&encryption=none&security=tls&sni=user.strosoa.dpdns.org&type=xhttp&host=user.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0625德国 

  
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
