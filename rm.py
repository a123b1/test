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

vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@fairleada.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=fairleada.oceanof.xyz&type=xhttp&host=fairleada.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0526美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@chaitjgx.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=chaitjgx.oceanof.xyz&type=xhttp&host=chaitjgx.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0526美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@rapl.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=rapl.oceanof.xyz&type=xhttp&host=rapl.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0526美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@colonizea.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=colonizea.oceanof.xyz&type=xhttp&host=colonizea.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0526美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@saberz.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=saberz.oceanof.xyz&type=xhttp&host=saberz.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0526美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@nganasanab.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=nganasanab.oceanof.xyz&type=xhttp&host=nganasanab.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0526美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@fixedstarj.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=fixedstarj.oceanof.xyz&type=xhttp&host=fixedstarj.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0526美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@calcitoninzr.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=calcitoninzr.oceanof.xyz&type=xhttp&host=calcitoninzr.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0526美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@plecotuspn.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=plecotuspn.oceanof.xyz&type=xhttp&host=plecotuspn.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0526美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@kilderkinc.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=kilderkinc.oceanof.xyz&type=xhttp&host=kilderkinc.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0526美国 
vless://f929cc78-e2a1-4ce3-8051-3e9538405144@104.17.15.87:80?flow=&encryption=none&security=&sni=&type=ws&host=britain.xydcqd.workers.dev&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0526英国 
vless://afcac633-0e1a-46c3-bef2-cc01cc0097c8@r1.mizulina.top:22231?flow=xtls-rprx-vision-udp443&encryption=none&security=tls&sni=r1.mizulina.top&type=tcp&host=&path=&headerType=none&alpn=&fp=edge&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0526美国 
vless://49f3fec2-1a21-481e-ae65-7c32ae262582@serv-ne-3.whit3.net:10444?flow=xtls-rprx-vision&encryption=none&security=reality&sni=serv-ne-3.whit3.net&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=praGYag8YPbz_rcd_Pa6Fqsi_IiQtO3e1AosYBcu6h4&sid=378086fbdb7c61cd&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0526荷兰 
vless://4c3fe585-ac09-41df-b284-888818888188@79.141.171.133:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=apple.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=0rtpNciTfV9TsoEc7Y8lS5LzBUzLppMnRY8bQC_bH3M&sid=aabbccdd&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0526英国 
vless://fae3277c-0541-4ae9-bbbb-8247453ea652@194.226.169.36:443?flow=&encryption=none&security=reality&sni=yahoo.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=i4Mx_tDND0Xxac3WyA7HgT9rvXdZlXpm5m1EGiQF-Uk&sid=b8aa&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0526英国 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMzciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjA1Mjbnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoic2VhOS5maXJld2FsbGNvbnRyYWN0LmNsaWNrIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjUwIiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNTI2576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InNlYTkuZmlyZXdhbGxjb250cmFjdC5jbGljayIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTo3ZTczMWVjMy1mOGUxLTQzZjYtOTJjZi0zOTc4ZDE0NzA1YzQ=@r3mrcg007117fb8.cybervena.com:50099?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0526台湾 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTo3ZTczMWVjMy1mOGUxLTQzZjYtOTJjZi0zOTc4ZDE0NzA1YzQ=@r3mrcg001286ek2.cybervena.com:50099?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0526台湾 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTo3ZTczMWVjMy1mOGUxLTQzZjYtOTJjZi0zOTc4ZDE0NzA1YzQ=@nbmrcg0034686rw.cybervena.com:50099?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0526台湾 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwMy4xODEuMTY0LjE0NSIsInBvcnQiOjUxNTU2LCJzY3kiOiJhdXRvIiwicHMiOiIwNTI25paw5Yqg5Z2hIiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMC5oZGFjZC5jb20iLCJwb3J0IjozMDgwNywic2N5IjoiYXV0byIsInBzIjoiMDUyNummmea4ryIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ2MTAuaGRhY2QuY29tIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwMy4xODEuMTY0LjE0NSIsInBvcnQiOjU0MDIyLCJzY3kiOiJhdXRvIiwicHMiOiIwNTI26aaZ5rivIiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjY0LCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYzNi5oZGFjZC5jb20iLCJwb3J0IjozMDgzNiwic2N5IjoiYXV0byIsInBzIjoiMDUyNuiLseWbvSIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTEyOC1nY206SlZyc0xMTjF0a044b1haTw==@chengbai02.ascwt179.com:13223?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0526英国 
anytls://SVtbyvCPsXLuA5MflClvBbQcfvLuLpqM5ExOu@45.82.120.168:63382?insecure=1&sni=api.namasha.co&alpn=h2&fp=&os=#0526德国 
anytls://pb5nmPUCcQUMAdiTQrQvqyGoyA@45.82.120.168:3026?insecure=1&sni=api.namasha.co&alpn=h2&fp=&os=#0526德国 
anytls://eDdiicpjlmIh09mh@45.82.120.168:54663?insecure=1&sni=api.namasha.co&alpn=h2&fp=&os=#0526德国 
hysteria2://EFzV7FtWg3xHb2sKK3Q54@45.82.120.168:20757?insecure=1&sni=api.namasha.co&alpn=&fp=&obfs=salamander&obfs-password=LSAvlhPSArGRLbAsS275p4I&mport=&os=#0526德国 
hysteria2://mwBxf3zEhvhIE9CW7sJuHfLZNUKgfF0T@45.82.120.168:45957?insecure=1&sni=api.namasha.co&alpn=&fp=&obfs=salamander&obfs-password=Y4BbjLhvE83CESHXmZpe4&mport=&os=#0526德国 
hysteria2://oUTGgEZc7aIx3byJ2M18looY55BlWppC1PX9n@45.82.120.168:44093?insecure=1&sni=api.namasha.co&alpn=&fp=&obfs=salamander&obfs-password=ik6WBf5cEslKmDUGGqiCzo&mport=&os=#0526德国 
anytls://RMswJdgy9WrHlY272o9mXBvCmZ1BG@45.82.120.168:46084?insecure=1&sni=api.namasha.co&alpn=h2&fp=&os=#0526德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.24.91.33:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0526德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@103.21.244.155:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0526德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@162.159.8.239:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0526德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@162.159.3.7:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0526德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@198.41.196.128:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0526德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@162.159.62.219:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0526德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@103.21.244.86:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0526德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@198.41.223.174:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0526德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.25.160.84:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0526德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@188.114.96.253:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0526德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.20.31.41:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0526德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.25.199.206:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0526德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@190.93.244.167:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0526德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.24.179.138:443?flow=&encryption=none&security=tls&sni=gt.vock33.qzz.io&type=xhttp&host=gt.vock33.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0526德国 


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
