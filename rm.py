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
trojan://b6200af42ccadea353f5b5856dd20d70@113.99.140.184:39001?flow=&security=tls&sni=113.99.140.184&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507中国 
hysteria2://ba6c3b17-ff47-4953-a255-450e83bb8cf9@185.126.255.78:53684?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&mport=&os=#0507乌克兰 
ss://Y2hhY2hhMjA6TjlrNGYyUE9SbDE0@14.18.253.178:8348?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0507以色列 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpvSjd4blVrbkV1TVNjTTIxY2xDeUVpdDY2SlJobVpyQXJSU0UweGVhcEdSMjRIcUg=@89.44.197.181:31348?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0507保加利亚 
vless://401374e6-df77-41fb-f638-dad8184f175b@170.114.46.190:443?flow=&encryption=none&security=tls&sni=pqh44v2.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507塞浦路斯 
vless://401374e6-df77-41fb-f638-dad8184f175b@45.159.217.161:443?flow=&encryption=none&security=tls&sni=pqh44v2.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507塞浦路斯 
vless://401374e6-df77-41fb-f638-dad8184f175b@45.85.118.141:443?flow=&encryption=none&security=tls&sni=pqh44v2.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507塞浦路斯 
ss://Y2hhY2hhMjA6djVhVVV0bWUzanhz@14.18.253.178:9003?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0507孟加拉国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE3Mi42Ny4yMzAuMjQyIiwicG9ydCI6ODAsInNjeSI6ImF1dG8iLCJwcyI6IjA1MDflt7Topb8iLCJuZXQiOiJ3cyIsImlkIjoiM2NhNDhhM2MtZjJjNC00YzZkLWE4NmQtZjAwYjUyYjY0ZDA4IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiI0NTExMzExNDUyNDM2MjAyNTA0MjUxOTI5MjQ1MzM2OC5zMTUuY2hpYmFiYS5maWxlZ2Vhci1zZy5tZSIsInBhdGgiOiIvczE1Lmh0bWwiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.16.109.184:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507德国 
ss://Y2hhY2hhMjA6YXZwQnFGRm1zWUJO@14.18.253.178:8335?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0507德国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTo2N2RZZmkxdUF2MlpUeFh2TG9lazM5@66.151.41.89:33133?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0507德国 
vless://588f094b-431b-422c-b80b-007945037072@95.164.47.60:443?flow=&encryption=none&security=tls&sni=de02.abvpn.ru&type=ws&host=de02.abvpn.ru&path=/websocket&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507德国 
vless://588f094b-431b-422c-b80b-007945037072@de02.abvpn.ru:443?flow=&encryption=none&security=tls&sni=de02.abvpn.ru&type=ws&host=de02.abvpn.ru&path=/websocket&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@198.41.202.129:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507德国 
hysteria2://nP6tt86qT7wN3QZbl@45.82.121.180:53479?insecure=1&sni=www.jquery.com&alpn=&fp=&obfs=salamander&obfs-password=z6mh1IepNIFSeYVVtXWuXdUn992H36yLJCX&mport=&os=#0507德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.19.192.183:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.58.119:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6YTg2OGEyZDctOTgyYS00Mjc3LTg0ZDUtZDUxMTUzMWZmNGVhQDQ1LjgyLjEyMS4xODA6MTU5OTM6d3M6L2FZcHBUZ3F0Szk2N0hpJTNGZWQlM0QyNTYwOnd3dy5qcXVlcnkuY29tOm5vbmU6dGxzOnd3dy5qcXVlcnkuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0507德国 
hysteria2://LNkrkMlklihnCyJbisaZQpg81xOu1WWdyq@45.82.121.180:22768?insecure=1&sni=www.jquery.com&alpn=&fp=&obfs=salamander&obfs-password=7qamUh43795USvZWJb766Z69ZXvgHsSM2x&mport=&os=#0507德国 
hysteria2://9a9X5BKX6tRneeCrTmXgN3hcf4Bhd@45.82.121.180:40010?insecure=1&sni=www.jquery.com&alpn=&fp=&obfs=salamander&obfs-password=neC5yAUTxogg9ocL&mport=&os=#0507德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.27.124.15:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507德国 
vless://01b1cc7b-763c-48ca-ad43-e066c0bf6e06@45.82.121.180:14673?flow=&encryption=none&security=tls&sni=www.jquery.com&type=ws&host=www.jquery.com&path=/MOX7oBe6CMKmLt5r6GOxsHwkNhxB5%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@162.159.7.2:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.19.160.168:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@162.159.199.61:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507德国 
trojan://705ff7f9-dddf-4292-9d86-77d55165e092@45.82.121.180:65087?flow=&security=tls&sni=www.jquery.com&type=ws&header=none&host=www.jquery.com&path=/sO4o6qnMeFFb7Q%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@172.66.150.203:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@162.159.252.210:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@188.114.98.210:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507德国 
hysteria2://rkda5KWLa9elsxUAXT02112hfAb@45.82.121.180:23280?insecure=1&sni=www.jquery.com&alpn=&fp=&obfs=salamander&obfs-password=1I4ibJIrb7zLClJbxS1j56zof3YC0&mport=&os=#0507德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.59.77:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507德国 
trojan://7c1f9ee3-f679-4c92-b435-261b4ec2ca38@45.82.121.180:12044?flow=&security=tls&sni=www.jquery.com&type=ws&header=none&host=www.jquery.com&path=/PRtqqvEtMBUVdBrecxWqKQi%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507德国 
vless://838f5273-5d2d-4630-a0f5-9cc8e4aef4d6@www.speedtest.net:443?flow=&encryption=none&security=tls&sni=ZjJuNdIy.rIpLeToOrY.InFo&type=ws&host=ZjJuNdIy.rIpLeToOrY.InFo&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507摩尔多瓦 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0507斯洛文尼亚共和国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNDQuMTI2IiwicG9ydCI6NDc4ODMsInNjeSI6ImF1dG8iLCJwcyI6IjA1MDfmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE0IiwicG9ydCI6NDIzNzUsInNjeSI6ImF1dG8iLCJwcyI6IjA1MDfmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQwIiwicG9ydCI6MzY2MDksInNjeSI6ImF1dG8iLCJwcyI6IjA1MDfmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0MTAyNCwic2N5IjoiYXV0byIsInBzIjoiMDUwN+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0MTI5MSwic2N5IjoiYXV0byIsInBzIjoiMDUwN+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo1NDY1Miwic2N5IjoiYXV0byIsInBzIjoiMDUwN+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE0IiwicG9ydCI6MzI5ODAsInNjeSI6ImF1dG8iLCJwcyI6IjA1MDfml6XmnKwiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yNTMuMjQyLjE5NyIsInBvcnQiOjM1MjQzLCJzY3kiOiJhdXRvIiwicHMiOiIwNTA35pel5pysIiwibmV0Ijoid3MiLCJpZCI6IjQ2YTUzOWQyLWQzYmEtNGE2ZS1hZWRiLWI3MjdkMmZjNjBmOCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoid2ViLnhjanMuaW5mbyIsInBhdGgiOiIvaG9tZSIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IndlYi54Y2pzLmluZm8iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzcuODQuNTMiLCJwb3J0Ijo1NTAwMiwic2N5IjoiYXV0byIsInBzIjoiMDUwN+aXpeacrCIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://3482c71a-d01c-4ae5-b454-fa8cb3785f66@94.131.20.3:443?flow=&security=tls&sni=chop-wrist-bud.stark-industries.solutions&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0507比利时 
ss://Y2hhY2hhMjA6cTJrU0dwNGF5RktC@14.18.253.178:8347?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0507法国 
vless://e13dc928-2afb-4ede-839b-40b0ab07122c@51.77.110.211:22351?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507法国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0507波兰 
vless://5453ae26-250d-4e79-b4ec-016baf806865@104.21.21.190:443?flow=&encryption=none&security=tls&sni=1wwwWdf.890606.XYz&type=ws&host=1wwwwdf.890606.xyz&path=/XcQF058rNJ3gc4aj&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507美国 
vless://aa424865-2762-404c-b767-66c9f98e026b@104.21.38.48:443?flow=&encryption=none&security=tls&sni=4rRRRrrRRRrRrRrRRrrRrRRrty.huaNgDi2031.DPdNS.OrG&type=ws&host=4rrrrrrrrrrrrrrrrrrrrrrrty.huangdi2031.dpdns.org&path=/25Rajr8UdFGa29fCwxS&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507美国 
vless://aa424865-2762-404c-b767-66c9f98e026b@104.21.83.113:443?flow=&encryption=none&security=tls&sni=edS859886XYzXS.859886.xYZ&type=ws&host=eds859886xyzxs.859886.xyz&path=/25Rajr8UdFGa29fCwxS&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507美国 
hysteria2://ba6c3b17-ff47-4953-a255-450e83bb8cf9@107.172.235.75:38939?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&mport=&os=#0507美国 
hysteria2://fbd83ebd-e05c-4196-9166-0d7805292680@107.172.235.75:38939?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&mport=&os=#0507美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE2IiwicG9ydCI6NDY3NTksInNjeSI6ImF1dG8iLCJwcyI6IjA1MDfnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE2IiwicG9ydCI6NTIwODIsInNjeSI6ImF1dG8iLCJwcyI6IjA1MDfnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE2IiwicG9ydCI6MzU5MjEsInNjeSI6ImF1dG8iLCJwcyI6IjA1MDfnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE5IiwicG9ydCI6NDQwMTUsInNjeSI6ImF1dG8iLCJwcyI6IjA1MDfnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE5IiwicG9ydCI6NTEwOTUsInNjeSI6ImF1dG8iLCJwcyI6IjA1MDfnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQxIiwicG9ydCI6NDQ0OTEsInNjeSI6ImF1dG8iLCJwcyI6IjA1MDfnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQxIiwicG9ydCI6NDY1OTcsInNjeSI6ImF1dG8iLCJwcyI6IjA1MDfnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjYzIiwicG9ydCI6Mzc4MDUsInNjeSI6ImF1dG8iLCJwcyI6IjA1MDfnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtaWV0Zjphc2QxMjM0NTY=@137.175.113.193:8388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0507美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE0NC4yNTUuMzYuMjU0IiwicG9ydCI6MTQxMDAsInNjeSI6ImF1dG8iLCJwcyI6IjA1MDfnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImY2ODY2YjBiLWY5NDYtNGEwMy04ZGYwLWM3ZTAwMTZiNTVhZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://aTArbZ2F0E@172.66.168.209:443?flow=&security=tls&sni=uSa-vp-27.bLAzECLOUD.SITE&type=ws&header=none&host=&path=/linkvkws&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507美国 
vless://5453ae26-250d-4e79-b4ec-016baf806865@172.67.163.14:443?flow=&encryption=none&security=tls&sni=1QQsSS.2031.PP.UA&type=ws&host=1qqsss.2031.pp.ua&path=/XcQF058rNJ3gc4aj&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507美国 
vless://aa424865-2762-404c-b767-66c9f98e026b@172.67.175.139:443?flow=&encryption=none&security=tls&sni=edS859886XYzXS.859886.xYZ&type=ws&host=eds859886xyzxs.859886.xyz&path=/25Rajr8UdFGa29fCwxS&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507美国 
trojan://5453ae26-250d-4e79-b4ec-016baf806865@172.67.205.22:443?flow=&security=tls&sni=1SSdDdFfffHhHJJJJ.20220420.Pp.uA&type=ws&header=none&host=1ssdddffffhhhjjjj.20220420.pp.ua&path=/OYzPAeaZdXUq2d6J3gc4aj&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507美国 
trojan://aa424865-2762-404c-b767-66c9f98e026b@172.67.219.54:443?flow=&security=tls&sni=4RrrrRrrrRrRRRtTtTTTtTYyyYYYyYYiIIIiiiiOooOOoOoOoooO.hUaNgdI2031.DPDnS.orG&type=ws&header=none&host=&path=/P6OrM7FLvAhFqZdFGa29fCwxS&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507美国 
vless://aa424865-2762-404c-b767-66c9f98e026b@172.67.219.54:443?flow=&encryption=none&security=tls&sni=4rRRRrrRRRrRrRrRRrrRrRRrty.huaNgDi2031.DPdNS.OrG&type=ws&host=4rrrrrrrrrrrrrrrrrrrrrrrty.huangdi2031.dpdns.org&path=/25Rajr8UdFGa29fCwxS&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@172.67.68.36:443?flow=&encryption=none&security=tls&sni=pqh28v6.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzguOTAuOCIsInBvcnQiOjM5MDc2LCJzY3kiOiJhdXRvIiwicHMiOiIwNTA3576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1nY206UENubkg2U1FTbmZvUzI3@38.114.114.108:8091?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0507美国 
ss://YWVzLTI1Ni1nY206a0RXdlhZWm9UQmNHa0M0@38.114.114.108:8882?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0507美国 
hysteria2://80aa5178-f936-11ed-8ce6-f23c91369f2d@c26d0357-supts0-tfvcxz-1nq4g.hy2.gotochinatown.net:8443?insecure=0&sni=c26d0357-supts0-tfvcxz-1nq4g.hy2.gotochinatown.net&alpn=&fp=&mport=&os=#0507美国 
ss://YWVzLTI1Ni1nY206NzdhMTJhM2QtNmRmMC00OGM4LWExODktYjA3MWZjZGExNDU2@cdn-p1-us.youku-dns.com:11511?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0507美国 
trojan://aTArbZ2F0E@cloudgetservice.mcloudservice.site:443?flow=&security=tls&sni=uSa-vp-27.bLAzECLOUD.SITE&type=ws&header=none&host=&path=/linkvkws&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507美国 
vless://c2226caf-0134-49d4-aa8c-0069e98b5882@104.17.148.22:443?flow=&encryption=none&security=tls&sni=72790032528889957475364702518915.v2line.online&type=ws&host=72790032528889957475364702518915.v2line.online&path=/netherlands/amsterdam/vl/ws/tls&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507英国 
vless://838f5273-5d2d-4630-a0f5-9cc8e4aef4d6@188.42.88.45:443?flow=&encryption=none&security=tls&sni=CxNiMjJz.cAfUnEaR.InFo&type=ws&host=CxNiMjJz.cAfUnEaR.InFo&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507英国 
vless://838f5273-5d2d-4630-a0f5-9cc8e4aef4d6@45.131.6.160:443?flow=&encryption=none&security=tls&sni=CxNiMjJz.cAfUnEaR.InFo&type=ws&host=CxNiMjJz.cAfUnEaR.InFo&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507英国 
vless://838f5273-5d2d-4630-a0f5-9cc8e4aef4d6@45.142.120.97:443?flow=&encryption=none&security=tls&sni=CxNiMjJz.cAfUnEaR.InFo&type=ws&host=CxNiMjJz.cAfUnEaR.InFo&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507英国 
vless://838f5273-5d2d-4630-a0f5-9cc8e4aef4d6@47.79.92.16:443?flow=&encryption=none&security=tls&sni=CxNiMjJz.cAfUnEaR.InFo&type=ws&host=CxNiMjJz.cAfUnEaR.InFo&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507英国 
vmess://eyJ2IjoiMiIsImFkZCI6ImR4djQucGFpNTAyODgudWsiLCJwb3J0IjoxNDEwMCwic2N5IjoiYXV0byIsInBzIjoiMDUwN+iLseWbvSIsIm5ldCI6InRjcCIsImlkIjoiZjY4NjZiMGItZjk0Ni00YTAzLThkZjAtYzdlMDAxNmI1NWFkIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTowUnNyY0ZKMXZPc1dFcWczUDU1aHZhYWNLZnVTaFQwY2MxaDB0OEFEME5BOHUxdVI=@92.38.171.215:31348?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0507西班牙 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.19:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0507越南 
vless://53fa8faf-ba4b-4322-9c69-a3e5b1555049@172.67.204.84:443?flow=&encryption=none&security=tls&sni=ipsychO.SUEx12.Ir&type=ws&host=ipsycho.suex12.ir&path=/re5IzbZ9IZZMddtw%3Fed%3D2560flow%3D-udp443flow%3D-udp443&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507韩国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQwIiwicG9ydCI6NTkwODIsInNjeSI6ImF1dG8iLCJwcyI6IjA1MDfpppnmuK8iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
trojan://2c605663-b89a-5734-a9d6-97d4743d72cf@183.232.235.2:8313?flow=&security=tls&sni=hk-13-568.flztjc.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507香港 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0IjozMjkxOSwic2N5IjoiYXV0byIsInBzIjoiMDUwN+mmmea4ryIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://2c605663-b89a-5734-a9d6-97d4743d72cf@dozo01.flztjc.top:8313?flow=&security=tls&sni=hk-13-568.flztjc.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0507香港 

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
