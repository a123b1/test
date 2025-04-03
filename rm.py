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

vless://3df883f7-eb8a-489a-af70-6745602ecc1c@103.21.244.144:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.16.244.36:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402德国 
trojan://0cda5f7e-cc55-4ff2-8ad8-268b9b99dd01@104.21.21.190:443?flow=&security=tls&sni=Us6-08.890606.xYZ&type=ws&header=none&host=us6-08.890606.xyz&path=/ILLcisbMYUd6MQzxVoMQ&alpn=http/1.1&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4yMS4yMS4yMjYiLCJwb3J0Ijo4MCwic2N5IjoiYXV0byIsInBzIjoiMDQwMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJhOGZjZTQ0Mi1hZTlhLTRjYzEtYTBjYy0yMDMwOGZmMGEwZGIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IjFjLjg5MDY4OS54eXoiLCJwYXRoIjoiL2xzVVZyOFZCeEY0eWxYbmdaIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://6040a753-e35b-4384-8713-96f3c639b621@104.21.69.41:443?flow=&security=tls&sni=kju84.890602.XYZ&type=ws&header=none&host=kju84.890602.xyz&path=/WxWOWO1YA9bs2HOmaeWimvT3&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402美国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.26.13.81:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.27.29.71:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.27.4.50:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402德国 
hysteria2://4ad42a4a-70b9-4177-8c50-ddc483cba07b@107.172.235.75:54254?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&os=#0402美国 
vless://ee6774c0-9b19-4ff1-8b30-2da4b71977e2@108.165.152.131:443?flow=&encryption=none&security=tls&sni=edccq.aimercc.filegear-sg.me&type=ws&host=edccq.aimercc.filegear-sg.me&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402台湾 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE0IiwicG9ydCI6NDAxMjUsInNjeSI6ImF1dG8iLCJwcyI6IjA0MDLml6XmnKwiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE0IiwicG9ydCI6MzQwOTMsInNjeSI6ImF1dG8iLCJwcyI6IjA0MDLmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE5IiwicG9ydCI6NDIwNTUsInNjeSI6ImF1dG8iLCJwcyI6IjA0MDLnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjEyMyIsInBvcnQiOjQxNDAyLCJzY3kiOiJhdXRvIiwicHMiOiIwNDAy576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQwIiwicG9ydCI6NDEwMDIsInNjeSI6ImF1dG8iLCJwcyI6IjA0MDLmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjYzIiwicG9ydCI6NDAxMDUsInNjeSI6ImF1dG8iLCJwcyI6IjA0MDLnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzQuMTAyLjIyOSIsInBvcnQiOjMxOTk4LCJzY3kiOiJhdXRvIiwicHMiOiIwNDAy576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://ee6774c0-9b19-4ff1-8b30-2da4b71977e2@121.150.230.201:12136?flow=&encryption=none&security=tls&sni=edccq.aimercc.filegear-sg.me&type=ws&host=edccq.aimercc.filegear-sg.me&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402台湾 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@13.112.73.126:443#0402日本 
vless://ea286109-d20f-415e-849e-4af20ab04b65@139.185.34.131:443?flow=&encryption=none&security=tls&sni=147135001195.sec22org.com&type=tcp&host=&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402美国 
ss://Y2hhY2hhMjA6cTJrU0dwNGF5RktC@14.18.253.178:8347#0402法国 
ss://Y2hhY2hhMjA6YXZwQnFGRm1zWUJO@14.18.253.178:8335#0402日本 
ss://Y2hhY2hhMjA6RHZQZkthOHZzVjlL@14.18.253.178:8334#0402新加坡 
ss://Y2hhY2hhMjA6djVhVVV0bWUzanhz@14.18.253.178:9003#0402孟加拉国 
ss://Y2hhY2hhMjA6TjlrNGYyUE9SbDE0@14.18.253.178:8348#0402以色列 
vmess://eyJ2IjoiMiIsImFkZCI6IjE0NC43Ni4yMzEuMjciLCJwb3J0IjoyMzE3Mywic2N5IjoiYXV0byIsInBzIjoiMDQwMuW+t+WbvSIsIm5ldCI6InRjcCIsImlkIjoiNGMyZGFmYjktMjIyYy00ODFjLTk2OTUtMWViZTRiYzBiNjkyIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://telegram-id-directvpn@16.170.192.19:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402瑞典 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@162.159.251.147:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402德国 
vless://6d2a3f0d-3d10-4e97-a73c-aa5f88d7184f@172.66.168.201:443?flow=&encryption=none&security=tls&sni=Is1-vLESs.greeNssH.ORG&type=ws&host=Is1-vLESs.greeNssH.ORG&path=/vless&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402摩尔多瓦 
trojan://85950277-f447-48f0-9ead-aaf6d5ff3cad@172.67.163.14:443?flow=&security=tls&sni=df5tym.2031.pp.ua&type=ws&header=none&host=df5tym.2031.pp.ua&path=/I4L1BP2DQVYmx5NYQ76MGGq&alpn=http/1.1&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402美国 
trojan://0cda5f7e-cc55-4ff2-8ad8-268b9b99dd01@172.67.204.120:443?flow=&security=tls&sni=Us6-05.890603.XYZ&type=ws&header=none&host=us6-05.890603.xyz&path=/ILLcisbMYUd6MQzxVoMQ&alpn=http/1.1&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402美国 
trojan://6040a753-e35b-4384-8713-96f3c639b621@172.67.204.22:443?flow=&security=tls&sni=kju84.890602.XYZ&type=ws&header=none&host=kju84.890602.xyz&path=/WxWOWO1YA9bs2HOmaeWimvT3&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402美国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.58.127:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.58.158:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.59.110:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402德国 
vless://ee6774c0-9b19-4ff1-8b30-2da4b71977e2@175.196.105.220:12209?flow=&encryption=none&security=tls&sni=edccq.aimercc.filegear-sg.me&type=ws&host=edccq.aimercc.filegear-sg.me&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402台湾 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo1OTU1NCwic2N5IjoiYXV0byIsInBzIjoiMDQwMuaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo1MTAzOSwic2N5IjoiYXV0byIsInBzIjoiMDQwMuaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo1NjkwMSwic2N5IjoiYXV0byIsInBzIjoiMDQwMuaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo1NTc1NCwic2N5IjoiYXV0byIsInBzIjoiMDQwMuaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989#0402波兰 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@188.114.98.202:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402德国 
hysteria2://5CBqBh6MeDq6GajcilBiDg%3D%3D@192-227-152-86.nip.io:61001?insecure=1&sni=192-227-152-86.nip.io&alpn=&fp=&os=#0402美国 
hysteria2://dongtaiwang.com@195.154.33.70:59967?insecure=1&sni=www.bing.com&alpn=&fp=&os=#0402法国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@198.41.196.251:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402德国 
ss://Y2hhY2hhMjAtaWV0Zjphc2QxMjM0NTY=@202.162.109.169:8388#0402新加坡 
vless://ee6774c0-9b19-4ff1-8b30-2da4b71977e2@211.219.39.209:16044?flow=&encryption=none&security=tls&sni=edccq.aimercc.filegear-sg.me&type=ws&host=edccq.aimercc.filegear-sg.me&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402台湾 
vless://ee6774c0-9b19-4ff1-8b30-2da4b71977e2@222.96.171.51:30019?flow=&encryption=none&security=tls&sni=edccq.aimercc.filegear-sg.me&type=ws&host=edccq.aimercc.filegear-sg.me&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402台湾 
hysteria2://4ad42a4a-70b9-4177-8c50-ddc483cba07b@23.132.228.217:58739?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&os=#0402美国 
ss://YWVzLTI1Ni1nY206Rm9PaUdsa0FBOXlQRUdQ@23.150.248.199:7307#0402美国 
ss://YWVzLTI1Ni1nY206UmV4bkJnVTdFVjVBRHhH@23.150.248.199:7002#0402美国 
ss://YWVzLTI1Ni1nY206VEV6amZBWXEySWp0dW9T@23.150.248.199:6679#0402美国 
ss://YWVzLTI1Ni1nY206ZmFCQW9ENTRrODdVSkc3@23.150.248.199:2375#0402美国 
vless://e657e5fb-c417-4d3f-d84e-a3a8f010f9fa@31.59.111.49:33718?flow=xtls-rprx-vision&encryption=none&security=reality&sni=icloud.cdn-apple.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=g1f1wLjim5gOVGnI5LGUV0dL4iFXPoiepOPZfSxJe14&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.208.203.47:443#0402美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.216.142.212:443#0402美国 
trojan://telegram-id-privatevpns@35.158.81.171:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402德国 
trojan://telegram-id-privatevpns@35.177.223.124:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402英国 
trojan://telegram-id-privatevpns@35.180.183.189:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402法国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.87.29.54:443#0402美国 
vless://ee6774c0-9b19-4ff1-8b30-2da4b71977e2@38.147.187.99:18181?flow=&encryption=none&security=tls&sni=edccq.aimercc.filegear-sg.me&type=ws&host=edccq.aimercc.filegear-sg.me&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402台湾 
trojan://oIwjHDXpKePvYIg8@43.162.127.44:443?flow=&security=tls&sni=myvps.cfd&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402新加坡 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@43.202.67.225:443#0402韩国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjEyMS41MC4xMTYiLCJwb3J0IjoyNzIyOCwic2N5IjoiYXV0byIsInBzIjoiMDQwMuWPsOa5viIsIm5ldCI6InRjcCIsImlkIjoiMWQ0ZDhmYjgtYzczYy00NDc0LWUzMDEtZGNiOTU3MDk0M2NhIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
hysteria2://ww1uAKR8WJ5PLbJSXJWZfqFKx3sY3B1hdJTWL@45.82.121.195:17868?insecure=1&sni=www.bing.com&alpn=&fp=&obfs=salamander&obfs-password=ayzE70UDtgCSO5UF5x5Do5ZMkB&os=#0402德国 
trojan://54690d9b-d0f0-4269-8504-87ad2dd6b669@45.82.121.195:8503?flow=&security=tls&sni=www.bing.com&type=ws&header=none&host=www.bing.com&path=/ZOl8dZaHdRHyVKWKQT70XsbP0i9XmnoW%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402德国 
trojan://2fa6149d-3af6-418f-86b3-ba719d6ec9a8@45.82.121.195:32569?flow=&security=tls&sni=www.bing.com&type=ws&header=none&host=www.bing.com&path=/6xqBoVVOTeM%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6YzVkMmJjODgtMThlOS00NDYwLWI4NTktNjkxMWUwMTAzNmMyQDQ1LjgyLjEyMS4xOTU6Mzk4NTE6d3M6L212cWhNVmpSQzBkSk1kNUhybSUzRmVkJTNEMjU2MDp3d3cuYmluZy5jb206bm9uZTp0bHM6d3d3LmJpbmcuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0402德国 
hysteria2://yoK9abYlzmSt55F6eIpMKsfUjYf@45.82.121.195:46105?insecure=1&sni=www.bing.com&alpn=&fp=&obfs=salamander&obfs-password=fvIbtt8ylRF5SJUIqiVHeAu7hGO6&os=#0402德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6YzY2YTljOTctYTc2OS00MWUwLWJhYWEtZTE3NmVhNzU1YmUzQDQ1LjgyLjEyMS4xOTU6MTg5OTY6d3M6LyUzRmVkJTNEMjU2MDp3d3cuYmluZy5jb206bm9uZTp0bHM6d3d3LmJpbmcuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0402德国 
vless://2ab9f783-761b-4f88-822f-3b40b5db36d2@45.82.121.195:54247?flow=&encryption=none&security=tls&sni=www.bing.com&type=ws&host=www.bing.com&path=/Q8puPCmE89SsxxBE3qZOAF5v3IqYnZP%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4xOTUiLCJwb3J0IjozNzgzMCwic2N5IjoiYXV0byIsInBzIjoiMDQwMuW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI4MmYyOTgyOS0wNjFkLTQ3OGUtOGMwNy1hZDhlY2RiM2ZlYWQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5iaW5nLmNvbSIsInBhdGgiOiIvaW1sP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ3d3cuYmluZy5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4xOTUiLCJwb3J0IjoxNDE4Mywic2N5IjoiYXV0byIsInBzIjoiMDQwMuW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJjNWQyYmM4OC0xOGU5LTQ0NjAtYjg1OS02OTExZTAxMDM2YzIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5iaW5nLmNvbSIsInBhdGgiOiIvS1E0UldTbGZzVVp1SnJNM1cyNTNIeUkzP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ3d3cuYmluZy5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
hysteria2://epmU3PzZ62jEP0cBVY@45.82.121.195:49208?insecure=1&sni=www.bing.com&alpn=&fp=&obfs=salamander&obfs-password=kI7UtVA4MEC3BlSNac&os=#0402德国 
hysteria2://M6fKIMkZLAvdyJZKM0aEW9uNs@45.82.121.195:25686?insecure=1&sni=www.bing.com&alpn=&fp=&obfs=salamander&obfs-password=dbUph9CMIgy629KH4&os=#0402德国 
hysteria2://beCnBmTpUWkqWNmhsujjorgFrRRRUapc@45.82.121.195:37622?insecure=1&sni=www.bing.com&alpn=&fp=&obfs=salamander&obfs-password=HxuTklKoSkn9BhduQIOW9OsT&os=#0402德国 
hysteria2://QZMiGl8J3jSOlidtiPCd2dnc6@45.82.121.195:3636?insecure=1&sni=www.bing.com&alpn=&fp=&obfs=salamander&obfs-password=SxZJc5rAediXCC0seCI0PqVCe&os=#0402德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6OTgzNGMwZGQtNzA2OC00ZWIxLTgxMWUtNjJhNjA4ZjFjN2FlQDQ1LjgyLjEyMS4xOTU6MTM5NzM6d3M6LzBFaGtrbjBQa3lQNTVKZ0hRUW1pOUF3WnZ0M2xCazVSJTNGZWQlM0QyNTYwOnd3dy5iaW5nLmNvbTpub25lOnRsczp3d3cuYmluZy5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0402德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6N2U4NmNiZWQtNjk1OC00OWVmLTljN2UtZjZiMGE0NDQ0OWI1QDQ1LjgyLjEyMS4xOTU6Mzk3Mzp3czovajdlV2RSaG13M1hkYXN1RkhBb2Y4d3pEdXlaViUzRmVkJTNEMjU2MDp3d3cuYmluZy5jb206bm9uZTp0bHM6d3d3LmJpbmcuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0402德国 
vless://bec3a7a2-95d5-47b7-9e1e-831d8edd5fc4@45.82.121.195:20083?flow=&encryption=none&security=tls&sni=www.bing.com&type=ws&host=www.bing.com&path=/3eheAU58Jo0glH0yHJ%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4xOTUiLCJwb3J0IjoyMjk2NCwic2N5IjoiYXV0byIsInBzIjoiMDQwMuW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIyYWI5Zjc4My03NjFiLTRmODgtODIyZi0zYjQwYjVkYjM2ZDIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5iaW5nLmNvbSIsInBhdGgiOiIveHFrRmp1ZUlQMEZpajU/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6Ind3dy5iaW5nLmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4xOTUiLCJwb3J0IjozNTIzNywic2N5IjoiYXV0byIsInBzIjoiMDQwMuW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI3NzA0ODE3OS03NjQ5LTQxYTYtYWQzNi1jZDYyNmYyNzQ2MDciLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5iaW5nLmNvbSIsInBhdGgiOiIvM25pMWI/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6Ind3dy5iaW5nLmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpjdklJODVUclc2bjBPR3lmcEhWUzF1@45.87.175.188:8080#0402荷兰 
trojan://telegram-id-directvpn@50.17.121.229:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@52.40.170.193:443#0402美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@52.88.180.184:443#0402美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.169.188.214:443#0402新加坡 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.179.52.175:443#0402新加坡 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.187.221.114:443#0402美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.254.9.107:443#0402新加坡 
vless://ee6774c0-9b19-4ff1-8b30-2da4b71977e2@83.229.123.36:8443?flow=&encryption=none&security=tls&sni=edccq.aimercc.filegear-sg.me&type=ws&host=edccq.aimercc.filegear-sg.me&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402台湾 
hysteria2://c8ed6f77-3a96-46f9-9959-79118f9c1019@85.194.246.115:53252?insecure=1&sni=www.bing.com&alpn=&fp=&os=#0402波兰 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989#0402斯洛文尼亚共和国 
hysteria2://4ad42a4a-70b9-4177-8c50-ddc483cba07b@92.112.126.122:30599?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&os=#0402乌克兰 
vless://1a7a39e4-8c9b-4052-b8b2-c0929536bba5@95.164.4.88:8443?flow=&encryption=none&security=tls&sni=pq-brazil1.09vpn.com&type=ws&host=pq-brazil1.09vpn.com&path=/vless/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0402巴西 
hysteria2://82febca6-8856-41fe-84df-c8bda0b72c7b@tw3.akebi.cc:2000?insecure=0&sni=hk03.akebi.cc&alpn=&fp=&os=#0402香港 
hysteria2://82febca6-8856-41fe-84df-c8bda0b72c7b@tw3.akebi.cc:2006?insecure=0&sni=au01.akebi.cc&alpn=&fp=&os=#0402澳大利亚 
hysteria2://82febca6-8856-41fe-84df-c8bda0b72c7b@tw3.akebi.cc:2005?insecure=0&sni=fr01.akebi.cc&alpn=&fp=&os=#0402法国 
hysteria2://82febca6-8856-41fe-84df-c8bda0b72c7b@tw3.akebi.cc:2003?insecure=0&sni=is01.akebi.cc&alpn=&fp=&os=#0402以色列 
hysteria2://82febca6-8856-41fe-84df-c8bda0b72c7b@tw3.akebi.cc:2020?insecure=0&sni=ua01.akebi.cc&alpn=&fp=&os=#0402乌克兰 
vmess://eyJ2IjoiMiIsImFkZCI6InY0MC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDg0MCwic2N5IjoiYXV0byIsInBzIjoiMDQwMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaTEwMC1jb3JlLXF1aWMtbGYuYW1lbXYuY29tIiwicGF0aCI6Ii9pbmRleCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 


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
