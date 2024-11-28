import re

from .abstract import ConfTree

__all__ = (
    "AristaCT",
    "CiscoCT",
    "HuaweiCT",
)


class AristaCT(ConfTree):
    spaces = "   "
    undo = "no"
    section_exit = "exit"
    section_separator = "!"
    sections_require_exit = [
        r"route-map \S+ (?:deny|permit) \d+",
    ]
    sections_without_exit = []
    junk_lines = [
        r"\s*!.*",
        r"end",
    ]
    mask_patterns = [
        r".*(?:password|secret)(?: sha512)? (\S+)",
        r".*(?:key|md5)(?: 7)? (\S+)",
    ]


class CiscoCT(ConfTree):
    spaces = " "
    undo = "no"
    section_exit = "exit"
    section_separator = "!"
    sections_require_exit = [
        r"route-map \S+ (?:deny|permit) \d+",
    ]
    sections_without_exit = [
        r"crypto pki certificate chain \S+ / certificate(?: ca| self-signed)? \S+",
    ]
    junk_lines = [
        r"\s*!.*",
        r"Building configuration...",
        r"Current configuration : \d+ bytes",
        r"version \S+",
        r"\s*exit-address-family",
        r"end",
    ]
    mask_patterns = [
        r".*secret 9 (\S+)",
    ]
    new_line_mask = "<<br>>"

    @classmethod
    def _mask_banners(cls, config: str) -> str:
        banners = []
        for section in re.finditer(
            r"banner (?P<type>(?:motd|login|exec)) (?P<sep>\S+)(?P<body>.*?)(?P=sep)\n",
            config,
            re.DOTALL,
        ):
            banners.append(section.group("body"))
        for banner in banners:
            config = config.replace(banner, banner.replace("\n", cls.new_line_mask))
        return config

    @classmethod
    def _mask_certificates(cls, config: str) -> str:
        certificates = []
        for cert in re.finditer(
            r"(?<=\s)certificate(?: ca| self-signed)? \S+\n(?P<body>.*?\s+quit)(?=\n)",
            config,
            re.DOTALL,
        ):
            certificates.append(cert.group("body"))
        for certificate in certificates:
            config = config.replace(certificate, certificate.replace("\n", cls.new_line_mask))
        return config

    @classmethod
    def pre_run(cls, config: str) -> str:
        config = cls._mask_banners(config)
        config = cls._mask_certificates(config)
        return config

    def post_run(self) -> None:
        for node in self.children.values():
            if node.line.startswith(("banner motd", "banner exec", "banner login")):
                node.line = node.line.replace(self.new_line_mask, "\n")
            elif node.line.startswith("crypto pki certificate chain"):
                for certificates in node.children.values():
                    for cert_body in certificates.children.values():
                        cert_body.line = cert_body.line.replace(self.new_line_mask, "\n")
                    certificates.rebuild()
        self.rebuild()


class HuaweiCT(ConfTree):
    spaces = " "
    undo = "undo"
    section_exit = "quit"
    section_separator = "#"
    sections_require_exit = [
        r"route-policy \S+ (?:deny|permit) node \d+",
        r"aaa / authentication-scheme \S+",
        r"aaa / authorization-scheme \S+",
        r"aaa / accounting-scheme \S+",
        r"aaa / domain \S+",
    ]
    sections_without_exit = [
        r"xpl \S+ .*",
    ]
    junk_lines = [
        r"\s*#.*",
        r"!.*",
        r"return",
    ]
    mask_patterns = [
        r".*(?:auth-code|(?:pre-)?shared-key|password|md5|key|authentication|read) cipher (\S+)(?: \S+)*",
        r".*password irreversible-cipher (\S+)",
        r".*pass-phrase (\S+) aes",
    ]

    @classmethod
    def _remove_spaces(cls, config: str) -> str:
        # у huawei в некоторых устройствах/версиях некоторые глобальные команды
        # выглядят так, как будто они находятся внутри секции, это ломает парсинг.
        # например пробел(ы) перед ntp-service, хотя это глобальный конфиг
        # #
        #  ntp-service server disable
        #  ntp-service source-interface LoopBack0
        #  ntp-service unicast-server 1.2.3.4
        # #
        # или пробел перед http
        # #
        #  http timeout 60
        #  http secure-server ssl-policy default_policy
        #  http server enable
        # #
        # поэтому удаляем пробел из конфигурации перед анализом
        #! то, что встретилось, возможно есть еще какие-то случаи

        return re.sub(
            pattern=r"""\n\s+(
                ntp-service\s
                |np\scapwap-reassembly\s
                |set\snp\srss\s
                |clock\stimezone\s
                |http\stimeout\s
                |http\sserver\s
                |http\ssecure-server\s
                |defence\sengine\s
                |sysname\s
                |header\sshell\sinformation\s
                |snmp-agent\s?
                |info-center\s
                )""",
            repl=r"\n\g<1>",
            string=config,
            flags=re.VERBOSE,
        )

    @classmethod
    def pre_run(cls, config: str) -> str:
        config = cls._remove_spaces(config)
        return config
