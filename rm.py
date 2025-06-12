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
vmess://eyJ2IjoiMiIsImFkZCI6IjE1MDAyLmt1YWl5aW4wMi50b3AiLCJwb3J0IjoxNTAwMiwic2N5IjoiYXV0byIsInBzIjoiMDYxMeS/hOe9l+aWryIsIm5ldCI6InRjcCIsImlkIjoiOWY1MTMxNjEtNTc2Yi0zYWJjLTljOTgtMDZlNTJjM2EyNGM2IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIxNTAwMi5rdWFpeWluMDIudG9wIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InRrLmh6bHQudGtkZG5zLnh5eiIsInBvcnQiOjIyNjQxLCJzY3kiOiJhdXRvIiwicHMiOiIwNjEx576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6Ijk4ZTk2YzlmLTRiYjMtMzlkNC05YTJjLWZhYzA0MjU3ZjdjNyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoienhqcC1hLnRrb25nLmNjIiwicGF0aCI6Ii8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0IjozMDA1Miwic2N5IjoiYXV0byIsInBzIjoiMDYxMeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InY3LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA3LCJzY3kiOiJhdXRvIiwicHMiOiIwNjEx576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoidjcuaGVkdWlhbi5saW5rIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InY3LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA3LCJzY3kiOiJhdXRvIiwicHMiOiIwNjEx576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYyOS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyOSwic2N5IjoiYXV0byIsInBzIjoiMDYxMee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQwIiwicG9ydCI6MzEyMDksInNjeSI6ImF1dG8iLCJwcyI6IjA2MTHmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzguOTAuOCIsInBvcnQiOjM5MDc2LCJzY3kiOiJhdXRvIiwicHMiOiIwNjEx576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0MTMwMiwic2N5IjoiYXV0byIsInBzIjoiMDYxMeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQxIiwicG9ydCI6NDE0OTEsInNjeSI6ImF1dG8iLCJwcyI6IjA2MTHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQxIiwicG9ydCI6NDE0OTEsInNjeSI6ImF1dG8iLCJwcyI6IjA2MTHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzguOTAuOCIsInBvcnQiOjQxNzY2LCJzY3kiOiJhdXRvIiwicHMiOiIwNjEx576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzguOTAuOCIsInBvcnQiOjQxNzY2LCJzY3kiOiJhdXRvIiwicHMiOiIwNjEx576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjY0LCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzguOTAuOCIsInBvcnQiOjQxNzY2LCJzY3kiOiJhdXRvIiwicHMiOiIwNjEx576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjY0LCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQwIiwicG9ydCI6NDMyOTIsInNjeSI6ImF1dG8iLCJwcyI6IjA2MTHmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE2IiwicG9ydCI6NDYxNTksInNjeSI6ImF1dG8iLCJwcyI6IjA2MTHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE2IiwicG9ydCI6NDYxNTksInNjeSI6ImF1dG8iLCJwcyI6IjA2MTHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzguOTAuOCIsInBvcnQiOjQ2OTIwLCJzY3kiOiJhdXRvIiwicHMiOiIwNjEx576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzguOTAuOCIsInBvcnQiOjQ2OTIwLCJzY3kiOiJhdXRvIiwicHMiOiIwNjEx576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjY0LCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzguOTAuOCIsInBvcnQiOjQ2OTIwLCJzY3kiOiJhdXRvIiwicHMiOiIwNjEx576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzQuMTAyLjIyOSIsInBvcnQiOjQ5MTc0LCJzY3kiOiJhdXRvIiwicHMiOiIwNjEx576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE5IiwicG9ydCI6NDkzNTUsInNjeSI6ImF1dG8iLCJwcyI6IjA2MTHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE5IiwicG9ydCI6NDkzNTUsInNjeSI6ImF1dG8iLCJwcyI6IjA2MTHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE5IiwicG9ydCI6NTEwOTUsInNjeSI6ImF1dG8iLCJwcyI6IjA2MTHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjEyMyIsInBvcnQiOjUyMzUyLCJzY3kiOiJhdXRvIiwicHMiOiIwNjEx576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE2IiwicG9ydCI6NTkwODIsInNjeSI6ImF1dG8iLCJwcyI6IjA2MTHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://f18d9e84-6988-442d-b3f2-885740a6e775@to01.34gpg.shop:443?flow=&encryption=none&security=tls&sni=to01.34gpg.shop&type=ws&host=to01.34gpg.shop&path=/f18d9e84-6988-442d-b3f2-885740a6e775&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611香港 
vmess://eyJ2IjoiMiIsImFkZCI6ImNvcy1jZG4taS5hbGljZG4ud2luIiwicG9ydCI6NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwNjEx576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjA5MjdkMWJmLWE0ZjQtNGIzOC05ZTQwLWM4MTYyYjBkNTNmNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiYWxpeXVuLWNvcy1jZG4tYXBpYmIuNTJlZHUubWVuIiwicGF0aCI6Ii9hcGkvdjEvc2VydmUiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJhbGl5dW4tY29zLWNkbi1hcGliYi41MmVkdS5tZW4iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE2Mi4xNTkuMTM1Ljc2IiwicG9ydCI6MjA1Mywic2N5IjoiYXV0byIsInBzIjoiMDYxMeazleWbvSIsIm5ldCI6IndzIiwiaWQiOiI4ODIyOTJhMy01NGU4LTRjOWMtZjBiNy1lNzQzNGNmNWRhNWIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImRlLmh1YXdlaXd1dTUueHl6IiwicGF0aCI6Ii8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJkZS5odWF3ZWl3dXU1Lnh5eiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE1MDAyLmt1YWl5aW4wMi50b3AiLCJwb3J0IjoxNTAwMiwic2N5IjoiYXV0byIsInBzIjoiMDYxMeS/hOe9l+aWryIsIm5ldCI6InRjcCIsImlkIjoiOWY1MTMxNjEtNTc2Yi0zYWJjLTljOTgtMDZlNTJjM2EyNGM2IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InRrLmh6bHQudGtkZG5zLnh5eiIsInBvcnQiOjIyNjQyLCJzY3kiOiJhdXRvIiwicHMiOiIwNjEx576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6Ijk4ZTk2YzlmLTRiYjMtMzlkNC05YTJjLWZhYzA0MjU3ZjdjNyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoienhqcC1iLnRrb25nLmNjIiwicGF0aCI6Ii8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InRrLmh6bHQudGtkZG5zLnh5eiIsInBvcnQiOjIyNjQzLCJzY3kiOiJhdXRvIiwicHMiOiIwNjEx576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6Ijk4ZTk2YzlmLTRiYjMtMzlkNC05YTJjLWZhYzA0MjU3ZjdjNyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoienhqcC1jLnRrb25nLmNjIiwicGF0aCI6Ii8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoienhqcC1jLnRrb25nLmNjIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InRrLmh6bHQudGtkZG5zLnh5eiIsInBvcnQiOjIyNjQzLCJzY3kiOiJhdXRvIiwicHMiOiIwNjEx576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6Ijk4ZTk2YzlmLTRiYjMtMzlkNC05YTJjLWZhYzA0MjU3ZjdjNyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoienhqcC1jLnRrb25nLmNjIiwicGF0aCI6Ii8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMi5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgxMiwic2N5IjoiYXV0byIsInBzIjoiMDYxMeaWsOWKoOWdoSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYyNC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyNCwic2N5IjoiYXV0byIsInBzIjoiMDYxMee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6InYyNC5oZWR1aWFuLmxpbmsiLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMi5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzMiwic2N5IjoiYXV0byIsInBzIjoiMDYxMee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMi5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzMiwic2N5IjoiYXV0byIsInBzIjoiMDYxMee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InY0MC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDg0MCwic2N5IjoiYXV0byIsInBzIjoiMDYxMee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaTEwMC1jb3JlLXF1aWMtbGYuYW1lbXYuY29tIiwicGF0aCI6Ii9pbmRleCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://1a79d43f-b41c-496b-a241-dcbeefa81f0e@91.103.140.206:443?flow=&encryption=none&security=tls&sni=0926.qiang2000.link&type=ws&host=0926.qiang2000.link&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611美国 
vless://ac5b2e52-435b-4461-a99c-1317ab0e2889@dddfcvg.freevpnatm.dpdns.org:443?flow=&encryption=none&security=tls&sni=dDDfcvG.fReEVPnatm.dPdNS.OrG&type=ws&host=dddfcvg.freevpnatm.dpdns.org&path=/KMeBwp0RuivA5B99DmZDo0oju2st1&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611美国 
vless://c8eac4b7-95ba-4ce0-920d-c3279eb3b391@104.21.78.243:443?flow=&encryption=none&security=tls&sni=cCVBNhJ.7282728.XYZ&type=ws&host=ccvbnhj.7282728.xyz&path=/6r23FpdcA4KNAXX&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611美国 
vless://585acd30-52bf-4b70-a537-e13649fafefc@162.159.140.167:443?flow=&encryption=none&security=tls&sni=XszAW34.7282728.xYZ&type=ws&host=xszaw34.7282728.xyz&path=/rU9rSjDSOd4yY2fOe%3Fed%3D2048/%40Evay_vpn----%40Evay_vpn----%40Evay_vpn----%40Evay_vpn----%40Evay_vpn----%40Evay_vpn----%40Evay_vpn----%40Evay_vpn----%40Evay_vpn----%40Evay_vpn----%40Evay_vpn&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611美国 
vless://ea286109-d20f-415e-849e-4af20ab04b65@135.148.211.208:443?flow=&encryption=none&security=tls&sni=147135001195.sec22org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611美国 
vless://895552fa-6284-4c1d-ba00-3944e0c7c626@172.67.212.82:443?flow=&encryption=none&security=tls&sni=EEdfR.131.Pp.ua&type=ws&host=eedfr.131.pp.ua&path=/C1SukvGdr58yeduy9AOG&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@all.tellmethetrue.shop:443?flow=&encryption=none&security=tls&sni=vp39.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611美国 
vless://2558c819-1363-4859-8fb9-f8cb104d49d2@176.223.66.8:39948?flow=&encryption=none&security=&sni=&type=tcp&host=divarcdn.com&path=&headerType=http&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611土耳其 
trojan://2c605663-b89a-5734-a9d6-97d4743d72cf@dozo01.flztjc.top:8313?flow=&security=tls&sni=hk-13-568.flztjc.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611香港 
trojan://2c605663-b89a-5734-a9d6-97d4743d72cf@dozo01.flztjc.top:8313?flow=&security=tls&sni=dozo01.flztjc.top&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611香港 
trojan://2b1ed981-6547-4094-998b-06a3323d6f6c@120.233.44.201:21031?flow=&security=tls&sni=k54.tudou211.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611马来西亚 
trojan://2b1ed981-6547-4094-998b-06a3323d6f6c@120.233.44.201:21031?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611马来西亚 
trojan://2b1ed981-6547-4094-998b-06a3323d6f6c@120.233.44.201:21079?flow=&security=tls&sni=k32.tudou211.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611马来西亚 
trojan://2b1ed981-6547-4094-998b-06a3323d6f6c@120.233.44.201:21079?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611马来西亚 
trojan://2b1ed981-6547-4094-998b-06a3323d6f6c@120.233.44.201:21102?flow=&security=tls&sni=k28.tudou211.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611德国 
trojan://2b1ed981-6547-4094-998b-06a3323d6f6c@120.233.44.201:21102?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611德国 
trojan://2b1ed981-6547-4094-998b-06a3323d6f6c@120.233.44.201:21179?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611阿拉伯酋长国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpMTVNOaDIxVHJYalIyb2syNVEybkU4RU5UMnpvQm1QdmthM1JDQ1VBSFpFTENuV29la1ZqdmFmODlxd2NSa2RieEVmZXAyYmMyYVV0bW54cXZGMWF5UVJlejFKSGpVTGo=@exchange.gameaurela.click:52952?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0611保加利亚 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0611斯洛文尼亚共和国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0IjozMDA1Miwic2N5IjoiYXV0byIsInBzIjoiMDYxMeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0MTAyNCwic2N5IjoiYXV0byIsInBzIjoiMDYxMeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0MTAyNCwic2N5IjoiYXV0byIsInBzIjoiMDYxMeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJvY2JjLmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0MTAyNCwic2N5IjoiYXV0byIsInBzIjoiMDYxMeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNDQuMTI2IiwicG9ydCI6NDc4ODMsInNjeSI6ImF1dG8iLCJwcyI6IjA2MTHmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNDQuMTI2IiwicG9ydCI6NDc4ODMsInNjeSI6ImF1dG8iLCJwcyI6IjA2MTHmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMi5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgxMiwic2N5IjoiYXV0byIsInBzIjoiMDYxMeaWsOWKoOWdoSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0611波兰 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjE0Ny4yMDEuMjMxIiwicG9ydCI6MjIwNjUsInNjeSI6ImF1dG8iLCJwcyI6IjA2MTHnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiOTYzYmY2ODQtYjYwNC00ZjY1LTg2NmEtMjA3MzNkYjgzN2M4IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjE0Ny4yMDEuMjMxIiwicG9ydCI6MjIwNjUsInNjeSI6ImF1dG8iLCJwcyI6IjA2MTHnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiOTYzYmY2ODQtYjYwNC00ZjY1LTg2NmEtMjA3MzNkYjgzN2M4IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiI0NS4xNDcuMjAxLjIzMSIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://78f71fb4-3425-4eb8-a734-8b5401634fa8@195.133.11.229:443?flow=&encryption=none&security=tls&sni=lessless.duckdns.org&type=ws&host=lessless.duckdns.org&path=/getupdates&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611澳大利亚 
trojan://85f133142f04dbf6547da33895cfabb3@203.156.253.12:39001?flow=&security=tls&sni=www.yrtok.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611韩国 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@125.141.26.12:4857?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0611韩国 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@221.150.109.89:11389?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0611韩国 
vmess://eyJ2IjoiMiIsImFkZCI6InY2LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA2LCJzY3kiOiJhdXRvIiwicHMiOiIwNjEx5pel5pysIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0Ijoib2NiYy5jb20iLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InY2LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA2LCJzY3kiOiJhdXRvIiwicHMiOiIwNjEx5pel5pysIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0Ijoib2NiYy5jb20iLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://dd6dcb10-4683-11f0-ae79-1239d0255272@51.38.65.155:443?flow=&security=tls&sni=uk1.test3.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611英国 
vless://2d47a067-fa29-4d62-b596-b58c8782e880@185.232.152.17:12243?flow=&encryption=none&security=&sni=&type=ws&host=&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611法国 
hysteria2://da0fc212-9e6a-4387-8e61-1e0ef0aae565@107.172.235.75:38834?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&mport=&os=#0611美国 
ss://YWVzLTI1Ni1jZmI6eWlqaWFuMDUwMw==@54.180.148.149:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0611韩国 
vless://616dcaf2-dde9-4ff9-8111-c36aed98751b@45.82.120.117:59017?flow=&encryption=none&security=tls&sni=high.work.lzg.me&type=ws&host=high.work.lzg.me&path=/7VdwhhAVwCjqWI%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611德国 
anytls://Fqttsw0ThxibG0qT7E8tz@45.82.120.117:23167?insecure=1&sni=high.work.lzg.me&alpn=h2&fp=&os=#0611德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@162.159.245.40:443?flow=&encryption=none&security=tls&sni=www.ujhyidfghj.dpdns.org&type=xhttp&host=www.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMC4xMTciLCJwb3J0Ijo0NTc2MCwic2N5IjoiYXV0byIsInBzIjoiMDYxMeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJiOTk0ODcwNi1kODU3LTQzYzktOWY0Zi01NmExMDg3M2QwZmQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImhpZ2gud29yay5semcubWUiLCJwYXRoIjoiL01SOUN1VXNZWkU3MDR5eENtZVpvQTFUVT9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiaGlnaC53b3JrLmx6Zy5tZSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://6985d05e-d438-4713-9580-47db7983b063@45.82.120.117:59409?flow=&security=tls&sni=high.work.lzg.me&type=ws&header=none&host=high.work.lzg.me&path=/1o3mE8suq31zIFLhuT33Fv1G%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611德国 
hysteria2://FsOBIVjfTbhcmWK3a1dO@45.82.120.117:13283?insecure=1&sni=high.work.lzg.me&alpn=&fp=&obfs=salamander&obfs-password=yxhZdESzHUd7q1EE6LHHGr&mport=&os=#0611德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NDVmOGI2NDUtZGM3Yy00MGNkLWE2OTktZjkzYzQ2NDg4ODRjQDQ1LjgyLjEyMC4xMTc6MTc1MjM6d3M6L253eUhxZDE1SDBadGUyeHg4dWIwREU2WGhTWFR4JTNGZWQlM0QyNTYwOmhpZ2gud29yay5semcubWU6bm9uZTp0bHM6aGlnaC53b3JrLmx6Zy5tZTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0611德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@198.41.209.156:443?flow=&encryption=none&security=tls&sni=www.ujhyidfghj.dpdns.org&type=xhttp&host=www.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611德国 
hysteria2://my6A8OadAoGFkG5WQkHYVN8lWOrK@45.82.120.117:38015?insecure=1&sni=high.work.lzg.me&alpn=&fp=&obfs=salamander&obfs-password=9kA4GMZnMxyFmO2kx9SsMLHAFh&mport=&os=#0611德国 
anytls://rulmkChxOVAEBiSU50ETN@45.82.120.117:59949?insecure=1&sni=high.work.lzg.me&alpn=h2&fp=&os=#0611德国 
trojan://e9d90c82-dab8-4a89-896e-a96ee5930595@45.82.120.117:28045?flow=&security=tls&sni=high.work.lzg.me&type=ws&header=none&host=high.work.lzg.me&path=/glwNKuAKh9zNu%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@141.101.121.246:443?flow=&encryption=none&security=tls&sni=www.ujhyidfghj.dpdns.org&type=xhttp&host=www.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@190.93.246.121:443?flow=&encryption=none&security=tls&sni=www.ujhyidfghj.dpdns.org&type=xhttp&host=www.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611德国 
hysteria2://LYKDLvF5yjgbQTnslL2hYwxdE2CrG64@45.82.120.117:35554?insecure=1&sni=high.work.lzg.me&alpn=&fp=&obfs=salamander&obfs-password=pTUrW9L6OVuvJxYyJ3h7fLpAZqHNut4jp&mport=&os=#0611德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.24.226.87:443?flow=&encryption=none&security=tls&sni=www.ujhyidfghj.dpdns.org&type=xhttp&host=www.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZWZkZWIzMDctNmEyZi00MzdiLThlMDItZDdhZjAxNTljY2FjQDQ1LjgyLjEyMC4xMTc6MTA3ODM6d3M6L1RCQXBuZWpvSXZCMG9BVnNmcDdzOXhNNVNSdUdBWXAlM0ZlZCUzRDI1NjA6aGlnaC53b3JrLmx6Zy5tZTpub25lOnRsczpoaWdoLndvcmsubHpnLm1lOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0611德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6OTMxN2EzYTktMzAwOC00MTgyLTgyNTctNTE2OGQxMGRiMGJlQDQ1LjgyLjEyMC4xMTc6NjE1NjU6d3M6L0JWd3lYTFFDTk1LU1dENTZkZ3hoZXFuJTNGZWQlM0QyNTYwOmhpZ2gud29yay5semcubWU6bm9uZTp0bHM6aGlnaC53b3JrLmx6Zy5tZTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0611德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.20.208.177:443?flow=&encryption=none&security=tls&sni=www.ujhyidfghj.dpdns.org&type=xhttp&host=www.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@141.101.123.154:443?flow=&encryption=none&security=tls&sni=www.ujhyidfghj.dpdns.org&type=xhttp&host=www.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6YjkxYzg5OGItNjJjNC00NjYxLThhMjYtMTUzMDRkZTU4MDMwQDQ1LjgyLjEyMC4xMTc6MjQ0MzA6d3M6L3ZiWmFBenEwemU0M1g4Z0Q0WHNBOEElM0ZlZCUzRDI1NjA6aGlnaC53b3JrLmx6Zy5tZTpub25lOnRsczpoaWdoLndvcmsubHpnLm1lOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0611德国 
hysteria2://r0yXlTzRL8ZbXKMpySm7Z@45.82.120.117:43172?insecure=1&sni=high.work.lzg.me&alpn=&fp=&obfs=salamander&obfs-password=f8KxelLCGaOSkOunMhUi0fXYgnMK&mport=&os=#0611德国 
anytls://x0nOIo76Urm90NAk9AhUgELasofRKiF16XlX@45.82.120.117:41493?insecure=1&sni=high.work.lzg.me&alpn=h2&fp=&os=#0611德国 
anytls://eJArBzAR0xckWsqxINwd@45.82.120.117:54630?insecure=1&sni=high.work.lzg.me&alpn=h2&fp=&os=#0611德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@162.159.243.78:443?flow=&encryption=none&security=tls&sni=www.ujhyidfghj.dpdns.org&type=xhttp&host=www.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611德国 
anytls://Qb6XJOtLJ2zbq3SqfRRkhWjdyEsXwPBvb70@45.82.120.117:33474?insecure=1&sni=high.work.lzg.me&alpn=h2&fp=&os=#0611德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@198.41.198.174:443?flow=&encryption=none&security=tls&sni=www.ujhyidfghj.dpdns.org&type=xhttp&host=www.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@162.159.8.51:443?flow=&encryption=none&security=tls&sni=www.ujhyidfghj.dpdns.org&type=xhttp&host=www.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611德国 
hysteria2://eGhN5ezzQCBBWUwaClzO9TX8fS8Cy9V0du@45.82.120.117:38797?insecure=1&sni=high.work.lzg.me&alpn=&fp=&obfs=salamander&obfs-password=zszvDxw1cCTKQgCzNAbOnuM&mport=&os=#0611德国 
anytls://14zfdpH5CgmIUkxDDDo@45.82.120.117:18011?insecure=1&sni=high.work.lzg.me&alpn=h2&fp=&os=#0611德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@108.162.196.116:443?flow=&encryption=none&security=tls&sni=www.ujhyidfghj.dpdns.org&type=xhttp&host=www.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.25.226.97:443?flow=&encryption=none&security=tls&sni=www.ujhyidfghj.dpdns.org&type=xhttp&host=www.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@103.21.244.170:443?flow=&encryption=none&security=tls&sni=www.ujhyidfghj.dpdns.org&type=xhttp&host=www.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MTQ1YzJkNGQtYzRkYi00NGE2LWI0N2MtOGEyYTUxMDVmMTRlQDQ1LjgyLjEyMC4xMTc6NTgyNTp3czovdHFjV2VtWWRmVlc2M0cyalJhTERkSTJETWl1VGF4R1olM0ZlZCUzRDI1NjA6aGlnaC53b3JrLmx6Zy5tZTpub25lOnRsczpoaWdoLndvcmsubHpnLm1lOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0611德国 
anytls://Q2ArI9iuOqn49B89pj3OhL3@45.82.120.117:48942?insecure=1&sni=high.work.lzg.me&alpn=h2&fp=&os=#0611德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@172.67.192.86:443?flow=&encryption=none&security=tls&sni=www.ujhyidfghj.dpdns.org&type=xhttp&host=www.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.22.35.167:443?flow=&encryption=none&security=tls&sni=www.ujhyidfghj.dpdns.org&type=xhttp&host=www.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611德国 
anytls://SjWvifRZ5k6jpPEAUu3TX0@45.82.120.117:18731?insecure=1&sni=high.work.lzg.me&alpn=h2&fp=&os=#0611德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMC4xMTciLCJwb3J0IjozMTE0MCwic2N5IjoiYXV0byIsInBzIjoiMDYxMeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIxYzI0NDQ5YS01YWI5LTQxZTEtYTVjYS02Y2U4NjA0NGNhNDAiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImhpZ2gud29yay5semcubWUiLCJwYXRoIjoiL3kyODRNMjF3ZU9oMlllRW54Z2NrbDRyUkU/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6ImhpZ2gud29yay5semcubWUiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@188.114.99.92:443?flow=&encryption=none&security=tls&sni=www.ujhyidfghj.dpdns.org&type=xhttp&host=www.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.49.21:443?flow=&encryption=none&security=tls&sni=www.ujhyidfghj.dpdns.org&type=xhttp&host=www.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.24.213.255:443?flow=&encryption=none&security=tls&sni=www.ujhyidfghj.dpdns.org&type=xhttp&host=www.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0611德国 
  
  
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
