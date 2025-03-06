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


ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@103.106.229.219:989#0305新加坡 
ss://Y2hhY2hhMjAtaWV0Zjphc2QxMjM0NTY=@103.149.182.191:8388#0305香港 
vless://base64-M2RmODgzZjctZWI4YS00ODlhLWFmNzAtNjc0NTYwMmVjYzFjQDEwMy4yMS4yNDQuMTEyOjQ0Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT13d3cuc2VjZ2UudXMua2cmdHlwZT14aHR0cCZob3N0PXd3dy5zZWNnZS51cy5rZyZwYXRoPS9aRVRqMllMaDI0bWlnNyZtb2RlPXBhY2tldC11cCZhbHBuPWgyJmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0305德国 
vless://base64-M2RmODgzZjctZWI4YS00ODlhLWFmNzAtNjc0NTYwMmVjYzFjQDEwMy4yMS4yNDQuMTU1OjQ0Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT13d3cuc2VjZ2UudXMua2cmdHlwZT14aHR0cCZob3N0PXd3dy5zZWNnZS51cy5rZyZwYXRoPS9aRVRqMllMaDI0bWlnNyZtb2RlPXBhY2tldC11cCZhbHBuPWgyJmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0305德国 
vless://base64-M2RmODgzZjctZWI4YS00ODlhLWFmNzAtNjc0NTYwMmVjYzFjQDEwMy4yMS4yNDQuMTc0OjQ0Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT13d3cuc2VjZ2UudXMua2cmdHlwZT14aHR0cCZob3N0PXd3dy5zZWNnZS51cy5rZyZwYXRoPS9aRVRqMllMaDI0bWlnNyZtb2RlPXBhY2tldC11cCZhbHBuPWgyJmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0305德国 
vless://base64-M2RmODgzZjctZWI4YS00ODlhLWFmNzAtNjc0NTYwMmVjYzFjQDEwMy4yMS4yNDQuODY6NDQzP2Zsb3c9JmVuY3J5cHRpb249bm9uZSZzZWN1cml0eT10bHMmc25pPXd3dy5zZWNnZS51cy5rZyZ0eXBlPXhodHRwJmhvc3Q9d3d3LnNlY2dlLnVzLmtnJnBhdGg9L1pFVGoyWUxoMjRtaWc3Jm1vZGU9cGFja2V0LXVwJmFscG49aDImZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0305德国 
vless://base64-M2RmODgzZjctZWI4YS00ODlhLWFmNzAtNjc0NTYwMmVjYzFjQDEwNC4xNi4xNTUuMTE0OjQ0Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT13d3cuc2VjZ2UudXMua2cmdHlwZT14aHR0cCZob3N0PXd3dy5zZWNnZS51cy5rZyZwYXRoPS9aRVRqMllMaDI0bWlnNyZtb2RlPXBhY2tldC11cCZhbHBuPWgyJmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0305德国 
vless://base64-M2RmODgzZjctZWI4YS00ODlhLWFmNzAtNjc0NTYwMmVjYzFjQDEwNC4yMC4xOTIuMTU1OjQ0Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT13d3cuc2VjZ2UudXMua2cmdHlwZT14aHR0cCZob3N0PXd3dy5zZWNnZS51cy5rZyZwYXRoPS9aRVRqMllMaDI0bWlnNyZtb2RlPXBhY2tldC11cCZhbHBuPWgyJmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0305德国 
vless://base64-M2RmODgzZjctZWI4YS00ODlhLWFmNzAtNjc0NTYwMmVjYzFjQDEwNC4yNC40Ni4xMTc6NDQzP2Zsb3c9JmVuY3J5cHRpb249bm9uZSZzZWN1cml0eT10bHMmc25pPXd3dy5zZWNnZS51cy5rZyZ0eXBlPXhodHRwJmhvc3Q9d3d3LnNlY2dlLnVzLmtnJnBhdGg9L1pFVGoyWUxoMjRtaWc3Jm1vZGU9cGFja2V0LXVwJmFscG49aDImZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0305德国 
vless://base64-M2RmODgzZjctZWI4YS00ODlhLWFmNzAtNjc0NTYwMmVjYzFjQDEwNC4yNS4xNjAuODQ6NDQzP2Zsb3c9JmVuY3J5cHRpb249bm9uZSZzZWN1cml0eT10bHMmc25pPXd3dy5zZWNnZS51cy5rZyZ0eXBlPXhodHRwJmhvc3Q9d3d3LnNlY2dlLnVzLmtnJnBhdGg9L1pFVGoyWUxoMjRtaWc3Jm1vZGU9cGFja2V0LXVwJmFscG49aDImZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0305德国 
trojan://base64-MWU2M2U1ODVhYjJmZWYzYWRjYzllYTc1YTYyYWJjMjNAMTA0LjI1MS4yMjcuMTgyOjQ0Mz9mbG93PSZzZWN1cml0eT10bHMmc25pPWhlemlqaWFzdXFpLmNvbSZ0eXBlPXRjcCZoZWFkZXI9bm9uZSZob3N0PSZwYXRoPSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0305香港 
vless://base64-ODE5NjY0ZTEtMjZmMi00OWRiLTgwMjUtYjE4YWRlZThmZDJjQDEwNy4xNzIuMTU3LjE0ODozMDk0ND9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9JnNuaT0mdHlwZT10Y3AmaG9zdD0mcGF0aD0maGVhZGVyVHlwZT1ub25lJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0305美国 
hysteria2://base64-MDlkMDBmMmYtZDhkYS00YzAyLWEzMDUtMzAzZDczNmViMmUyQDEwNy4xNzIuMjM1Ljc1OjQzNjE1P2luc2VjdXJlPTEmc25pPWR4b2JnNGF6bWsuZ2Fmbm9kZS5zYnMmYWxwbj0mZnA9Jm9zPQ==#0305美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE0IiwicG9ydCI6MzU1NjUsInNjeSI6ImF1dG8iLCJwcyI6IjAzMDXml6XmnKwiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE5IiwicG9ydCI6NDIwNTUsInNjeSI6ImF1dG8iLCJwcyI6IjAzMDXnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE5IiwicG9ydCI6NDQwMTQsInNjeSI6ImF1dG8iLCJwcyI6IjAzMDXnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE5IiwicG9ydCI6NTAwOTUsInNjeSI6ImF1dG8iLCJwcyI6IjAzMDXnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQxIiwicG9ydCI6MzIwNzcsInNjeSI6ImF1dG8iLCJwcyI6IjAzMDXnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1jZmI6aEdrUTY5MTV0RA==@120.232.81.50:15084#0305日本 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@13.250.31.57:443#0305新加坡 
vless://base64-ZTIwZWJlMDEtMTgxNS00YzA5LThlNzctZmIyZjE2ODI2M2NlQDEzNS4xNDguMTYzLjkwOjQ0Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT0xNDcxMzUwMDExNzguc2VjMjJvcmcuY29tJnR5cGU9dGNwJmhvc3Q9JnBhdGg9JmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0305美国 
ss://Y2hhY2hhMjA6TjlrNGYyUE9SbDE0@14.18.253.178:8348#0305以色列 
ss://Y2hhY2hhMjA6djVhVVV0bWUzanhz@14.18.253.178:9003#0305孟加拉国 
ss://Y2hhY2hhMjA6RHZQZkthOHZzVjlL@14.18.253.178:8334#0305新加坡 
ss://Y2hhY2hhMjA6YXZwQnFGRm1zWUJO@14.18.253.178:8335#0305日本 
ss://Y2hhY2hhMjA6cTJrU0dwNGF5RktC@14.18.253.178:8347#0305法国 
ss://Y2hhY2hhMjA6QURabVJRVUdIVHdY@14.18.253.178:8339#0305韩国 
vless://base64-M2I5YmM3NzMtMDVlYi00ZDVmLThjMWYtNTczNDJjMGM0ZjQwQDE0Ny4xMzUuMTAuMTAzOjQ0Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT0xNDcxMzUwMTAxMDMuc2VjMTlvcmcuY29tJnR5cGU9dGNwJmhvc3Q9JnBhdGg9JmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0305美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE1MS4xMDEuMTk0LjE2OCIsInBvcnQiOjgwLCJzY3kiOiJhdXRvIiwicHMiOiIwMzA15b635Zu9IiwibmV0Ijoid3MiLCJpZCI6IjdkYzc4NTgyLTg4YTgtNGI0Yy05ZTNlLTUwODMxZDY3Mjc2NiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiYW1kLmFsIiwicGF0aCI6Ii9YRVNBTElTVEhFQkVTVD9lZD0yMDQ4IiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiYW1kLmFsIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE1MS4xMDEuNjYuMTY4IiwicG9ydCI6ODAsInNjeSI6ImF1dG8iLCJwcyI6IjAzMDXlvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiN2RjNzg1ODItODhhOC00YjRjLTllM2UtNTA4MzFkNjcyNzY2IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJhbWQuYWwiLCJwYXRoIjoiL1hFU0FMSVNUSEVCRVNUP2VkPTIwNDgiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJhbWQuYWwiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@18.179.9.121:443#0305日本 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@18.236.83.127:443#0305美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0MjEyMCwic2N5IjoiYXV0byIsInBzIjoiMDMwNeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo1MzkwMiwic2N5IjoiYXV0byIsInBzIjoiMDMwNeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.186.79.53:989#0305丹麦 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989#0305波兰 
vless://base64-M2RmODgzZjctZWI4YS00ODlhLWFmNzAtNjc0NTYwMmVjYzFjQDE4OC4xMTQuOTYuMjUzOjQ0Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT13d3cuc2VjZ2UudXMua2cmdHlwZT14aHR0cCZob3N0PXd3dy5zZWNnZS51cy5rZyZwYXRoPS9aRVRqMllMaDI0bWlnNyZtb2RlPXBhY2tldC11cCZhbHBuPWgyJmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0305德国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpXVlUyN0xxdUFNT2VYbVllU3RJODk3@188.126.83.62:32448#0305瑞典 
vless://base64-M2RmODgzZjctZWI4YS00ODlhLWFmNzAtNjc0NTYwMmVjYzFjQDE5OC40MS4xOTYuMTI4OjQ0Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT13d3cuc2VjZ2UudXMua2cmdHlwZT14aHR0cCZob3N0PXd3dy5zZWNnZS51cy5rZyZwYXRoPS9aRVRqMllMaDI0bWlnNyZtb2RlPXBhY2tldC11cCZhbHBuPWgyJmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0305德国 
ss://Y2hhY2hhMjAtaWV0Zjphc2QxMjM0NTY=@202.162.109.169:8388#0305新加坡 
ss://YWVzLTI1Ni1nY206WTZSOXBBdHZ4eHptR0M=@23.154.136.132:5000#0305美国 
ss://YWVzLTI1Ni1nY206ZzVNZUQ2RnQzQ1dsSklk@23.154.136.132:5004#0305美国 
ss://YWVzLTI1Ni1nY206WTZSOXBBdHZ4eHptR0M=@23.154.136.132:5601#0305美国 
trojan://base64-dGVsZWdyYW0taWQtcHJpdmF0ZXZwbnNAMy43OC4xMDguMTIyOjIyMjIyP2Zsb3c9JnNlY3VyaXR5PXRscyZzbmk9dHJvamFuLmJ1cmdlcmlwLmNvLnVrJnR5cGU9dGNwJmhlYWRlcj1ub25lJmhvc3Q9JnBhdGg9JmFscG49aHR0cC8xLjEmZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0305德国 
vless://base64-ZTY1N2U1ZmItYzQxNy00ZDNmLWQ4NGUtYTNhOGYwMTBmOWZhQDMxLjU5LjExMS40OTozMzcxOD9mbG93PXh0bHMtcnByeC12aXNpb24mZW5jcnlwdGlvbj1ub25lJnNlY3VyaXR5PXJlYWxpdHkmc25pPWljbG91ZC5jZG4tYXBwbGUuY29tJnR5cGU9dGNwJmhvc3Q9JnBhdGg9JmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD1jaHJvbWUmcGJrPWcxZjF3TGppbTVnT1ZHbkk1TEdVVjBkTDRpRlhQb2llcE9QWmZTeEplMTQmc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0305美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.217.73.31:443#0305美国 
trojan://base64-dGVsZWdyYW0taWQtZGlyZWN0dnBuQDM1LjE3Ni4yMi41OjIyMjIyP2Zsb3c9JnNlY3VyaXR5PXRscyZzbmk9dHJvamFuLmJ1cmdlcmlwLmNvLnVrJnR5cGU9dGNwJmhlYWRlcj1ub25lJmhvc3Q9JnBhdGg9JmFscG49aHR0cC8xLjEmZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0305英国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.86.89.247:443#0305美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.91.198.93:443#0305美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.91.216.191:443#0305美国 
trojan://base64-OTBjMGJjODctZDdkZC00MjMzLTliMWEtY2M5ZTdjZjMwNjQ5QDM2LjE1MS4yNTEuMTI6MTIwMDM/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT0zNi4xNTEuMjUxLjEyJnR5cGU9dGNwJmhlYWRlcj1ub25lJmhvc3Q9JnBhdGg9JmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0305香港 
vless://base64-NTFlNDRkMDEtNWZhMC00N2QzLThlZTMtYWQxZjA0ZDNhYmNjQDM3LjIwMi4yMzcuMTA3OjIzMjk3P2Zsb3c9JmVuY3J5cHRpb249bm9uZSZzZWN1cml0eT0mc25pPSZ0eXBlPXdzJmhvc3Q9JnBhdGg9LyZoZWFkZXJUeXBlPW5vbmUmYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0305德国 
vless://base64-ZWJhNjM2NTktZTFjMC00ZmJhLWEwODktYmY1NGIyMWUwNWNhQDM3LjIwMi4yMzcuMTA3OjQ1NDk1P2Zsb3c9JmVuY3J5cHRpb249bm9uZSZzZWN1cml0eT0mc25pPSZ0eXBlPXdzJmhvc3Q9JnBhdGg9LyZoZWFkZXJUeXBlPW5vbmUmYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0305德国 
ss://YWVzLTI1Ni1nY206S2l4THZLendqZWtHMDBybQ==@38.114.114.77:5500#0305美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjNoLXBvbGFuZDEuMDl2cG4uY29tIiwicG9ydCI6ODQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDMwNeazouWFsCIsIm5ldCI6IndzIiwiaWQiOiJhNDg1MDQ4MS05Yjk1LTQzMGYtOWIyZC0xOTJkMjQxMGI0ZjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvdm1lc3MvIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@43.201.0.67:443#0305韩国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@43.203.244.103:443#0305韩国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjE0NC40OC4xMjgiLCJwb3J0Ijo4NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwMzA15rOi5YWwIiwibmV0Ijoid3MiLCJpZCI6ImE0ODUwNDgxLTliOTUtNDMwZi05YjJkLTE5MmQyNDEwYjRmNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii92bWVzcy8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMC4yMTMiLCJwb3J0Ijo2MjQ1OSwic2N5IjoiYXV0byIsInBzIjoiMDMwNeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJmZjRhMDExYy1lZGZlLTQ2OTEtYmIwMi0wNjkxZjdmNjhkODYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tIiwicGF0aCI6Ii9kP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJkb3dubG9hZC53aW5kb3dzdXBkYXRlLmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZmY0YTAxMWMtZWRmZS00NjkxLWJiMDItMDY5MWY3ZjY4ZDg2QDQ1LjgyLjEyMC4yMTM6NzI5Mjp3czovRXNYZmpYWFlBc2NVS2hEMmclM0ZlZCUzRDI1NjA6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206bm9uZTp0bHM6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0305德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MDllYzhjYzItZDdlYS00ODA3LTkwOTgtNTdhYjlmMDFlYjllQDQ1LjgyLjEyMC4yMTM6NTg1NDE6d3M6L3h3bWJKOGEzV2s4UkJGbmplcyUzRmVkJTNEMjU2MDpkb3dubG9hZC53aW5kb3dzdXBkYXRlLmNvbTpub25lOnRsczpkb3dubG9hZC53aW5kb3dzdXBkYXRlLmNvbTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0305德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMC4yMTMiLCJwb3J0Ijo0OTE5Niwic2N5IjoiYXV0byIsInBzIjoiMDMwNeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIzNGQ2MzU2OC1lNDgyLTQxMDMtYTg0Yi1lMGQyZTZjYjI5NTYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tIiwicGF0aCI6Ii9NT2hkb1lYMWZ0OEJMN2pvP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJkb3dubG9hZC53aW5kb3dzdXBkYXRlLmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtcG9seTEzMDU6Yjg4Mzk3Y2MtZjI0NC00YzUxLWFhYzgtZTRmOWNiZTA3MjI2QDQ1LjgyLjEyMC4yMTM6MTgzNTE6d3M6L2V0TFBjTGZhSXdXdE5aWUJubE40cEQ0cHNIJTNGZWQlM0QyNTYwOmRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tOm5vbmU6dGxzOmRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0305德国 
trojan://base64-MDllYzhjYzItZDdlYS00ODA3LTkwOTgtNTdhYjlmMDFlYjllQDQ1LjgyLjEyMC4yMTM6NTg1MTY/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1kb3dubG9hZC53aW5kb3dzdXBkYXRlLmNvbSZ0eXBlPXdzJmhlYWRlcj1ub25lJmhvc3Q9ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb20mcGF0aD0vcmhHRXcwdjglM0ZlZCUzRDI1NjAmYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0305德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMC4yMTMiLCJwb3J0Ijo0MzA0MSwic2N5IjoiYXV0byIsInBzIjoiMDMwNeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIxYzkzNWZmNi05NGRmLTQ1MTctYjRmYy03MmYxOTZkMDhjZTciLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tIiwicGF0aCI6Ii9aRVRqMllMaDI0bWlnNz9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
hysteria2://base64-cEs0QzhXZm1NT25LTkJqSEF3Uk9UVkw3NTdkS2h1enA0NGZaRVBANDUuODIuMTIwLjIxMzo4MjI1P2luc2VjdXJlPTEmc25pPWRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tJmFscG49JmZwPSZvYmZzPXNhbGFtYW5kZXImb2Jmcy1wYXNzd29yZD1lTjdWVlIwRFhZOUU2NmoxenRxbXFoaWEmb3M9#0305德国 
hysteria2://base64-VnpabnJsYTZuVDR2cWdHZWN6WTVWR1p2OGlANDUuODIuMTIwLjIxMzozODQxOD9pbnNlY3VyZT0xJnNuaT1kb3dubG9hZC53aW5kb3dzdXBkYXRlLmNvbSZhbHBuPSZmcD0mb2Jmcz1zYWxhbWFuZGVyJm9iZnMtcGFzc3dvcmQ9OElrbUYxYXk5Qk84MHI1WGFvamRveWNoNVRVTXdkRmdPJm9zPQ==#0305德国 
vless://base64-MWM5MzVmZjYtOTRkZi00NTE3LWI0ZmMtNzJmMTk2ZDA4Y2U3QDQ1LjgyLjEyMC4yMTM6MTkzODg/Zmxvdz0mZW5jcnlwdGlvbj1ub25lJnNlY3VyaXR5PXRscyZzbmk9ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb20mdHlwZT13cyZob3N0PWRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tJnBhdGg9L0VaRHlOazY0YXklM0ZlZCUzRDI1NjAmaGVhZGVyVHlwZT1ub25lJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0305德国 
hysteria2://base64-YlZER1pPYVJSREpUbHpUb3dTMGwxa25YZHllZlA3WXZWb055M2drQDQ1LjgyLjEyMC4yMTM6MjAxMTg/aW5zZWN1cmU9MSZzbmk9ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb20mYWxwbj0mZnA9Jm9iZnM9c2FsYW1hbmRlciZvYmZzLXBhc3N3b3JkPXpFNDZia3l4dVRWb0FaSkVIdnYmb3M9#0305德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMC4yMTMiLCJwb3J0Ijo0NzQxOSwic2N5IjoiYXV0byIsInBzIjoiMDMwNeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI2MzQ3YzA4Yi0wODU4LTRkMTUtODkyNi03ZjFhMTBjODkzMmIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tIiwicGF0aCI6Ii9GeGhTMkgwbW1XSGZDODlRRzRnZno4V1U/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6ImRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
hysteria2://base64-TFQ0am1ncWJiQkZ4TmhWcGYweUA0NS44Mi4xMjAuMjEzOjQ2NTU3P2luc2VjdXJlPTEmc25pPWRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tJmFscG49JmZwPSZvYmZzPXNhbGFtYW5kZXImb2Jmcy1wYXNzd29yZD1zemlnSXVxY29iVXVjanVyaVl5V1JjYXEmb3M9#0305德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6YmJjMzVhOTItODdlYS00YmRhLTg0ZTQtOTJlYmRiMTU1MjM0QDQ1LjgyLjEyMC4yMTM6NDE0MzQ6d3M6L3VwcElpcVdCcXl1RWRqNTV3SlVlclglM0ZlZCUzRDI1NjA6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206bm9uZTp0bHM6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0305德国 
hysteria2://base64-dmJtTkFOcE9hYnFuRVVEejNxbGc5MmZaZzlYODJmUHVANDUuODIuMTIwLjIxMzozNjU0OT9pbnNlY3VyZT0xJnNuaT1kb3dubG9hZC53aW5kb3dzdXBkYXRlLmNvbSZhbHBuPSZmcD0mb2Jmcz1zYWxhbWFuZGVyJm9iZnMtcGFzc3dvcmQ9eENuY05EalhwcW9tMzY3S1p0Q3gmb3M9#0305德国 
vless://base64-YmJjMzVhOTItODdlYS00YmRhLTg0ZTQtOTJlYmRiMTU1MjM0QDQ1LjgyLjEyMC4yMTM6NjA0NTY/Zmxvdz0mZW5jcnlwdGlvbj1ub25lJnNlY3VyaXR5PXRscyZzbmk9ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb20mdHlwZT13cyZob3N0PWRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tJnBhdGg9L1dvUFNqVGFRb1NUZGY5dnFoJTNGZWQlM0QyNTYwJmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0305德国 
hysteria2://base64-VWljaDZPRmpPZ3M5bGZ6ME9yeHVUWDRsaEA0NS44Mi4xMjAuMjEzOjYzMzUyP2luc2VjdXJlPTEmc25pPWRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tJmFscG49JmZwPSZvYmZzPXNhbGFtYW5kZXImb2Jmcy1wYXNzd29yZD10bzNrSEhHWUlzcFZTRjcwZTM0VUI5R2ZacDYyJm9zPQ==#0305德国 
hysteria2://base64-Z0lOSVQ1RmJJR1BjaUo0Z1c5emlGUUFRY1lFQ3FYNkA0NS44Mi4xMjAuMjEzOjQ0MTE4P2luc2VjdXJlPTEmc25pPWRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tJmFscG49JmZwPSZvYmZzPXNhbGFtYW5kZXImb2Jmcy1wYXNzd29yZD1VVmI2eGpmMTY4NUpkWm9wR1Bnc0daNmFubmZHUkJXOWpVTGEmb3M9#0305德国 
hysteria2://base64-ZG9uZ3RhaXdhbmcuY29tQDQ2LjE3LjQxLjE4OTo1MTIyND9pbnNlY3VyZT0xJnNuaT13d3cuYmluZy5jb20mYWxwbj0mZnA9Jm9zPQ==#0305俄罗斯 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@52.13.119.156:443#0305美国 
trojan://base64-dGVsZWdyYW0taWQtcHJpdmF0ZXZwbnNANTIuMjE1LjI1LjE0NzoyMjIyMj9mbG93PSZzZWN1cml0eT10bHMmc25pPXRyb2phbi5idXJnZXJpcC5jby51ayZ0eXBlPXRjcCZoZWFkZXI9bm9uZSZob3N0PSZwYXRoPSZhbHBuPWh0dHAvMS4xJmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0305爱尔兰 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.244.204.173:443#0305美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.65.101.11:443#0305日本 
hysteria2://base64-cFBnT0xGd21rbVlZQlppNnE2Wmp6SzZnSlRRQDY0LjIzLjE3OC4yMDg6ODI0Mz9pbnNlY3VyZT0xJnNuaT1iaW5nLmNvbSZhbHBuPSZmcD0mb3M9#0305美国 
vless://base64-OGI1NGE2YzctMjU0NC00YTA3LTk1MjAtYjRlNTI1MmJhMmI3QDg5LjE4Ny4yOC4xMjY6ODQ0Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT11bC1qYXBhbjEuMDl2cG4uY29tJnR5cGU9d3MmaG9zdD0mcGF0aD0vdmxlc3MvJmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0305日本 
ss://YWVzLTI1Ni1nY206SUhXTFlaU1NTWDRHU0tMQQ==@8tv68qhq.slashdevslashnetslashtun.net:16013#0305新加坡 
ss://YWVzLTI1Ni1nY206WU1CM1FMODVMN0YxS0pSNw==@8tv68qhq.slashdevslashnetslashtun.net:18013#0305日本 
ss://YWVzLTI1Ni1nY206V05XNU1aSlg1N1pKVU5RVQ==@8tv68qhq.slashdevslashnetslashtun.net:16009#0305新加坡 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989#0305斯洛文尼亚共和国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpPREEyTUdaaA==@95.164.36.59:8388#0305奥地利 
vless://base64-MWE3YTM5ZTQtOGM5Yi00MDUyLWI4YjItYzA5Mjk1MzZiYmE1QDk1LjE2NC40Ljg4Ojg0NDM/Zmxvdz0mZW5jcnlwdGlvbj1ub25lJnNlY3VyaXR5PXRscyZzbmk9cHEtYnJhemlsMS4wOXZwbi5jb20mdHlwZT13cyZob3N0PSZwYXRoPS92bGVzcy8maGVhZGVyVHlwZT1ub25lJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0305巴西 
ss://YWVzLTI1Ni1nY206MDQwN1dLSUVJWE1UTEdDNg==@qh62onjn.slashdevslashnetslashtun.net:16007#0305新加坡 
ss://YWVzLTI1Ni1nY206RkNFVU9BU1JRSkMwTE4wSw==@qh62onjn.slashdevslashnetslashtun.net:15009#0305香港 
ss://YWVzLTI1Ni1nY206UkJOMVVOR1ZQRjFCUVhQSw==@ti3hyra4.slashdevslashnetslashtun.net:15006#0305香港 
ss://YWVzLTI1Ni1nY206QkZZQ09LSFRDOEhJV1dSQg==@ti3hyra4.slashdevslashnetslashtun.net:16006#0305新加坡 
ss://YWVzLTI1Ni1nY206ODRITVJBV0lMS0I0OVFVWg==@ti3hyra4.slashdevslashnetslashtun.net:18002#0305日本 
ss://YWVzLTI1Ni1nY206WTJVNThTOTBFM0dTVDFBUQ==@ti3hyra4.slashdevslashnetslashtun.net:21001#0305台湾 
hysteria2://base64-NGE0ODg3MWQ0OWMzZjIwZmQ5M2QzNjVjNDllNDVmNzhAdi5jY3MudmFhbGEuY2F0OjQ0Mz9pbnNlY3VyZT0wJnNuaT12LmNjcy52YWFsYS5jYXQmYWxwbj0mZnA9Jm9zPQ==#0305美国 
ss://YWVzLTI1Ni1nY206NFM4NUxGMlEzUUs5MjE3MQ==@w72tapyb.slashdevslashnetslashtun.net:18008#0305日本 
vmess://eyJ2IjoiMiIsImFkZCI6Ind3dy5hZXR2LmNvbSIsInBvcnQiOjgwLCJzY3kiOiJhdXRvIiwicHMiOiIwMzA15b635Zu9IiwibmV0Ijoid3MiLCJpZCI6IjdkYzc4NTgyLTg4YTgtNGI0Yy05ZTNlLTUwODMxZDY3Mjc2NiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiYW1kLmFsIiwicGF0aCI6Ii9YRVNBTElTVEhFQkVTVD9lZD0yMDQ4IiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiYW1kLmFsIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
hysteria2://base64-OTk5ZmU5N2EtNWNkMS00ZjlmLTk4MjYtODVkYjJiNTBhNmVmQHlpbmdndW8xLnN1OC5sb2w6ODg5OT9pbnNlY3VyZT0wJnNuaT15aW5nZ3VvMS5zdTgubG9sJmFscG49JmZwPSZvcz0=#0305英国 


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
