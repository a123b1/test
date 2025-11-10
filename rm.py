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

vmess://eyJ2IjoiMiIsImFkZCI6IjEwMy4yNDMuMjYuMjA5IiwicG9ydCI6ODA4MCwic2N5IjoiYXV0byIsInBzIjoiMTEwN+mmmea4ryIsIm5ldCI6InRjcCIsImlkIjoiYmM3ZTY4NDAtYWI4My00NTcwLWVhYWUtZDlhZmYxZTJkYTA5IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoiaHR0cCIsImhvc3QiOiIiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwMy4yNDMuMjYuMjA5IiwicG9ydCI6ODA4MCwic2N5IjoiYXV0byIsInBzIjoiMTEwN+mmmea4ryIsIm5ldCI6InRjcCIsImlkIjoiYmM3ZTY4NDAtYWI4My00NTcwLWVhYWUtZDlhZmYxZTJkYTA5IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoiaHR0cCIsImhvc3QiOiIxMDMuMjQzLjI2LjIwOSIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://1b57001bd214304027025a740b6cf1ac@117.172.176.22:373?flow=&security=tls&sni=www.nintendogames.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE1Mi43MC45Mi42OSIsInBvcnQiOjgwLCJzY3kiOiJhdXRvIiwicHMiOiIxMTA36Z+p5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJiYjljMzk5My1hNGI5LTRkYWQtYWViOS1hYzg2MzcxYWU2OGIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJodHRwIiwiaG9zdCI6IiIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://cdc453bb-34c8-4405-a322-56f6878ccd40@198.186.131.216:47387?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107德国 
trojan://BxceQaOe@203.198.122.129:443?flow=&security=tls&sni=203.198.122.129&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107香港 
trojan://BxceQaOe@203.198.122.129:443?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107香港 
trojan://BxceQaOe@203.198.122.129:443?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107香港 
trojan://1b57001bd214304027025a740b6cf1ac@203.198.122.194:443?flow=&security=tls&sni=www.nintendogames.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107香港 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@218.237.185.230:4652?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1107韩国 
hysteria2://6286105c-fb6d-11ef-be96-f23c93136cb3@227fd503-t4ssg0-t5vo4i-4550.la.shifen.uk:1743?insecure=1&sni=227fd503-t4ssg0-t5vo4i-4550.la.shifen.uk&alpn=&fp=&mport=&os=#1107美国 
hysteria2://6286105c-fb6d-11ef-be96-f23c93136cb3@227fd503-t4ssg0-t5vo4i-4550.la.shifen.uk:1743?insecure=1&sni=&alpn=&fp=&mport=&os=#1107美国 
trojan://BxceQaOe@36.150.215.244:2753?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107新加坡 
trojan://BxceQaOe@36.150.215.248:4492?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107日本 
trojan://BxceQaOe@36.151.251.38:25891?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107美国 
hysteria2://be8cc8f6-0c6a-11f0-a5a3-f23c93141fad@37a48ffc-t4whs0-t5a0jp-b4pt.la.shifen.uk:1743?insecure=1&sni=37a48ffc-t4whs0-t5a0jp-b4pt.la.shifen.uk&alpn=&fp=&mport=&os=#1107美国 
hysteria2://17cdeb6c-f046-11ee-bdac-f23c93141fad@3d2c11f1-t52o00-tdw2ye-2gok.la.shifen.uk:1743?insecure=1&sni=&alpn=&fp=&mport=&os=#1107美国 
hysteria2://17cdeb6c-f046-11ee-bdac-f23c93141fad@3d2c11f1-t52o00-tdw2ye-2gok.la.shifen.uk:1743?insecure=1&sni=3d2c11f1-t52o00-tdw2ye-2gok.la.shifen.uk&alpn=&fp=&mport=&os=#1107美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQzLjI0Ny4xMzQuMjEzIiwicG9ydCI6NTk1MTYsInNjeSI6ImF1dG8iLCJwcyI6IjExMDfpppnmuK8iLCJuZXQiOiJ0Y3AiLCJpZCI6IjI5MDZlMTllLWM5OWYtNDU2ZS1iY2IzLWM1NDcyZmQ1OTRlNSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Imh0dHAiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ2LjI5LjM0LjIwNSIsInBvcnQiOjU5OTU2LCJzY3kiOiJhdXRvIiwicHMiOiIxMTA3576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJjYTBjOTkzNy01OGE2LTQ0ZWEtOTExMS1hNmFiYWMyNjdkMGYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ2LjI5LjM0LjIwNSIsInBvcnQiOjQxMzQ2LCJzY3kiOiJhdXRvIiwicHMiOiIxMTA3576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI2MDYzYWQwZC0yNmZlLTQ2YTctYmY3OC1kZmVhNzFhZmRlOWIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ2LjI5LjM0LjIwNSIsInBvcnQiOjIyOTQ3LCJzY3kiOiJhdXRvIiwicHMiOiIxMTA3576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkNzI5MWZjNC0xNzAyLTQ4MjYtOGZlMS1hYjMwMWIxYzhmODIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
hysteria2://1b609740-eec2-11ef-8543-f23c93136cb3@47cc555c-t55r40-tdtaxw-au6.la.shifen.uk:1743?insecure=1&sni=47cc555c-t55r40-tdtaxw-au6.la.shifen.uk&alpn=&fp=&mport=&os=#1107美国 
trojan://BxceQaOe@58.152.30.26:443?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107香港 
trojan://BxceQaOe@58.152.46.98:443?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107香港 
trojan://BxceQaOe@58.152.46.98:443?flow=&security=tls&sni=58.152.46.98&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107香港 
trojan://BxceQaOe@58.152.53.186:443?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107香港 
hysteria2://6286105c-fb6d-11ef-be96-f23c93136cb3@5bedbab5-t3bpc0-t49cd4-4550.la.shifen.uk:1743?insecure=1&sni=&alpn=&fp=&mport=&os=#1107美国 
hysteria2://be8cc8f6-0c6a-11f0-a5a3-f23c93141fad@61f04f6d-t4v9c0-t5amrp-b4pt.la.shifen.uk:1743?insecure=1&sni=&alpn=&fp=&mport=&os=#1107美国 
hysteria2://be8cc8f6-0c6a-11f0-a5a3-f23c93141fad@61f04f6d-t4v9c0-t5amrp-b4pt.la.shifen.uk:1743?insecure=1&sni=61f04f6d-t4v9c0-t5amrp-b4pt.la.shifen.uk&alpn=&fp=&mport=&os=#1107美国 
hysteria2://7a2512b4-09ee-11f0-8d46-f23c9313b177@67e01b04-t3dk00-tcm6ys-deip.la.shifen.uk:1743?insecure=1&sni=67e01b04-t3dk00-tcm6ys-deip.la.shifen.uk&alpn=&fp=&mport=&os=#1107美国 
hysteria2://712bdc36-24be-11ee-be53-f23c9313b177@68407ef0-t3dk00-tcl9of-5fdt.la.shifen.uk:1743?insecure=1&sni=&alpn=&fp=&mport=&os=#1107美国 
hysteria2://6286105c-fb6d-11ef-be96-f23c93136cb3@68f48101-t4teo0-t5waci-4550.la.shifen.uk:1743?insecure=1&sni=68f48101-t4teo0-t5waci-4550.la.shifen.uk&alpn=&fp=&mport=&os=#1107美国 
hysteria2://537d7098-fdbe-11ef-8ebc-f23c93141fad@6e206c57-t3b340-tcj7b6-d70y.la.shifen.uk:1743?insecure=1&sni=&alpn=&fp=&mport=&os=#1107美国 
hysteria2://94931862-1484-11f0-9ab7-f23c95b6f51d@98f4acfe-t4un40-tdini3-cdfn.la.shifen.uk:1743?insecure=1&sni=&alpn=&fp=&mport=&os=#1107美国 
hysteria2://df7bed3c-06eb-11f0-8ebc-f23c93141fad@9edb1f6e-t56dc0-t9lxaa-1glq.la.shifen.uk:1743?insecure=1&sni=9edb1f6e-t56dc0-t9lxaa-1glq.la.shifen.uk&alpn=&fp=&mport=20000%3A50000&os=#1107美国 
hysteria2://06c625ea-5902-11ee-9e87-f23c9313b177@c01db724-t3dk00-t3ss2y-4mce.la.shifen.uk:1743?insecure=1&sni=c01db724-t3dk00-t3ss2y-4mce.la.shifen.uk&alpn=&fp=&mport=&os=#1107美国 
hysteria2://1b609740-eec2-11ef-8543-f23c93136cb3@c0a37350-t4x400-tdtx5w-au6.la.shifen.uk:1743?insecure=1&sni=c0a37350-t4x400-tdtx5w-au6.la.shifen.uk&alpn=&fp=&mport=20000%3A50000&os=#1107美国 
hysteria2://17cdeb6c-f046-11ee-bdac-f23c93141fad@c37b0be5-t3kyo0-t3lvgh-2gok.la.shifen.uk:1743?insecure=1&sni=&alpn=&fp=&mport=&os=#1107美国 
hysteria2://6286105c-fb6d-11ef-be96-f23c93136cb3@cc65f71a-t4v9c0-t5waci-4550.la.shifen.uk:1743?insecure=1&sni=&alpn=&fp=&mport=&os=#1107美国 
hysteria2://1b609740-eec2-11ef-8543-f23c93136cb3@d48dac10-t4v9c0-tdtx5w-au6.la.shifen.uk:1743?insecure=1&sni=d48dac10-t4v9c0-tdtx5w-au6.la.shifen.uk&alpn=&fp=&mport=&os=#1107美国 
hysteria2://537d7098-fdbe-11ef-8ebc-f23c93141fad@dcc40639-t3cxs0-tcj7b6-d70y.la.shifen.uk:1743?insecure=1&sni=dcc40639-t3cxs0-tcj7b6-d70y.la.shifen.uk&alpn=&fp=&mport=&os=#1107美国 
hysteria2://537d7098-fdbe-11ef-8ebc-f23c93141fad@dcc40639-t3cxs0-tcj7b6-d70y.la.shifen.uk:1743?insecure=1&sni=&alpn=&fp=&mport=&os=#1107美国 
hysteria2://df7bed3c-06eb-11f0-8ebc-f23c93141fad@e10829f0-t4un40-t9lb2a-1glq.la.shifen.uk:1743?insecure=1&sni=&alpn=&fp=&mport=&os=#1107美国 
hysteria2://df7bed3c-06eb-11f0-8ebc-f23c93141fad@e10829f0-t4un40-t9lb2a-1glq.la.shifen.uk:1743?insecure=1&sni=e10829f0-t4un40-t9lb2a-1glq.la.shifen.uk&alpn=&fp=&mport=&os=#1107美国 
hysteria2://be8cc8f6-0c6a-11f0-a5a3-f23c93141fad@ea9466bf-t3dk00-t3i5yp-b4pt.la.shifen.uk:1743?insecure=1&sni=&alpn=&fp=&mport=&os=#1107美国 
hysteria2://1b609740-eec2-11ef-8543-f23c93136cb3@eb8d3417-t4teo0-tdtx5w-au6.la.shifen.uk:1743?insecure=1&sni=&alpn=&fp=&mport=&os=#1107美国 
hysteria2://712bdc36-24be-11ee-be53-f23c9313b177@fe1d6996-t4v9c0-tcl9of-5fdt.la.shifen.uk:1743?insecure=1&sni=&alpn=&fp=&mport=&os=#1107美国 
ss://YWVzLTEyOC1nY206STFxcll4T1h4UFlDT2toVA==@nl1.web3sp.com:50829?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1107荷兰 
trojan://adbac894-90b9-4913-b77e-a715a8d4ebc8@oss-cn-shanghai.letssepub.com:20021?flow=&security=tls&sni=dingding-doc.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107香港 
trojan://adbac894-90b9-4913-b77e-a715a8d4ebc8@oss-cn-shanghai.letssepub.com:20021?flow=&security=tls&sni=oss-cn-shanghai.letssepub.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107香港 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTowMTRlOTBkZi1hM2VlLTQ2NTQtYTlmNi1kMTE4ZTAyZGQwMmE=@sl.fgmcx.top:41047?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1107新加坡 
vmess://eyJ2IjoiMiIsImFkZCI6InY5LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA5LCJzY3kiOiJhdXRvIiwicHMiOiIxMTA36aaZ5rivIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoiYmFpZHUuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@104.16.170.148:443?flow=&encryption=none&security=tls&sni=ver.vmkc9.netlib.re&type=xhttp&host=ver.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107德国 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@198.41.201.41:443?flow=&encryption=none&security=tls&sni=ver.vmkc9.netlib.re&type=xhttp&host=ver.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107德国 
anytls://NTJdPLlaTPlqHwEwf4b2PceCXE2fIsKHN6SS@37.114.49.234:46966?insecure=1&sni=cm1.awslcn.info&alpn=h2&fp=&os=#1107德国 
anytls://kjq9L8OAsKxsbffAjV9Pn7LN@37.114.49.234:40226?insecure=1&sni=cm1.awslcn.info&alpn=h2&fp=&os=#1107德国 
trojan://2b1186d7-d782-47e4-8030-b63f8adb5503@37.114.49.234:26176?flow=&security=tls&sni=cm1.awslcn.info&type=ws&header=none&host=cm1.awslcn.info&path=/FVMsFtHxC%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107德国 
hysteria2://BQxzZppGYcsDXVpIu@37.114.49.234:26102?insecure=1&sni=cm1.awslcn.info&alpn=&fp=&obfs=salamander&obfs-password=EBgBw91iQrTxWk9MI5mFciz7KDzLt7c3S9j&mport=&os=#1107德国 
trojan://d34ad3a0-7172-4ff2-b627-599f66ec0d8c@37.114.49.234:31363?flow=&security=tls&sni=cm1.awslcn.info&type=ws&header=none&host=cm1.awslcn.info&path=/gTlb0sMrPDDc%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107德国 
trojan://cdd671d1-18c0-4581-a8ec-01d24673cdc0@37.114.49.234:21992?flow=&security=tls&sni=cm1.awslcn.info&type=ws&header=none&host=cm1.awslcn.info&path=/rZYfkJjqiKi%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107德国 
hysteria2://iQagbAKtu4DmyvgCNeVrkM0WTRZzgQD8a@37.114.49.234:6934?insecure=1&sni=cm1.awslcn.info&alpn=&fp=&obfs=salamander&obfs-password=cJB7h8Mny8eyFXNZ4OnSU&mport=&os=#1107德国 
hysteria2://hDtb38j2IArH4laSpMIR81oPRYdbawHCK3V45Lj5@37.114.49.234:2756?insecure=1&sni=cm1.awslcn.info&alpn=&fp=&obfs=salamander&obfs-password=ywZTis80D4odwkZFa5BWhQCFBqj&mport=&os=#1107德国 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@173.245.58.158:443?flow=&encryption=none&security=tls&sni=ver.vmkc9.netlib.re&type=xhttp&host=ver.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107德国 
trojan://00dae2de-d3a0-43ae-b66d-6e05621b1b5c@37.114.49.234:13377?flow=&security=tls&sni=cm1.awslcn.info&type=ws&header=none&host=cm1.awslcn.info&path=/J3OzYUZ%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107德国 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@188.114.98.202:443?flow=&encryption=none&security=tls&sni=ver.vmkc9.netlib.re&type=xhttp&host=ver.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107德国 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@104.27.104.179:443?flow=&encryption=none&security=tls&sni=ver.vmkc9.netlib.re&type=xhttp&host=ver.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjM3LjExNC40OS4yMzQiLCJwb3J0Ijo4NDA2LCJzY3kiOiJhdXRvIiwicHMiOiIxMTA35b635Zu9IiwibmV0Ijoid3MiLCJpZCI6IjE2ZDhkZTIwLWU5ZmUtNDM5Yy04OTkwLTA0MDU1NTYzZDU2MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiY20xLmF3c2xjbi5pbmZvIiwicGF0aCI6Ii9pa3VCN2dpYzl3d3RrRVpFOW9LRFVHZ3hSVnllNj9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiY20xLmF3c2xjbi5pbmZvIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
hysteria2://0ixfJe5TCWmntJpMMutDPmz@37.114.49.234:12543?insecure=1&sni=cm1.awslcn.info&alpn=&fp=&obfs=salamander&obfs-password=NMPRzZDe3sWSXcJiOhSSbIXDuQSs&mport=&os=#1107德国 
anytls://PjQ4USQvHoROPWqIBXDLwTK0JbptzvhjALId@37.114.49.234:60239?insecure=1&sni=cm1.awslcn.info&alpn=h2&fp=&os=#1107德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjM3LjExNC40OS4yMzQiLCJwb3J0Ijo2MTg4Niwic2N5IjoiYXV0byIsInBzIjoiMTEwN+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJkMzRhZDNhMC03MTcyLTRmZjItYjYyNy01OTlmNjZlYzBkOGMiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImNtMS5hd3NsY24uaW5mbyIsInBhdGgiOiIvZDg3RHNPTTRRZjhPdldDQ3puMjBpMDdyP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJjbTEuYXdzbGNuLmluZm8iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@173.245.58.127:443?flow=&encryption=none&security=tls&sni=ver.vmkc9.netlib.re&type=xhttp&host=ver.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107德国 
hysteria2://CA5HiSfFZtukC9Q2r6I@37.114.49.234:48246?insecure=1&sni=cm1.awslcn.info&alpn=&fp=&obfs=salamander&obfs-password=iGLeFxna3ss4QqTJcXf2n6t&mport=&os=#1107德国 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@198.41.202.17:443?flow=&encryption=none&security=tls&sni=ver.vmkc9.netlib.re&type=xhttp&host=ver.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107德国 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@104.27.29.71:443?flow=&encryption=none&security=tls&sni=ver.vmkc9.netlib.re&type=xhttp&host=ver.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107德国 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@104.25.22.17:443?flow=&encryption=none&security=tls&sni=ver.vmkc9.netlib.re&type=xhttp&host=ver.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107德国 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@173.245.59.97:443?flow=&encryption=none&security=tls&sni=ver.vmkc9.netlib.re&type=xhttp&host=ver.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107德国 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@103.21.244.144:443?flow=&encryption=none&security=tls&sni=ver.vmkc9.netlib.re&type=xhttp&host=ver.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107德国 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@198.41.209.186:443?flow=&encryption=none&security=tls&sni=ver.vmkc9.netlib.re&type=xhttp&host=ver.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107德国 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@104.16.244.36:443?flow=&encryption=none&security=tls&sni=ver.vmkc9.netlib.re&type=xhttp&host=ver.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107德国 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@104.27.4.50:443?flow=&encryption=none&security=tls&sni=ver.vmkc9.netlib.re&type=xhttp&host=ver.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107德国 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@162.159.251.147:443?flow=&encryption=none&security=tls&sni=ver.vmkc9.netlib.re&type=xhttp&host=ver.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107德国 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@198.41.196.251:443?flow=&encryption=none&security=tls&sni=ver.vmkc9.netlib.re&type=xhttp&host=ver.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1107德国 



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
