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

ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@103.106.229.219:989#0219新加坡 
vless://base64,NGUwZTA5MDEtMzc0YS00YzFmLWY3MWUtOWY4NDFlMzY0ODllQDEwNC4xNy4xNDguMjI6MjA4Mj9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9JnNuaT0mdHlwZT13cyZob3N0PW5vdmluc29mdC5pci5vcmFkb3Nob3AuY29tLnBlcnNpYW5nc20uaXIuZGlnaWthbGEuY29tLmFiYWRpcy5pci5zaGFkLmlyLmRpdmFyLmlyLmRvd25sb2FkbHkuY29tLmFwYXJhdC5jb20uY2FmZWJhemFyLmlyLnZhcnplc2gzLmNvbS5uaW5pc2l0ZS5jb20uYWJhZGlzLmlyLmJhbWEuaXIucDMwZG93bmxvYWQuaXIudGVsZXdlYmlvbi5ibWkuaXIuc2hhZC5pci5tYXlrZXQuY29tLm5pbmlzaXRlLnRvcC4mcGF0aD0vJTQwc3Bpa2V2cG4tJTQwc3Bpa2V2cG4tJTQwc3Bpa2V2cG4tJTQwc3Bpa2V2cG4tJTQwc3Bpa2V2cG4tJTQwc3Bpa2V2cG4lM0ZlZCUzRDIwODImaGVhZGVyVHlwZT1ub25lJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0219美国 
vless://base64,ZGNmNzQyOTktNDJjMi00YTVjLTkwMGUtMmM5MmIxNmUwZjhlQDEwNC4yMC4yMTIuMjI4OjQ0Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT1ub0ZpTGVwYW5FTC5QYUdFcy5EZVYmdHlwZT13cyZob3N0PW5vZmlsZXBhbmVsLnBhZ2VzLmRldiZwYXRoPS9wZmhGcGdvY3Q0VU05b0xxJTNGZWQlM0QyNTYwJmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0219美国 
hysteria2://base64,NDU0N2RlYzctMTM4OS00NTM2LWE0NzUtYWE4Mjk1Zjk4ZDJmQDEwNy4xNzIuMjM1Ljc1OjQzNjE1P2luc2VjdXJlPTEmc25pPWR4b2JnNGF6bWsuZ2Fmbm9kZS5zYnMmYWxwbj0mZnA9Jm9zPQ==#0219阿富汗 
hysteria2://base64,ZWJhZTdhMjctNjc0Yi00YTIyLWIxYmUtZmY0NTZjZGEyMjEwQDEwNy4xNzIuMjM1Ljc1OjQzNjE1P2luc2VjdXJlPTEmc25pPWR4b2JnNGF6bWsuZ2Fmbm9kZS5zYnMmYWxwbj0mZnA9Jm9zPQ==#0219阿富汗 
trojan://base64,QWltZXJAMTA3LjE3My4xNDkuMTIwOjIwODc/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1hZ2VweS5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD1hZ2VweS5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnBhdGg9LyUzRmVkJTNEMjU2MCZhbHBuPWh0dHAvMS4xJmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0219美国 
trojan://base64,QWltZXJAMTA4LjE2NS4xNTIuMTEzOjQ0Mz9mbG93PSZzZWN1cml0eT10bHMmc25pPWFnZXB0LmFtYmVyY2MuZmlsZWdlYXItc2cubWUmdHlwZT13cyZoZWFkZXI9bm9uZSZob3N0PWFnZXB0LmFtYmVyY2MuZmlsZWdlYXItc2cubWUmcGF0aD0vJTNGZWQlM0QyNTYwJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0219 
trojan://base64,QWltZXJAMTA4LjE2NS4xNTIuMjAyOjIwODM/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1hZ2VweS5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD1hZ2VweS5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnBhdGg9LyUzRmVkJTNEMjU2MCZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0219 
trojan://base64,QWltZXJAMTA4LjE2NS4xNTIuMzY6MjA5Nj9mbG93PSZzZWN1cml0eT10bHMmc25pPWFnZXB5LmFtYmVyY2MuZmlsZWdlYXItc2cubWUmdHlwZT13cyZoZWFkZXI9bm9uZSZob3N0PWFnZXB5LmFtYmVyY2MuZmlsZWdlYXItc2cubWUmcGF0aD0vJTNGZWQlM0QyNTYwJmFscG49aHR0cC8xLjEmZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0219美国 
ss://YWVzLTEyOC1nY206YjYzN2YyZTQ3Yjc4MjdiMzA4ZWJmMzk5MDA4MDc1ZDI=@119.167.230.252:28164#0219日本 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE5IiwicG9ydCI6NDQ2MTQsInNjeSI6ImF1dG8iLCJwcyI6IjAyMTnnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjEyMyIsInBvcnQiOjQ1NDAyLCJzY3kiOiJhdXRvIiwicHMiOiIwMjE5576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjY0LCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQwIiwicG9ydCI6NTQwODIsInNjeSI6ImF1dG8iLCJwcyI6IjAyMTnnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1jZmI6aEdrUTY5MTV0RA==@120.232.81.50:15084#0219日本 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzQuMTAyLjIyOSIsInBvcnQiOjUyOTA4LCJzY3kiOiJhdXRvIiwicHMiOiIwMjE5576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjY0LCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://base64,QWltZXJAMTI5LjE1NC4yMDcuMjAzOjQ0Mz9mbG93PSZzZWN1cml0eT10bHMmc25pPWFnZXB0LmFtYmVyY2MuZmlsZWdlYXItc2cubWUmdHlwZT13cyZoZWFkZXI9bm9uZSZob3N0PWFnZXB0LmFtYmVyY2MuZmlsZWdlYXItc2cubWUmcGF0aD0vJTNGZWQlM0QyNTYwJmFscG49aHR0cC8xLjEmZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0219澳大利亚 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@13.213.40.92:443#0219新加坡 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@134.255.210.49:989#0219德国 
vless://base64,NTQ2OTRhMzMtYThkYy00N2RkLWJjMzgtYWNkMzk3MWUwMDU1QDEzNS4xNDguNzQuMTU0OjQ0Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT0xNDcxMzUwMDQwMDIuc2VjMjBvcmcuY29tJnR5cGU9dGNwJmhvc3Q9JnBhdGg9JmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0219美国 
hysteria2://base64,aU1xWTN1R181cGdFajNoQ2Z5SEItMHZCQDE0My4xOTguMjM1LjQ5OjQ0Mz9pbnNlY3VyZT0xJnNuaT0mYWxwbj0mZnA9Jm9zPQ==#0219美国 
vless://base64,M2I5YmM3NzMtMDVlYi00ZDVmLThjMWYtNTczNDJjMGM0ZjQwQDE0Ny4xMzUuMTAuMTAzOjQ0Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT0xNDcxMzUwMTAxMDMuc2VjMTlvcmcuY29tJnR5cGU9dGNwJmhvc3Q9JnBhdGg9JmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0219美国 
vless://base64,M2I5YmM3NzMtMDVlYi00ZDVmLThjMWYtNTczNDJjMGM0ZjQwQDE0Ny4xMzUuMTI1LjExNzo0NDM/Zmxvdz0mZW5jcnlwdGlvbj1ub25lJnNlY3VyaXR5PXRscyZzbmk9MTQ3MTM1MDEwMTAzLnNlYzE5b3JnLmNvbSZ0eXBlPXRjcCZob3N0PSZwYXRoPSZoZWFkZXJUeXBlPW5vbmUmYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MCZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0219美国 
vless://base64,M2I5YmM3NzMtMDVlYi00ZDVmLThjMWYtNTczNDJjMGM0ZjQwQDE0Ny4xMzUuMTI1LjEyMDo0NDM/Zmxvdz0mZW5jcnlwdGlvbj1ub25lJnNlY3VyaXR5PXRscyZzbmk9MTQ3MTM1MDEwMTAzLnNlYzE5b3JnLmNvbSZ0eXBlPXRjcCZob3N0PSZwYXRoPSZoZWFkZXJUeXBlPW5vbmUmYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0219美国 
trojan://base64,dGVsZWdyYW0taWQtcHJpdmF0ZXZwbnNAMTUuMTg4LjE5OS4xNzA6MjIyMjI/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT10cm9qYW4uYnVyZ2VyaXAuY28udWsmdHlwZT10Y3AmaGVhZGVyPW5vbmUmaG9zdD0mcGF0aD0mYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0219法国 
vless://base64,NzJhZWFjYjAtNDlhMy00MWIwLWE0ZjYtMzgwZDNiZTg4YTVlQDE1MS4xMDEuMi4xMzM6NDQzP2Zsb3c9JmVuY3J5cHRpb249bm9uZSZzZWN1cml0eT10bHMmc25pPWxpdmUud2tycS5jb20mdHlwZT13cyZob3N0PWJhbGUuYWkmcGF0aD0vd3MmaGVhZGVyVHlwZT1ub25lJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0219美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@154.90.62.168:989#0219韩国 
ss://YWVzLTI1Ni1nY206NTNSSVVRRFpSM0IyM1RBMw==@156.231.104.18:18008#0219日本 
ss://YWVzLTI1Ni1nY206NE9BS0o4Q0FTRVJBV1hJMQ==@156.231.104.23:18013#0219日本 
ss://YWVzLTI1Ni1nY206UEdGMlRHVUNIUUJDNUlQNQ==@156.231.104.26:18016#0219日本 
ss://YWVzLTI1Ni1nY206TUhaVUVPWDNLQlhBVjA5Sw==@156.245.190.16:15007#0219南非 
ss://YWVzLTI1Ni1nY206WkRHQzBRMkUxMTJVQUpPNg==@156.245.190.23:15014#0219南非 
vless://base64,MDU0ZDUwM2QtNDc0OC00N2E2LTgxMTgtNzFhOTZjNTFmMmQ5QDE3Mi42Ni4xNjguMTk3OjQ0Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT1ObDItRnVsTC5Qckl2QXRlaVAuTmVUJnR5cGU9d3MmaG9zdD1ObDItRnVsTC5Qckl2QXRlaVAuTmVUJnBhdGg9L1ZMRVNTJmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0219美国 
vless://base64,ZjhmMTc2M2YtMjQxMS00MTcwLTkwM2QtMGFkMzBhNDlkMWM1QDE3Mi42Ni4xNjguMTk5OjQ0Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT1DYS1GdUxMLlBSaVZBdGVpUC5uZVQmdHlwZT13cyZob3N0PUNhLUZ1TEwuUFJpVkF0ZWlQLm5lVCZwYXRoPS9WTEVTUyZoZWFkZXJUeXBlPW5vbmUmYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0219美国 
trojan://base64,cUNmdTh0JHN7Mm07c1R4bUAxNzIuNjYuNDQuMTk0OjIwNTM/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1KT2luTWFIZElTZVJ2RXItQzFDLlBhR0VTLmRFViZ0eXBlPXdzJmhlYWRlcj1ub25lJmhvc3Q9am9pbm1haGRpc2VydmVyLWMxYy5wYWdlcy5kZXYmcGF0aD0vdHJqOUZJMm9JR243ZFpjNGczJTNGZWQlM0QyNTYwJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0219美国 
trojan://base64,OlojJTNjZElHJ2MqOypPfUAxNzIuNjYuNDcuODM6NDQzP2Zsb3c9JnNlY3VyaXR5PXRscyZzbmk9Sm9pbm1BaERpU2VSdkVSLWNzbi5QYUdlUy5ERXYmdHlwZT13cyZoZWFkZXI9bm9uZSZob3N0PWpvaW5tYWhkaXNlcnZlci1jc24ucGFnZXMuZGV2JnBhdGg9L3RyVnhYamM5MDMxTUM4c250RiUzRmVkJTNEMjU2MCZhbHBuPWh0dHAvMS4xJTJDaDImZnA9cmFuZG9taXplZCZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0219美国 
trojan://base64,dGVsZWdyYW0taWQtcHJpdmF0ZXZwbnNAMTguMTM0LjUwLjEwMToyMjIyMj9mbG93PSZzZWN1cml0eT10bHMmc25pPXRyb2phbi5idXJnZXJpcC5jby51ayZ0eXBlPXRjcCZoZWFkZXI9bm9uZSZob3N0PSZwYXRoPSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0219美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@18.181.176.166:443#0219日本 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo1OTEwNCwic2N5IjoiYXV0byIsInBzIjoiMDIxOeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.186.79.53:989#0219丹麦 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.193.49.88:989#0219罗马尼亚 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.173:989#0219葡萄牙 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpZVE5qTkRZNQ==@185.234.64.35:8388#0219 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.237.185.160:989#0219美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.47.252.251:989#0219美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.47.253.171:989#0219美国 
trojan://base64,QWltZXJAMTg4LjE2NC4xNTkuMTcxOjQ0Mz9mbG93PSZzZWN1cml0eT10bHMmc25pPWFnZXB0LmFtYmVyY2MuZmlsZWdlYXItc2cubWUmdHlwZT13cyZoZWFkZXI9bm9uZSZob3N0PWFnZXB0LmFtYmVyY2MuZmlsZWdlYXItc2cubWUmcGF0aD0vJTNGZWQlM0QyNTYwJmFscG49aHR0cC8xLjEmZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0219新加坡 
trojan://base64,QWltZXJAMTg4LjE2NC4xNTkuOTE6MjA4Mz9mbG93PSZzZWN1cml0eT10bHMmc25pPWFnZXB5LmFtYmVyY2MuZmlsZWdlYXItc2cubWUmdHlwZT13cyZoZWFkZXI9bm9uZSZob3N0PWFnZXB5LmFtYmVyY2MuZmlsZWdlYXItc2cubWUmcGF0aD0vJTNGZWQlM0QyNTYwJmFscG49aHR0cC8xLjEmZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0219新加坡 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@188.214.36.155:989#0219罗马尼亚 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4OC42OC4yNTAuMjAyIiwicG9ydCI6MTUwNjcsInNjeSI6ImF1dG8iLCJwcyI6IjAyMTnms6LlhbAiLCJuZXQiOiJ3cyIsImlkIjoiOTEzYmI5MjEtMTBhYi00OTVhLTkxOGQtMGI0YzY3NTQ1MGM3IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiL3ZtZXNzLWFyZ28/ZWQ9MjA0OCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://base64,QWltZXJAMTkzLjEyMi4xMjUuMjA5OjQ4OTc1P2Zsb3c9JnNlY3VyaXR5PXRscyZzbmk9YWdlcHkuYW1iZXJjYy5maWxlZ2Vhci1zZy5tZSZ0eXBlPXdzJmhlYWRlcj1ub25lJmhvc3Q9YWdlcHkuYW1iZXJjYy5maWxlZ2Vhci1zZy5tZSZwYXRoPS8lM0ZlZCUzRDI1NjAmYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0219 
hysteria2://base64,ZG9uZ3RhaXdhbmcuY29tQDE5NS4xNTQuMzMuNzA6MTM4NjE/aW5zZWN1cmU9MSZzbmk9d3d3LmJpbmcuY29tJmFscG49JmZwPSZvcz0=#0219法国 
trojan://base64,QWltZXJAMTk4LjYyLjYyLjE5MjoyMDgzP2Zsb3c9JnNlY3VyaXR5PXRscyZzbmk9YWdlcHQuYW1iZXJjYy5maWxlZ2Vhci1zZy5tZSZ0eXBlPXdzJmhlYWRlcj1ub25lJmhvc3Q9YWdlcHQuYW1iZXJjYy5maWxlZ2Vhci1zZy5tZSZwYXRoPS8lM0ZlZCUzRDI1NjAmYWxwbj1odHRwLzEuMSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0219美国 
trojan://base64,QWltZXJAMjA2LjIzOC4yMzYuMzE6ODQ0Mz9mbG93PSZzZWN1cml0eT10bHMmc25pPWFnZXB0LmFtYmVyY2MuZmlsZWdlYXItc2cubWUmdHlwZT13cyZoZWFkZXI9bm9uZSZob3N0PWFnZXB0LmFtYmVyY2MuZmlsZWdlYXItc2cubWUmcGF0aD0vJTNGZWQlM0QyNTYwJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0219 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1E=@211.178.105.134:51633#0219韩国 
ss://YWVzLTI1Ni1jZmI6Qk5tQVhYeEFIWXBUUmR6dQ==@217.30.10.18:9020#0219波兰 
ss://YWVzLTI1Ni1jZmI6VTZxbllSaGZ5RG1uOHNnbg==@217.30.10.18:9041#0219波兰 
ss://YWVzLTI1Ni1jZmI6S25KR2FkM0ZxVHZqcWJhWA==@217.30.10.18:9014#0219波兰 
ss://YWVzLTI1Ni1jZmI6Y3A4cFJTVUF5TGhUZlZXSA==@217.30.10.18:9064#0219 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1E=@218.38.103.150:28902#0219韩国 
ss://YWVzLTI1Ni1nY206TEtHOEc4Vkw2MFJTQjU5UA==@23.185.248.13:17003#0219哥伦比亚 
vless://base64,MDU1MTkwNTgtZDJhYy00ZjI4LTllNGEtMmIyYTEzODY3NDllQDMuMTIwLjIxMi4xMjY6MjIyMjI/Zmxvdz0mZW5jcnlwdGlvbj1ub25lJnNlY3VyaXR5PXRscyZzbmk9dGVsZWdyYW0tY2hhbm5lbC12bGVzc2NvbmZpZy5zb2hhbGEudWsmdHlwZT13cyZob3N0PXRlbGVncmFtLWNoYW5uZWwtdmxlc3Njb25maWcuc29oYWxhLnVrJnBhdGg9L3RlbGVncmFtLWNoYW5uZWwtdmxlc3Njb25maWctd3MmaGVhZGVyVHlwZT1ub25lJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTAmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0219德国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@3.36.73.26:443#0219韩国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@3.39.249.88:443#0219韩国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@37.143.129.230:989#0219意大利 
vmess://eyJ2IjoiMiIsImFkZCI6IjM4LjMzLjI0LjkwIiwicG9ydCI6MzcwMDEsInNjeSI6ImF1dG8iLCJwcyI6IjAyMTnnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii9wYXRoLzE3Mzk5NzMzMTM0MTUiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjNoLXBvbGFuZDEuMDl2cG4uY29tIiwicG9ydCI6ODQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDIxOee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJhNDg1MDQ4MS05Yjk1LTQzMGYtOWIyZC0xOTJkMjQxMGI0ZjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvdm1lc3MvIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjE0NC40OC4xMjgiLCJwb3J0Ijo4NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwMjE5576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImE0ODUwNDgxLTliOTUtNDMwZi05YjJkLTE5MmQyNDEwYjRmNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii92bWVzcy8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ODVjZTdjYTYtZGYwYS00MmIyLWI4YzUtYTNmZDYxMGJlMzE4QDQ1LjgyLjEyMi4yMTE6NTc1MjA6d3M6LzRidjlhS0dEOVZjR0NwJTNGZWQlM0QyNTYwOmFwaS5uYW1hc2hhLmNvOm5vbmU6dGxzOmFwaS5uYW1hc2hhLmNvOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0219德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NzA1YTVkYWItNmU2My00NWZjLWJkMDAtN2RhYWFhNWEzMjkyQDQ1LjgyLjEyMi4yMTE6NTYyNzU6d3M6L2MwUGlBUW1QcFlMMHBaNDA2bXFGRXp3dTZySzc4SE8lM0ZlZCUzRDI1NjA6YXBpLm5hbWFzaGEuY286bm9uZTp0bHM6YXBpLm5hbWFzaGEuY286W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0219德国 
trojan://base64,MGFjODdiNjQtZTNlZi00OGYxLTgyNGMtZjBhOWI0ZmU2NDczQDQ1LjgyLjEyMi4yMTE6MjU1OTU/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1hcGkubmFtYXNoYS5jbyZ0eXBlPXdzJmhlYWRlcj1ub25lJmhvc3Q9YXBpLm5hbWFzaGEuY28mcGF0aD0vU04xZ0hiU3BZZVVWd2dZejgxNTAyM2RnZGVqayUzRmVkJTNEMjU2MCZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0219德国 
hysteria2://base64,Ujh0N1NmcXdNQ0xVcmRnaUZPeVRANDUuODIuMTIyLjIxMTozMTIzP2luc2VjdXJlPTEmc25pPWFwaS5uYW1hc2hhLmNvJmFscG49JmZwPSZvYmZzPXNhbGFtYW5kZXImb2Jmcy1wYXNzd29yZD1sYWgwY1p0aWtuM3NlRWlocTRMaVhaYUl1ekJXclNsR3NQa0c1Q2kmb3M9#0219德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMi4yMTEiLCJwb3J0IjoyNzgyNSwic2N5IjoiYXV0byIsInBzIjoiMDIxOeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI0MGJiYzVmMC1kNjFmLTRmYzEtYTJjZC05YjFiMGEwMjcwMmMiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaS5uYW1hc2hhLmNvIiwicGF0aCI6Ii9vM2hkUDF5aFNjUzZ6Y2hBTE5xdExpeDFiNj9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiYXBpLm5hbWFzaGEuY28iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMi4yMTEiLCJwb3J0IjozMDI4NCwic2N5IjoiYXV0byIsInBzIjoiMDIxOeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI0ZDZkOGNjMy01ZDg5LTQ0NGUtYThkYS05N2ZmZDBkODQyODAiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaS5uYW1hc2hhLmNvIiwicGF0aCI6Ii9RNXVLTW1tNjdVNXRYdzk/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6ImFwaS5uYW1hc2hhLmNvIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://base64,ZTZhMjc4OTEtMDJhMy00ZDc3LWE0YTAtOWFhMmU4M2ExZjUyQDQ1LjgyLjEyMi4yMTE6MjkwNz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT1hcGkubmFtYXNoYS5jbyZ0eXBlPXdzJmhvc3Q9YXBpLm5hbWFzaGEuY28mcGF0aD0vRTRiRWk2dUZDSyUzRmVkJTNEMjU2MCZoZWFkZXJUeXBlPW5vbmUmYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0219德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMi4yMTEiLCJwb3J0Ijo1MDQ3LCJzY3kiOiJhdXRvIiwicHMiOiIwMjE55b635Zu9IiwibmV0Ijoid3MiLCJpZCI6IjcwNWE1ZGFiLTZlNjMtNDVmYy1iZDAwLTdkYWFhYTVhMzI5MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiYXBpLm5hbWFzaGEuY28iLCJwYXRoIjoiL2RybEFmNGc2Nj9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiYXBpLm5hbWFzaGEuY28iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMi4yMTEiLCJwb3J0Ijo0MzIzMCwic2N5IjoiYXV0byIsInBzIjoiMDIxOeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJlNmEyNzg5MS0wMmEzLTRkNzctYTRhMC05YWEyZTgzYTFmNTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaS5uYW1hc2hhLmNvIiwicGF0aCI6Ii9Tc2lpP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJhcGkubmFtYXNoYS5jbyIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMi4yMTEiLCJwb3J0Ijo0NTMzNCwic2N5IjoiYXV0byIsInBzIjoiMDIxOeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI4NWNlN2NhNi1kZjBhLTQyYjItYjhjNS1hM2ZkNjEwYmUzMTgiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaS5uYW1hc2hhLmNvIiwicGF0aCI6Ii9oTT9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiYXBpLm5hbWFzaGEuY28iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
hysteria2://base64,aTNBajkxa015S2h3YjdFa0hZZ2toZUA0NS44Mi4xMjIuMjExOjU3NjQ0P2luc2VjdXJlPTEmc25pPWFwaS5uYW1hc2hhLmNvJmFscG49JmZwPSZvYmZzPXNhbGFtYW5kZXImb2Jmcy1wYXNzd29yZD1RT1E5Z3VjRU5TUExIaVhERkF4dTFxamVOWVhaRVpqa2h0VTJGZksmb3M9#0219德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NGQ2ZDhjYzMtNWQ4OS00NDRlLWE4ZGEtOTdmZmQwZDg0MjgwQDQ1LjgyLjEyMi4yMTE6MzA1Nzk6d3M6L1VWeVlzZ2s5VHFoRXR4S0pqMnhodzUlM0ZlZCUzRDI1NjA6YXBpLm5hbWFzaGEuY286bm9uZTp0bHM6YXBpLm5hbWFzaGEuY286W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0219德国 
hysteria2://base64,dHg2THZiQlhIelVNbHhQbVdTZkRxQnVSdERVcW9SM0hjakA0NS44Mi4xMjIuMjExOjE1MDU3P2luc2VjdXJlPTEmc25pPWFwaS5uYW1hc2hhLmNvJmFscG49JmZwPSZvYmZzPXNhbGFtYW5kZXImb2Jmcy1wYXNzd29yZD13TWpHWGgzZTljelp2SWRoRnJ3cmomb3M9#0219德国 
hysteria2://base64,ekxXMW9sWmZQV1haUTNqOXl6MU96TFowS1JOd2pzSUxUbkdhQDQ1LjgyLjEyMi4yMTE6NjQ5Njg/aW5zZWN1cmU9MSZzbmk9YXBpLm5hbWFzaGEuY28mYWxwbj0mZnA9Jm9iZnM9c2FsYW1hbmRlciZvYmZzLXBhc3N3b3JkPVlKaHB2Y0JrZzZXSjRYYzFHRjBnbFVZVTRqTUVEV3FTJm9zPQ==#0219德国 
vless://base64,YmNhNjJkNjItMmE3MS00NWJiLWE1Y2EtNjhlMDAwMWRmNjA4QDQ1LjgyLjEyMi4yMTE6MTE5Nzc/Zmxvdz0mZW5jcnlwdGlvbj1ub25lJnNlY3VyaXR5PXRscyZzbmk9YXBpLm5hbWFzaGEuY28mdHlwZT13cyZob3N0PWFwaS5uYW1hc2hhLmNvJnBhdGg9L2pBblVDcXc5OHFsVFJUWU5vYnBPZ0lMYlRjWlR5JTNGZWQlM0QyNTYwJmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0219德国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpvWklvQTY5UTh5aGNRVjhrYTNQYTNB@45.87.175.65:8080#0219德国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@47.129.37.234:443#0219新加坡 
trojan://base64,dGVsZWdyYW0taWQtcHJpdmF0ZXZwbnNANTIuMTguMTg1LjI4OjIyMjIyP2Zsb3c9JnNlY3VyaXR5PXRscyZzbmk9dHJvamFuLmJ1cmdlcmlwLmNvLnVrJnR5cGU9dGNwJmhlYWRlcj1ub25lJmhvc3Q9JnBhdGg9JmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0219爱尔兰 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@52.197.129.53:443#0219日本 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@52.79.101.162:443#0219 
trojan://base64,dGVsZWdyYW0taWQtcHJpdmF0ZXZwbnNANTQuMTU1Ljc2LjY0OjIyMjIyP2Zsb3c9JnNlY3VyaXR5PXRscyZzbmk9dHJvamFuLmJ1cmdlcmlwLmNvLnVrJnR5cGU9dGNwJmhlYWRlcj1ub25lJmhvc3Q9JnBhdGg9JmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0219爱尔兰 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.184.126.174:443#0219美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.218.121.242:443#0219美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.244.0.4:443#0219美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.95.50.167:443#0219日本 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@57.180.246.231:443#0219日本 
trojan://base64,QWltZXJANTkuMi43NS42NDozNzcyMj9mbG93PSZzZWN1cml0eT10bHMmc25pPWFnZXB5LmFtYmVyY2MuZmlsZWdlYXItc2cubWUmdHlwZT13cyZoZWFkZXI9bm9uZSZob3N0PWFnZXB5LmFtYmVyY2MuZmlsZWdlYXItc2cubWUmcGF0aD0vJTNGZWQlM0QyNTYwJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0219 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@62.100.205.48:989#0219英国 
ssr://NjIuMTAwLjIwNS40ODo5ODk6b3JpZ2luOmFlcy0yNTYtY2ZiOnBsYWluOlpqaG1OMkZEZW1OUVMySnpSamh3TXc9PS8/b2Jmc3BhcmFtPSZwcm90b3BhcmFtPSZyZW1hcmtzPU1ESXhPZWlMc2VXYnZRPT0mb3M9 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpPSDUxaWNNSnQ2aVB5TmY2OFVXckhW@77.239.99.180:34775#0219英国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@84.17.53.160:989#0219瑞士 
vless://base64,OGI1NGE2YzctMjU0NC00YTA3LTk1MjAtYjRlNTI1MmJhMmI3QDg5LjE4Ny4yOC4xMjY6ODQ0Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT11bC1qYXBhbjEuMDl2cG4uY29tJnR5cGU9d3MmaG9zdD0mcGF0aD0vdmxlc3MvJmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0219美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpOakJsWkRsaw==@89.221.224.166:1443#0219岛 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989#0219 
trojan://base64,QWltZXJAOTIuMjQzLjc1LjQ5OjIwODc/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1hZ2VweS5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD1hZ2VweS5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnBhdGg9LyUzRmVkJTNEMjU2MCZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0219 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpPV1k0T0RCbQ==@95.164.36.59:8388#0219奥地利 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpPV1k0T0RCbQ==@at1.opensocks.site:8388#0219奥地利 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpvMzh5dXZ6U2UzbTVhRE5wSHRVUEgxekd3YkdFWFhNRHNHd1ZhdWIyU1lFbUhVYTJXR1pVamllelgzVnZ2YTlDQ3pwanhZdHVKTGdLc1Nuc3lLQmY5Y2lQVmJhM3k0bzM=@beta.mattenadene.org:54075#0219美国 
trojan://base64,Mzc0NzAwMDEwMzI3NDI5MTIwMEBjYXBhYmxlLWVlbC50cmVlZnJvZzc2MS5vbmU6NDQzP2Zsb3c9JnNlY3VyaXR5PXRscyZzbmk9Y2FwYWJsZS1lZWwudHJlZWZyb2c3NjEub25lJnR5cGU9dGNwJmhlYWRlcj1ub25lJmhvc3Q9JnBhdGg9JmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0219土耳其 
vless://base64,N2Y5NzAyN2EtNmY2MC01NzIzLWIxMDEtZWVmNjJhYWIxN2RiQGZhY3VsdHkudWNkYXZpcy5lZHU6NDQzP2Zsb3c9JmVuY3J5cHRpb249bm9uZSZzZWN1cml0eT10bHMmc25pPWZhY3VsdHkudWNkYXZpcy5lZHUmdHlwZT13cyZob3N0PUpvaW5CZWRlLW1vc2l2Mi5pciZwYXRoPS8maGVhZGVyVHlwZT1ub25lJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0219美国 
vless://base64,YjI3ZjRkOTctMjU2Mi00ODY3LWFlMjAtNDVlNjI1ZWVjNWY1QGhhamxhYi51Y2RhdmlzLmVkdTo0NDM/Zmxvdz0mZW5jcnlwdGlvbj1ub25lJnNlY3VyaXR5PXRscyZzbmk9aGFqbGFiLnVjZGF2aXMuZWR1JnR5cGU9d3MmaG9zdD13V3cuU3BFZUR0RXNULk5lVC5adUxhLmFJci5Ja0NvU2FMZVMuaVIuRDY2MjU5OS52MDUuZmVhZGxlbmV0d29ya3Yyc2EubmV0JnBhdGg9LyZoZWFkZXJUeXBlPW5vbmUmYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0219美国 
trojan://base64,QWltZXJAaWduYWNpby5ucy5jbG91ZGZsYXJlLmNvbTo0NDM/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1hZ2VweS5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD1hZ2VweS5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnBhdGg9LyUzRmVkJTNEMjU2MCZhbHBuPWh0dHAvMS4xJmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0219美国 
trojan://base64,Mzc0NzAwMDEwMzI3NDI5MTIwMEBpbW1lbnNlLWdpYmJvbi50cmVlZnJvZzc2MS5vbmU6NDQzP2Zsb3c9JnNlY3VyaXR5PXRscyZzbmk9aW1tZW5zZS1naWJib24udHJlZWZyb2c3NjEub25lJnR5cGU9dGNwJmhlYWRlcj1ub25lJmhvc3Q9JnBhdGg9JmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0219土耳其 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpOakJsWkRsaw==@is3.opensocks.site:8388#0219岛 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpOakJsWkRsaw==@is3.opensocks.site:1443#0219岛 
vmess://eyJ2IjoiMiIsImFkZCI6Imtra2doZHJhZ3hjLmZhc2s1MTEuY2ZkIiwicG9ydCI6MjU3NzcsInNjeSI6ImF1dG8iLCJwcyI6IjAyMTnpn6nlm70iLCJuZXQiOiJ3cyIsImlkIjoiNTBiM2ZiMWItNTU5MS00NzQzLThlOWItMDYwMWM1ZGZlODZkIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJra2tnaGRyYWd4Yy5mYXNrNTExLmNmZCIsInBhdGgiOiIvP2VkPTEwMjQiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTo3MmJiMzA3Mi03ZWZkLTRkNjctOWJlYi0yY2Q5YzE4ZTY5ZjQ=@kr.fastsoonlink.com:40032#0219韩国 
trojan://base64,NWFmN2ZhM2EtYWQ5Yy00MzQ2LWJhN2YtMTg0ZTg5YzkxNzU4QGxtLmthaXFzei5jb206NTEwNzU/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1tbWJpejEwLnJlZGFwcmljb3RjbG91ZC5jb20mdHlwZT10Y3AmaGVhZGVyPW5vbmUmaG9zdD0mcGF0aD0mYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0219 
trojan://base64,NjVmMTQ4MzEtNWM2Ny00ODNmLTllODUtZjNhYTczZjIxMTg3QG5haXUtc2cuMDV2cjlueXFnNS5kb3dubG9hZDoxMzAyNz9mbG93PSZzZWN1cml0eT10bHMmc25pPWNsb3VkZmxhcmUubm9kZS1zc2wuY2RuLWFsaWJhYmEuY29tJnR5cGU9dGNwJmhlYWRlcj1ub25lJmhvc3Q9JnBhdGg9JmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0219新加坡 
trojan://base64,NjVmMTQ4MzEtNWM2Ny00ODNmLTllODUtZjNhYTczZjIxMTg3QG5haXUtdXMuMDV2cjlueXFnNS5kb3dubG9hZDoxMzAxOT9mbG93PSZzZWN1cml0eT10bHMmc25pPWNsb3VkZmxhcmUubm9kZS1zc2wuY2RuLWFsaWJhYmEuY29tJnR5cGU9dGNwJmhlYWRlcj1ub25lJmhvc3Q9JnBhdGg9JmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTAmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0219 
trojan://base64,QWltZXJAcHJhbmFiLm5zLmNsb3VkZmxhcmUuY29tOjQ0Mz9mbG93PSZzZWN1cml0eT10bHMmc25pPWFnZXB5LmFtYmVyY2MuZmlsZWdlYXItc2cubWUmdHlwZT13cyZoZWFkZXI9bm9uZSZob3N0PWFnZXB5LmFtYmVyY2MuZmlsZWdlYXItc2cubWUmcGF0aD0vJTNGZWQlM0QyNTYwJmFscG49aHR0cC8xLjEmZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0219美国 
vmess://eyJ2IjoiMiIsImFkZCI6InMxLmRiLWxpbmswMi50b3AiLCJwb3J0Ijo4MDgwLCJzY3kiOiJhdXRvIiwicHMiOiIwMjE5576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjRiMzY2MjVjLWI5ZDktM2VhNi1hZWQ1LTg2ZDYyYzcwZTE2ZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiMTAwLTIxMy02MS0xMDIuczEuZGItbGluazAyLnRvcCIsInBhdGgiOiIvZGFiYWkuaW4xMDQuMjEuMTUxLjIwMiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InMxLmRiLWxpbmswMi50b3AiLCJwb3J0Ijo4MCwic2N5IjoiYXV0byIsInBzIjoiMDIxOee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI0YjM2NjI1Yy1iOWQ5LTNlYTYtYWVkNS04NmQ2MmM3MGUxNmQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IjEwMC00OS0xNDEtMjA5LnMxLmRiLWxpbmswMi50b3AiLCJwYXRoIjoiL2RhYmFpLmluMTA0LjE3LjE2OS4xMTUiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InMxLmRiLWxpbmswMi50b3AiLCJwb3J0IjoyMDg2LCJzY3kiOiJhdXRvIiwicHMiOiIwMjE5576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjUzMmUxNTQxLTRiNjUtMzQwOS04MWYxLTQzZjIwNjg0NjYxNSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiMTAwLTIzNi0xOTUtNjEuczEuZGItbGluazAyLnRvcCIsInBhdGgiOiIvZGFiYWkuaW4xNzIuNjQuMi41OSIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://base64,QWltZXJAc2FnZS5ucy5jbG91ZGZsYXJlLmNvbTo0NDM/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1hZ2VweS5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD1hZ2VweS5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnBhdGg9LyUzRmVkJTNEMjU2MCZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0219 
hysteria2://base64,Zjk4OGE4NGEtMjM2YS00YWFlLTg4MjMtYjg0NzU3NzY5ZWE3QHNlcnYwMS50cmV2ZWx5LnVzLmtnOjU5MzUwP2luc2VjdXJlPTEmc25pPXd3dy5iaW5nLmNvbSZhbHBuPSZmcD0mb3M9#0219波兰 
hysteria2://base64,ZmMxMGE0ZDYtZjk0Ni00NzhmLWEzZGItNTdmNzNjZGIwNDA3QHNlcnYwNS50cmV2ZWx5LnVzLmtnOjU5MzUwP2luc2VjdXJlPTEmc25pPXd3dy5iaW5nLmNvbSZhbHBuPSZmcD0mb3M9#0219波兰 
hysteria2://base64,ZjdkOTQ4YWUtODBjOS00NzhjLTg5NGEtNWRhMmIxNTM0MTg5QHNlcnYwOS50cmV2ZWx5LnVzLmtnOjU5MzUwP2luc2VjdXJlPTEmc25pPXd3dy5iaW5nLmNvbSZhbHBuPSZmcD0mb3M9#0219波兰 
hysteria2://base64,ZjdjZjQ3NjUtNTc0NS00OTBiLThmOGMtOWY4NjU5MDFmOTcxQHNlcnYxMC50cmV2ZWx5LnVzLmtnOjU5MzUwP2luc2VjdXJlPTEmc25pPXd3dy5iaW5nLmNvbSZhbHBuPSZmcD0mb3M9#0219波兰 
hysteria2://base64,ZmE4YTAxODctNjAxMS00ZjFmLWJkZjQtYmJmOTI4MjU5MDAwQHNlcnYxMS50cmV2ZWx5LnVzLmtnOjU5MzUwP2luc2VjdXJlPTEmc25pPXd3dy5iaW5nLmNvbSZhbHBuPSZmcD0mb3M9#0219波兰 
hysteria2://base64,ZmI1MDhkODYtMTY3OS00YjIyLThjMDktMGNkNGNkYmI4ODdkQHNlcnYxMi50cmV2ZWx5LnVzLmtnOjU5MzUwP2luc2VjdXJlPTEmc25pPXd3dy5iaW5nLmNvbSZhbHBuPSZmcD0mb3M9#0219波兰 
hysteria2://base64,ZjZmNDA0YjMtNjJmNi00N2FhLWI0ZDgtOTNjNWNkYWUxYTBhQHNlcnYxMy50cmV2ZWx5LnVzLmtnOjU5MzUwP2luc2VjdXJlPTEmc25pPXd3dy5iaW5nLmNvbSZhbHBuPSZmcD0mb3M9#0219波兰 
hysteria2://base64,ZmJmODkxYmMtYTk0YS00NDdkLTg0MTctYzYzN2NhMTFjMzYxQHNlcnYxNi50cmV2ZWx5LnVzLmtnOjU5MzUwP2luc2VjdXJlPTEmc25pPXd3dy5iaW5nLmNvbSZhbHBuPSZmcD0mb3M9#0219法国 
trojan://base64,Mzc0NzAwMDEwMzI3NDI5MTIwMEBzZXR0bGVkLXNlYWwudHJlZWZyb2c3NjEub25lOjQ0Mz9mbG93PSZzZWN1cml0eT10bHMmc25pPXNldHRsZWQtc2VhbC50cmVlZnJvZzc2MS5vbmUmdHlwZT10Y3AmaGVhZGVyPW5vbmUmaG9zdD0mcGF0aD0mYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0219土耳其 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989#0219波兰 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@176.103.53.105:989#0219乌克兰 
hysteria2://base64,ZG9uZ3RhaXdhbmcuY29tQDQ2LjE3LjQxLjE4OTo1MTIyND9pbnNlY3VyZT0xJnNuaT13d3cuYmluZy5jb20mYWxwbj0mZnA9Jm9zPQ==#0219俄罗斯 
ss://Y2hhY2hhMjA6djVhVVV0bWUzanhz@14.18.253.178:9003#0219孟加拉国 
ss://Y2hhY2hhMjA6YXZwQnFGRm1zWUJO@14.18.253.178:8335#0219日本 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjEyMyIsInBvcnQiOjQ1NDAyLCJzY3kiOiJhdXRvIiwicHMiOiIwMjE5576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjY0LCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjA6QURabVJRVUdIVHdY@14.18.253.178:8339#0219韩国 
ss://Y2hhY2hhMjA6RHZQZkthOHZzVjlL@14.18.253.178:8334#0219新加坡 
ss://Y2hhY2hhMjA6cTJrU0dwNGF5RktC@14.18.253.178:8347#0219法国 


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
