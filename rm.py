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

vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@103.21.244.114:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@103.21.244.191:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207德国 
vless://fef4a93d-eb4f-4657-b56b-32a0dc060045@104.18.32.47:443?flow=&encryption=none&security=tls&sni=dev.twistsparrow.xyz&type=ws&host=dev.twistsparrow.xyz&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0207英国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@104.20.64.155:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@104.24.9.3:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@104.25.194.251:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@104.25.202.125:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@104.27.206.118:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207德国 
hysteria2://zhangyang@130.61.50.75:6443?insecure=1&sni=dash.cloudflare.com&alpn=h3&fp=&mport=&os=#0207德国 
vless://d6b1327d-2bec-4366-a3a1-9b1284f95841@138.124.79.9:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=sun6-21.userapi.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=SbVKOEMjK0sIlbwg4akyBg5mL5KZwwB-ed4eEE7YnRc&sid=6ba85179e30d4fc2&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207瑞士 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@162.159.62.219:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@173.245.59.126:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@173.245.59.65:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207德国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0207波兰 
vless://fef4a93d-eb4f-4657-b56b-32a0dc060045@188.114.98.0:443?flow=&encryption=none&security=tls&sni=dev.twistsparrow.xyz&type=ws&host=dev.twistsparrow.xyz&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0207英国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@198.41.192.217:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@198.41.196.174:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMC4xNTciLCJwb3J0IjozODY1Miwic2N5IjoiYXV0byIsInBzIjoiMDIwN+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI5NDg2MGE5ZS0wNjg3LTRiZWUtODRlMS03NmM2MTYwZGMzMzIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5iaW5nLmNvbSIsInBhdGgiOiIvdHZIZ2VqP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ3d3cuYmluZy5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
hysteria2://vqNyMPGF702oH3WtIIJGIgnwir@45.82.120.157:11303?insecure=1&sni=www.bing.com&alpn=&fp=&obfs=salamander&obfs-password=gP8BEFMY3CVCIo880LaivsYQ&mport=&os=#0207德国 
hysteria2://fFCvJT1epl35oD495b@45.82.120.157:31857?insecure=1&sni=www.bing.com&alpn=&fp=&obfs=salamander&obfs-password=NJneVEj2miievP5nXIhfXawTQ&mport=&os=#0207德国 
hysteria2://uMYfxCOA1oYlp99gHzVcwNn1dGXU@45.82.120.157:43408?insecure=1&sni=www.bing.com&alpn=&fp=&obfs=salamander&obfs-password=gY67SJ0oCzgaA7jVNl2i6Q4cm6xH78t6k1Z5Bve9&mport=&os=#0207德国 
hysteria2://IhmI3Yp1cVAlAuqdj0e7sjEJFCmZIHawEYm@45.82.120.157:12788?insecure=1&sni=www.bing.com&alpn=&fp=&obfs=salamander&obfs-password=A6lqYJjB3eOCjOo4&mport=&os=#0207德国 
vless://7f264e76-6a25-4580-a00c-2aaeeed29ef4@45.82.120.157:65401?flow=&encryption=none&security=tls&sni=www.bing.com&type=ws&host=www.bing.com&path=/zH3woBu3CW4zGf1lgHR5uMMs3hS%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207德国 
vless://3e7f67de-648e-4871-b51a-a225214d41ee@47.80.13.85:443?flow=&encryption=none&security=reality&sni=api.company-target.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=TRP10HqKUXEQ3O-cfsq93DycfBmbJe9KM36yvSa8Mmw&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207韩国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@54k5.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=54k5.oceanof.xyz&type=xhttp&host=54k5.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207美国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@6b66.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=6b66.oceanof.xyz&type=xhttp&host=6b66.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207美国 
vless://fd8972d7-cf5e-11f0-9970-45e1d80c4039@78.153.139.68:8443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=images.apple.com&type=tcp&host=&path=&headerType=none&alpn=&fp=random&pbk=pekfYPV5U8EjfQ4_zS5c6I2NnOZ2jUlyMGAWa4FWPF4&sid=58c512b4422e2517&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207芬兰 
vless://fd8972d7-cf5e-11f0-9970-45e1d80c4039@78.153.139.68:8443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=images.apple.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=pekfYPV5U8EjfQ4_zS5c6I2NnOZ2jUlyMGAWa4FWPF4&sid=58c512b4422e2517&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207芬兰 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjAyMDfnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoidC5tZS9yaXBhb2ppZWRpYW4iLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjAyMDfnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjAyMDfnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoiam9zcy5ncGoxLndlYi5pZCIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjAyMDfnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiODIuMTk4LjI0Ni45NyIsInBhdGgiOiI/ZWQ9MjA0OCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjAyMDfnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiODIuMTk4LjI0Ni45NyIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjAyMDfnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiNDEyMC1iZTA0LTEzRUY1NjA5Njk4OS40NTcuUHAuVWEiLCJwYXRoIjoiL2tUNVZIWWNNcnBoZXNxUk96U1BvSHJCbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://7e2b2894-3b5c-4b65-acc5-e1784f4047f2@89.169.162.214:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=yandex.ru&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=zii4nGNapnFKL6SN8GzWNqFlElBvUCUFUThEP0kFH04&sid=e57932a42872a362&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207土耳其 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@9850.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=9850.oceanof.xyz&type=xhttp&host=9850.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207美国 
vmess://eyJ2IjoiMiIsImFkZCI6ImdmLnVzYTIwMzAuaW5kZXZzLmluIiwicG9ydCI6ODAsInNjeSI6ImF1dG8iLCJwcyI6IjAyMDfnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiNTE5NmFhZTctMTQ3OS00ZjNjLTk3OGItNjhlNzQ5NzdiNTA5IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJnZi51c2EyMDMwLmluZGV2cy5pbiIsInBhdGgiOiIva2wwMWlIdTF2Z2JKbVE1SUtNQml2blIzIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@i05.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=i05.oceanof.xyz&type=xhttp&host=i05.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207美国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@iry650.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=iry650.oceanof.xyz&type=xhttp&host=iry650.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207美国 
vmess://eyJ2IjoiMiIsImFkZCI6Im5leHRtaS5oYWpteWFiLmlyIiwicG9ydCI6MjA1Mywic2N5IjoiYXV0byIsInBzIjoiMDIwN+iNt+WFsCIsIm5ldCI6IndzIiwiaWQiOiI5NTg1NjM2YS01NGJjLTQxOWEtOTBhMS03NmM1YzZlYzc0ZGYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwcC5oYWpteWFiLmlyIiwicGF0aCI6Ii8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ5YWt4dnRmYnlrLmhham15YWIuaXIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6Im5leHRtaS5oYWpteWFiLmlyIiwicG9ydCI6MjA1Mywic2N5IjoiYXV0byIsInBzIjoiMDIwN+iNt+WFsCIsIm5ldCI6IndzIiwiaWQiOiI5NTg1NjM2YS01NGJjLTQxOWEtOTBhMS03NmM1YzZlYzc0ZGYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwcC5oYWpteWFiLmlyIiwicGF0aCI6Ii8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@px17.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=px17.oceanof.xyz&type=xhttp&host=px17.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207美国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@pxc62.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=pxc62.oceanof.xyz&type=xhttp&host=pxc62.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207美国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@q24.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=q24.oceanof.xyz&type=xhttp&host=q24.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207美国 
vmess://eyJ2IjoiMiIsImFkZCI6InN5NC42MjA3MjAueHl6IiwicG9ydCI6NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwMjA35r6z5aSn5Yip5LqaIiwibmV0Ijoid3MiLCJpZCI6IjUxNmQ4YTdhLTNmMGItNDFkMy1iYWQwLTI0NjExNjM4MTUxNiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoic3k0LjYyMDcyMC54eXoiLCJwYXRoIjoiLyIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@ua527.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=ua527.oceanof.xyz&type=xhttp&host=ua527.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207美国 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMC5oZGFjZC5jb20iLCJwb3J0IjozMDgwNywic2N5IjoiYXV0byIsInBzIjoiMDIwN+mmmea4ryIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMi5oZGFjZC5jb20iLCJwb3J0IjozMDgxMiwic2N5IjoiYXV0byIsInBzIjoiMDIwN+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ2MTIuaGRhY2QuY29tIiwicGF0aCI6Ij9lZD0yMDQ4IiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMi5oZGFjZC5jb20iLCJwb3J0IjozMDgxMiwic2N5IjoiYXV0byIsInBzIjoiMDIwN+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMi5oZGFjZC5jb20iLCJwb3J0IjozMDgxMiwic2N5IjoiYXV0byIsInBzIjoiMDIwN+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIyMDAxOmJjODozMmQ3OjMwMjo6MTAiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMi5oZGFjZC5jb20iLCJwb3J0IjozMDgxMiwic2N5IjoiYXV0byIsInBzIjoiMDIwN+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJncmVlbjIuY2RudGVuY2VudG11c2ljLmNvbSIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMC5oZGFjZC5jb20iLCJwb3J0IjozMDgzMCwic2N5IjoiYXV0byIsInBzIjoiMDIwN+iNt+WFsCIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJpbWcxNC4zNjBidXlpbWcuY29tIiwicGF0aCI6Ii9vYmoiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InY4LmhkYWNkLmNvbSIsInBvcnQiOjMwODA4LCJzY3kiOiJhdXRvIiwicHMiOiIwMjA3576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiJjaHJvbWUiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@wnr128.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=wnr128.oceanof.xyz&type=xhttp&host=wnr128.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0207美国 


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
