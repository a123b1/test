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
trojan://humanity@104.18.152.77:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0807法国 
trojan://humanity@104.21.46.3:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=h2%2Chttp/1.1%2Ch3&fp=chrome&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0807法国 
trojan://humanity@104.26.14.137:443?flow=&security=tls&sni=www.ignitelimit.com&type=ws&header=none&host=&path=/assignment&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0807法国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@13.50.4.72:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=0&fragment=,100-200,10-60&os=#0807瑞典 
vless://60ba3369-9a78-40fe-98c3-233a6f107043@135.106.140.23:443?flow=&encryption=none&security=tls&sni=qwesd.rutendingaltos.top&type=xhttp&host=qwesd.rutendingaltos.top&path=/assets/build/_app/immutable/chunks/stream-one/&mode=auto&alpn=&fp=edge&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0807美国 
vless://XpnTeam-15@140.248.186.45:443?flow=&encryption=none&security=tls&sni=ssl.fastly.com&type=ws&host=Appxdn.global.ssl.fastly.net&path=/&headerType=none&alpn=http/1.1&fp=chrome&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0807英国 
vless://f04c31f7-cfab-4824-d167-4137d836ea82@151.101.56.6:443?flow=&encryption=none&security=tls&sni=ssl.fastly.com&type=ws&host=c12.com&path=/&headerType=none&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0807芬兰 
vless://c6f220ed-41f2-21ba-438c-80f05ebbf92a@170.168.97.5:8443?flow=&encryption=none&security=reality&sni=download.nvidia.com&type=grpc&host=&serviceName=TunService&mode=gun&alpn=&fp=chrome&pbk=D2SXHZRRYM0WcFChGWd57XB-U73aIsGfMpe2-Gq5XSs&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0807美国 
vless://60ba3369-9a78-40fe-98c3-233a6f107043@178.72.162.73:443?flow=&encryption=none&security=tls&sni=ru6.ethicsdinnerpave.online&type=xhttp&host=ru6.ethicsdinnerpave.online&path=/assets/build/_app/immutable/chunks/stream-one/&mode=auto&alpn=&fp=qq&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0807亚美尼亚 
ss://YWVzLTI1Ni1nY206ZDFmYTJmNGI5OGEzOGJjOA==@194.87.47.152:10901?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=0&fragment=,100-200,10-60&os=#0807意大利 
ss://YWVzLTI1Ni1nY206ODFhMjA0MjkxNjVkZjg3ZQ==@195.133.23.200:10806?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=0&fragment=,100-200,10-60&os=#0807俄罗斯 
ss://YWVzLTI1Ni1nY206ZDk5YzQyMjE5OWU2MmI2Yg==@195.133.23.5:10910?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=0&fragment=,100-200,10-60&os=#0807俄罗斯 
ss://YWVzLTI1Ni1nY206YmRiMzEzYWRmNzRjMmVkZQ==@195.133.5.207:10860?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=0&fragment=,100-200,10-60&os=#0807香港 
vless://28d0edc6-93c9-4465-bac9-720274d8b8c4@201.51.1.11:40443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=deepl.com&type=tcp&host=&path=&headerType=none&alpn=&fp=qq&pbk=WRveYv8IuUyvai4jgnQ6nWCL971-wKboe8evES5arlg&sid=69d4&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0807俄罗斯 
ss://YWVzLTI1Ni1nY206ZmJjZWM3Njk1M2EyZDE3Mw==@212.193.6.107:10988?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=0&fragment=,100-200,10-60&os=#0807加拿大 
vless://5dc56757-458e-4df2-9e71-2a14ce47e8af@217.60.193.4:443?flow=&encryption=none&security=tls&sni=ddc-akn.astralweb.tech&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0807德国 
vless://95e8532b-cc69-42d4-9553-e3c23292b15b@45.151.101.103:8443?flow=&encryption=none&security=reality&sni=maps.apple.com&type=grpc&host=&serviceName=your-custom-path&mode=gun&alpn=&fp=chrome&pbk=OMlQAFrCMZ3DX0xlnbEZiByLBFzpUE8XJHJsrBzLdlY&sid=2da4299da566b7&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0807美国 
ss://YWVzLTI1Ni1nY206NmIzOWFlMzIzNGRmZDY4Yg==@46.17.45.76:10808?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=0&fragment=,100-200,10-60&os=#0807香港 
hysteria2://7836b28e-8451-4596-ad3e-e3601b2335ba@78.159.240.69:8443?insecure=0&sni=quic.tyr-agentstvo.tech&alpn=&fp=&mport=&os=#0807英国 
vless://7c74b0e4-f132-5583-4692-622a7d6b71a4@88.218.44.4:993?flow=xtls-rprx-vision&encryption=none&security=reality&sni=swcdn.apple.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=Nnpwm8dqFl9dlMJmg0M9G11vmgCKzNagFTn4tH4sWy4&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0807俄罗斯 
vless://7c74b0e4-f132-5583-4692-622a7d6b71a4@88.218.44.4:993?flow=xtls-rprx-vision&encryption=none&security=reality&sni=download.nvidia.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=EG3y7UktGRlzSZZ2oXT_YaO2gVP4ca3Xe6AQ0u9A5DQ&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0807荷兰 
vless://9500cf8b-020a-4a70-906c-e14bb5375875@94.183.254.26:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=www.sciencedirect.com&type=tcp&host=&path=&headerType=none&alpn=&fp=firefox&pbk=cNWgfJHerzIEb0RXxncP8R9Ex8-FkALOtbhneEIHpR0&sid=a1b2c4d4a1b2c5d5&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0807伊朗 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@98.89.48.191:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=0&fragment=,100-200,10-60&os=#0807美国 
vless://5dc56757-458e-4df2-9e71-2a14ce47e8af@ddc-akn.astralweb.tech:443?flow=&encryption=none&security=tls&sni=ddc-akn.astralweb.tech&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0807德国 
vless://5dc56757-458e-4df2-9e71-2a14ce47e8af@ddc-chr.astralweb.tech:443?flow=&encryption=none&security=tls&sni=ddc-chr.astralweb.tech&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0807荷兰 
hysteria2://71cada65-d23e-418c-88e4-a06188d14689@de-two.quiet-rogue.site:443?insecure=0&sni=de-two.quiet-rogue.site&alpn=&fp=&mport=&os=#0807美国 
vless://f692629b-3557-488a-9c9b-60775331e423@eeg1.fi1-cosmostechnology.ru:443?flow=&encryption=none&security=reality&sni=fi1-cosmostechnology.ru&type=grpc&host=&serviceName=fi1cosmos&mode=gun&alpn=&fp=firefox&pbk=f3Mwf_vaM2TDw1X8HZORkYPLY0-DE5smNYgHuhrQLTA&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0807爱尔兰 
vless://44ae52b9-76fc-444d-8e43-186b4384b80a@free-amsterdam-node-1.cloudwidecdn.com:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=www.apple.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=PryGoq51ilG0eLUPl9i0xCvmk1xpwkyFSr_tG4GNLlU&sid=1d86d17709852910&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0807加拿大 
vless://f04c31f7-cfab-4824-d167-4137d836ea82@i3.cloud--vpn.site:443?flow=&encryption=none&security=tls&sni=ssl.fastly.com&type=ws&host=c12.com&path=/&headerType=none&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0807芬兰 
anytls://f93d0a97-c3a8-47af-b2be-ea4904c9918b@jjz.jjznodenode.top:17960?insecure=0&sni=hk.jjznodenode.top&alpn=&fp=&os=#0807希腊 
anytls://f93d0a97-c3a8-47af-b2be-ea4904c9918b@jjz.jjznodenode.top:17964?insecure=0&sni=jjz.jjznodenode.top&alpn=&fp=&os=#0807台湾 
anytls://f93d0a97-c3a8-47af-b2be-ea4904c9918b@jjz.jjznodenode.top:17968?insecure=0&sni=jjz.jjznodenode.top&alpn=&fp=&os=#0807日本 
hysteria2://16ab4d4a-fd81-4535-9b7b-346677226ce8@jp.cryptoofarm.com:443?insecure=0&sni=jp.cryptoofarm.com&alpn=&fp=&mport=&os=#0807立陶宛 
vless://f692629b-3557-488a-9c9b-60775331e423@lt3.fi1-cosmostechnology.ru:443?flow=&encryption=none&security=reality&sni=fi1-cosmostechnology.ru&type=grpc&host=&serviceName=fi1cosmos&mode=gun&alpn=&fp=firefox&pbk=f3Mwf_vaM2TDw1X8HZORkYPLY0-DE5smNYgHuhrQLTA&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0807英国 
hysteria2://22j0d00lev7mq0yv@musicclips.videolinks.ru:8443?insecure=0&sni=musicclips.videolinks.ru&alpn=&fp=&obfs=salamander&obfs-password=8zzng75tz4tf82pj&mport=&os=#0807英国 
vless://5dc56757-458e-4df2-9e71-2a14ce47e8af@nl2-akn.astralweb.tech:443?flow=&encryption=none&security=tls&sni=nl2-akn.astralweb.tech&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0807土耳其 
vless://8c7ac0ea-b1e4-4c20-bc16-1437559f3ac4@sa-84018978331c4eaf.sr-37f423695609b2ef.r.vpvpn.club:443?flow=&encryption=none&security=reality&sni=obrienteamnissan.com&type=xhttp&host=&path=/&mode=auto&alpn=&fp=qq&pbk=XBBVeMURFu7jmYJ9MZwjEWgfQlGTnRs0B5So5Fy7jWs&sid=c1cdebeccbb470ae&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=%7B%22xPaddingBytes%22%3A%22100-1000%22%2C%22scMaxEachPostBytes%22%3A1000000%2C%22scMinPostsIntervalMs%22%3A30%7D&os=#0807美国 
vless://f692629b-3557-488a-9c9b-60775331e423@sk.fi1-cosmostechnology.ru:443?flow=&encryption=none&security=reality&sni=fi1-cosmostechnology.ru&type=grpc&host=&serviceName=fi1cosmos&mode=gun&alpn=&fp=firefox&pbk=f3Mwf_vaM2TDw1X8HZORkYPLY0-DE5smNYgHuhrQLTA&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0807英国 
vless://28d0edc6-93c9-4465-bac9-720274d8b8c4@status.netraidly.ru:40443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=deepl.com&type=tcp&host=&path=&headerType=none&alpn=&fp=qq&pbk=WRveYv8IuUyvai4jgnQ6nWCL971-wKboe8evES5arlg&sid=69d4&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&os=#0807俄罗斯 
hysteria2://NWsm6X9QXr6XTYPuHMUoSP5A3MDl@37.114.49.36:9215?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=BpKuSp19LesWJUOxeeKM8W0E2&mport=&os=#0807德国 
hysteria2://HNYv2mkTkzYdfkQwvyUq7TWwqs70qSvjMM5igQrA@37.114.49.36:42888?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=wFMLKhPkEJ9Ou1wKtctCjLGy8EQmyXOj7D&mport=&os=#0807德国 
hysteria2://Wt0v7GgHfBXz6z8GkxsC0GU@37.114.49.36:29823?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=qT0P1KvFyto0l9TZR7BVcCAkCvFxMtXmGD&mport=&os=#0807德国 
hysteria2://zuMj7LyV22MlI9Z94kZdbEQl25xz2kuyX3VRZYuY@37.114.49.36:39064?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=lTGEW60MkAKoyBePQuS&mport=&os=#0807德国 
hysteria2://7MHrmjuUnD3dZ7z3yAs74tPim@37.114.49.36:58851?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=i29qoLSwI4tsenFzcx2DCmuFhW7jtrfpWbiI2T&mport=&os=#0807德国 
hysteria2://uuVdlwXuekE53kjXi8okwAJR@37.114.49.36:3640?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=XRd5FbQSqvaU7PSXuD7Qt4aazlK5pa17v1EgjI&mport=&os=#0807德国 
hysteria2://CXpaE7eWLVgX5PVFzq9@37.114.49.36:13114?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=fIgGAJGVQrzijpckiaUdM4F9FmIiPrEmTUvAP0oa&mport=&os=#0807德国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@xpedestriannfydogwood.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=xpedestriannfydogwood.oceanof.xyz&type=xhttp&host=xpedestriannfydogwood.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0807美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@pzerohourjineligible.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=pzerohourjineligible.oceanof.xyz&type=xhttp&host=pzerohourjineligible.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0807美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@fwecamorraeedition.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=fwecamorraeedition.oceanof.xyz&type=xhttp&host=fwecamorraeedition.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0807美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@sibookbinderdviremia.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=sibookbinderdviremia.oceanof.xyz&type=xhttp&host=sibookbinderdviremia.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0807美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@cacetamidernthydrofoil.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=cacetamidernthydrofoil.oceanof.xyz&type=xhttp&host=cacetamidernthydrofoil.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0807美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@slthyrseothiotepa.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=slthyrseothiotepa.oceanof.xyz&type=xhttp&host=slthyrseothiotepa.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0807美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@nfrontfjblueelder.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=nfrontfjblueelder.oceanof.xyz&type=xhttp&host=nfrontfjblueelder.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0807美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@lnewdealerqccup.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=lnewdealerqccup.oceanof.xyz&type=xhttp&host=lnewdealerqccup.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0807美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@qaffluentedfschoolbag.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=qaffluentedfschoolbag.oceanof.xyz&type=xhttp&host=qaffluentedfschoolbag.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0807美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@kpsalmistfanergy.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=kpsalmistfanergy.oceanof.xyz&type=xhttp&host=kpsalmistfanergy.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0807美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@tutinkindpaythrillful.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=tutinkindpaythrillful.oceanof.xyz&type=xhttp&host=tutinkindpaythrillful.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0807美国 
vless://0aaccaf6-8535-4b73-8039-a8c1a21abbbb@junaidedastavein.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=junaidedastavein.oceanof.xyz&type=xhttp&host=junaidedastavein.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=76b27b80a58027dc3cf1da68dac17010ed93997d0b603e2fadbe85012493b5a7&extra=&os=#0807美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.24.205.235:443?flow=&encryption=none&security=tls&sni=cdu.34892.qzz.io&type=xhttp&host=cdu.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0807德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.27.104.179:443?flow=&encryption=none&security=tls&sni=cdu.34892.qzz.io&type=xhttp&host=cdu.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0807德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@103.21.244.164:443?flow=&encryption=none&security=tls&sni=cdu.34892.qzz.io&type=xhttp&host=cdu.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0807德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.17.107.191:443?flow=&encryption=none&security=tls&sni=cdu.34892.qzz.io&type=xhttp&host=cdu.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0807德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.16.139.79:443?flow=&encryption=none&security=tls&sni=cdu.34892.qzz.io&type=xhttp&host=cdu.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0807德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.19.135.80:443?flow=&encryption=none&security=tls&sni=cdu.34892.qzz.io&type=xhttp&host=cdu.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0807德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@162.159.130.238:443?flow=&encryption=none&security=tls&sni=cdu.34892.qzz.io&type=xhttp&host=cdu.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0807德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@190.93.244.167:443?flow=&encryption=none&security=tls&sni=cdu.34892.qzz.io&type=xhttp&host=cdu.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0807德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.23.98.214:443?flow=&encryption=none&security=tls&sni=cdu.34892.qzz.io&type=xhttp&host=cdu.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0807德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@190.93.246.240:443?flow=&encryption=none&security=tls&sni=cdu.34892.qzz.io&type=xhttp&host=cdu.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0807德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@103.21.244.173:443?flow=&encryption=none&security=tls&sni=cdu.34892.qzz.io&type=xhttp&host=cdu.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&pcs=&extra=&os=#0807德国 
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
