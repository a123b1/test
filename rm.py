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

vmess://eyJ2IjoiMiIsImFkZCI6IjEwMy4xODEuMTY0LjE0NSIsInBvcnQiOjU0MDIyLCJzY3kiOiJhdXRvIiwicHMiOiIwNDIx6aaZ5rivIiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwMy4xODEuMTY0LjE0NSIsInBvcnQiOjU0MDIyLCJzY3kiOiJhdXRvIiwicHMiOiIwNDIx6aaZ5rivIiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjY0LCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwMy4xODEuMTY0LjE0NSIsInBvcnQiOjUxNTU2LCJzY3kiOiJhdXRvIiwicHMiOiIwNDIx5paw5Yqg5Z2hIiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.146:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0421越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.250:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0421越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.69:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0421越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.126:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0421越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.149:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0421越南 
ss://YWVzLTI1Ni1nY206YzVmY2RmNzgyOTExMmNiNA==@45.140.169.225:10974?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0421香港 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjE0IiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNDIx576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjE0IiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNDIx576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjMzIiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNDIx576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InNlYTkuZmlyZXdhbGxjb250cmFjdC5jbGljayIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjMzIiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNDIx576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjUwIiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNDIx576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjUwIiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNDIx576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjUwIiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNDIx576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InNlYTkuZmlyZXdhbGxjb250cmFjdC5jbGljayIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjUwIiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNDIx576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImZyYTUuY2hhc2VtMjAyNnN1ZC5jb20iLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMjUwIiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNDIx576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMzciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoic2VhOS5maXJld2FsbGNvbnRyYWN0LmNsaWNrIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMzciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuMzciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuNDYiLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOSIsInBvcnQiOjE4MCwic2N5IjoiYXV0byIsInBzIjoiMDQyMee+juWbvSIsIm5ldCI6InRjcCIsImlkIjoiZDEzZmMyZjUtM2UwNS00Nzk1LTgxZWItNDQxNDNhMDllNTUyIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJzZWE5LmZpcmV3YWxsY29udHJhY3QuY2xpY2siLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOSIsInBvcnQiOjE4MCwic2N5IjoiYXV0byIsInBzIjoiMDQyMee+juWbvSIsIm5ldCI6InRjcCIsImlkIjoiZDEzZmMyZjUtM2UwNS00Nzk1LTgxZWItNDQxNDNhMDllNTUyIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOSIsInBvcnQiOjE4MCwic2N5IjoiYXV0byIsInBzIjoiMDQyMee+juWbvSIsIm5ldCI6InRjcCIsImlkIjoiZDEzZmMyZjUtM2UwNS00Nzk1LTgxZWItNDQxNDNhMDllNTUyIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiNDEyMC1CRTA0LTEzZWY1NjA5Njk4OS40NTcuUFAudWEiLCJwYXRoIjoiL2tUNVZIWWNNcnBoZXNxUk96U1BvSHJCbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoidGlhbmppdS5wYWdlcy5kZXYiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoiam9zcy5ncGoxLndlYi5pZCIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiODIuMTk4LjI0Ni45NyIsInBhdGgiOiI/ZWQ9MjA0OCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiODIuMTk4LjI0Ni45NyIsInBhdGgiOiJlZD0yMDQ4IiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiMjAwMTpiYzg6MzJkNzozMDI6OjEwIiwicGF0aCI6Ii8/ZWQ9MjA0OCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiY2RuZmlyZS54aWFvbWlzcGVlZC5jb20iLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTEyOC1nY206SlZyc0xMTjF0a044b1haTw==@chengbai02.ascwt179.com:13223?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=0&fragment=,100-200,10-60&os=#0421英国 
ss://YWVzLTEyOC1nY206SlZyc0xMTjF0a044b1haTw==@chengbai02.ascwt179.com:13223?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0421英国 
vmess://eyJ2IjoiMiIsImFkZCI6ImVmYW4uZG5zZWZhbjA0ODgxLmNvbSIsInBvcnQiOjc3NTQsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjHpppnmuK8iLCJuZXQiOiJ0Y3AiLCJpZCI6IjAwOWU1NThkLTNjZjQtNDlkOC1iNWU0LTgyYzllMTRmZTFhNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoic2VhOS5maXJld2FsbGNvbnRyYWN0LmNsaWNrIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6ImVmYW4uZG5zZWZhbjA0ODgxLmNvbSIsInBvcnQiOjc3NTQsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjHpppnmuK8iLCJuZXQiOiJ0Y3AiLCJpZCI6IjAwOWU1NThkLTNjZjQtNDlkOC1iNWU0LTgyYzllMTRmZTFhNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiZWZhbi5kbnNlZmFuMDQ4ODEuY29tIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6ImVmYW4uZG5zZWZhbjA0ODgxLmNvbSIsInBvcnQiOjc3NTQsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjHpppnmuK8iLCJuZXQiOiJ0Y3AiLCJpZCI6IjAwOWU1NThkLTNjZjQtNDlkOC1iNWU0LTgyYzllMTRmZTFhNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiZnJhNS5jaGFzZW0yMDI2c3VkLmNvbSIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6ImVmYW4uZG5zZWZhbjA0ODgxLmNvbSIsInBvcnQiOjc3NTQsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjHpppnmuK8iLCJuZXQiOiJ0Y3AiLCJpZCI6IjAwOWU1NThkLTNjZjQtNDlkOC1iNWU0LTgyYzllMTRmZTFhNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTo3ZTczMWVjMy1mOGUxLTQzZjYtOTJjZi0zOTc4ZDE0NzA1YzQ=@r3mrcg001286ek2.cybervena.com:50099?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0421台湾 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTplNzc3NTEzZS05ZGY1LTRkYzMtYmM4NC03NGU1NjQzNDVhODE=@usgpt.slianrk.com:13012?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0421美国 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMC5oZGFjZC5jb20iLCJwb3J0IjozMDgwNywic2N5IjoiYXV0byIsInBzIjoiMDQyMemmmea4ryIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ2MTAuaGRhY2QuY29tIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMC5oZGFjZC5jb20iLCJwb3J0IjozMDgwNywic2N5IjoiYXV0byIsInBzIjoiMDQyMemmmea4ryIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYzNi5oZGFjZC5jb20iLCJwb3J0IjozMDgzNiwic2N5IjoiYXV0byIsInBzIjoiMDQyMeiLseWbvSIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InZtNTE1NDQ1NDIuZG5zODY1NjgxNS5jb20iLCJwb3J0Ijo3NzU0LCJzY3kiOiJhdXRvIiwicHMiOiIwNDIx6aaZ5rivIiwibmV0IjoidGNwIiwiaWQiOiI3Y2Q5NmRiZS1lY2VjLTQ5MzctOWUwNS04N2FiNzBhZjJmMzAiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTc1LjIyMC4yMzEiLCJwb3J0IjozNzkxMiwic2N5IjoiYXV0byIsInBzIjoiMDQyMeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJhNTdlMjhiMy01ZjEyLTQ4MTQtYTM0ZS05YTJhZmVlNzg4M2QiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5kaWdpdGFsb2NlYW4uY29tIiwicGF0aCI6Ii8wVm0/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6Ind3dy5kaWdpdGFsb2NlYW4uY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
anytls://U7mb6gGvN4Vo0Lk5xg9WFlcY@5.175.220.231:3849?insecure=1&sni=www.digitalocean.com&alpn=h2&fp=&os=#0421德国 
hysteria2://KNk0rRbTyRn1Ubx2okm18kNOiva49Ih3e1r5L3ZN@5.175.220.231:54088?insecure=1&sni=www.digitalocean.com&alpn=&fp=&obfs=salamander&obfs-password=ewEV2hz6BD0lNh2H9Wv154c74sA53HsraKkfJV&mport=&os=#0421德国 
anytls://Y852wsEDe2IW6ZcOMFsAZr@5.175.220.231:63697?insecure=1&sni=www.digitalocean.com&alpn=h2&fp=&os=#0421德国 
anytls://6vHNftKy5zm52li76YQmJ0u@5.175.220.231:56084?insecure=1&sni=www.digitalocean.com&alpn=h2&fp=&os=#0421德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTc1LjIyMC4yMzEiLCJwb3J0IjozMDU5LCJzY3kiOiJhdXRvIiwicHMiOiIwNDIx5b635Zu9IiwibmV0Ijoid3MiLCJpZCI6ImUzZTc4NDcwLTM4MzMtNDlmZC04NDgxLWQwOWI5YmM0YWE3OCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoid3d3LmRpZ2l0YWxvY2Vhbi5jb20iLCJwYXRoIjoiL0xvVWR2SlJjSXVwUUY0ajh4dXFaRmQ/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6Ind3dy5kaWdpdGFsb2NlYW4uY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://a29194e4-d802-4c2e-861c-6fba1c1109ad@5.175.220.231:63155?flow=&security=tls&sni=www.digitalocean.com&type=ws&header=none&host=www.digitalocean.com&path=/D6iEvLEG%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0421德国 
hysteria2://tvOSsDfoZTfsxqtYGlvo5KG4C@5.175.220.231:54025?insecure=1&sni=www.digitalocean.com&alpn=&fp=&obfs=salamander&obfs-password=XYpwCnZrNz2VXn1HYfRBSWXQHIeb5e2&mport=&os=#0421德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZTNlNzg0NzAtMzgzMy00OWZkLTg0ODEtZDA5YjliYzRhYTc4QDUuMTc1LjIyMC4yMzE6MjczMzI6d3M6L2pyY1YyS2VXbjFxcGZNYkklM0ZlZCUzRDI1NjA6d3d3LmRpZ2l0YWxvY2Vhbi5jb206bm9uZTp0bHM6d3d3LmRpZ2l0YWxvY2Vhbi5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0421德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6YjZiZTI0MGQtZTc0Ni00N2YyLTg3OWMtNjE4YjA2YTVkMTQ1QDUuMTc1LjIyMC4yMzE6NTI5NzE6d3M6L0dnWnZzR0VwYzVLRDBZMElVUmkyNnVyRWNQNkQlM0ZlZCUzRDI1NjA6d3d3LmRpZ2l0YWxvY2Vhbi5jb206bm9uZTp0bHM6d3d3LmRpZ2l0YWxvY2Vhbi5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0421德国 
anytls://QFD40rbT8mD0X73G7AiD5llb@5.175.220.231:54413?insecure=1&sni=www.digitalocean.com&alpn=h2&fp=&os=#0421德国 
vless://df87a0e4-b483-442a-aa78-e798fa5a208a@5.175.220.231:35815?flow=&encryption=none&security=tls&sni=www.digitalocean.com&type=ws&host=www.digitalocean.com&path=/N67TCa5hFSZEzxu%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0421德国 
hysteria2://shWcRgmAbm9T8kRQQNUy7cJUmZoqeCMBJmvk9KSa@5.175.220.231:10348?insecure=1&sni=www.digitalocean.com&alpn=&fp=&obfs=salamander&obfs-password=hDr8jGVPAXlAZgJL3eheGvMxoirJ8nv5lOXWtyQX&mport=&os=#0421德国 
trojan://c3fcb8e2-5ed9-49a6-bf2d-47ab5d1a1a0a@5.175.220.231:8229?flow=&security=tls&sni=www.digitalocean.com&type=ws&header=none&host=www.digitalocean.com&path=/l5ig7PZ14H0Ps4GZBfaq8%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0421德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@198.41.215.192:443?flow=&encryption=none&security=tls&sni=kocvf.vidlx.qzz.io&type=xhttp&host=kocvf.vidlx.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0421德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@remarriagew.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=remarriagew.oceanof.xyz&type=xhttp&host=remarriagew.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0421美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@deathibq.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=deathibq.oceanof.xyz&type=xhttp&host=deathibq.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0421美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.27.29.71:443?flow=&encryption=none&security=tls&sni=kocvf.vidlx.qzz.io&type=xhttp&host=kocvf.vidlx.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0421德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@watermelonqn.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=watermelonqn.oceanof.xyz&type=xhttp&host=watermelonqn.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0421美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@deplorabley.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=deplorabley.oceanof.xyz&type=xhttp&host=deplorabley.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0421美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.27.87.206:443?flow=&encryption=none&security=tls&sni=kocvf.vidlx.qzz.io&type=xhttp&host=kocvf.vidlx.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0421德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@173.245.59.70:443?flow=&encryption=none&security=tls&sni=kocvf.vidlx.qzz.io&type=xhttp&host=kocvf.vidlx.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0421德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@162.159.18.195:443?flow=&encryption=none&security=tls&sni=kocvf.vidlx.qzz.io&type=xhttp&host=kocvf.vidlx.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0421德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@panamafgx.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=panamafgx.oceanof.xyz&type=xhttp&host=panamafgx.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0421美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@afluttero.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=afluttero.oceanof.xyz&type=xhttp&host=afluttero.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0421美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.25.97.141:443?flow=&encryption=none&security=tls&sni=kocvf.vidlx.qzz.io&type=xhttp&host=kocvf.vidlx.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0421德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.27.27.86:443?flow=&encryption=none&security=tls&sni=kocvf.vidlx.qzz.io&type=xhttp&host=kocvf.vidlx.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0421德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.27.65.243:443?flow=&encryption=none&security=tls&sni=kocvf.vidlx.qzz.io&type=xhttp&host=kocvf.vidlx.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0421德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@manihotjw.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=manihotjw.oceanof.xyz&type=xhttp&host=manihotjw.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0421美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.21.115.63:443?flow=&encryption=none&security=tls&sni=kocvf.vidlx.qzz.io&type=xhttp&host=kocvf.vidlx.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0421德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@socialitevo.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=socialitevo.oceanof.xyz&type=xhttp&host=socialitevo.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0421美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@dabj.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=dabj.oceanof.xyz&type=xhttp&host=dabj.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0421美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.16.228.174:443?flow=&encryption=none&security=tls&sni=kocvf.vidlx.qzz.io&type=xhttp&host=kocvf.vidlx.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0421德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.16.42.49:443?flow=&encryption=none&security=tls&sni=kocvf.vidlx.qzz.io&type=xhttp&host=kocvf.vidlx.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0421德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@pressonjn.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=pressonjn.oceanof.xyz&type=xhttp&host=pressonjn.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0421美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@krautab.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=krautab.oceanof.xyz&type=xhttp&host=krautab.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0421美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@188.114.98.202:443?flow=&encryption=none&security=tls&sni=kocvf.vidlx.qzz.io&type=xhttp&host=kocvf.vidlx.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0421德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@103.21.244.235:443?flow=&encryption=none&security=tls&sni=kocvf.vidlx.qzz.io&type=xhttp&host=kocvf.vidlx.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0421德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@solsticefk.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=solsticefk.oceanof.xyz&type=xhttp&host=solsticefk.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0421美国 

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
