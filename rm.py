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
vmess://eyJ2IjoiMiIsImFkZCI6InY2LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA2LCJzY3kiOiJhdXRvIiwicHMiOiIwNTIx5pel5pysIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0Ijoib2NiYy5jb20iLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.33:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0521越南 
trojan://5453ae26-250d-4e79-b4ec-016baf806865@172.67.205.22:443?flow=&security=tls&sni=1SSdDdFfffHhHJJJJ.20220420.Pp.uA&type=ws&header=none&host=1ssdddffffhhhjjjj.20220420.pp.ua&path=/OYzPAeaZdXUq2d6J3gc4aj&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521美国 
trojan://c8eac4b7-95ba-4ce0-920d-c3279eb3b391@172.67.181.193:443?flow=&security=tls&sni=EEeEee4.hUAngSHANG2030.dPdNS.org&type=ws&header=none&host=&path=/ptGwaGzcA4KNAXX&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521美国 
trojan://ac5b2e52-435b-4461-a99c-1317ab0e2889@104.21.46.90:443?flow=&security=tls&sni=DddVfGty.frEeVpnAtM.dpdNS.oRG&type=ws&header=none&host=&path=/HmfeUdLKf899DmZDo0oju2st1&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521美国 
vless://0a23af3f-3f9b-4333-ae89-796f7fe2f9ce@172.67.175.139:443?flow=&encryption=none&security=tls&sni=S859886xYZXs.859886.xYz&type=ws&host=s859886xyzxs.859886.xyz&path=/25Rajr8UdFGa29fCwxS&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521美国 
vless://52c0e96b-b8d7-44a5-a995-bd866bf39ec6@104.21.63.226:443?flow=&encryption=none&security=tls&sni=M10DdD.457.Pp.ua&type=ws&host=m10ddd.457.pp.ua&path=/YzFLmzNIEQsAmceLxv94lPbgMw&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521美国 
vless://fefba36d-5142-42f1-b14d-db5249511d93@104.21.82.39:443?flow=&encryption=none&security=tls&sni=5rty.191288.xyz&type=ws&host=5rty.191288.xyz&path=/dRTvoZIiPpwkqKrjE&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521美国 
vmess://eyJ2IjoiMiIsImFkZCI6Ijl1eWlvcHNkZmguaXJhbi5wcC51YSIsInBvcnQiOjQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDUyMee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI5MDZiYTkyZi1lZjk2LTQxMzMtOGVlZS1mMzMyMDJhNWE3MjEiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ijl1eWlvcHNkZmguaXJhbi5wcC51YSIsInBhdGgiOiIvREF4SmRkT2RUZDVwVmFtOXciLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://39a91eaf-a379-4fff-a9c8-1cb01442b76f@104.31.16.95:2053?flow=&encryption=none&security=tls&sni=ir.akcovufun.ir&type=ws&host=ir.akcovufun.ir&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521塞浦路斯 
vless://690ab90e-3f21-422b-8cb1-bc9845c7af1e@172.67.73.163:8080?flow=&encryption=none&security=&sni=&type=ws&host=IO.IhJtq0hklC.ZULAiR.OrG.&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521法国 
vless://690ab90e-3f21-422b-8cb1-bc9845c7af1e@104.26.14.85:8080?flow=&encryption=none&security=&sni=&type=ws&host=IO.IhJtq0hklC.ZULAiR.OrG.&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521法国 
vless://690ab90e-3f21-422b-8cb1-bc9845c7af1e@104.26.15.85:8080?flow=&encryption=none&security=&sni=&type=ws&host=IO.IhJtq0hklC.ZULAiR.OrG.&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521法国 
vless://19859922-a02c-4f4c-a081-ee59535910f7@104.17.147.22:8880?flow=&encryption=none&security=&sni=&type=ws&host=de-snapp.academigroup.ir.&path=/Join--EXPRESSVPN_420--Join--EXPRESSVPN_420--Join--EXPRESSVPN_420--Join--EXPRESSVPN_420--Join--EXPRESSVPN_420--Join--EXPRESSVPN_420--Join--EXPRESSVPN_420--Join--EXPRESSVPN_420--Join--EXPRESSVPN_420--Join--EXPRESSVPN_420--Join--EXPRESSVPN_420--Join--EXPRESSVPN_420--Join--EXPRESSVPN_420%3Fed%3D2048&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521德国 
ss://YWVzLTI1Ni1nY206NzdhMTJhM2QtNmRmMC00OGM4LWExODktYjA3MWZjZGExNDU2@cdn-p1-us.youku-dns.com:11511?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0521美国 
trojan://0a335fd6-be0b-11ec-8dfa-f23c91cfbbc9@abeeaaca-swq1s0-sxkd63-17z95.cu.plebai.net:15229?flow=&security=tls&sni=abeeaaca-swq1s0-sxkd63-17z95.cu.plebai.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521美国 
vmess://eyJ2IjoiMiIsImFkZCI6InRrLmh6bHQudGtkZG5zLnh5eiIsInBvcnQiOjIyNjQxLCJzY3kiOiJhdXRvIiwicHMiOiIwNTIx576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6Ijk4ZTk2YzlmLTRiYjMtMzlkNC05YTJjLWZhYzA0MjU3ZjdjNyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoienhqcC1hLnRrb25nLmNjIiwicGF0aCI6Ii8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InRrLmh6bHQudGtkZG5zLnh5eiIsInBvcnQiOjIyNjQyLCJzY3kiOiJhdXRvIiwicHMiOiIwNTIx576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6Ijk4ZTk2YzlmLTRiYjMtMzlkNC05YTJjLWZhYzA0MjU3ZjdjNyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoienhqcC1iLnRrb25nLmNjIiwicGF0aCI6Ii8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InY3LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA3LCJzY3kiOiJhdXRvIiwicHMiOiIwNTIx576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMi5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgxMiwic2N5IjoiYXV0byIsInBzIjoiMDUyMeaWsOWKoOWdoSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InY0MC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDg0MCwic2N5IjoiYXV0byIsInBzIjoiMDUyMee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaTEwMC1jb3JlLXF1aWMtbGYuYW1lbXYuY29tIiwicGF0aCI6Ii9pbmRleCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQwIiwicG9ydCI6MzE2MDksInNjeSI6ImF1dG8iLCJwcyI6IjA1MjHmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE2IiwicG9ydCI6MzU5MjEsInNjeSI6ImF1dG8iLCJwcyI6IjA1MjHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzguOTAuOCIsInBvcnQiOjM5MDc2LCJzY3kiOiJhdXRvIiwicHMiOiIwNTIx576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://2558c819-1363-4859-8fb9-f8cb104d49d2@176.223.66.8:39948?flow=&encryption=none&security=&sni=&type=tcp&host=divarcdn.com&path=&headerType=http&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521土耳其 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQwIiwicG9ydCI6NDAyOTIsInNjeSI6ImF1dG8iLCJwcyI6IjA1MjHmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjEyMyIsInBvcnQiOjQwMzkyLCJzY3kiOiJhdXRvIiwicHMiOiIwNTIx576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjY0LCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzguOTAuOCIsInBvcnQiOjQxNzY2LCJzY3kiOiJhdXRvIiwicHMiOiIwNTIx576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQxIiwicG9ydCI6NDQ0OTEsInNjeSI6ImF1dG8iLCJwcyI6IjA1MjHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQxIiwicG9ydCI6NDY1OTcsInNjeSI6ImF1dG8iLCJwcyI6IjA1MjHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE2IiwicG9ydCI6NDY3NTksInNjeSI6ImF1dG8iLCJwcyI6IjA1MjHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzguOTAuOCIsInBvcnQiOjQ2OTIwLCJzY3kiOiJhdXRvIiwicHMiOiIwNTIx576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjY0LCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0OTI5MSwic2N5IjoiYXV0byIsInBzIjoiMDUyMeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE5IiwicG9ydCI6NDkzNTUsInNjeSI6ImF1dG8iLCJwcyI6IjA1MjHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE2IiwicG9ydCI6NTIwODIsInNjeSI6ImF1dG8iLCJwcyI6IjA1MjHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQwIiwicG9ydCI6NTkxNTIsInNjeSI6ImF1dG8iLCJwcyI6IjA1MjHmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0521斯洛文尼亚共和国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0IjozMDA1Miwic2N5IjoiYXV0byIsInBzIjoiMDUyMeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0MTAyNCwic2N5IjoiYXV0byIsInBzIjoiMDUyMeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE0IiwicG9ydCI6NDIzNzUsInNjeSI6ImF1dG8iLCJwcyI6IjA1MjHmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNDQuMTI2IiwicG9ydCI6NDc4ODMsInNjeSI6ImF1dG8iLCJwcyI6IjA1MjHmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0OTEyMSwic2N5IjoiYXV0byIsInBzIjoiMDUyMeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJvY2JjLmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0521波兰 
vless://8c8873fb-6e68-4359-8d67-092d399612c9@95.38.38.226:24000?flow=&encryption=none&security=&sni=&type=tcp&host=www.irna.ir.www.alibaba.ir&path=&headerType=http&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521法国 
vless://5a24dc4b-4711-402a-ec6d-7c174b290c83@92.112.53.153:18217?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0521日本 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE0IiwicG9ydCI6MzI5ODAsInNjeSI6ImF1dG8iLCJwcyI6IjA1MjHml6XmnKwiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzcuODQuNTMiLCJwb3J0Ijo1NTAwMiwic2N5IjoiYXV0byIsInBzIjoiMDUyMeaXpeacrCIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://23651a65-bef3-431a-b040-5e8c158a9867@95.38.38.226:27000?flow=&encryption=none&security=&sni=&type=tcp&host=irna.alibaba.ir.speedtest.net&path=&headerType=http&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521俄罗斯 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@37.235.49.152:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0521以色列 
vless://ee317e25-4c44-4b3f-81fd-93420678bd34@45.87.102.244:21851?flow=xtls-rprx-vision&encryption=none&security=reality&sni=one-piece.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=EcToF-48rTWeedF6qD5yUrJ3AC_Y3FrzGUE5UP5bg2A&sid=6ba85179e30d4fc2&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@51.15.23.63:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0521挪威 
vless://af50bdbf-1715-a461-cbb4-ebbea9ed338c@51.195.35.2:4768?flow=xtls-rprx-vision&encryption=none&security=reality&sni=yandex.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=1juiWgfU1-cGsbu9zxKCly7Vn3WGES5x6S86r90_vwc&sid=b7e284c9b786f709&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521法国 
vless://34ec142b-eaae-4ff1-944f-c07c0b8081fe@51.210.73.120:56624?flow=&encryption=none&security=&sni=&type=xhttp&host=amirzaplus.com&path=/newgame%3Fed%3D2048&mode=auto&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521法国 
vless://eff09fb3-17f7-44ee-bc00-6fa5a3e0e9da@65.21.102.23:54401?flow=&encryption=none&security=reality&sni=zula.ir&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=AqGO4WCsGfcX046DebowJcVTKANHPazld7XyAHD_RQE&sid=e5201e3c&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521芬兰 
trojan://1a17b19d-4896-4531-af79-6e91d8ef8228@13.215.59.38:6668?flow=&security=tls&sni=baidu.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521新加坡 
trojan://1a17b19d-4896-4531-af79-6e91d8ef8228@13.112.11.151:6668?flow=&security=tls&sni=baidu.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521日本 
vless://af50bdbf-1715-a461-cbb4-ebbea9ed338c@146.19.143.150:4768?flow=xtls-rprx-vision&encryption=none&security=reality&sni=yandex.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=1juiWgfU1-cGsbu9zxKCly7Vn3WGES5x6S86r90_vwc&sid=b7e284c9b786f709&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521爱沙尼亚 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpjdklJODVUclc2bjBPR3lmcEhWUzF1@45.87.175.166:8080?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0521荷兰 
vmess://eyJ2IjoiMiIsImFkZCI6InYyNS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyNSwic2N5IjoiYXV0byIsInBzIjoiMDUyMeWKoOaLv+WkpyIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
hysteria2://4463ca5d-0ae4-48c2-830a-eba4ee097bce@107.172.235.75:22262?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&mport=&os=#0521美国 
hysteria2://4463ca5d-0ae4-48c2-830a-eba4ee097bce@85.235.205.212:55182?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&mport=&os=#0521俄罗斯 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@103.21.244.215:443?flow=&encryption=none&security=tls&sni=www.strosoa.dpdns.org&type=xhttp&host=www.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521德国 
hysteria2://SOqicTlpXNLeme9q9NRhyhhXQtvd25ppZXUoKQv@45.82.121.72:21043?insecure=1&sni=high.work.lzg.me&alpn=&fp=&obfs=salamander&obfs-password=aTU86bZvnD4wt3OQn&mport=&os=#0521德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.25.226.97:443?flow=&encryption=none&security=tls&sni=www.strosoa.dpdns.org&type=xhttp&host=www.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521德国 
hysteria2://koTI7Ws6wsMZ7lDjNFHnDVvK@45.82.121.72:12347?insecure=1&sni=high.work.lzg.me&alpn=&fp=&obfs=salamander&obfs-password=JVJoN6YeNqTJKjm20Su&mport=&os=#0521德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.25.233.114:443?flow=&encryption=none&security=tls&sni=www.strosoa.dpdns.org&type=xhttp&host=www.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521德国 
anytls://x8iGpiv3TMn8xCgkN9DVZYpTQ0@45.82.121.72:21865?insecure=1&sni=high.work.lzg.me&alpn=h2&fp=&os=#0521德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.21.110.201:443?flow=&encryption=none&security=tls&sni=www.strosoa.dpdns.org&type=xhttp&host=www.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.18.154.3:443?flow=&encryption=none&security=tls&sni=www.strosoa.dpdns.org&type=xhttp&host=www.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521德国 
trojan://1a16f672-1fd9-4335-a62d-3b5a8f7e5747@45.82.121.72:23303?flow=&security=tls&sni=high.work.lzg.me&type=ws&header=none&host=high.work.lzg.me&path=/zBfrr76p4mA63L1wvcZPFgN%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZTE2Y2MzYjUtZTg1YS00NzY5LTk2ZjAtMmRjOGI5NjBkYjVkQDQ1LjgyLjEyMS43MjozMzA3Njp3czovM01yQjdQaFp6bldZR0JQT0JWN2tNVDlLc2tyODBIJTNGZWQlM0QyNTYwOmhpZ2gud29yay5semcubWU6bm9uZTp0bHM6aGlnaC53b3JrLmx6Zy5tZTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0521德国 
hysteria2://feCkljXbU1tsCIY2v@45.82.121.72:26458?insecure=1&sni=high.work.lzg.me&alpn=&fp=&obfs=salamander&obfs-password=PfJdPRGXgl0sFDd8Q&mport=&os=#0521德国 
trojan://5473fdf1-4b60-4ee8-b675-f8e4580cd6ea@45.82.121.72:57491?flow=&security=tls&sni=high.work.lzg.me&type=ws&header=none&host=high.work.lzg.me&path=/tC9juWkpxMmhEtWs%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521德国 
hysteria2://hSQrd2303DufDjAup7Mreo6QjHPAlup@45.82.121.72:32135?insecure=1&sni=high.work.lzg.me&alpn=&fp=&obfs=salamander&obfs-password=DzpFykDsLxHm3lRLcCva1InI&mport=&os=#0521德国 
hysteria2://wfHFlakscvY0t21eOGNyqShZblGzsgfsZJ@45.82.121.72:57751?insecure=1&sni=high.work.lzg.me&alpn=&fp=&obfs=salamander&obfs-password=c5PGVqIHX1ZZdFZHsJQTexwIpAHgDxWcZh&mport=&os=#0521德国 
vless://e5cdb910-208a-4863-9652-7377a24ec8d6@45.82.121.72:49704?flow=&encryption=none&security=tls&sni=high.work.lzg.me&type=ws&host=high.work.lzg.me&path=/PVQy51C6cjUSFmcRYrkLetOj%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@162.159.254.11:443?flow=&encryption=none&security=tls&sni=www.strosoa.dpdns.org&type=xhttp&host=www.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521德国 
vless://b26f2388-2d2e-4784-850b-8e6f869bf829@45.82.121.72:10423?flow=&encryption=none&security=tls&sni=high.work.lzg.me&type=ws&host=high.work.lzg.me&path=/ARodMl1yNdzV2anRzT%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521德国 
hysteria2://K1rAu66MFH3sCs2v@45.82.121.72:31084?insecure=1&sni=high.work.lzg.me&alpn=&fp=&obfs=salamander&obfs-password=BYP7M8JNbjXvRO0qKzi43t&mport=&os=#0521德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.49.21:443?flow=&encryption=none&security=tls&sni=www.strosoa.dpdns.org&type=xhttp&host=www.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@198.41.196.144:443?flow=&encryption=none&security=tls&sni=www.strosoa.dpdns.org&type=xhttp&host=www.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS43MiIsInBvcnQiOjIyMzY2LCJzY3kiOiJhdXRvIiwicHMiOiIwNTIx5b635Zu9IiwibmV0Ijoid3MiLCJpZCI6ImUxNmNjM2I1LWU4NWEtNDc2OS05NmYwLTJkYzhiOTYwZGI1ZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiaGlnaC53b3JrLmx6Zy5tZSIsInBhdGgiOiIvTjVKaU9BdFNrRHBDRDBGdlc/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6ImhpZ2gud29yay5semcubWUiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.25.151.253:443?flow=&encryption=none&security=tls&sni=www.strosoa.dpdns.org&type=xhttp&host=www.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@141.101.115.238:443?flow=&encryption=none&security=tls&sni=www.strosoa.dpdns.org&type=xhttp&host=www.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NjAxYTY0ZWMtNmQ0OS00M2FmLWJhNDctMDE2YmY3OTg2MzNmQDQ1LjgyLjEyMS43Mjo1ODMxNjp3czovTHJoQmo1ODQzejklM0ZlZCUzRDI1NjA6aGlnaC53b3JrLmx6Zy5tZTpub25lOnRsczpoaWdoLndvcmsubHpnLm1lOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0521德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@172.66.45.147:443?flow=&encryption=none&security=tls&sni=www.strosoa.dpdns.org&type=xhttp&host=www.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.21.235.139:443?flow=&encryption=none&security=tls&sni=www.strosoa.dpdns.org&type=xhttp&host=www.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521德国 
anytls://eTQMEuQVA85cMP4mCnL7E9J9wowWM@45.82.121.72:27911?insecure=1&sni=high.work.lzg.me&alpn=h2&fp=&os=#0521德国 
vless://d781fc15-a3b8-47c3-8911-77266aa78e39@45.82.121.72:14316?flow=&encryption=none&security=tls&sni=high.work.lzg.me&type=ws&host=high.work.lzg.me&path=/D9o9NLjfMv%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0521德国 


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
