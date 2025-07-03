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
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@103.163.218.2:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0702越南 
vless://1343289b-3518-48da-9ee6-1bc99860b505@104.16.1.106:80?flow=&encryption=none&security=&sni=mrdnzdtnbkwbdfsqoncu.dissertationhelpspecialist.com&type=ws&host=mrdnzdtnbkwbdfsqoncu.dissertationhelpspecialist.com&path=/TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService-TwixService%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
vless://Parsashonam-273@104.17.147.22:2086?flow=&encryption=none&security=&sni=&type=ws&host=ws.DafieMikoneTheWeekendPlay.SpAcE.&path=/---Parsashonam---Parsashonam---Parsashonam---Parsashonam---Parsashonam---Parsashonam---Parsashonam---Parsashonam---Parsashonam%3Fed%3D2048&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702芬兰 
vless://a96cb093-b164-4bc6-bd27-deb0e385de07@104.21.68.76:443?flow=&encryption=none&security=tls&sni=DDDDdddD.222769.xYZ&type=ws&host=dddddddd.222769.xyz&path=/3zsSOohi9huFfjEPpIlRig3qizHXb&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702美国 
vless://c7f423b7-ced8-43da-a9ae-e906cb4a222c@104.21.89.221:443?flow=&encryption=none&security=tls&sni=KKkkKKKkkkkKLO.999824.xYz&type=ws&host=kkkkkkkkkkkklo.999824.xyz&path=/wU3lZaUTRQTqot0LE&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702美国 
vless://e4cbe8b8-37db-4aaa-8469-b84f34c51ebc@104.21.90.226:443?flow=&encryption=none&security=tls&sni=444RRrt5.7777155.xYZ&type=ws&host=444rrrt5.7777155.xyz&path=/6OWLjRc26b0nHYr5hYXD&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjExMS4yNi4xMDkuNzkiLCJwb3J0IjozMDgwNywic2N5IjoiYXV0byIsInBzIjoiMDcwMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjExMS4yNi4xMDkuNzkiLCJwb3J0IjozMDg0MCwic2N5IjoiYXV0byIsInBzIjoiMDcwMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaTEwMC1jb3JlLXF1aWMtbGYuYW1lbXYuY29tIiwicGF0aCI6Ii9pbmRleCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjExMS4yNi4xMDkuNzkiLCJwb3J0IjozMDgyOSwic2N5IjoiYXV0byIsInBzIjoiMDcwMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE3IiwicG9ydCI6NDY3NTksInNjeSI6ImF1dG8iLCJwcyI6IjA3MDLnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE3IiwicG9ydCI6NTg4ODIsInNjeSI6ImF1dG8iLCJwcyI6IjA3MDLnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1nY206ZHd6MUd0Rjc=@120.233.128.98:30015?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0702台湾 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@125.141.31.72:15098?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0702韩国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE1MDAyLmt1YWl5aW4wMi50b3AiLCJwb3J0IjoxNTAwMiwic2N5IjoiYXV0byIsInBzIjoiMDcwMuS/hOe9l+aWryIsIm5ldCI6InRjcCIsImlkIjoiOWY1MTMxNjEtNTc2Yi0zYWJjLTljOTgtMDZlNTJjM2EyNGM2IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIxNTAwMi5rdWFpeWluMDIudG9wIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://662e38ba-8427-4955-94aa-76f5347a0ce8@172.67.161.129:443?flow=&encryption=none&security=tls&sni=cCccCcCCV.666470.Xyz&type=ws&host=ccccccccv.666470.xyz&path=/6DuxYMYmrGrnGKRtF5UvWyyVQu&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702美国 
vless://c7f423b7-ced8-43da-a9ae-e906cb4a222c@172.67.191.140:443?flow=&encryption=none&security=tls&sni=SSssSSsssSsSsswwweR.999824.XYz&type=ws&host=sssssssssssssswwwer.999824.xyz&path=/wU3lZaUTRQTqot0LE&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702美国 
vless://a96cb093-b164-4bc6-bd27-deb0e385de07@172.67.191.174:443?flow=&encryption=none&security=tls&sni=DDDDdddD.222769.xYZ&type=ws&host=dddddddd.222769.xyz&path=/3zsSOohi9huFfjEPpIlRig3qizHXb&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702美国 
vless://cf8c791e-9d0b-4e90-aaf6-41ac62468416@172.67.216.240:443?flow=&encryption=none&security=tls&sni=eeeEeR.857856.XyZ&type=ws&host=eeeeer.857856.xyz&path=/dtBdvnoJO8180gomOew3d&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702美国 
vless://fa050497-fc2a-45ee-89c0-96670c4ecb65@172.67.218.209:443?flow=&encryption=none&security=tls&sni=pPP0.89890604.xYZ&type=ws&host=ppp0.89890604.xyz&path=/0USILhLWoWgQPuXTwt&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702美国 
hysteria2://915eb335-8524-447e-9197-465d4c63b16f@185.126.255.78:37058?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&mport=&os=#0702乌克兰 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.153.197.5:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0702摩尔多瓦 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0702波兰 
vless://bdbfd26c-725b-4922-b970-e7dfb46afb7b@219.76.13.166:443?flow=&encryption=none&security=tls&sni=edge.ekt.me&type=ws&host=edge.ekt.me&path=/socks5%3A//admin%3Aadmin%40206.237.13.40%3A1080&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702香港 
hysteria2://915eb335-8524-447e-9197-465d4c63b16f@23.132.228.217:26747?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&mport=&os=#0702意大利 
trojan://a698c4a6-c3c9-11ee-9693-f23c91cfbbc9@274ba953-sytz40-t09za6-1m0fq.cm5.cnkuaishou.com:27235?flow=&security=tls&sni=274ba953-sytz40-t09za6-1m0fq.cm5.cnkuaishou.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702法国 
vless://03e92910-34b1-4245-ac63-04a865f43cd5@3er4.4444916.xyz:443?flow=&encryption=none&security=tls&sni=3Er4.4444916.xYz&type=ws&host=3er4.4444916.xyz&path=/f7vKDX2UecxmlPhIJoo2wcE6Q&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702美国 
trojan://0de37cdc-abff-11ef-b7c6-f23c913c8d2b@57100505-sytz40-t389l0-1rsuw.cm5.cnkuaishou.com:27233?flow=&security=tls&sni=57100505-sytz40-t389l0-1rsuw.cm5.cnkuaishou.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702日本 
trojan://bcc58e88-e147-11ec-b286-f23c91cfbbc9@83242d49-sy41s0-szh3gf-ggww.cm5.cnkuaishou.com:21233?flow=&security=tls&sni=83242d49-sy41s0-szh3gf-ggww.cm5.cnkuaishou.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702马来西亚 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0702斯洛文尼亚共和国 
vless://0f5bd9ef-cba9-4867-a6cf-028077a3d840@94.232.168.16:30501?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702波兰 
vmess://eyJ2IjoiMiIsImFkZCI6IkZmZnZ2VmJuaEp1aTguMjIyNTYwLlhZeiIsInBvcnQiOjQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDcwMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI3NzAxZGRmNS02YTQ4LTQwMWItYTNlYy04YWY1MmI2ZGViNDgiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvbWx5UjV0bWNLeDNod2VCb3B1aFdFYklYIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://897a4bec-26b8-11e8-94be-00505695472c@bestcf.030101.xyz:443?flow=&encryption=none&security=tls&sni=xv6.jpmj.dpdns.org&type=ws&host=xv6.jpmj.dpdns.org&path=/bbs%3Fed%3D2048&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702美国 
vmess://eyJ2IjoiMiIsImFkZCI6ImNjNDI0ZGU0LXN3ZDM0MC1zd3AzZjMtMXRldWMuaGdjMS50Y3BiYnIubmV0IiwicG9ydCI6ODA4MCwic2N5IjoiYXV0byIsInBzIjoiMDcwMummmea4ryIsIm5ldCI6IndzIiwiaWQiOiJhNWE4MWEzNC1mMjU3LTExZWYtYmE4Mi1mMjNjOTEzYzhkMmIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://ce921385-2b31-45fe-84c5-1843e8ae845b@cccccccf.222769.xyz:443?flow=&encryption=none&security=tls&sni=ccCcCcCf.222769.Xyz&type=ws&host=cccccccf.222769.xyz&path=/1xrOld7e5RpK3I98dxLkez&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702美国 
ss://YWVzLTEyOC1nY206NDdhMWI4NmEtNzMxZi00NDY3LWFhNDAtZmI3OThiYzYzOTAy@d1.cloudtaste.xyz:52743?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0702美国 
trojan://2c605663-b89a-5734-a9d6-97d4743d72cf@dozo01.flztjc.top:8313?flow=&security=tls&sni=hk-13-568.flztjc.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702香港 
vless://a96cb093-b164-4bc6-bd27-deb0e385de07@eeeeeeeeed.999864.xyz:443?flow=&encryption=none&security=tls&sni=EEeeeEeEEd.999864.xyZ&type=ws&host=eeeeeeeeed.999864.xyz&path=/3zsSOohi9huFfjEPpIlRig3qizHXb&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702美国 
trojan://3f514ea2-4662-11ed-a8bf-f23c91cfbbc9@f01b2667-sytz40-szptnz-1kcpe.cm5.cnkuaishou.com:14234?flow=&security=tls&sni=f01b2667-sytz40-szptnz-1kcpe.cm5.cnkuaishou.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702印度尼西亚 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpmZWFmYzJlZi1kNWZkLTRmNmQtODAzYi1mYWQ0YTVjYzFmMGU=@h.cm2.xiaomi-api.xyz:19832?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0702日本 
vless://31961d72-b3df-4f0b-84c3-c4575b2b142b@newus-ceg5.555199.xyz:8443?flow=xtls-rprx-vision&encryption=none&security=tls&sni=ssl.wsfog.co.uk&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702美国 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMi5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgxMiwic2N5IjoiYXV0byIsInBzIjoiMDcwMuaWsOWKoOWdoSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYyOC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyOCwic2N5IjoiYXV0byIsInBzIjoiMDcwMumfqeWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InY0MC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDg0MCwic2N5IjoiYXV0byIsInBzIjoiMDcwMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaTEwMC1jb3JlLXF1aWMtbGYuYW1lbXYuY29tIiwicGF0aCI6Ii9pbmRleCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InY2LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA2LCJzY3kiOiJhdXRvIiwicHMiOiIwNzAy5pel5pysIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0Ijoib2NiYy5jb20iLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InY5LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA5LCJzY3kiOiJhdXRvIiwicHMiOiIwNzAy6aaZ5rivIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoiYmFpZHUuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IngxMC44NTk4ODUueFl6IiwicG9ydCI6NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwNzAy576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImRhMTI4MjQ2LTMzYjAtNGM4OC1hNDRlLWQ5MWU5ZTBhMWUwNSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoieDEwLjg1OTg4NS54eXoiLCJwYXRoIjoiLzBGaFVrcVFVZHhPaE1COUpzZ1Rhend6OSIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IngxMC44NTk4ODUueHl6IiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6Ing5Ljg1OTg4NS5YWXoiLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjA3MDLnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiZGExMjgyNDYtMzNiMC00Yzg4LWE0NGUtZDkxZTllMGExZTA1IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ4OS44NTk4ODUueHl6IiwicGF0aCI6Ii8wRmhVa3FRVWR4T2hNQjlKc2dUYXp3ejkiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ4OS44NTk4ODUueHl6IiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@172.66.31.125:443?flow=&encryption=none&security=tls&sni=top.vycodcx.dpdns.org&type=xhttp&host=top.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@172.67.192.86:443?flow=&encryption=none&security=tls&sni=top.vycodcx.dpdns.org&type=xhttp&host=top.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NzdiNWQzYzktMDBiOS00MDlmLTgwNDMtMTQzMjE5MzJlNThjQDQ1LjgyLjEyMS4yMzc6NjE3OTE6d3M6L0JHRCUzRmVkJTNEMjU2MDp3d3cuYW1lYmxvLmpwOm5vbmU6dGxzOnd3dy5hbWVibG8uanA6W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0702德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.23.117.19:443?flow=&encryption=none&security=tls&sni=top.vycodcx.dpdns.org&type=xhttp&host=top.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.26.13.81:443?flow=&encryption=none&security=tls&sni=top.vycodcx.dpdns.org&type=xhttp&host=top.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.21.205.14:443?flow=&encryption=none&security=tls&sni=top.vycodcx.dpdns.org&type=xhttp&host=top.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4yMzciLCJwb3J0IjoxODg0Nywic2N5IjoiYXV0byIsInBzIjoiMDcwMuW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI3N2I1ZDNjOS0wMGI5LTQwOWYtODA0My0xNDMyMTkzMmU1OGMiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5hbWVibG8uanAiLCJwYXRoIjoiL2J5P2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ3d3cuYW1lYmxvLmpwIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4yMzciLCJwb3J0IjoxMTI4NCwic2N5IjoiYXV0byIsInBzIjoiMDcwMuW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJhNGRjMzgwMS05ZWUwLTQzYTItOTUzMS02NGQ0MGM4OTQ1YjYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5hbWVibG8uanAiLCJwYXRoIjoiL1cxN3VJeXpWYjFtOWNUWTFBU1h1MzhKWTc/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6Ind3dy5hbWVibG8uanAiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4yMzciLCJwb3J0Ijo2MTczOSwic2N5IjoiYXV0byIsInBzIjoiMDcwMuW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIwMTExMzMxMS1hMzBjLTRiOTUtYjFiZC03NzEzYzM2YmU3MTAiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5hbWVibG8uanAiLCJwYXRoIjoiL1E5dzRxZUh0ekdER2JmP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ3d3cuYW1lYmxvLmpwIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
hysteria2://ftg8hDewhhi2sl8ZJCTcLxAJ4kXVraAKk0LF4@45.82.121.237:26976?insecure=1&sni=www.ameblo.jp&alpn=&fp=&obfs=salamander&obfs-password=4rtRX0AacktTeyvVk&mport=&os=#0702德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@103.21.244.237:443?flow=&encryption=none&security=tls&sni=top.vycodcx.dpdns.org&type=xhttp&host=top.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
vless://3de085ee-1986-4592-957a-7fbe455992cc@45.82.121.237:8016?flow=&encryption=none&security=tls&sni=www.ameblo.jp&type=ws&host=www.ameblo.jp&path=/LeZMTdlB%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
anytls://CaT3yMmeziCviescWitdnGUMHVjuagfgUOI@45.82.121.237:46984?insecure=1&sni=www.ameblo.jp&alpn=h2&fp=&os=#0702德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@198.41.198.174:443?flow=&encryption=none&security=tls&sni=top.vycodcx.dpdns.org&type=xhttp&host=top.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZDZiMTExM2QtZGM3MC00YjY4LTkzNTEtMmQ1OTAyNWQwNmI1QDQ1LjgyLjEyMS4yMzc6MjY1NjE6d3M6LzNLM0ltRlVJajA4eSUzRmVkJTNEMjU2MDp3d3cuYW1lYmxvLmpwOm5vbmU6dGxzOnd3dy5hbWVibG8uanA6W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0702德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.20.208.177:443?flow=&encryption=none&security=tls&sni=top.vycodcx.dpdns.org&type=xhttp&host=top.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
hysteria2://10V0hPWFQ6o99N1tiBINIh7YXXau@45.82.121.237:12906?insecure=1&sni=www.ameblo.jp&alpn=&fp=&obfs=salamander&obfs-password=Wbc7UbNMFGkUrAtcH38Ut2SO0op1qJVIVlG&mport=&os=#0702德国 
hysteria2://rG92kTv73HBKOTynwyg2X1lIMf5Omq5RcHS9K58@45.82.121.237:48826?insecure=1&sni=www.ameblo.jp&alpn=&fp=&obfs=salamander&obfs-password=axcMhh8x2QP3sSZkHNbzBZFr3&mport=&os=#0702德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4yMzciLCJwb3J0Ijo0MzQwNiwic2N5IjoiYXV0byIsInBzIjoiMDcwMuW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIzZGNiZDY5NS1mMjkyLTQwZDMtYWEzNi1iYzEzNGFmMTE1ZTAiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5hbWVibG8uanAiLCJwYXRoIjoiL3ZmUXVPRXFuSjZobXNJNT9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoid3d3LmFtZWJsby5qcCIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@162.159.251.147:443?flow=&encryption=none&security=tls&sni=top.vycodcx.dpdns.org&type=xhttp&host=top.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
anytls://ihcYAp7k2Vgvrd9FT@45.82.121.237:41334?insecure=1&sni=www.ameblo.jp&alpn=h2&fp=&os=#0702德国 
anytls://kWDE9sRvbLC9rKlgQI5AO88Zz1KQu0DD8u2CYP@45.82.121.237:28050?insecure=1&sni=www.ameblo.jp&alpn=h2&fp=&os=#0702德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@103.21.244.249:443?flow=&encryption=none&security=tls&sni=top.vycodcx.dpdns.org&type=xhttp&host=top.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4yMzciLCJwb3J0IjoyNjM0Mywic2N5IjoiYXV0byIsInBzIjoiMDcwMuW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI3YTg4NGMwZi1jNDNhLTQ2NjYtYjNjZS04YmRhOTYxNTRjNjEiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5hbWVibG8uanAiLCJwYXRoIjoiL1d6WjVGVVpIVFZHWlZsb1BROW50UEUyR0o0P2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ3d3cuYW1lYmxvLmpwIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://50cc0a85-91d2-421b-a886-322493d2d1af@45.82.121.237:43316?flow=&encryption=none&security=tls&sni=www.ameblo.jp&type=ws&host=www.ameblo.jp&path=/erHfuMVA3E6cu%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@108.162.195.45:443?flow=&encryption=none&security=tls&sni=top.vycodcx.dpdns.org&type=xhttp&host=top.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.16.124.206:443?flow=&encryption=none&security=tls&sni=top.vycodcx.dpdns.org&type=xhttp&host=top.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
hysteria2://jHxp3bUBL0d1vfTRqjCtjB9K8jOQP69sj6dIzhQE@45.82.121.237:27606?insecure=1&sni=www.ameblo.jp&alpn=&fp=&obfs=salamander&obfs-password=kyiJB2qdcqCbyxQPLxcJhOR6WwLuj&mport=&os=#0702德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4yMzciLCJwb3J0Ijo0ODM0MCwic2N5IjoiYXV0byIsInBzIjoiMDcwMuW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIyYzI4YmMxNC03MmM2LTQ0YzUtYjQ4NC1jOTA3MzliN2UwZTMiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5hbWVibG8uanAiLCJwYXRoIjoiL0V6aGEzZFFjUkhlU3o/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6Ind3dy5hbWVibG8uanAiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
anytls://YbXHfLKsIHsuiXgwYQYuS@45.82.121.237:19069?insecure=1&sni=www.ameblo.jp&alpn=h2&fp=&os=#0702德国 
hysteria2://UJ8zXekmJRaaZLJvVJaFUWblpj@45.82.121.237:34192?insecure=1&sni=www.ameblo.jp&alpn=&fp=&obfs=salamander&obfs-password=JGEi1YLZv21TDlDdrg0JbLMotvtN&mport=&os=#0702德国 
anytls://7x3MCpPvVr6JcLAgF67TqVu5cYk26njx4a2EEv@45.82.121.237:64027?insecure=1&sni=www.ameblo.jp&alpn=h2&fp=&os=#0702德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@188.114.98.212:443?flow=&encryption=none&security=tls&sni=top.vycodcx.dpdns.org&type=xhttp&host=top.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.24.226.87:443?flow=&encryption=none&security=tls&sni=top.vycodcx.dpdns.org&type=xhttp&host=top.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.18.33.143:443?flow=&encryption=none&security=tls&sni=top.vycodcx.dpdns.org&type=xhttp&host=top.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.59.110:443?flow=&encryption=none&security=tls&sni=top.vycodcx.dpdns.org&type=xhttp&host=top.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@172.67.208.147:443?flow=&encryption=none&security=tls&sni=top.vycodcx.dpdns.org&type=xhttp&host=top.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
anytls://q2mNODfwD8GRZPM9CcC@45.82.121.237:45022?insecure=1&sni=www.ameblo.jp&alpn=h2&fp=&os=#0702德国 
hysteria2://hF0FfEaRBX5We1JnQEn54sReQ@45.82.121.237:14904?insecure=1&sni=www.ameblo.jp&alpn=&fp=&obfs=salamander&obfs-password=F5mYJiYLPMOYhp3bfm3VGj8aUpMyXO7cu8cs0J87&mport=&os=#0702德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.20.8.8:443?flow=&encryption=none&security=tls&sni=top.vycodcx.dpdns.org&type=xhttp&host=top.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.58.158:443?flow=&encryption=none&security=tls&sni=top.vycodcx.dpdns.org&type=xhttp&host=top.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@141.101.113.6:443?flow=&encryption=none&security=tls&sni=top.vycodcx.dpdns.org&type=xhttp&host=top.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
hysteria2://sFDvxgQqrXJu04aM6i2xxn1BUp97oYXNmkv1S6o@45.82.121.237:53831?insecure=1&sni=www.ameblo.jp&alpn=&fp=&obfs=salamander&obfs-password=VCMMhYs7WKor5Ah4lzLFopyn6jk&mport=&os=#0702德国 
vless://7584d697-9089-4281-ae0c-f95ea3b6ba2d@45.82.121.237:60393?flow=&encryption=none&security=tls&sni=www.ameblo.jp&type=ws&host=www.ameblo.jp&path=/598Kc9LU8FBOp0spXQkT3pdoIX%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@103.21.244.144:443?flow=&encryption=none&security=tls&sni=top.vycodcx.dpdns.org&type=xhttp&host=top.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
hysteria2://NUrwoYB05b8aqDPMY@45.82.121.237:15266?insecure=1&sni=www.ameblo.jp&alpn=&fp=&obfs=salamander&obfs-password=UyZwPCfJU5LAPnyKFA7mOVKS69FS1&mport=&os=#0702德国 
anytls://U6DucafFx4fsyGqSVJEwsK9PR6YSA6LYj@45.82.121.237:23166?insecure=1&sni=www.ameblo.jp&alpn=h2&fp=&os=#0702德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@141.101.123.154:443?flow=&encryption=none&security=tls&sni=top.vycodcx.dpdns.org&type=xhttp&host=top.vycodcx.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0702德国 
anytls://zRkA5PJV8JlCkeSIzrWG6cDtdV4yINN6MIApM@45.82.121.237:56418?insecure=1&sni=www.ameblo.jp&alpn=h2&fp=&os=#0702德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4yMzciLCJwb3J0IjozNTYxNSwic2N5IjoiYXV0byIsInBzIjoiMDcwMuW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIwYTY4ZjIxZi1mMmNlLTQ5ZjEtYjkyZS0yNjY3Nzg4YWVjNTciLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5hbWVibG8uanAiLCJwYXRoIjoiL3MwYnRPM3ZIMHp4WDF0ZjZMRkhmWVY5NHc/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6Ind3dy5hbWVibG8uanAiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
  
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
