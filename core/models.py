from django.db import models


class Cliente(models.Model):
    nome = models.CharField(max_length=255)
    cnpj_cpf = models.CharField(max_length=20, blank=True, verbose_name="CNPJ/CPF")
    endereco = models.CharField(max_length=255, blank=True)
    contato = models.CharField(max_length=255, blank=True, help_text="Nome e telefone/e-mail do contato principal")
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Maquina(models.Model):
    """
    Representa um equipamento/veículo que passa pelos checklists e relatórios
    fotográficos (remessa, devolução, checklist de máquina).
    """

    identificador = models.CharField(
        max_length=100,
        unique=True,
        help_text="Placa, número de série, patrimônio ou outro código único da máquina",
    )
    descricao = models.CharField(max_length=255, help_text="Ex: Empilhadeira Toyota 2.5t")
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Máquina"
        verbose_name_plural = "Máquinas"
        ordering = ["identificador"]

    def __str__(self):
        return f"{self.identificador} — {self.descricao}"