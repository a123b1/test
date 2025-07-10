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

vmess://eyJ2IjoiMiIsImFkZCI6IjExMS4yNi4xMDkuNzkiLCJwb3J0IjozMDg0MCwic2N5IjoiYXV0byIsInBzIjoiMDcwOee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaTEwMC1jb3JlLXF1aWMtbGYuYW1lbXYuY29tIiwicGF0aCI6Ii9pbmRleCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://ea286109-d20f-415e-849e-4af20ab04b65@8.210.29.68:443?flow=&encryption=none&security=tls&sni=147135001195.sec22org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709美国 
vless://6337837a-2b47-4e0d-a695-75c5a4a8ad51@45.144.167.46:19816?flow=&encryption=none&security=tls&sni=rs-hk.lzjnb.shop&type=ws&host=rs-hk.lzjnb.shop&path=/lzjjjj666&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709香港 
vless://0eb8618b-69d5-482a-b701-0b3be31870eb@118.163.37.32:81?flow=&encryption=none&security=tls&sni=interior-xenia-vz-ee01649f.koyeb.app&type=ws&host=interior-xenia-vz-ee01649f.koyeb.app&path=/vl&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709美国 
vless://ffcf7ec1-3e09-4821-b3d9-b426a107b73b@172.67.220.32:443?flow=&encryption=none&security=tls&sni=xXCvVBNhJ.999836.XYz&type=ws&host=xxcvvbnhj.999836.xyz&path=/O9jlBCbIm3xr1D40NK&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709美国 
vless://07a3df8f-2a2c-42f8-ad92-65889d90f3bf@104.21.69.41:443?flow=&encryption=none&security=tls&sni=DdDFRt5.890602.xyZ&type=ws&host=dddfrt5.890602.xyz&path=/5UW2C42lpZ7Dj4VDwVOkZfoq&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709美国 
vless://2d068083-2cb0-4ae3-a44a-6fc82f3039cc@104.21.38.90:443?flow=&encryption=none&security=tls&sni=DDDCccdVfg.222856.xYZ&type=ws&host=dddcccdvfg.222856.xyz&path=/laTDC7FYNlEa06b88JSo&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709美国 
vless://c226ac5d-65e9-4379-95c3-fb542bc242d8@172.67.130.204:443?flow=&encryption=none&security=tls&sni=HHhhhHhhhhH.777198.xYz&type=ws&host=hhhhhhhhhhh.777198.xyz&path=/OjdW89Bpg4ykd4O&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709美国 
vless://cf8c791e-9d0b-4e90-aaf6-41ac62468416@172.67.216.240:443?flow=&encryption=none&security=tls&sni=eeeEeR.857856.XyZ&type=ws&host=eeeeer.857856.xyz&path=/dtBdvnoJO8180gomOew3d&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709美国 
vless://7248e825-887c-48b9-83bc-c26bc6392bf8@172.67.214.21:443?flow=&encryption=none&security=tls&sni=XxcvfGT678.191268.Xyz&type=ws&host=xxcvfgt678.191268.xyz&path=/W02wBrOOqlSUywV3ibrzzKXJGy3S1&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709美国 
vless://662e38ba-8427-4955-94aa-76f5347a0ce8@172.67.149.202:443?flow=&encryption=none&security=tls&sni=OooIIi.222560.xyz&type=ws&host=oooiii.222560.xyz&path=/6DuxYMYmrGrnGKRtF5UvWyyVQu&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709美国 
vless://57c4f3b6-19bd-493e-bf85-aa4a92cc20e7@172.67.187.28:443?flow=&encryption=none&security=tls&sni=nnNnNnnnNnNnhhY.IRAN2035.DPDNs.oRg&type=ws&host=nnnnnnnnnnnnhhy.iran2035.dpdns.org&path=/F8LFEGnyMsJ1ullAwKQmIGQ02idh&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709美国 
vless://c891d9fe-c4eb-4526-94e0-d9bf841c572a@104.21.61.229:443?flow=&encryption=none&security=tls&sni=WwSsDe.FreEVPN2027.DPdNS.oRG&type=ws&host=wwssde.freevpn2027.dpdns.org&path=/YVOu6Dbaf1WT6O9LnD&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709美国 
vless://89f4b265-9a4c-451d-9ca9-013fd65362ac@104.18.20.69:443?flow=&encryption=none&security=tls&sni=us4s.pqvip.top&type=ws&host=us4s.pqvip.top&path=/pq/us4&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709美国 
vless://662e38ba-8427-4955-94aa-76f5347a0ce8@172.67.131.76:443?flow=&encryption=none&security=tls&sni=rrRRrrrRrnNNNNnnmM.222767.xyz&type=ws&host=rrrrrrrrrnnnnnnnmm.222767.xyz&path=/6DuxYMYmrGrnGKRtF5UvWyyVQu&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQwIiwicG9ydCI6MzIyMDksInNjeSI6ImF1dG8iLCJwcyI6IjA3MDnmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjYzIiwicG9ydCI6Mzc3NTUsInNjeSI6ImF1dG8iLCJwcyI6IjA3MDnnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjEyMSIsInBvcnQiOjQ5OTEyLCJzY3kiOiJhdXRvIiwicHMiOiIwNzA5576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpmOGY3YUN6Y1BLYnNGOHAz@185.123.101.241:990?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0709土耳其 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQwIiwicG9ydCI6NTI1NTIsInNjeSI6ImF1dG8iLCJwcyI6IjA3MDnmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjEyMSIsInBvcnQiOjU5MjIyLCJzY3kiOiJhdXRvIiwicHMiOiIwNzA5576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjExMS4yNi4xMDkuNzkiLCJwb3J0IjozMDgwNywic2N5IjoiYXV0byIsInBzIjoiMDcwOee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjExMS4yNi4xMDkuNzkiLCJwb3J0IjozMDgyOSwic2N5IjoiYXV0byIsInBzIjoiMDcwOee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpCb2cwRUxtTU05RFN4RGRR@85.210.120.237:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0709英国 
trojan://d0d08cddacc3190ea81b1b792e1b5fde@36.151.192.27:51083?flow=&security=tls&sni=www.baidu.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709香港 
trojan://d0d08cddacc3190ea81b1b792e1b5fde@36.151.192.27:444?flow=&security=tls&sni=www.baidu.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709香港 
trojan://7367d04e-4c59-4dff-a50e-12e730a09891@155.117.228.70:26193?flow=&security=tls&sni=155.117.228.70&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709香港 
trojan://d0d08cddacc3190ea81b1b792e1b5fde@36.151.251.58:21829?flow=&security=tls&sni=www.baidu.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709日本 
trojan://d0d08cddacc3190ea81b1b792e1b5fde@36.151.192.27:53248?flow=&security=tls&sni=www.baidu.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709日本 
trojan://d0d08cddacc3190ea81b1b792e1b5fde@36.151.192.27:4448?flow=&security=tls&sni=www.baidu.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709韩国 
trojan://d0d08cddacc3190ea81b1b792e1b5fde@36.156.102.123:10600?flow=&security=tls&sni=www.baidu.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709新加坡 
trojan://d0d08cddacc3190ea81b1b792e1b5fde@36.151.192.27:4446?flow=&security=tls&sni=www.baidu.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709新加坡 
trojan://d0d08cddacc3190ea81b1b792e1b5fde@36.151.192.27:4447?flow=&security=tls&sni=www.baidu.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709美国 
trojan://d0d08cddacc3190ea81b1b792e1b5fde@36.156.102.123:8657?flow=&security=tls&sni=www.baidu.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709美国 
trojan://6757b7d6-fa32-4708-b5d1-30e3cf928b51@104.21.6.179:443?flow=&security=tls&sni=ZZzzzZZ.890601.XYZ&type=ws&header=none&host=&path=/l96MZ8se5Kl2p8BiMhP42l&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709美国 
trojan://ffcf7ec1-3e09-4821-b3d9-b426a107b73b@172.67.220.32:443?flow=&security=tls&sni=eEEfGty6.999836.XYz&type=ws&header=none&host=&path=/XmTzATQPJv9RO3xr1D40NK&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709美国 
trojan://f108e0e2-5f12-42b6-9e67-1b2f073ffb2b@172.67.219.196:443?flow=&security=tls&sni=CCcvfgt6.852224.dpdns.org&type=ws&header=none&host=&path=/CA5bMmr2JMum8sDKRwvFCJq&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709美国 
trojan://288124da-0d68-42f4-9f48-70dc4dcc55a6@104.21.77.79:443?flow=&security=tls&sni=SsXCDfR5.986986.shoP&type=ws&header=none&host=ssxcdfr5.986986.shop&path=/raChT39pjLFYRA5HdHEIupMZeK&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709加拿大 
trojan://47760ab9-662b-4d11-a44c-93fbf1da0ab7@109.71.253.98:60649?flow=&security=tls&sni=high.work.lzg.me&type=ws&header=none&host=high.work.lzg.me&path=/IIFwMldvIvbmGbrYcVE20zc6hQfZd7%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@198.41.196.144:443?flow=&encryption=none&security=tls&sni=cm5.vock33.qzz.io&type=xhttp&host=cm5.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709德国 
anytls://7CFEyydQBc3losehpXMZGRQYk6AuYK6BwMWY3tnl@109.71.253.98:18457?insecure=1&sni=high.work.lzg.me&alpn=h2&fp=&os=#0709德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.21.95.192:443?flow=&encryption=none&security=tls&sni=cm5.vock33.qzz.io&type=xhttp&host=cm5.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6YjljZGE5N2QtM2IwOC00M2I5LWE2ZDItOWI3M2YxYmVhNGY2QDEwOS43MS4yNTMuOTg6MTU5NzY6d3M6LzZ6eVdwNHJnJTNGZWQlM0QyNTYwOmhpZ2gud29yay5semcubWU6bm9uZTp0bHM6aGlnaC53b3JrLmx6Zy5tZTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0709德国 
anytls://EYaOh3ga5J2ffe6Ce89k5098T@109.71.253.98:38489?insecure=1&sni=high.work.lzg.me&alpn=h2&fp=&os=#0709德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuOTgiLCJwb3J0IjoyMjg2MSwic2N5IjoiYXV0byIsInBzIjoiMDcwOeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJiMzc4YzJlYS1lNTE3LTRlYTMtYjEwNy04NzgxYzc2NDI5MzMiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImhpZ2gud29yay5semcubWUiLCJwYXRoIjoiL2xCekV5b0NsWT9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiaGlnaC53b3JrLmx6Zy5tZSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.16.109.184:443?flow=&encryption=none&security=tls&sni=cm5.vock33.qzz.io&type=xhttp&host=cm5.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709德国 
hysteria2://eYopKxunYdQ3dULBdekTgtDdHPsp@109.71.253.98:56446?insecure=1&sni=high.work.lzg.me&alpn=&fp=&obfs=salamander&obfs-password=RdX73CFlEM3cYMZLnTlH3BQV1AdxdVrwAb6Z&mport=&os=#0709德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.16.2.114:443?flow=&encryption=none&security=tls&sni=cm5.vock33.qzz.io&type=xhttp&host=cm5.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuOTgiLCJwb3J0IjoyOTc4LCJzY3kiOiJhdXRvIiwicHMiOiIwNzA55b635Zu9IiwibmV0Ijoid3MiLCJpZCI6ImQ5M2RjMGQ4LWQxMGUtNGU2MC1iOTg1LTRjMTQ4MDVmZTE1ZSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiaGlnaC53b3JrLmx6Zy5tZSIsInBhdGgiOiIvRlo/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6ImhpZ2gud29yay5semcubWUiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
anytls://wj36mH2PsbBJdYYgzI3jc77yR@109.71.253.98:12882?insecure=1&sni=high.work.lzg.me&alpn=h2&fp=&os=#0709德国 
vless://f6cc439c-4cda-4077-a33e-f19ea940e535@109.71.253.98:37621?flow=&encryption=none&security=tls&sni=high.work.lzg.me&type=ws&host=high.work.lzg.me&path=/l0Oge2wdq1deLhxhr61sWlPDSod8c%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709德国 
vless://d93dc0d8-d10e-4e60-b985-4c14805fe15e@109.71.253.98:28055?flow=&encryption=none&security=tls&sni=high.work.lzg.me&type=ws&host=high.work.lzg.me&path=/EwOJupJAkNZBGxDUnvAZiJj1%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6YjM3OGMyZWEtZTUxNy00ZWEzLWIxMDctODc4MWM3NjQyOTMzQDEwOS43MS4yNTMuOTg6Mzc5OTY6d3M6L1NzQUw3RnZpUiUzRmVkJTNEMjU2MDpoaWdoLndvcmsubHpnLm1lOm5vbmU6dGxzOmhpZ2gud29yay5semcubWU6W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0709德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.59.32:443?flow=&encryption=none&security=tls&sni=cm5.vock33.qzz.io&type=xhttp&host=cm5.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709德国 
hysteria2://fknkpbVJeDGdJpyh0sA@109.71.253.98:55850?insecure=1&sni=high.work.lzg.me&alpn=&fp=&obfs=salamander&obfs-password=2rOcZBRiEii5eWwY&mport=&os=#0709德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@103.21.244.223:443?flow=&encryption=none&security=tls&sni=cm5.vock33.qzz.io&type=xhttp&host=cm5.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.19.254.193:443?flow=&encryption=none&security=tls&sni=cm5.vock33.qzz.io&type=xhttp&host=cm5.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuOTgiLCJwb3J0Ijo0MjM5NSwic2N5IjoiYXV0byIsInBzIjoiMDcwOeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJmNmNjNDM5Yy00Y2RhLTQwNzctYTMzZS1mMTllYTk0MGU1MzUiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImhpZ2gud29yay5semcubWUiLCJwYXRoIjoiL25LVk5XYzJrcm5SQ2RaelhYMz9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiaGlnaC53b3JrLmx6Zy5tZSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZDkzZGMwZDgtZDEwZS00ZTYwLWI5ODUtNGMxNDgwNWZlMTVlQDEwOS43MS4yNTMuOTg6NDAwMjY6d3M6L3d3Umw3Z0xkOE55M0F1M2lRMGR1NiUzRmVkJTNEMjU2MDpoaWdoLndvcmsubHpnLm1lOm5vbmU6dGxzOmhpZ2gud29yay5semcubWU6W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0709德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NTQwYWY0OGYtOTM0OS00YzNlLTk5OTgtODM4OWUxM2ZhNDg1QDEwOS43MS4yNTMuOTg6MjA4NjE6d3M6L0FybzNCNVhpVHpBS0RWN1ZhSE82TVNRVEpLY24lM0ZlZCUzRDI1NjA6aGlnaC53b3JrLmx6Zy5tZTpub25lOnRsczpoaWdoLndvcmsubHpnLm1lOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0709德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@172.66.216.95:443?flow=&encryption=none&security=tls&sni=cm5.vock33.qzz.io&type=xhttp&host=cm5.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@188.114.96.66:443?flow=&encryption=none&security=tls&sni=cm5.vock33.qzz.io&type=xhttp&host=cm5.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@198.41.199.217:443?flow=&encryption=none&security=tls&sni=cm5.vock33.qzz.io&type=xhttp&host=cm5.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709德国 
anytls://H0lzSdhYfPhaaj7pYs6QcMW4nhiL0iCGBlLNDCu@109.71.253.98:14998?insecure=1&sni=high.work.lzg.me&alpn=h2&fp=&os=#0709德国 
trojan://4581bc61-ef9e-41ac-9fb4-4621e4411d9a@109.71.253.98:41186?flow=&security=tls&sni=high.work.lzg.me&type=ws&header=none&host=high.work.lzg.me&path=/IRN1KDnjvvl1QQV4YMWeAo2AZ4Nyq%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709德国 
anytls://pzwM6I2eZ90YBmOjQmHuv4AcKhFBPN@109.71.253.98:16075?insecure=1&sni=high.work.lzg.me&alpn=h2&fp=&os=#0709德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@198.41.203.51:443?flow=&encryption=none&security=tls&sni=cm5.vock33.qzz.io&type=xhttp&host=cm5.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@172.66.45.147:443?flow=&encryption=none&security=tls&sni=cm5.vock33.qzz.io&type=xhttp&host=cm5.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709德国 
trojan://b9cda97d-3b08-43b9-a6d2-9b73f1bea4f6@109.71.253.98:24992?flow=&security=tls&sni=high.work.lzg.me&type=ws&header=none&host=high.work.lzg.me&path=/YtX2jZV2V1BKPgh%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709德国 
anytls://we4ARIINbtsPoJ1T6tcbJDluPgop@109.71.253.98:11822?insecure=1&sni=high.work.lzg.me&alpn=h2&fp=&os=#0709德国 
hysteria2://Dr3ks59KnjHEX82AIRKBf4TfI9ArfoPPfzQps4@109.71.253.98:64131?insecure=1&sni=high.work.lzg.me&alpn=&fp=&obfs=salamander&obfs-password=odgqjwuRNKK3afYiDUO8hkZ6EAO1HGlJC&mport=&os=#0709德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.18.172.121:443?flow=&encryption=none&security=tls&sni=cm5.vock33.qzz.io&type=xhttp&host=cm5.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709德国 
anytls://J5aqeFJ9h0F8TFMomBIwhVDOzg9c6qJhchxgjEf@109.71.253.98:33309?insecure=1&sni=high.work.lzg.me&alpn=h2&fp=&os=#0709德国 
hysteria2://SJ26LpvDyo1ogNzh2lG8U8cfQjDXfqyVUGg5CSE2@109.71.253.98:9282?insecure=1&sni=high.work.lzg.me&alpn=&fp=&obfs=salamander&obfs-password=hOPeUqQfGKjkbfgSY6uQQwV&mport=&os=#0709德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.16.228.174:443?flow=&encryption=none&security=tls&sni=cm5.vock33.qzz.io&type=xhttp&host=cm5.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709德国 
hysteria2://rTxPea1j0vcJzYSg82zXC@109.71.253.98:27941?insecure=1&sni=high.work.lzg.me&alpn=&fp=&obfs=salamander&obfs-password=s5zEJjWQ6SLeZijTH1Dx6OHmsp4VgWxz5tn&mport=&os=#0709德国 
hysteria2://kAZzXrYsqscCoR7G3z@109.71.253.98:9337?insecure=1&sni=high.work.lzg.me&alpn=&fp=&obfs=salamander&obfs-password=hkEPzarMhmJDFkQz3moA&mport=&os=#0709德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@162.159.254.11:443?flow=&encryption=none&security=tls&sni=cm5.vock33.qzz.io&type=xhttp&host=cm5.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuOTgiLCJwb3J0Ijo3MDU1LCJzY3kiOiJhdXRvIiwicHMiOiIwNzA55b635Zu9IiwibmV0Ijoid3MiLCJpZCI6IjQ3NzYwYWI5LTY2MmItNGQxMS1hNDRjLTkzZmJmMWRhMGFiNyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiaGlnaC53b3JrLmx6Zy5tZSIsInBhdGgiOiIvVDluNWdHblYyMkZnWkY/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6ImhpZ2gud29yay5semcubWUiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
hysteria2://j9BgFycuHzHq3Rs7PJHXCHIdIv4W5wVnZ0PADi@109.71.253.98:3961?insecure=1&sni=high.work.lzg.me&alpn=&fp=&obfs=salamander&obfs-password=vJoNr0eHFuYHJjtbW9kMlJ2BXepP&mport=&os=#0709德国 
vless://df82055b-17b8-43ed-9d85-e061a6f58049@109.71.253.98:28713?flow=&encryption=none&security=tls&sni=high.work.lzg.me&type=ws&host=high.work.lzg.me&path=/Ny2rAHYZKecaqwzJdTNGKVXh%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0709德国 
hysteria2://krPSxf8KODI2xsJkmhp19f8CRIfqxX@109.71.253.98:27377?insecure=1&sni=high.work.lzg.me&alpn=&fp=&obfs=salamander&obfs-password=dxDpZ1sLdx4JirbLUlJ1tXBGZmT20uascjZf&mport=&os=#0709德国 

 
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
