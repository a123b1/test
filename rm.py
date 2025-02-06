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

hysteria2://base64,MjJhZjY5MTgtMTNkNi00YmFkLWE4MGQtNDZkZjQ4YzFkZGI0QDEwNy4xNzIuMjM1Ljc1OjQzNjE1P2luc2VjdXJlPTEmc25pPWR4b2JnNGF6bWsuZ2Fmbm9kZS5zYnMmYWxwbj0mZnA9Jm9zPQ==#0205美国 
trojan://base64,QWltZXJAMTA3LjE3NC43OS4xNDk6NDQzP2Zsb3c9JnNlY3VyaXR5PXRscyZzbmk9bmdlcHouYW1iZXJjYy5maWxlZ2Vhci1zZy5tZSZ0eXBlPXdzJmhlYWRlcj1ub25lJmhvc3Q9bmdlcHouYW1iZXJjYy5maWxlZ2Vhci1zZy5tZSZwYXRoPS8lM0ZlZCUzRDI1NjAmYWxwbj1odHRwLzEuMSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0205台湾 
trojan://base64,QWltZXJAMTEyLjE3MC4yNTUuNjc6NTAwMDA/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnBhdGg9LyUzRmVkJTNEMjU2MCZhbHBuPWh0dHAvMS4xJmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0205台湾 
trojan://base64,QWltZXJAMTE5LjE5Ni4zNC4xNzM6NTAwMDA/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnBhdGg9LyUzRmVkJTNEMjU2MCZhbHBuPWh0dHAvMS4xJmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0205台湾 
trojan://base64,QWltZXJAMTE5LjE5OC42Ny40ODoxMDAzMz9mbG93PSZzZWN1cml0eT10bHMmc25pPW5nZXB6LmFtYmVyY2MuZmlsZWdlYXItc2cubWUmdHlwZT13cyZoZWFkZXI9bm9uZSZob3N0PW5nZXB6LmFtYmVyY2MuZmlsZWdlYXItc2cubWUmcGF0aD0vJTNGZWQlM0QyNTYwJmFscG49aHR0cC8xLjEmZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0205台湾 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE5IiwicG9ydCI6NDQ2MTQsInNjeSI6ImF1dG8iLCJwcyI6IjAyMDXnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjEyMyIsInBvcnQiOjQ1NDAyLCJzY3kiOiJhdXRvIiwicHMiOiIwMjA1576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjY0LCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjYzIiwicG9ydCI6NDA1NjUsInNjeSI6ImF1dG8iLCJwcyI6IjAyMDXnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1jZmI6aEdrUTY5MTV0RA==@120.232.81.50:16088#0205香港 
ss://YWVzLTI1Ni1jZmI6aEdrUTY5MTV0RA==@120.232.81.50:15084#0205日本 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzQuMTAyLjIyOSIsInBvcnQiOjUyOTA4LCJzY3kiOiJhdXRvIiwicHMiOiIwMjA1576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjY0LCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://base64,QWltZXJAMTI1LjEzMC4xMDUuNjA6MTIxNTA/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnBhdGg9LyUzRmVkJTNEMjU2MCZhbHBuPWh0dHAvMS4xJmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0205台湾 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpmOGY3YUN6Y1BLYnNGOHAz@129.232.134.112:990#0205南非 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@13.125.215.15:443#0205韩国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@13.229.229.102:443#0205新加坡 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@13.231.129.236:443#0205日本 
trojan://base64,dGVsZWdyYW0taWQtcHJpdmF0ZXZwbnNAMTMuNDEuMTExLjE0OjIyMjIyP2Zsb3c9JnNlY3VyaXR5PXRscyZzbmk9dHJvamFuLmJ1cmdlcmlwLmNvLnVrJnR5cGU9dGNwJmhlYWRlcj1ub25lJmhvc3Q9JnBhdGg9JmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTAmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0205英国 
trojan://base64,dGVsZWdyYW0taWQtcHJpdmF0ZXZwbnNAMTMuNTMuMjI0LjkzOjIyMjIyP2Zsb3c9JnNlY3VyaXR5PXRscyZzbmk9dHJvamFuLmJ1cmdlcmlwLmNvLnVrJnR5cGU9dGNwJmhlYWRlcj1ub25lJmhvc3Q9JnBhdGg9JmFscG49aHR0cC8xLjEmZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0205瑞典 
ss://Y2hhY2hhMjA6cTJrU0dwNGF5RktC@14.18.253.178:8347#0205法国 
ss://Y2hhY2hhMjA6RHZQZkthOHZzVjlL@14.18.253.178:8334#0205新加坡 
vmess://eyJ2IjoiMiIsImFkZCI6IjE0NC4yMDIuMjIuNDUiLCJwb3J0Ijo4ODgxLCJzY3kiOiJhdXRvIiwicHMiOiIwMjA1576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkYjVhZmFlNC1hYzIzLTQxYTYtODM3OC1mMzA3YTlhNDc0MzYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJodHRwIiwiaG9zdCI6Im1vaS5pciIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://base64,MDA2MGZiM2EtMDZkMS01OTYyLTg1Y2ItNWYyMmFjNTI4ZDY4QDE1MS4xMDEuMTkzLjY6ODA/Zmxvdz0mZW5jcnlwdGlvbj1ub25lJnNlY3VyaXR5PSZzbmk9MC1NT1NJVjItMC5DT00mdHlwZT13cyZob3N0PTAtTU9TSVYyLTAuQ09NJnBhdGg9JmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0205波兰 
trojan://base64,QWltZXJAMTYyLjE1OS40NC40ODo0NDM/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnBhdGg9LyUzRmVkJTNEMjU2MCZhbHBuPWh0dHAvMS4xJmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0205台湾 
vless://base64,OTQxMGYyM2UtODRiMy00YzY2LWNjMDYtYjAxOGM4NTVhMjdhQDE3Mi4yNDUuMTU2LjE0NzoxNDY4MT9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9JnNuaT0mdHlwZT10Y3AmaG9zdD0mcGF0aD0maGVhZGVyVHlwZT1ub25lJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0205美国 
vless://base64,MDU0ZDUwM2QtNDc0OC00N2E2LTgxMTgtNzFhOTZjNTFmMmQ5QDE3Mi42Ni4xNjguMTk3OjQ0Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT1ObDItRnVsTC5Qckl2QXRlaVAuTmVUJnR5cGU9d3MmaG9zdD1ObDItRnVsTC5Qckl2QXRlaVAuTmVUJnBhdGg9L1ZMRVNTJmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0205荷兰 
vless://base64,OWIxZjU2NWQtNTBmYi00NDVmLTgzMmEtZDM5NDc1OTg5ZjcyQDE3Mi42Ni4xNjguMTk5OjQ0Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT1pVC1GVWxMLlBSSVZBVEVpUC5uRXQmdHlwZT13cyZob3N0PWlULUZVbEwuUFJJVkFURWlQLm5FdCZwYXRoPS9WTEVTUyZoZWFkZXJUeXBlPW5vbmUmYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0205意大利 
vless://base64,YWIxZDFkMTAtNWQyNi00YmM5LTg0NzYtMzUwZDIwNWJkZTI4QDE3Mi42Ni4xNjguMjAwOjQ0Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT1VSzEtdkxFc3MuZ3JlZW5TU0guT1JnJnR5cGU9d3MmaG9zdD1VSzEtdkxFc3MuZ3JlZW5TU0guT1JnJnBhdGg9L3ZsZXNzJmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0205直布罗陀 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@176.103.53.105:989#0205乌克兰 
trojan://base64,QWltZXJAMTc4LjEyOC4xOTguMTIwOjg0NDM/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnBhdGg9LyUzRmVkJTNEMjU2MCZhbHBuPWh0dHAvMS4xJmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0205台湾 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@18.141.25.54:443#0205新加坡 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@18.143.78.171:443#0205新加坡 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpmOGY3YUN6Y1BLYnNGOHAz@181.119.30.20:990#0205哥伦比亚 
trojan://base64,QWltZXJAMTgzLjEwMi43MS4yMDA6NTAwMDA/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnBhdGg9LyUzRmVkJTNEMjU2MCZhbHBuPWh0dHAvMS4xJmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0205台湾 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMjMiLCJwb3J0Ijo1MTAzNywic2N5IjoiYXV0byIsInBzIjoiMDIwNeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMjMiLCJwb3J0Ijo1NjYwMSwic2N5IjoiYXV0byIsInBzIjoiMDIwNeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://base64,ODliM2NiYmEtZTZhYy00ODVhLTk0ODEtOTc2YTA0MTVlYWI5QDE4NS4xOC4yNTAuMTI6ODA/Zmxvdz0mZW5jcnlwdGlvbj1ub25lJnNlY3VyaXR5PSZzbmk9JnR5cGU9d3MmaG9zdD1hbmEtU0VyVklDZS54QWJqQ0RaLndPUmtFcnMuZGVWJnBhdGg9LzFZNk1ONURGVjh6QjgyQWklM0ZlZCUzRDI1NjAmaGVhZGVyVHlwZT1ub25lJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0205西班牙 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.186.79.53:989#0205丹麦 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.193.49.88:989#0205爱沙尼亚 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989#0205波兰 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.237.185.160:989#0205立陶宛 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.47.252.251:989#0205秘鲁 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.47.253.171:989#0205厄瓜多尔 
trojan://base64,QWltZXJAMTg4LjE2Ni4xNjIuMjAxOjQ0Mz9mbG93PSZzZWN1cml0eT10bHMmc25pPW5nZXB6LmFtYmVyY2MuZmlsZWdlYXItc2cubWUmdHlwZT13cyZoZWFkZXI9bm9uZSZob3N0PW5nZXB6LmFtYmVyY2MuZmlsZWdlYXItc2cubWUmcGF0aD0vJTNGZWQlM0QyNTYwJmFscG49aHR0cC8xLjEmZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0205台湾 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@188.214.36.155:989#0205爱沙尼亚 
trojan://base64,QWltZXJAMTkyLjIyNy4yNDcuNzU6NDQzP2Zsb3c9JnNlY3VyaXR5PXRscyZzbmk9bmdlcHouYW1iZXJjYy5maWxlZ2Vhci1zZy5tZSZ0eXBlPXdzJmhlYWRlcj1ub25lJmhvc3Q9bmdlcHouYW1iZXJjYy5maWxlZ2Vhci1zZy5tZSZwYXRoPS8lM0ZlZCUzRDI1NjAmYWxwbj1odHRwLzEuMSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0205台湾 
vmess://eyJ2IjoiMiIsImFkZCI6IjE5OC40MS4yMDkuNzAiLCJwb3J0Ijo4MCwic2N5IjoiYXV0byIsInBzIjoiMDIwNeaWsOWKoOWdoSIsIm5ldCI6IndzIiwiaWQiOiJlNjU0MzMxOS0wNTc0LTQyYWMtYjc3OC0xYzQzMjVkNjI2ZjUiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImNodW5jaHVhbi5rZWppeGlhb3FpNjY2LnN0b3JlIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
trojan://base64,QWltZXJAMjEwLjIyMi4zMC4xODA6MTcxMDA/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnBhdGg9LyUzRmVkJTNEMjU2MCZhbHBuPWh0dHAvMS4xJmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0205台湾 
trojan://base64,QWltZXJAMjExLjE5OS42NS4xODY6MTQ1MjQ/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnBhdGg9LyUzRmVkJTNEMjU2MCZhbHBuPWh0dHAvMS4xJmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0205台湾 
trojan://base64,QWltZXJAMjExLjI1Mi4xMi4yMjc6NTAwMDA/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnBhdGg9LyUzRmVkJTNEMjU2MCZhbHBuPWh0dHAvMS4xJmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0205台湾 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@213.156.137.67:989#0205哈萨克 
ss://YWVzLTI1Ni1jZmI6cnBnYk5uVTlyRERVNGFXWg==@217.30.10.18:9094#0205波兰 
ss://YWVzLTI1Ni1jZmI6SmRtUks5Z01FcUZnczhuUA==@217.30.10.18:9003#0205波兰 
ss://YWVzLTI1Ni1jZmI6RkFkVXZNSlVxNXZEZ0tFcQ==@217.30.10.18:9006#0205波兰 
ss://YWVzLTI1Ni1jZmI6RVhOM1MzZVFwakU3RUp1OA==@217.30.10.18:9027#0205波兰 
ss://YWVzLTI1Ni1jZmI6QmVqclF2dHU5c3FVZU51Wg==@217.30.10.18:9024#0205波兰 
ss://YWVzLTI1Ni1jZmI6Rkc1ZGRMc01QYlY1Q3V0RQ==@217.30.10.18:9050#0205波兰 
ss://YWVzLTI1Ni1jZmI6TTN0MlpFUWNNR1JXQmpSYQ==@217.30.10.18:9011#0205波兰 
ss://YWVzLTI1Ni1jZmI6cDl6NUJWQURIMllGczNNTg==@217.30.10.18:9040#0205波兰 
ss://YWVzLTI1Ni1jZmI6UVdERHZWRTlucE51clFmQQ==@217.30.10.18:9026#0205波兰 
ss://YWVzLTI1Ni1jZmI6WkVUNTlMRjZEdkNDOEtWdA==@217.30.10.18:9005#0205波兰 
ss://YWVzLTI1Ni1jZmI6VWtYUnNYdlI2YnVETUcyWQ==@217.30.10.18:9001#0205波兰 
ss://YWVzLTI1Ni1jZmI6VVRKQTU3eXBrMlhLUXBubQ==@217.30.10.18:9033#0205波兰 
ss://YWVzLTI1Ni1jZmI6WFB0ekE5c0N1ZzNTUFI0Yw==@217.30.10.18:9025#0205波兰 
ss://YWVzLTI1Ni1jZmI6QndjQVVaazhoVUZBa0RHTg==@217.30.10.18:9031#0205波兰 
ss://YWVzLTI1Ni1jZmI6Z1lDWVhma1VRRXMyVGFKUQ==@217.30.10.18:9038#0205波兰 
ss://YWVzLTI1Ni1jZmI6THAyN3JxeUpxNzJiWnNxWA==@217.30.10.18:9045#0205波兰 
ss://YWVzLTI1Ni1jZmI6VFBxWDhlZGdiQVVSY0FNYg==@217.30.10.18:9079#0205波兰 
ss://YWVzLTI1Ni1jZmI6ZjhucEtnTnpka3NzMnl0bg==@217.30.10.18:9088#0205波兰 
ss://YWVzLTI1Ni1jZmI6d2ZMQzJ5N3J6WnlDbXV5dA==@217.30.10.18:9093#0205波兰 
trojan://base64,QWltZXJAMjIwLjk0LjcuODY6MTY0NDM/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnBhdGg9LyUzRmVkJTNEMjU2MCZhbHBuPWh0dHAvMS4xJmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0205波兰 
trojan://base64,QWltZXJAMjMuOTQuMjExLjE0ODo0NDM/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnBhdGg9LyUzRmVkJTNEMjU2MCZhbHBuPWh0dHAvMS4xJmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0205台湾 
trojan://base64,dGVsZWdyYW0taWQtZGlyZWN0dnBuQDMuMjIuMjUzLjI0NToyMjIyMj9mbG93PSZzZWN1cml0eT10bHMmc25pPXRyb2phbi5idXJnZXJpcC5jby51ayZ0eXBlPXRjcCZoZWFkZXI9bm9uZSZob3N0PSZwYXRoPSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0wJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0205美国 
trojan://base64,QWltZXJAMy4yMzAuMjA3LjU5Ojg0NDM/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnBhdGg9LyUzRmVkJTNEMjU2MCZhbHBuPWh0dHAvMS4xJmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0205台湾 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@3.35.138.163:443#0205韩国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.217.145.61:443#0205美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.218.228.243:443#0205美国 
trojan://base64,dGVsZWdyYW0taWQtcHJpdmF0ZXZwbnNAMzQuMjUwLjEyMy4xODg6MjIyMjI/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT10cm9qYW4uYnVyZ2VyaXAuY28udWsmdHlwZT10Y3AmaGVhZGVyPW5vbmUmaG9zdD0mcGF0aD0mYWxwbj1odHRwLzEuMSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0205爱尔兰 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.163.107.154:443#0205美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.91.132.50:443#0205美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@37.143.129.230:989#0205芬兰 
trojan://base64,aW5zdGFsbHNoaWVsZEAzOC4xODAuMjQ5LjE3Nzo4NDQzP2Zsb3c9JnNlY3VyaXR5PXRscyZzbmk9MzguMTgwLjI0OS4xNzcmdHlwZT10Y3AmaGVhZGVyPW5vbmUmaG9zdD0mcGF0aD0mYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0205新加坡 
vmess://eyJ2IjoiMiIsImFkZCI6IjM4LjU0Ljk0LjEyMiIsInBvcnQiOjIwNTMsInNjeSI6ImF1dG8iLCJwcyI6IjAyMDXnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiMmNhOGI5YzMtYTJjNy00ZjNlLWIzZjQtYWNkODU1MjVhY2UxIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiL0wwMjI5LTE2IiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjNoLXBvbGFuZDEuMDl2cG4uY29tIiwicG9ydCI6ODQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDIwNeazouWFsCIsIm5ldCI6IndzIiwiaWQiOiJhNDg1MDQ4MS05Yjk1LTQzMGYtOWIyZC0xOTJkMjQxMGI0ZjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvdm1lc3MvIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjE0NC40OC4xMjgiLCJwb3J0Ijo4NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwMjA15rOi5YWwIiwibmV0Ijoid3MiLCJpZCI6ImE0ODUwNDgxLTliOTUtNDMwZi05YjJkLTE5MmQyNDEwYjRmNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii92bWVzcy8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
trojan://base64,QWltZXJANDUuMTQ3LjUwLjE1NDo0NDM/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD1uZ2Vwei5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnBhdGg9LyUzRmVkJTNEMjU2MCZhbHBuPWh0dHAvMS4xJmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0205台湾 
trojan://base64,QWltZXJANDUuMTU1LjEyMS4xNjk6NDQzP2Zsb3c9JnNlY3VyaXR5PXRscyZzbmk9bmdlcHouYW1iZXJjYy5maWxlZ2Vhci1zZy5tZSZ0eXBlPXdzJmhlYWRlcj1ub25lJmhvc3Q9bmdlcHouYW1iZXJjYy5maWxlZ2Vhci1zZy5tZSZwYXRoPS8lM0ZlZCUzRDI1NjAmYWxwbj1odHRwLzEuMSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0205台湾 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToxUld3WGh3ZkFCNWdBRW96VTRHMlBn@45.158.171.132:8080#0205荷兰 
hysteria2://base64,ZG9uZ3RhaXdhbmcuY29tQDQ2LjE3LjQxLjE4OTo1MDcxNz9pbnNlY3VyZT0xJnNuaT13d3cuYmluZy5jb20mYWxwbj0mZnA9Jm9zPQ==#0205俄罗斯 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@47.129.101.151:443#0205新加坡 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@47.129.38.168:443#0205新加坡 
vmess://eyJ2IjoiMiIsImFkZCI6IjUwMDA4LmJhaWR1LWNkbi50b3AiLCJwb3J0Ijo1MDAwOCwic2N5IjoiYXV0byIsInBzIjoiMDIwNeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNzIyZWU2NjAtY2E1Ny00NjdmLTllZGEtNTczOTg1OTIxMmY5IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjUwMDExLmJhaWR1LWNkbi50b3AiLCJwb3J0Ijo1MDAxMSwic2N5IjoiYXV0byIsInBzIjoiMDIwNeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNzIyZWU2NjAtY2E1Ny00NjdmLTllZGEtNTczOTg1OTIxMmY5IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjUwMDEyLmJhaWR1LWNkbi50b3AiLCJwb3J0Ijo1MDAxMiwic2N5IjoiYXV0byIsInBzIjoiMDIwNeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiMjI0ZTNlZDQtOTZkMi00YWUwLThkMjQtMDcwYjAwMzkwNzRlIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://base64,dGVsZWdyYW0taWQtZGlyZWN0dnBuQDUyLjE4Ljk1LjEwODoyMjIyMj9mbG93PSZzZWN1cml0eT10bHMmc25pPXRyb2phbi5idXJnZXJpcC5jby51ayZ0eXBlPXRjcCZoZWFkZXI9bm9uZSZob3N0PSZwYXRoPSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0205爱尔兰 
trojan://base64,dGVsZWdyYW0taWQtZGlyZWN0dnBuQDUyLjYwLjIxMy45ODoyMjIyMj9mbG93PSZzZWN1cml0eT10bHMmc25pPXRyb2phbi5idXJnZXJpcC5jby51ayZ0eXBlPXRjcCZoZWFkZXI9bm9uZSZob3N0PSZwYXRoPSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0205加拿大 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@52.78.178.243:443#0205韩国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.185.251.195:443#0205美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.212.56.86:443#0205美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.214.157.34:443#0205美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.255.245.79:443#0205新加坡 
trojan://base64,dGVsZWdyYW0taWQtcHJpdmF0ZXZwbnNANTQuNzIuMTIyLjQxOjIyMjIyP2Zsb3c9JnNlY3VyaXR5PXRscyZzbmk9dHJvamFuLmJ1cmdlcmlwLmNvLnVrJnR5cGU9dGNwJmhlYWRlcj1ub25lJmhvc3Q9JnBhdGg9JmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0205爱尔兰 
trojan://base64,QWltZXJANTkuMC4yMDEuMjMxOjM1NTMxP2Zsb3c9JnNlY3VyaXR5PXRscyZzbmk9bmdlcHouYW1iZXJjYy5maWxlZ2Vhci1zZy5tZSZ0eXBlPXdzJmhlYWRlcj1ub25lJmhvc3Q9bmdlcHouYW1iZXJjYy5maWxlZ2Vhci1zZy5tZSZwYXRoPS8lM0ZlZCUzRDI1NjAmYWxwbj1odHRwLzEuMSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0205台湾 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpHNFIwOGliN3k0MjcweXpubExwU1FQ@77.83.246.74:443#0205波兰 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpXMm50SWFJanlvaDZiVkZsWHZRcllz@80.242.56.218:50042#0205荷兰 
vless://base64,ZGYwNjgwY2EtZTQzYy00OThkLWVkODYtOGUxOTZlZWRkMDEyQDg0LjMyLjEzMS4xNzg6ODg4MD9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9JnNuaT0mdHlwZT1ncnBjJmhvc3Q9JnNlcnZpY2VOYW1lPSZtb2RlPW5vbmUmYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0205美国 
vless://base64,MTJjZWFkZTktMjBmNy00MTVjLTk3NjUtN2I0NGVjMzllN2JjQDg1LjEzMy4yMDEuMjI6MjA1Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT1sZHBudXVyejMuaW1hbWhhc3Nhbi5pbmZvJnR5cGU9d3MmaG9zdD1sZHBudXVyejMuaW1hbWhhc3Nhbi5pbmZvJnBhdGg9L3FsSlBXa2RHNWR1WTF4TXk0UnZRamRGaUwmaGVhZGVyVHlwZT1ub25lJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0205瑞典 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989#0205斯洛文尼亚共和国 
vless://base64,MmQ3YzdhYTUtMzY0YS00ZGJiLTkzN2EtZjhlNGY1ZjczMDA3QDk0LjEzMS4xMTEuMTk1OjQ0Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT1kZTQuY29ubmVjdG9uLnN1cmYmdHlwZT13cyZob3N0PWRlNC5jb25uZWN0b24uc3VyZiZwYXRoPS92bGVzcyZoZWFkZXJUeXBlPW5vbmUmYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0205德国 
vless://base64,ZDM0MmQxMWUtZDQyNC00NTgzLWIzNmUtNTI0YWIxZjBhZmE0QDk0LjI1MC4yNDYuMjAwOjgwODA/Zmxvdz0mZW5jcnlwdGlvbj1ub25lJnNlY3VyaXR5PXRscyZzbmk9YS5taWZlbmcudXMua2cmdHlwZT13cyZob3N0PWEubWlmZW5nLnVzLmtnJnBhdGg9LyUzRmVkJTNEMjU2MCZoZWFkZXJUeXBlPW5vbmUmYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0205韩国 
trojan://base64,NjUwODY1MjAzMDc3NjQ5MDBAYXJyaXZpbmctbG9uZ2hvcm4uc2hpbmVyNDI3LnNraW46NDQzP2Zsb3c9JnNlY3VyaXR5PXRscyZzbmk9YXJyaXZpbmctbG9uZ2hvcm4uc2hpbmVyNDI3LnNraW4mdHlwZT10Y3AmaGVhZGVyPW5vbmUmaG9zdD0mcGF0aD0mYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MCZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0205美国 
ss://YWVzLTEyOC1nY206ZTJjNjJhNzMtMzEzMi00OGE2LWEwMjAtMjVjM2FlMGQ4YWYy@cu1.guguyun.xyz:23733#0205美国 
trojan://base64,NjUwODY1MjAzMDc3NjQ5MDBAZHluYW1pYy1zaHJldy5zaGluZXI0Mjcuc2tpbjo0NDM/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1keW5hbWljLXNocmV3LnNoaW5lcjQyNy5za2luJnR5cGU9dGNwJmhlYWRlcj1ub25lJmhvc3Q9JnBhdGg9JmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTAmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0205新加坡 
trojan://base64,NjUwODY1MjAzMDc3NjQ5MDBAZW5nYWdlZC1jYXR0bGUuc2hpbmVyNDI3LnNraW46NDQzP2Zsb3c9JnNlY3VyaXR5PXRscyZzbmk9ZW5nYWdlZC1jYXR0bGUuc2hpbmVyNDI3LnNraW4mdHlwZT10Y3AmaGVhZGVyPW5vbmUmaG9zdD0mcGF0aD0mYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MCZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0205韩国 
vless://base64,YzgzNDk0NmItYzg3Ni01MGE4LTg0Y2UtY2FkM2NiYThiZDg2QGZhY3VsdHkudWNkYXZpcy5lZHU6NDQzP2Zsb3c9JmVuY3J5cHRpb249bm9uZSZzZWN1cml0eT10bHMmc25pPWZhY3VsdHkudWNkYXZpcy5lZHUmdHlwZT13cyZob3N0PVBBQkxPTy1NT1NUQUZBLkNPTSZwYXRoPS8maGVhZGVyVHlwZT1ub25lJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0205比利时 
vless://base64,YWIyMjAyNTUtOTBmNC00YjMyLTg1MjYtM2UxZmNlMGUzNTIzQGZpc2hsYWIudWNkYXZpcy5lZHU6NDQzP2Zsb3c9JmVuY3J5cHRpb249bm9uZSZzZWN1cml0eT10bHMmc25pPWZpc2hsYWIudWNkYXZpcy5lZHUmdHlwZT13cyZob3N0PUpvaW5CZWRlLS12bWVzc29yZy0tdm1lc3NvcmcuaVImcGF0aD0vJTQwdm1lc3NvcmctLS0tJTQwdm1lc3NvcmctLS0tLSU0MHZtZXNzb3JnLS0tLSU0MHZtZXNzb3JnLS0tLSU0MHZtZXNzb3JnLS0tLSU0MHZtZXNzb3JnLS0tLSU0MHZtZXNzb3JnLS0tLSU0MHZtZXNzb3JnLS0tLSU0MHZtZXNzb3JnLS0tLSU0MHZtZXNzb3JnLS0tLSU0MHZtZXNzb3JnLS0tLSU0MHZtZXNzb3JnJTNGZWQlM0QyNDgwJmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0205德国 
trojan://base64,NjUwODY1MjAzMDc3NjQ5MDBAZ3JhdGVmdWwtbGFyay5zaGluZXI0Mjcuc2tpbjo0NDM/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1ncmF0ZWZ1bC1sYXJrLnNoaW5lcjQyNy5za2luJnR5cGU9dGNwJmhlYWRlcj1ub25lJmhvc3Q9JnBhdGg9JmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0205美国 
vless://base64,YWIzYmVlMzEtNmQ1Ni00YTUwLThhODQtNzBlMTE0MzUyNzgzQGtub3dsZWRnZW1hcC51Ym50ZGRucy5jb206NDQzP2Zsb3c9JmVuY3J5cHRpb249bm9uZSZzZWN1cml0eT10bHMmc25pPWtub3dsZWRnZW1hcC51Ym50ZGRucy5jb20mdHlwZT13cyZob3N0PWtub3dsZWRnZW1hcC51Ym50ZGRucy5jb20mcGF0aD0vZ2V0dXBkYXRlcyZoZWFkZXJUeXBlPW5vbmUmYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0205保加利亚 
ss://YWVzLTEyOC1nY206YWJiZDU4NTctZDRjYS00MWFjLTk2YWMtN2UzYjhhZDRmMGM2@mdss-tw.04z3susick.download:12031#0205台湾 
ss://YWVzLTEyOC1nY206YWJiZDU4NTctZDRjYS00MWFjLTk2YWMtN2UzYjhhZDRmMGM2@mdss-tw.04z3susick.download:12029#0205台湾 
vmess://eyJ2IjoiMiIsImFkZCI6InBsZXguY29tIiwicG9ydCI6ODAsInNjeSI6ImF1dG8iLCJwcyI6IjAyMDXlvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiY2EzODc1OTctZDc5ZS00OGMyLTg5YTctZTJkYzY2YTg4YTcwIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ0ZWxlZ3JhbS1pc3Z2cG4uaXIiLCJwYXRoIjoiL3JhY2V2cG4/dGVsZWdyYW0tQElTVnZwbi10ZWxlZ3JhbS1ASVNWdnBuLXRlbGVncmFtLUBJU1Z2cG4tdGVsZWdyYW0tQElTVnZwbiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTozRkIyM0ExOS05NDI0LTQwQzctOTEzOS0zNTQwMjI4MjgzRkE=@sgp.fastsoonlink.com:40005#0205新加坡 
ss://YWVzLTEyOC1nY206MWEyM2JmZWYtNzNkZi00NWY2LThjYTMtNTgyNzFmOTVhZTMw@south.sf0jm.xyz:49228#0205斯洛伐克 
vmess://eyJ2IjoiMiIsImFkZCI6InRrLmh6bHQudGtkZG5zLnh5eiIsInBvcnQiOjIyNjQxLCJzY3kiOiJhdXRvIiwicHMiOiIwMjA1576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6Ijk4ZTk2YzlmLTRiYjMtMzlkNC05YTJjLWZhYzA0MjU3ZjdjNyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoienhqcC1hLnRrb25nLmNjIiwicGF0aCI6Ii8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InhnLmRhc2h1YWkuY3lvdSIsInBvcnQiOjE5OTAxLCJzY3kiOiJhdXRvIiwicHMiOiIwMjA16aaZ5rivIiwibmV0IjoidGNwIiwiaWQiOiI0OGUxZjI4ZS0yYTBiLTQ3ZWUtYjgyYi04MTBlNzU0MzkyNzQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InhnLmRhc2h1YWkuY3lvdSIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://base64,YjQyOTUzZDUtY2EwMi00ZTdkLTg2NmMtYmVkNTAyNzE3OTc5QDUuMTgwLjI1My4zNzo1MjYwMz9mbG93PSZzZWN1cml0eT10bHMmc25pPXd3dy5qcXVlcnkuY29tJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD13d3cuanF1ZXJ5LmNvbSZwYXRoPS9PbVhkcWpJWGVWJTNGZWQlM0QyNTYwJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0205德国 
vless://base64,Y2E0NGJmZWQtMGUwOS00MTlhLWE2M2EtMWY0OThmY2Y1Y2YyQDUuMTgwLjI1My4zNzozOTYyNz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT13d3cuanF1ZXJ5LmNvbSZ0eXBlPXdzJmhvc3Q9d3d3LmpxdWVyeS5jb20mcGF0aD0vQko2cTJxUlcycCUzRmVkJTNEMjU2MCZoZWFkZXJUeXBlPW5vbmUmYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0205德国 
hysteria2://base64,Y1pyMVJxWTB4QmJYSFJDTlZHZkg1TjlhTUtFbmhOZmNQblFBQmxANS4xODAuMjUzLjM3OjMyODQ1P2luc2VjdXJlPTEmc25pPXd3dy5qcXVlcnkuY29tJmFscG49JmZwPSZvYmZzPXNhbGFtYW5kZXImb2Jmcy1wYXNzd29yZD0yeWF4TTZ6RkNBMWNDME9Hd20mb3M9#0205德国 
hysteria2://base64,eTZPWHdWTmdqcFU0VFMzeUNzTlpTUmg5YW5HTFV2M0hIY0FoQDUuMTgwLjI1My4zNzo0MTQyNz9pbnNlY3VyZT0xJnNuaT13d3cuanF1ZXJ5LmNvbSZhbHBuPSZmcD0mb2Jmcz1zYWxhbWFuZGVyJm9iZnMtcGFzc3dvcmQ9aVY2TlRYeGs2OXpBY1VFcHFDJm9zPQ==#0205德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MzYxNjIyOTEtNzM5MC00YzgzLWFiZTEtODMzYzE0OTkzY2Y3QDUuMTgwLjI1My4zNzo0MTgzOTp3czovV0diRXBjaUFSWUk5YzRvUGZndCUzRmVkJTNEMjU2MDp3d3cuanF1ZXJ5LmNvbTpub25lOnRsczp3d3cuanF1ZXJ5LmNvbTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0205德国 
trojan://base64,Y2JiNzc5ODQtNzBjZi00ZjY1LWIxMTQtMGE0YTZkNmJkNjI1QDUuMTgwLjI1My4zNzoxNjQxOD9mbG93PSZzZWN1cml0eT10bHMmc25pPXd3dy5qcXVlcnkuY29tJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD13d3cuanF1ZXJ5LmNvbSZwYXRoPS9JVHhubGhPUGhnWjNBdU1rJTNGZWQlM0QyNTYwJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0205德国 
hysteria2://base64,V3NUQU1xWmY1dFJIRTlUS2F0MFBVSDVjVURjODRGRXZ4QDUuMTgwLjI1My4zNzozNTAwND9pbnNlY3VyZT0xJnNuaT13d3cuanF1ZXJ5LmNvbSZhbHBuPSZmcD0mb2Jmcz1zYWxhbWFuZGVyJm9iZnMtcGFzc3dvcmQ9UjhIY1JXNkVJVEdhRnVEeDNsTTNGRW0mb3M9#0205德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4zNyIsInBvcnQiOjI2NjkyLCJzY3kiOiJhdXRvIiwicHMiOiIwMjA15b635Zu9IiwibmV0Ijoid3MiLCJpZCI6IjZmNTUwZGY5LTliYTMtNDA1Ny1hZjNkLWVhYjM4ZTY1ZDE3NiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoid3d3LmpxdWVyeS5jb20iLCJwYXRoIjoiL1k/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6Ind3dy5qcXVlcnkuY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4zNyIsInBvcnQiOjQxMjcsInNjeSI6ImF1dG8iLCJwcyI6IjAyMDXlvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiZGNjOGE4YzMtYjMzMS00MTA1LTgzNDItMDVkODgzOGQwNjUyIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ3d3cuanF1ZXJ5LmNvbSIsInBhdGgiOiIvajI1aThIWGNkZ1BiSHlDUXFDR0hEME5HP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ3d3cuanF1ZXJ5LmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZGNjOGE4YzMtYjMzMS00MTA1LTgzNDItMDVkODgzOGQwNjUyQDUuMTgwLjI1My4zNzozNTcxMDp3czovaCUzRmVkJTNEMjU2MDp3d3cuanF1ZXJ5LmNvbTpub25lOnRsczp3d3cuanF1ZXJ5LmNvbTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0205德国 
hysteria2://base64,ODRUeTB2YUJFZ09iUnVBRGpZWUA1LjE4MC4yNTMuMzc6MjQ4MzE/aW5zZWN1cmU9MSZzbmk9d3d3LmpxdWVyeS5jb20mYWxwbj0mZnA9Jm9iZnM9c2FsYW1hbmRlciZvYmZzLXBhc3N3b3JkPU90aDZZTDRSMFlCeWdhOXImb3M9#0205德国 
vless://base64,MDdlMzM1ZmYtYmU2YS00MTY2LTg3MGMtY2Q3Y2QwZTBmYWVkQDUuMTgwLjI1My4zNzozMzc3Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT13d3cuanF1ZXJ5LmNvbSZ0eXBlPXdzJmhvc3Q9d3d3LmpxdWVyeS5jb20mcGF0aD0vQkVvNmRDJTNGZWQlM0QyNTYwJmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0205德国 
trojan://base64,NzFlM2RiZWUtYjAyZi00MDRhLWI4MWUtNTdhYmZhOTJjMmEyQDUuMTgwLjI1My4zNzo2MzgwOD9mbG93PSZzZWN1cml0eT10bHMmc25pPXd3dy5qcXVlcnkuY29tJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD13d3cuanF1ZXJ5LmNvbSZwYXRoPS9aR0w3JTNGZWQlM0QyNTYwJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0205德国 
hysteria2://base64,OTNqbmYzMkZoc3JjdGxjSXA2R3dCTElhSzlIR0lYNmZaMjZtQDUuMTgwLjI1My4zNzozNDkzOD9pbnNlY3VyZT0xJnNuaT13d3cuanF1ZXJ5LmNvbSZhbHBuPSZmcD0mb2Jmcz1zYWxhbWFuZGVyJm9iZnMtcGFzc3dvcmQ9MEU4N1N6ZWk0MjJGMFNacmFvMiZvcz0=#0205德国 
trojan://base64,ZGNjOGE4YzMtYjMzMS00MTA1LTgzNDItMDVkODgzOGQwNjUyQDUuMTgwLjI1My4zNzo1MjUxMD9mbG93PSZzZWN1cml0eT10bHMmc25pPXd3dy5qcXVlcnkuY29tJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD13d3cuanF1ZXJ5LmNvbSZwYXRoPS8xUTYyUll0ZGxGT0VjSnZFWSUzRmVkJTNEMjU2MCZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0205德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4zNyIsInBvcnQiOjI2Njc1LCJzY3kiOiJhdXRvIiwicHMiOiIwMjA15b635Zu9IiwibmV0Ijoid3MiLCJpZCI6ImFhNGM0NDgyLTdkYjctNGE0ZS1hNDZkLTgyZmNkOTFjMGM2NSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoid3d3LmpxdWVyeS5jb20iLCJwYXRoIjoiL2o1VjE/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6Ind3dy5qcXVlcnkuY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NDc4MjY1YzEtZDY2Mi00NjdkLWEzZWEtODc0NTk4MTQ2N2Y2QDUuMTgwLjI1My4zNzoyMTU1NTp3czovdjhjQlI2a3RCRmNWdjFqaVBUN3olM0ZlZCUzRDI1NjA6d3d3LmpxdWVyeS5jb206bm9uZTp0bHM6d3d3LmpxdWVyeS5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0205德国 
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
