import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core.models import Cliente, Maquina


class Command(BaseCommand):
    help = "Popula Clientes e Máquinas a partir dos arquivos dados/clientes.csv e dados/maquinas.csv"

    def add_arguments(self, parser):
        parser.add_argument(
            "--pasta",
            default="dados",
            help="Pasta onde estão os arquivos clientes.csv e maquinas.csv (padrão: dados/)",
        )

    def handle(self, *args, **options):
        pasta = Path(options["pasta"])
        caminho_clientes = pasta / "clientes.csv"
        caminho_maquinas = pasta / "maquinas.csv"

        if not caminho_clientes.exists() and not caminho_maquinas.exists():
            raise CommandError(
                f"Nenhum arquivo encontrado em '{pasta}/'. "
                f"Crie '{caminho_clientes}' e/ou '{caminho_maquinas}'."
            )

        total_clientes = 0
        if caminho_clientes.exists():
            with open(caminho_clientes, newline="", encoding="utf-8-sig") as f:
                for linha in csv.DictReader(f):
                    nome = (linha.get("nome") or "").strip()
                    if not nome:
                        continue
                    _, criado = Cliente.objects.get_or_create(
                        nome=nome,
                        defaults={
                            "cnpj_cpf": (linha.get("cnpj_cpf") or "").strip(),
                            "endereco": (linha.get("endereco") or "").strip(),
                            "contato": (linha.get("contato") or "").strip(),
                        },
                    )
                    if criado:
                        total_clientes += 1
            self.stdout.write(self.style.SUCCESS(f"{total_clientes} cliente(s) novo(s) criado(s)."))
        else:
            self.stdout.write(self.style.WARNING(f"'{caminho_clientes}' não encontrado — pulando clientes."))

        total_maquinas = 0
        if caminho_maquinas.exists():
            with open(caminho_maquinas, newline="", encoding="utf-8-sig") as f:
                for linha in csv.DictReader(f):
                    identificador = (linha.get("identificador") or "").strip()
                    if not identificador:
                        continue

                    _, criado = Maquina.objects.get_or_create(
                        identificador=identificador,
                        defaults={"descricao": (linha.get("descricao") or "").strip()},
                    )
                    if criado:
                        total_maquinas += 1
            self.stdout.write(self.style.SUCCESS(f"{total_maquinas} máquina(s) nova(s) criada(s)."))
        else:
            self.stdout.write(self.style.WARNING(f"'{caminho_maquinas}' não encontrado — pulando máquinas."))