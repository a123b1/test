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

vmess://eyJ2IjoiMiIsImFkZCI6InY4LmhkYWNkLmNvbSIsInBvcnQiOjMwODA4LCJzY3kiOiJhdXRvIiwicHMiOiIwNTEw576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYzNi5oZGFjZC5jb20iLCJwb3J0IjozMDgzNiwic2N5IjoiYXV0byIsInBzIjoiMDUxMOiLseWbvSIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYzNS5oZGFjZC5jb20iLCJwb3J0IjozMDgzNSwic2N5IjoiYXV0byIsInBzIjoiMDUxMOazleWbvSIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYzNS5oZGFjZC5jb20iLCJwb3J0IjozMDgzNSwic2N5IjoiYXV0byIsInBzIjoiMDUxMOazleWbvSIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMC5oZGFjZC5jb20iLCJwb3J0IjozMDgzMCwic2N5IjoiYXV0byIsInBzIjoiMDUxMOiNt+WFsCIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ2MzAuaGRhY2QuY29tIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMC5oZGFjZC5jb20iLCJwb3J0IjozMDgwNywic2N5IjoiYXV0byIsInBzIjoiMDUxMOmmmea4ryIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMC5oZGFjZC5jb20iLCJwb3J0IjozMDgwNywic2N5IjoiYXV0byIsInBzIjoiMDUxMOmmmea4ryIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ2MTAuaGRhY2QuY29tIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://YWVzLTEyOC1nY206SlZyc0xMTjF0a044b1haTw==@chengbai02.ascwt179.com:13223?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=0&fragment=,100-200,10-60&os=#0510英国 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjA1MTDnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiMjAwMTpiYzg6MzJkNzozMDI6OjEwIiwicGF0aCI6Ii8/ZWQ9MjA0OCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjA1MTDnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoidGlhbmppdS5wYWdlcy5kZXYiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjA1MTDnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoiam9zcy5ncGoxLndlYi5pZCIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjA1MTDnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiODIuMTk4LjI0Ni45NyIsInBhdGgiOiI/ZWQ9MjA0OCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjA1MTDnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoidGlhbmppdS5wYWdlcy5kZXYiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjA1MTDnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoianAxLnNzdGFuay50b3AiLCJwYXRoIjoiL2hlbGxvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOSIsInBvcnQiOjE4MCwic2N5IjoiYXV0byIsInBzIjoiMDUxMOe+juWbvSIsIm5ldCI6InRjcCIsImlkIjoiZDEzZmMyZjUtM2UwNS00Nzk1LTgxZWItNDQxNDNhMDllNTUyIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOSIsInBvcnQiOjE4MCwic2N5IjoiYXV0byIsInBzIjoiMDUxMOe+juWbvSIsIm5ldCI6InRjcCIsImlkIjoiZDEzZmMyZjUtM2UwNS00Nzk1LTgxZWItNDQxNDNhMDllNTUyIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOSIsInBvcnQiOjE4MCwic2N5IjoiYXV0byIsInBzIjoiMDUxMOe+juWbvSIsIm5ldCI6InRjcCIsImlkIjoiZDEzZmMyZjUtM2UwNS00Nzk1LTgxZWItNDQxNDNhMDllNTUyIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJzZWE5LmZpcmV3YWxsY29udHJhY3QuY2xpY2siLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOSIsInBvcnQiOjE4MCwic2N5IjoiYXV0byIsInBzIjoiMDUxMOe+juWbvSIsIm5ldCI6InRjcCIsImlkIjoiZDEzZmMyZjUtM2UwNS00Nzk1LTgxZWItNDQxNDNhMDllNTUyIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOSIsInBvcnQiOjE4MCwic2N5IjoiYXV0byIsInBzIjoiMDUxMOe+juWbvSIsIm5ldCI6InRjcCIsImlkIjoiZDEzZmMyZjUtM2UwNS00Nzk1LTgxZWItNDQxNDNhMDllNTUyIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiI4Mi4xOTguMjQ2LjkiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOSIsInBvcnQiOjE4MCwic2N5IjoiYWVzLTEyOC1nY20iLCJwcyI6IjA1MTDnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMzciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjA1MTDnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoic2VhOS5maXJld2FsbGNvbnRyYWN0LmNsaWNrIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMzciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjA1MTDnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMzciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjA1MTDnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMzciLCJwb3J0IjoxODAsInNjeSI6ImFlcy0xMjgtZ2NtIiwicHMiOiIwNTEw576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMzciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjA1MTDnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMzciLCJwb3J0IjoxODAsInNjeSI6ImFlcy0xMjgtZ2NtIiwicHMiOiIwNTEw576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjUwIiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNTEw576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjUwIiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNTEw576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImZyYTUuY2hhc2VtMjAyNnN1ZC5jb20iLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjUwIiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNTEw576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InNlYTkuZmlyZXdhbGxjb250cmFjdC5jbGljayIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjUwIiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNTEw576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjUwIiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNTEw576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjUwIiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNTEw576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IjgyLjE5OC4yNDYuMjUwIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjUwIiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNTEw576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImZyYTM1LmNoYXNlbTIwMjZzdWQuY29tIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjMzIiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNTEw576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjMzIiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNTEw576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InNlYTkuZmlyZXdhbGxjb250cmFjdC5jbGljayIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjMzIiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNTEw576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjMzIiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNTEw576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IkhMLUZSRUVET00tMS5VTkRFRi5ORVRXT1JLIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjMzIiwicG9ydCI6MTgwLCJzY3kiOiJhZXMtMTI4LWdjbSIsInBzIjoiMDUxMOe+juWbvSIsIm5ldCI6InRjcCIsImlkIjoiZDEzZmMyZjUtM2UwNS00Nzk1LTgxZWItNDQxNDNhMDllNTUyIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjMzIiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNTEw576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImZyYTM1LmNoYXNlbTIwMjZzdWQuY29tIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjMzIiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNTEw576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjMzIiwicG9ydCI6MTgwLCJzY3kiOiJhZXMtMTI4LWdjbSIsInBzIjoiMDUxMOe+juWbvSIsIm5ldCI6InRjcCIsImlkIjoiZDEzZmMyZjUtM2UwNS00Nzk1LTgxZWItNDQxNDNhMDllNTUyIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjE0IiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNTEw576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjE0IiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNTEw576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjE0IiwicG9ydCI6MTgwLCJzY3kiOiJhZXMtMTI4LWdjbSIsInBzIjoiMDUxMOe+juWbvSIsIm5ldCI6InRjcCIsImlkIjoiZDEzZmMyZjUtM2UwNS00Nzk1LTgxZWItNDQxNDNhMDllNTUyIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjE0IiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNTEw576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjE0IiwicG9ydCI6MTgwLCJzY3kiOiJhZXMtMTI4LWdjbSIsInBzIjoiMDUxMOe+juWbvSIsIm5ldCI6InRjcCIsImlkIjoiZDEzZmMyZjUtM2UwNS00Nzk1LTgxZWItNDQxNDNhMDllNTUyIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@77.110.96.142:443?flow=&encryption=none&security=tls&sni=sni.latonyamadeline.ndjp.net&type=ws&host=sni.latonyamadeline.ndjp.net&path=/%3Fed%3D2560%26https%3A//t.me/WangCai2%F0%9F%87%A8%F0%9F%87%B3&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510拉脱维亚 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@77.110.96.142:443?flow=&encryption=none&security=tls&sni=sni.latonyamadeline.ndjp.net&type=ws&host=sni.latonyamadeline.ndjp.net&path=/&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510西班牙 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@62.60.149.222:8443?flow=&encryption=none&security=tls&sni=sni.latonyamadeline.ndjp.net&type=ws&host=sni.latonyamadeline.ndjp.net&path=/%3Fed%3D2560%26https%3A//t.me/WangCai2%F0%9F%87%A8%F0%9F%87%B3&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510沙特阿拉伯 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@46.8.229.26:2053?flow=&encryption=none&security=tls&sni=sni.111000.v6.army&type=ws&host=sni.111000.v6.army&path=/%3Fed%3D2560%26https%3A//t.me/wangcai2%F0%9F%87%A8%F0%9F%87%B3&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510捷克 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@46.8.229.26:8443?flow=&encryption=none&security=tls&sni=sni.111000.v6.army&type=ws&host=sni.111000.v6.army&path=/%3Fed%3D2560%26https%3A//t.me/wangcai2%F0%9F%87%A8%F0%9F%87%B3&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510拉脱维亚 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@46.8.229.218:2053?flow=&encryption=none&security=tls&sni=sni.111000.v6.army&type=ws&host=sni.111000.v6.army&path=/%3Fed%3D2560%26https%3A//t.me/wangcai2%F0%9F%87%A8%F0%9F%87%B3&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510拉脱维亚 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@217.144.190.230:443?flow=&encryption=none&security=tls&sni=sni.latonyamadeline.ndjp.net&type=ws&host=sni.latonyamadeline.ndjp.net&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510拉脱维亚 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@217.144.190.230:443?flow=&encryption=none&security=tls&sni=sni.latonyamadeline.ndjp.net&type=ws&host=sni.latonyamadeline.ndjp.net&path=/%3Fed%3D2560%26https%3A//t.me/WangCai2%F0%9F%87%A8%F0%9F%87%B3&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510拉脱维亚 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@194.247.186.199:443?flow=&encryption=none&security=tls&sni=sni.latonyamadeline.ndjp.net&type=ws&host=sni.latonyamadeline.ndjp.net&path=/%3Fed%3D2560%26https%3A//t.me/WangCai2%F0%9F%87%A8%F0%9F%87%B3&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510拉脱维亚 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@194.147.33.251:443?flow=&encryption=none&security=tls&sni=sni.111000.v6.army&type=ws&host=sni.111000.v6.army&path=/%3Fed%3D2560%26https%3A//t.me/WangCai2%F0%9F%87%A8%F0%9F%87%B3&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510拉脱维亚 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@193.23.219.205:8443?flow=&encryption=none&security=tls&sni=sni.latonyamadeline.ndjp.net&type=ws&host=sni.latonyamadeline.ndjp.net&path=/%3Fed%3D2560%26https%3A//t.me/WangCai2%F0%9F%87%A8%F0%9F%87%B3&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510拉脱维亚 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@193.23.219.205:8443?flow=&encryption=none&security=tls&sni=sni.latonyamadeline.ndjp.net&type=ws&host=sni.latonyamadeline.ndjp.net&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510香港 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@151.242.69.214:2053?flow=&encryption=none&security=tls&sni=sni.111000.v6.army&type=ws&host=sni.111000.v6.army&path=/%3Fed%3D2560%26https%3A//t.me/wangcai2%F0%9F%87%A8%F0%9F%87%B3&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510拉脱维亚 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@150.251.147.97:8443?flow=&encryption=none&security=tls&sni=sni.111000.v6.army&type=ws&host=sni.111000.v6.army&path=/%3Fed%3D2560%26https%3A//t.me/wangcai2%F0%9F%87%A8%F0%9F%87%B3&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510阿拉伯酋长国 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@148.253.210.141:443?flow=&encryption=none&security=tls&sni=sni.latonyamadeline.ndjp.net&type=ws&host=sni.latonyamadeline.ndjp.net&path=/%3Fed%3D2560%26https%3A//t.me/WangCai2%F0%9F%87%A8%F0%9F%87%B3&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510拉脱维亚 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@144.31.237.162:2053?flow=&encryption=none&security=tls&sni=sni.111000.v6.army&type=ws&host=sni.111000.v6.army&path=/%3Fhttps%3A//t.me/WangCai2%F0%9F%87%A8%F0%9F%87%B3%3D&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510沙特阿拉伯 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@138.124.16.38:8443?flow=&encryption=none&security=tls&sni=sni.111000.v6.army&type=ws&host=sni.111000.v6.army&path=/%3Fhttps%3A//t.me/WangCai2%F0%9F%87%A8%F0%9F%87%B3%3D&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510拉脱维亚 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwMy4xODEuMTY0LjE0NSIsInBvcnQiOjUxNTU2LCJzY3kiOiJhdXRvIiwicHMiOiIwNTEw5paw5Yqg5Z2hIiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwMy4xODEuMTY0LjE0NSIsInBvcnQiOjU0MDIyLCJzY3kiOiJhdXRvIiwicHMiOiIwNTEw6aaZ5rivIiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwMy4xODEuMTY0LjE0NSIsInBvcnQiOjU0MDIyLCJzY3kiOiJhdXRvIiwicHMiOiIwNTEw6aaZ5rivIiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjY0LCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwMy4xODEuMTY0LjE0NSIsInBvcnQiOjU0MDIyLCJzY3kiOiJhdXRvIiwicHMiOiIwNTEw6aaZ5rivIiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjY0LCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwMy4xODEuMTY0LjE0NSIsInBvcnQiOjUxNTU2LCJzY3kiOiJhdXRvIiwicHMiOiIwNTEw5paw5Yqg5Z2hIiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwMy4xODEuMTY0LjE0NSIsInBvcnQiOjU0MDIyLCJzY3kiOiJhdXRvIiwicHMiOiIwNTEw6aaZ5rivIiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwMy4xODEuMTY0LjE0NSIsInBvcnQiOjU0MDIyLCJzY3kiOiJhdXRvIiwicHMiOiIwNTEw6aaZ5rivIiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwMy4xODEuMTY0LjE0NSIsInBvcnQiOjUxNTU2LCJzY3kiOiJhdXRvIiwicHMiOiIwNTEw5paw5Yqg5Z2hIiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtcG9seTEzMDU6YzU1YjE0M2YtMGU3ZC00YTVlLTk3ZGItNTMwNmRmMDc0NDVhQDEwOS43MS4yNTMuMTk1OjU5MDI6d3M6LzJPbjdQeEs3JTNGZWQlM0QyNTYwOnN3ZGlzdC5hcHBsZS5jb206bm9uZTp0bHM6c3dkaXN0LmFwcGxlLmNvbTpbXTo6ZmFsc2U6LDEwMC0yMDAsMTAtNjA6#0510德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NjliYzY3ZmMtMjBhOS00N2YzLWE3YzktYjQxMTFiN2FhNjRhQDEwOS43MS4yNTMuMTk1OjQ4MDE6d3M6L2N4SDdIalcyMTN4OE4lM0ZlZCUzRDI1NjA6c3dkaXN0LmFwcGxlLmNvbTpub25lOnRsczpzd2Rpc3QuYXBwbGUuY29tOltdOjpmYWxzZTosMTAwLTIwMCwxMC02MDo=#0510德国 
hysteria2://bJTTi7P4vRdnUr2Of5f0eNFkSgCUeshmmM@109.71.253.195:16858?insecure=0&sni=swdist.apple.com&alpn=&fp=&obfs=salamander&obfs-password=DVM3F6CkvZkrMNsfiKDTy9ksoob2gX3&mport=&os=#0510德国 
hysteria2://FUee4MrqPrsTIEsUu98EKOy8avd@109.71.253.195:53720?insecure=0&sni=swdist.apple.com&alpn=&fp=&obfs=salamander&obfs-password=bqMEBBbyKZ9yLJSQM5CQB2qIC4QhrU6uchPW&mport=&os=#0510德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTk1IiwicG9ydCI6NTE5NjcsInNjeSI6ImF1dG8iLCJwcyI6IjA1MTDlvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiNjliYzY3ZmMtMjBhOS00N2YzLWE3YzktYjQxMTFiN2FhNjRhIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJzd2Rpc3QuYXBwbGUuY29tIiwicGF0aCI6Ii9obkJNRUphcWltOWkyRHZTYVRzSFZ4dHBXZWdUdkc/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiJzd2Rpc3QuYXBwbGUuY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://Y2hhY2hhMjAtcG9seTEzMDU6N2IyYjI2OGYtMzJiYy00ZjA3LTk1MmEtMGEzNjM2ZGFlNjIwQDEwOS43MS4yNTMuMTk1OjYxNjE3OndzOi9xdk40aUNIRHQzZlgxWHklM0ZlZCUzRDI1NjA6c3dkaXN0LmFwcGxlLmNvbTpub25lOnRsczpzd2Rpc3QuYXBwbGUuY29tOltdOjpmYWxzZTosMTAwLTIwMCwxMC02MDo=#0510德国 
hysteria2://qjNRDsh1N8AStTJT4BbbbOWZB8bRNP80JrKa@109.71.253.195:19727?insecure=0&sni=swdist.apple.com&alpn=&fp=&obfs=salamander&obfs-password=ObalFM8D9LLCa6kBKJUM3PwRDA2Y8&mport=&os=#0510德国 
anytls://64KKJY8CLn0ggQH1drwzIFQwQUCK3UyfQ@109.71.253.195:41222?insecure=0&sni=swdist.apple.com&alpn=h2&fp=&os=#0510德国 
vless://caaca38f-4442-4b20-9d3d-62d64d35c93e@109.71.253.195:23818?flow=&encryption=none&security=tls&sni=swdist.apple.com&type=ws&host=swdist.apple.com&path=/LDxqfUKA7dqOVbeWWf7wm2bmyY2R%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510德国 
trojan://7b2b268f-32bc-4f07-952a-0a3636dae620@109.71.253.195:20960?flow=&security=tls&sni=swdist.apple.com&type=ws&header=none&host=swdist.apple.com&path=/HWl0eeJoJp%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510德国 
anytls://xaWepRMbCqxQLljwxYgwDxEyb26A2@109.71.253.195:52251?insecure=0&sni=swdist.apple.com&alpn=h2&fp=&os=#0510德国 
trojan://e6e78261-1225-43f0-924e-a8e4688d960c@109.71.253.195:45919?flow=&security=tls&sni=swdist.apple.com&type=ws&header=none&host=swdist.apple.com&path=/gWRA3KNCuPHBWiAelk%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510德国 
trojan://c55b143f-0e7d-4a5e-97db-5306df07445a@109.71.253.195:12867?flow=&security=tls&sni=swdist.apple.com&type=ws&header=none&host=swdist.apple.com&path=/YlslRyiO9JX%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTk1IiwicG9ydCI6MjAxOTIsInNjeSI6ImF1dG8iLCJwcyI6IjA1MTDlvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiMWJlODFhZWItZWM0Zi00NDRkLWJlZWYtNjk2YjY0ZjJlMzVlIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJzd2Rpc3QuYXBwbGUuY29tIiwicGF0aCI6Ii81NUNzOTZnNlhRWW0xOGZIZTV5QUpjQmJOYzJ6YkE/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiJzd2Rpc3QuYXBwbGUuY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTk1IiwicG9ydCI6ODA2MSwic2N5IjoiYXV0byIsInBzIjoiMDUxMOW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJjYTgwYzQ1MC0wYmRmLTRlMTItOWIwZS1iNWI5MDdmOWE0OTEiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InN3ZGlzdC5hcHBsZS5jb20iLCJwYXRoIjoiL1l2dVd1ZDBnc1loWTNZb0g4P2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoic3dkaXN0LmFwcGxlLmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
hysteria2://AWAFvBicBZoVV0oHCtkWdwqwtnWicMIkK6voX@109.71.253.195:19937?insecure=0&sni=swdist.apple.com&alpn=&fp=&obfs=salamander&obfs-password=uuPUEjhs85uuRuxKJPxjyGpON4rp1SRppx&mport=&os=#0510德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.18.24.219:443?flow=&encryption=none&security=tls&sni=vod.cjowefs.qzz.io&type=xhttp&host=vod.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@instillmus.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=instillmus.oceanof.xyz&type=xhttp&host=instillmus.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@pouchedz.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=pouchedz.oceanof.xyz&type=xhttp&host=pouchedz.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.16.42.49:443?flow=&encryption=none&security=tls&sni=vod.cjowefs.qzz.io&type=xhttp&host=vod.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@173.245.59.70:443?flow=&encryption=none&security=tls&sni=vod.cjowefs.qzz.io&type=xhttp&host=vod.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@beckettilj.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=beckettilj.oceanof.xyz&type=xhttp&host=beckettilj.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@radiou.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=radiou.oceanof.xyz&type=xhttp&host=radiou.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.18.21.130:443?flow=&encryption=none&security=tls&sni=vod.cjowefs.qzz.io&type=xhttp&host=vod.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@stabileeq.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=stabileeq.oceanof.xyz&type=xhttp&host=stabileeq.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@attunek.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=attunek.oceanof.xyz&type=xhttp&host=attunek.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.27.113.190:443?flow=&encryption=none&security=tls&sni=vod.cjowefs.qzz.io&type=xhttp&host=vod.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.18.248.218:443?flow=&encryption=none&security=tls&sni=vod.cjowefs.qzz.io&type=xhttp&host=vod.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@pimozideb.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=pimozideb.oceanof.xyz&type=xhttp&host=pimozideb.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@batchus.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=batchus.oceanof.xyz&type=xhttp&host=batchus.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@141.101.121.129:443?flow=&encryption=none&security=tls&sni=vod.cjowefs.qzz.io&type=xhttp&host=vod.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@tiaragq.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=tiaragq.oceanof.xyz&type=xhttp&host=tiaragq.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@cragaib.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=cragaib.oceanof.xyz&type=xhttp&host=cragaib.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@yearlongww.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=yearlongww.oceanof.xyz&type=xhttp&host=yearlongww.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@tantalizerr.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=tantalizerr.oceanof.xyz&type=xhttp&host=tantalizerr.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.25.199.178:443?flow=&encryption=none&security=tls&sni=vod.cjowefs.qzz.io&type=xhttp&host=vod.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@103.21.244.203:443?flow=&encryption=none&security=tls&sni=vod.cjowefs.qzz.io&type=xhttp&host=vod.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@preteenmlr.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=preteenmlr.oceanof.xyz&type=xhttp&host=preteenmlr.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@scatzgp.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=scatzgp.oceanof.xyz&type=xhttp&host=scatzgp.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@theyus.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=theyus.oceanof.xyz&type=xhttp&host=theyus.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@eventur.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=eventur.oceanof.xyz&type=xhttp&host=eventur.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.16.228.174:443?flow=&encryption=none&security=tls&sni=vod.cjowefs.qzz.io&type=xhttp&host=vod.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@hornbookhlu.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=hornbookhlu.oceanof.xyz&type=xhttp&host=hornbookhlu.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.25.18.25:443?flow=&encryption=none&security=tls&sni=vod.cjowefs.qzz.io&type=xhttp&host=vod.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@103.21.244.114:443?flow=&encryption=none&security=tls&sni=vod.cjowefs.qzz.io&type=xhttp&host=vod.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.24.205.235:443?flow=&encryption=none&security=tls&sni=vod.cjowefs.qzz.io&type=xhttp&host=vod.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@162.159.18.195:443?flow=&encryption=none&security=tls&sni=vod.cjowefs.qzz.io&type=xhttp&host=vod.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@uniformndy.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=uniformndy.oceanof.xyz&type=xhttp&host=uniformndy.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@173.245.59.242:443?flow=&encryption=none&security=tls&sni=vod.cjowefs.qzz.io&type=xhttp&host=vod.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0510德国 


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
