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


ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.142:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1102越南 
vless://0f4f3a75-ae36-4992-8cb5-6638f45afcb2@216.133.148.215:36987?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102美国 
hysteria2://6286105c-fb6d-11ef-be96-f23c93136cb3@227fd503-t4ssg0-t5vo4i-4550.la.shifen.uk:1743?insecure=0&sni=&alpn=&fp=&mport=&os=#1102美国 
hysteria2://17cdeb6c-f046-11ee-bdac-f23c93141fad@3d2c11f1-t52o00-tdw2ye-2gok.la.shifen.uk:1743?insecure=0&sni=&alpn=&fp=&mport=&os=#1102美国 
vless://a25ff90c-964c-485a-b72a-858864a27dc0@69.84.182.18:443?flow=&encryption=none&security=tls&sni=cdn-node-oss-63.paofu.de&type=ws&host=cdn-node-oss-63.paofu.de&path=/profile/sharenode&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#1102美国 
hysteria2://537d7098-fdbe-11ef-8ebc-f23c93141fad@6e206c57-t3b340-tcj7b6-d70y.la.shifen.uk:1743?insecure=0&sni=&alpn=&fp=&mport=&os=#1102美国 
hysteria2://17cdeb6c-f046-11ee-bdac-f23c93141fad@c37b0be5-t3kyo0-t3lvgh-2gok.la.shifen.uk:1743?insecure=0&sni=&alpn=&fp=&mport=&os=#1102美国 
hysteria2://6286105c-fb6d-11ef-be96-f23c93136cb3@cc65f71a-t4v9c0-t5waci-4550.la.shifen.uk:1743?insecure=0&sni=&alpn=&fp=&mport=&os=#1102美国 
hysteria2://537d7098-fdbe-11ef-8ebc-f23c93141fad@dcc40639-t3cxs0-tcj7b6-d70y.la.shifen.uk:1743?insecure=0&sni=&alpn=&fp=&mport=&os=#1102美国 
hysteria2://df7bed3c-06eb-11f0-8ebc-f23c93141fad@e10829f0-t4un40-t9lb2a-1glq.la.shifen.uk:1743?insecure=0&sni=&alpn=&fp=&mport=&os=#1102美国 
hysteria2://be8cc8f6-0c6a-11f0-a5a3-f23c93141fad@ea9466bf-t3dk00-t3i5yp-b4pt.la.shifen.uk:1743?insecure=0&sni=&alpn=&fp=&mport=&os=#1102美国 
hysteria2://1b609740-eec2-11ef-8543-f23c93136cb3@eb8d3417-t4teo0-tdtx5w-au6.la.shifen.uk:1743?insecure=0&sni=&alpn=&fp=&mport=&os=#1102美国 
hysteria2://712bdc36-24be-11ee-be53-f23c9313b177@fe1d6996-t4v9c0-tcl9of-5fdt.la.shifen.uk:1743?insecure=0&sni=&alpn=&fp=&mport=&os=#1102美国 
vless://188f8a72-6b58-4cf2-ab66-766a9388e6ba@103.173.178.215:39738?flow=&encryption=none&security=tls&sni=5c8d.fsafasdfas.online&type=ws&host=5c8d.fsafasdfas.online&path=telegram%F0%9F%87%A8%F0%9F%87%B3%40wangcai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102新加坡 
trojan://bca467b8c15211d189008a93c7519d3b@117.172.176.24:2283?flow=&security=tls&sni=www.nintendogames.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#1102新加坡 
trojan://bca467b8c15211d189008a93c7519d3b@117.172.176.24:2283?flow=&security=tls&sni=www.nintendogames.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102新加坡 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTowMTRlOTBkZi1hM2VlLTQ2NTQtYTlmNi1kMTE4ZTAyZGQwMmE=@sl.fgmcx.top:41047?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1102新加坡 
vmess://eyJ2IjoiMiIsImFkZCI6IjE1Mi43MC45Mi42OSIsInBvcnQiOjgwLCJzY3kiOiJhdXRvIiwicHMiOiIxMTAy6Z+p5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJiYjljMzk5My1hNGI5LTRkYWQtYWViOS1hYzg2MzcxYWU2OGIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJodHRwIiwiaG9zdCI6IiIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@218.237.185.230:4652?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1102韩国 
trojan://bca467b8c15211d189008a93c7519d3b@117.172.176.24:1332?flow=&security=tls&sni=www.nintendogames.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#1102日本 
trojan://bca467b8c15211d189008a93c7519d3b@117.172.176.24:1332?flow=&security=tls&sni=www.nintendogames.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102日本 
vmess://eyJ2IjoiMiIsImFkZCI6IjAwNzExNzU4LXN2YTc0MC10YnJoY2stMXRocWIuaGszLnA1cHYuY29tIiwicG9ydCI6ODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMDLpppnmuK8iLCJuZXQiOiJ3cyIsImlkIjoiNGY0YzY4NzYtZmNmNi0xMWVmLTk0YWEtZjIzYzkxM2M4ZDJiIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJicm9hZGNhc3Rsdi5jaGF0LmJpbGliaWxpLmNvbSIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwMy4yNDMuMjYuMjA5IiwicG9ydCI6ODA4MCwic2N5IjoiYXV0byIsInBzIjoiMTEwMummmea4ryIsIm5ldCI6InRjcCIsImlkIjoiYmM3ZTY4NDAtYWI4My00NTcwLWVhYWUtZDlhZmYxZTJkYTA5IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoiaHR0cCIsImhvc3QiOiIxMDMuMjQzLjI2LjIwOSIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://BxceQaOe@203.198.122.129:443?flow=&security=tls&sni=203.198.122.129&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102香港 
trojan://BxceQaOe@203.198.122.129:443?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102香港 
vmess://eyJ2IjoiMiIsImFkZCI6IjM2LjEzMy43My4zNiIsInBvcnQiOjExODE5LCJzY3kiOiJhdXRvIiwicHMiOiIxMTAy6aaZ5rivIiwibmV0IjoidGNwIiwiaWQiOiJkZTMyNzUyYy0wNjYxLTQ2N2UtODJkMy0zNWJjNzQwYTc4N2YiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjM2LjEzMy43My4zNiIsInBvcnQiOjExODE5LCJzY3kiOiJhdXRvIiwicHMiOiIxMTAy6aaZ5rivIiwibmV0IjoidGNwIiwiaWQiOiJkZTMyNzUyYy0wNjYxLTQ2N2UtODJkMy0zNWJjNzQwYTc4N2YiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IjM2LjEzMy43My4zNiIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjM2LjEzMy43My4zNiIsInBvcnQiOjExODE5LCJzY3kiOiJhdXRvIiwicHMiOiIxMTAy6aaZ5rivIiwibmV0IjoidGNwIiwiaWQiOiJkZTMyNzUyYy0wNjYxLTQ2N2UtODJkMy0zNWJjNzQwYTc4N2YiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://BxceQaOe@36.151.192.242:194?flow=&security=tls&sni=36.151.192.242&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102香港 
trojan://BxceQaOe@36.151.192.242:194?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102香港 
trojan://BxceQaOe@36.151.192.242:4556?flow=&security=tls&sni=36.151.192.242&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102香港 
trojan://BxceQaOe@36.151.192.242:4556?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102香港 
vmess://eyJ2IjoiMiIsImFkZCI6IjQzLjI0Ny4xMzQuMjEzIiwicG9ydCI6NTk1MTYsInNjeSI6ImF1dG8iLCJwcyI6IjExMDLpppnmuK8iLCJuZXQiOiJ0Y3AiLCJpZCI6IjI5MDZlMTllLWM5OWYtNDU2ZS1iY2IzLWM1NDcyZmQ1OTRlNSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Imh0dHAiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
trojan://BxceQaOe@58.152.46.98:443?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102香港 
trojan://BxceQaOe@58.152.46.98:443?flow=&security=tls&sni=58.152.46.98&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102香港 
trojan://bca467b8c15211d189008a93c7519d3b@58.152.53.42:443?flow=&security=tls&sni=www.nintendogames.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#1102香港 
trojan://bca467b8c15211d189008a93c7519d3b@58.152.53.42:443?flow=&security=tls&sni=www.nintendogames.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102香港 
vmess://eyJ2IjoiMiIsImFkZCI6IjdmMzQ2MjM1LXN2NG40MC10NzZ4Mmktd2o2di5oazMucDVwdi5jb20iLCJwb3J0Ijo4MCwic2N5IjoiYXV0byIsInBzIjoiMTEwMummmea4ryIsIm5ldCI6IndzIiwiaWQiOiI4NDdjMDNiMi0wYTlkLTExZWItYThiZi1mMjNjOTFjZmJiYzkiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJyb2FkY2FzdGx2LmNoYXQuYmlsaWJpbGkuY29tIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgwZjA4MDZkLXN6Zzc0MC10NDFwNHktMWhwbzAuaGszLnA1cHYuY29tIiwicG9ydCI6ODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMDLpppnmuK8iLCJuZXQiOiJ3cyIsImlkIjoiYzNkYzhkMjYtYWIyYi0xMWVjLWE4YmYtZjIzYzkxY2ZiYmM5IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJicm9hZGNhc3Rsdi5jaGF0LmJpbGliaWxpLmNvbSIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjhlNDJmOGQxLXN2MHhzMC1zenhoOXctNDZnYy5oazMucDVwdi5jb20iLCJwb3J0Ijo4MCwic2N5IjoiYXV0byIsInBzIjoiMTEwMummmea4ryIsIm5ldCI6IndzIiwiaWQiOiIyMjVkMWNjYS1kNzQ0LTExZWYtYjc5MC1mMjNjOTFjZmJiYzkiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJyb2FkY2FzdGx2LmNoYXQuYmlsaWJpbGkuY29tIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6ImE0ZjI5NzhlLXN2YTc0MC10NDhpeTctZ3lkaC5oazMucDVwdi5jb20iLCJwb3J0Ijo4MCwic2N5IjoiYXV0byIsInBzIjoiMTEwMummmea4ryIsIm5ldCI6IndzIiwiaWQiOiJiNjhmNGI0Yy0yZDAyLTExZWMtOWVlOC1mMjNjOTEzYzhkMmIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJyb2FkY2FzdGx2LmNoYXQuYmlsaWJpbGkuY29tIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6ImRkMmQyM2M3LXQwNDlzMC10MXA4cWwtMXQ4cTMuaGszLnA1cHYuY29tIiwicG9ydCI6ODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMDLpppnmuK8iLCJuZXQiOiJ3cyIsImlkIjoiNzc1YmFhNGEtZDc1Yi0xMWVmLWExMWEtZjIzYzkxM2M4ZDJiIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJicm9hZGNhc3Rsdi5jaGF0LmJpbGliaWxpLmNvbSIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://adbac894-90b9-4913-b77e-a715a8d4ebc8@oss-cn-shanghai.letssepub.com:20021?flow=&security=tls&sni=dingding-doc.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102香港 
trojan://adbac894-90b9-4913-b77e-a715a8d4ebc8@oss-cn-shanghai.letssepub.com:20021?flow=&security=tls&sni=oss-cn-shanghai.letssepub.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102香港 
vmess://eyJ2IjoiMiIsImFkZCI6InY5LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA5LCJzY3kiOiJhdXRvIiwicHMiOiIxMTAy6aaZ5rivIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoiYmFpZHUuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://b27e35a7-51f4-468e-8921-56a4901dd923@199.34.230.114:2053?flow=&encryption=none&security=tls&sni=om1.omidsuccess.uk&type=ws&host=om1.omidsuccess.uk&path=/containers/de&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102德国 
vless://b27e35a7-51f4-468e-8921-56a4901dd923@199.34.230.114:2053?flow=&encryption=none&security=tls&sni=om1.omidsuccess.uk&type=ws&host=om1.omidsuccess.uk&path=/containers/de&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102德国 
vless://b27e35a7-51f4-468e-8921-56a4901dd923@199.34.230.114:2053?flow=&encryption=none&security=tls&sni=om1.omidsuccess.uk&type=ws&host=om1.omidsuccess.uk&path=/containers/de&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#1102德国 
vmess://eyJ2IjoiMiIsImFkZCI6Ijc3LjM3LjMzLjI1IiwicG9ydCI6ODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMDLlvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiZDk2N2ZmY2EtZGU5MC00ZGFhLWJkMDAtZDUyN2U1YmFlMTFmIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJnb29nbGUud2hhdHNhcHAuc25hcHAudG9yb2IuYmFzYWxhbS5sZW9zaG9wcGluZzc3LmlyLiIsInBhdGgiOiIvP0JJQV9URUxFR1JBTShAQVpBUkJBWUpBQjEpVE0oQEFaQVJCQVlKQUIxKVRNKEBBWkFSQkFZSkFCMSlUTShAQVpBUkJBWUpBQjEpVE0oQEFaQVJCQVlKQUIxKVRNKEBBWkFSQkFZSkFCMSkiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6Ijc3LjM3LjMzLjY3IiwicG9ydCI6ODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMDLlvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiZDk2N2ZmY2EtZGU5MC00ZGFhLWJkMDAtZDUyN2U1YmFlMTFmIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJnb29nbGUud2hhdHNhcHAuc25hcHAudG9yb2IuYmFzYWxhbS5sZW9zaG9wcGluZzc3LmlyLiIsInBhdGgiOiIvP0JJQV9URUxFR1JBTShAQVpBUkJBWUpBQjEpVE0oQEFaQVJCQVlKQUIxKVRNKEBBWkFSQkFZSkFCMSlUTShAQVpBUkJBWUpBQjEpVE0oQEFaQVJCQVlKQUIxKVRNKEBBWkFSQkFZSkFCMSkiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://3a47b7e2-ca09-49d4-b752-e01acf86b80b@104.23.99.41:443?flow=&encryption=none&security=tls&sni=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&type=xhttp&host=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&path=/%3FtunnelId%3Db74887b60&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjM3LjExNC40OS4xMTciLCJwb3J0IjoxOTIyOCwic2N5IjoiYXV0byIsInBzIjoiMTEwMuW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJlNDVjM2FkYi00ZTIwLTRkMWItYWFjZi05NzQ3YmIxN2I3ZTciLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InNzY2EuaXJ1bmRucy5uZXQiLCJwYXRoIjoiL0tOeE5PRm1nNlo/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6InNzY2EuaXJ1bmRucy5uZXQiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
hysteria2://RoErfo1wj7oXNxxykK61vOzAghxFmUa7A1oN3@37.114.49.117:17139?insecure=1&sni=ssca.irundns.net&alpn=&fp=&obfs=salamander&obfs-password=W9ICfYNqB3CGhhUQbN&mport=&os=#1102德国 
anytls://oRet2qA4Jzegx5hY0QlQ3bYjnwWBHjm5@37.114.49.117:46768?insecure=1&sni=ssca.irundns.net&alpn=h2&fp=&os=#1102德国 
vless://3a47b7e2-ca09-49d4-b752-e01acf86b80b@162.159.252.125:443?flow=&encryption=none&security=tls&sni=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&type=xhttp&host=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&path=/%3FtunnelId%3Db74887b60&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102德国 
vless://3a47b7e2-ca09-49d4-b752-e01acf86b80b@104.27.6.183:443?flow=&encryption=none&security=tls&sni=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&type=xhttp&host=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&path=/%3FtunnelId%3Db74887b60&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102德国 
vless://3a47b7e2-ca09-49d4-b752-e01acf86b80b@104.19.133.213:443?flow=&encryption=none&security=tls&sni=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&type=xhttp&host=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&path=/%3FtunnelId%3Db74887b60&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102德国 
hysteria2://eVt5ustHpN84fpJfK8WQhJWNCIAhf5Kbnl54@37.114.49.117:53739?insecure=1&sni=ssca.irundns.net&alpn=&fp=&obfs=salamander&obfs-password=uBnJAfuWfbb8jm1cTAmnL7z&mport=&os=#1102德国 
anytls://KuDisNHdOwnmt5zdYn@37.114.49.117:65499?insecure=1&sni=ssca.irundns.net&alpn=h2&fp=&os=#1102德国 
vless://3a47b7e2-ca09-49d4-b752-e01acf86b80b@103.21.244.86:443?flow=&encryption=none&security=tls&sni=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&type=xhttp&host=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&path=/%3FtunnelId%3Db74887b60&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102德国 
vless://3a47b7e2-ca09-49d4-b752-e01acf86b80b@188.114.98.101:443?flow=&encryption=none&security=tls&sni=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&type=xhttp&host=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&path=/%3FtunnelId%3Db74887b60&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102德国 
vless://3a47b7e2-ca09-49d4-b752-e01acf86b80b@198.41.196.128:443?flow=&encryption=none&security=tls&sni=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&type=xhttp&host=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&path=/%3FtunnelId%3Db74887b60&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjM3LjExNC40OS4xMTciLCJwb3J0Ijo1NzAzNCwic2N5IjoiYXV0byIsInBzIjoiMTEwMuW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJhZmU2NWM1Yi1kYjI2LTQwN2ItYWI5MC0yNTEwYWUzNmYzNDMiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InNzY2EuaXJ1bmRucy5uZXQiLCJwYXRoIjoiLzlvNnRNU2pkTmR2eWM5TkwwUkl2P2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJzc2NhLmlydW5kbnMubmV0IiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
hysteria2://tl0zSpjaOdxNqCNzS3z35ViWbOlpQIpoNTM0@37.114.49.117:52855?insecure=1&sni=ssca.irundns.net&alpn=&fp=&obfs=salamander&obfs-password=rHmwTnGifWFdCqzR1&mport=&os=#1102德国 
vless://3a47b7e2-ca09-49d4-b752-e01acf86b80b@141.101.121.129:443?flow=&encryption=none&security=tls&sni=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&type=xhttp&host=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&path=/%3FtunnelId%3Db74887b60&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102德国 
vless://3a47b7e2-ca09-49d4-b752-e01acf86b80b@104.25.94.26:443?flow=&encryption=none&security=tls&sni=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&type=xhttp&host=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&path=/%3FtunnelId%3Db74887b60&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102德国 
vless://3a47b7e2-ca09-49d4-b752-e01acf86b80b@104.20.251.171:443?flow=&encryption=none&security=tls&sni=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&type=xhttp&host=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&path=/%3FtunnelId%3Db74887b60&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102德国 
vless://3a47b7e2-ca09-49d4-b752-e01acf86b80b@141.101.113.130:443?flow=&encryption=none&security=tls&sni=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&type=xhttp&host=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&path=/%3FtunnelId%3Db74887b60&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102德国 
vless://3a47b7e2-ca09-49d4-b752-e01acf86b80b@104.20.51.130:443?flow=&encryption=none&security=tls&sni=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&type=xhttp&host=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&path=/%3FtunnelId%3Db74887b60&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102德国 
vless://3a47b7e2-ca09-49d4-b752-e01acf86b80b@103.21.244.155:443?flow=&encryption=none&security=tls&sni=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&type=xhttp&host=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&path=/%3FtunnelId%3Db74887b60&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102德国 
hysteria2://joMd8MsTLV6of1GsaX3J4Zw7YR6xDRY8QUN@37.114.49.117:31834?insecure=1&sni=ssca.irundns.net&alpn=&fp=&obfs=salamander&obfs-password=JCEwXr7E0kq3ishJ77V6CR4XKdDKnxNDUEHkDbx&mport=&os=#1102德国 
vless://3a47b7e2-ca09-49d4-b752-e01acf86b80b@104.25.160.84:443?flow=&encryption=none&security=tls&sni=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&type=xhttp&host=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&path=/%3FtunnelId%3Db74887b60&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102德国 
vless://3a47b7e2-ca09-49d4-b752-e01acf86b80b@188.114.96.253:443?flow=&encryption=none&security=tls&sni=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&type=xhttp&host=a.8.b.3.0.8.0.0.0.0.7.4.0.1.0.0.2.ip6.arpa&path=/%3FtunnelId%3Db74887b60&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1102德国 

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
