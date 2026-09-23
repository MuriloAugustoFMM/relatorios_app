from django.db import models
from django.utils import timezone

from core.models import Cliente, Maquina


class TipoChecklist(models.TextChoices):
    REMESSA = "REMESSA", "Relatório Fotográfico de Remessa"
    DEVOLUCAO = "DEVOLUCAO", "Relatório Fotográfico de Devolução"
    CHECKLIST_MAQUINA = "CHECKLIST_MAQUINA", "Checklist de Máquina"


class Checklist(models.Model):
    """
    Registro principal de um relatório/checklist.

    - REMESSA / DEVOLUCAO: tipicamente usam fotos "soltas" (anexadas ao final,
      sem vínculo a uma pergunta específica) — ver Foto.item = None.
    - CHECKLIST_MAQUINA: usa ItemChecklist (pergunta/resposta), com fotos
      podendo estar vinculadas a um item específico.
    """

    tipo = models.CharField(max_length=30, choices=TipoChecklist.choices)
    titulo = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        help_text="Gerado automaticamente: TIPO + IDENTIFICADOR DA MÁQUINA + DATA",
    )
    maquina = models.ForeignKey(Maquina, on_delete=models.PROTECT, related_name="checklists")
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="checklists",
        null=True,
        blank=True,
        help_text="Cliente para o qual esta operação foi feita",
    )
    responsavel = models.CharField(max_length=255, help_text="Quem preencheu o relatório")
    medidor = models.CharField(
        max_length=100, blank=True, help_text="Leitura do horímetro/odômetro no momento do checklist"
    )
    referencia_sistema = models.CharField(
        max_length=100, blank=True, help_text="Código de referência no sistema/ERP, se houver"
    )
    data = models.DateField(default=timezone.now)
    observacoes_gerais = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    # Armazena o caminho do PDF já gerado (no MinIO), para não precisar
    # regenerar toda vez que alguém for só baixar o relatório.
    pdf_gerado = models.FileField(upload_to="pdfs/%Y/%m/", blank=True, null=True)

    class Meta:
        verbose_name = "Checklist"
        verbose_name_plural = "Checklists"
        ordering = ["-data", "-criado_em"]

    def __str__(self):
        return self.titulo or f"{self.get_tipo_display()} — {self.maquina_id}"

    def gerar_titulo(self):
        data_str = self.data.strftime("%Y%m%d")
        return f"{self.tipo}_{self.maquina.identificador}_{data_str}"

    def save(self, *args, **kwargs):
        if not self.titulo:
            self.titulo = self.gerar_titulo()
        super().save(*args, **kwargs)

    @property
    def usa_itens_estruturados(self):
        return self.tipo == TipoChecklist.CHECKLIST_MAQUINA


class ItemChecklist(models.Model):
    """
    Pergunta/item de verificação de um CHECKLIST_MAQUINA (ex: "Nível de óleo OK?").
    Não é usado pelos relatórios de REMESSA/DEVOLUCAO, que usam fotos soltas.
    """

    class Resultado(models.TextChoices):
        CONFORME = "CONFORME", "Conforme"
        NAO_CONFORME = "NAO_CONFORME", "Não conforme"
        NAO_APLICAVEL = "NAO_APLICAVEL", "Não aplicável"

    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name="itens")
    ordem = models.PositiveIntegerField(default=0)
    pergunta = models.CharField(max_length=255)
    resultado = models.CharField(max_length=20, choices=Resultado.choices, blank=True)
    observacao = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Item do Checklist"
        verbose_name_plural = "Itens do Checklist"
        ordering = ["ordem", "id"]

    def __str__(self):
        return self.pergunta


class Foto(models.Model):
    """
    Foto anexada a um checklist. Pode ser:
    - solta (item=None): caso dos relatórios de REMESSA/DEVOLUCAO
    - vinculada a um item (item=<ItemChecklist>): caso do CHECKLIST_MAQUINA
    O arquivo em si vai para o MinIO; aqui ficam só a referência e os metadados.
    """

    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name="fotos")
    item = models.ForeignKey(
        ItemChecklist, on_delete=models.CASCADE, related_name="fotos", null=True, blank=True
    )
    imagem = models.ImageField(upload_to="fotos/%Y/%m/%d/")
    legenda = models.CharField(max_length=255, blank=True)
    ordem = models.PositiveIntegerField(default=0, help_text="Define a posição da foto no PDF final")
    tirada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Foto"
        verbose_name_plural = "Fotos"
        ordering = ["ordem", "tirada_em"]

    def __str__(self):
        return f"Foto #{self.pk} — {self.checklist.titulo}"