from __future__ import annotations

import datetime
import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import urlopen


DEFAULT_MODEL_HINT = "REU"


@dataclass
class HeaterCandidate:
    ip: str
    port: int
    modelo: str
    mac: str | None
    tela: str | None


def detect_local_network(prefix: int) -> ipaddress.IPv4Network:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        local_ip = sock.getsockname()[0]
    finally:
        sock.close()

    interface = ipaddress.IPv4Interface(f"{local_ip}/{prefix}")
    return interface.network


def http_get_text(ip: str, port: int, endpoint: str, timeout: float) -> str | None:
    base = f"http://{ip}:{port}/"
    url = urljoin(base, endpoint.lstrip("/"))
    try:
        with urlopen(url, timeout=timeout) as response:
            payload = response.read()
        return payload.decode("utf-8", errors="replace").strip()
    except (URLError, HTTPError, TimeoutError, OSError):
        return None


def looks_like_rinnai(modelo: str, model_hint: str) -> bool:
    text = modelo.strip().upper()
    if not text:
        return False

    if model_hint and model_hint.upper() in text:
        return True

    return "RINNAI" in text or "REU" in text


def probe_host(
    ip: str,
    ports: Iterable[int],
    timeout: float,
    model_hint: str,
) -> list[HeaterCandidate]:
    matches: list[HeaterCandidate] = []
    for port in ports:
        modelo = http_get_text(ip, port, "/read_modelo", timeout)
        if not modelo or not looks_like_rinnai(modelo, model_hint):
            continue

        mac = http_get_text(ip, port, "/connect", timeout)
        tela = http_get_text(ip, port, "/tela_", timeout)
        matches.append(
            HeaterCandidate(
                ip=ip,
                port=port,
                modelo=modelo,
                mac=mac,
                tela=tela,
            )
        )
    return matches


def scan_network(
    network: ipaddress.IPv4Network,
    ports: list[int],
    timeout: float,
    workers: int,
    model_hint: str,
) -> list[HeaterCandidate]:
    hosts = [str(host) for host in network.hosts()]
    results: list[HeaterCandidate] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(probe_host, ip, ports, timeout, model_hint): ip
            for ip in hosts
        }
        for future in as_completed(futures):
            matches = future.result()
            if matches:
                results.extend(matches)

    results.sort(key=lambda item: (ipaddress.ip_address(item.ip), item.port))
    return results


class HeaterStatus:
    def __init__(self):
        self.T = None
        self.on = None

    def parse(self, data: str):
        parts = data.split(",")
        self.status_code = int(parts[0])
        if len(parts) == 14:
            self.burning = parts[2] == "1"
            self.T = int(parts[7]) + 32
            self.firmware = datetime.datetime.strptime(parts[9], "%b %d %Y").date()
        else:
            self.ip = parts[16]
            self.T = int(parts[18]) + 32
            self.firmware = datetime.datetime.strptime(parts[22], "%b %d %Y").date()
            self.mac = parts[25]
            self.wifi_signal = int(parts[-3])
        return self


class Controller:
    def __init__(self):
        self.status_dict = {11: "Off", 41: "StandBy", 42: "Shower"}
        self.cidr_prefix = 24
        self.ports = {80}
        self.timeout = 1
        self.workers = 64
        self.model_hint = "REU"
        self.found = self.find()
        if not self.found:
            raise RuntimeError("Heater not found")
        self.found = self.found[0]

    def turnOnOff(self):
        return self.getParsed("/lig")

    def getModel(self):
        return self.getRequest("/read_modelo")

    def find(self):
        network = detect_local_network(self.cidr_prefix)
        matches = scan_network(
            network, self.ports, self.timeout, self.workers, self.model_hint
        )
        return [asdict(match) for match in matches]

    def getRequest(self, uri: str):
        return http_get_text(self.found["ip"], self.found["port"], uri, self.timeout)

    def getParsed(self, uri: str):
        response = self.getRequest(uri)
        if response is None:
            raise RuntimeError(f"Request failed for endpoint: {uri}")
        return HeaterStatus().parse(response)

    def getData(self, full: bool = False, raw: bool = False):
        return (self.getRequest if raw else self.getParsed)("/bus" if full else "/tela_")

    def getBurning(self):
        return self.getData().burning

    def getTemp(self):
        return self.getData().T

    def incTemp(self):
        return self.getParsed("/inc").T

    def decTemp(self):
        return self.getParsed("/dec").T

    def useHistory(self):
        hist = []
        payload = self.getRequest("/historico")
        if not payload:
            return hist
        for line in payload.split(";")[:-1]:
            data = line.split(",")
            hist.append(
                {
                    "time": datetime.time.fromisoformat(data[0]),
                    "temp": int(data[1]) + 32,
                    "vol": int(data[2]),
                    "gas": int(data[3]),
                    "timestamp": int(data[4]),
                }
            )
        return hist

    def errorHistory(self):
        hist = []
        payload = self.getRequest("/erros")
        if not payload:
            return hist
        for line in payload.split(";")[:-1]:
            data = line.split(",")
            hist.append({"code": int(data[0]), "timestamp": int(data[1])})
        return hist

    def lastError(self):
        return self.errorHistory()[0]["code"]

    def setTemp(self, new_t: int):
        t = self.getTemp()
        beg = t
        while t > new_t:
            t = self.decTemp()
        while t < new_t:
            t = self.incTemp()
        return beg, t
