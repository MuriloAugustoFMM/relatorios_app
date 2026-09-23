from django import forms

from core.models import Maquina
from .models import Checklist, ItemChecklist


class ChecklistForm(forms.ModelForm):
    """
    Formulário do usuário comum. 'titulo' NÃO aparece aqui de propósito —
    é preenchido sozinho pelo save() do model (Checklist.gerar_titulo).

    'maquina' é um campo oculto: quem preenche ele é o JS de busca no
    template (novo.html), a partir da seleção de um resultado já
    cadastrado. Se a máquina ainda não existir, o usuário preenche
    'nova_maquina_descricao' (obrigatório nesse caso) e, opcionalmente,
    'nova_maquina_identificador' — e a máquina é criada no save().
    """

    maquina = forms.ModelChoiceField(
        queryset=Maquina.objects.filter(ativo=True),
        required=False,
        widget=forms.HiddenInput(),
        label="Máquina",
    )
    nova_maquina_descricao = forms.CharField(
        required=False,
        max_length=255,
        label="Descrição do equipamento (se ainda não estiver cadastrado)",
    )
    nova_maquina_identificador = forms.CharField(
        required=False,
        max_length=100,
        label="Identificação — placa/patrimônio/série",
    )

    class Meta:
        model = Checklist
        fields = [
            "tipo", "maquina", "cliente", "responsavel",
            "medidor", "referencia_sistema", "data", "observacoes_gerais",
        ]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}),
            "observacoes_gerais": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()
        maquina = cleaned.get("maquina")
        nova_descricao = (cleaned.get("nova_maquina_descricao") or "").strip()
        novo_identificador = (cleaned.get("nova_maquina_identificador") or "").strip()

        if not maquina and not nova_descricao:
            raise forms.ValidationError(
                "Busque e selecione uma máquina já cadastrada, ou informe ao menos "
                "a descrição do equipamento para cadastrar uma nova."
            )

        if not maquina and (not nova_descricao or not novo_identificador):
            raise forms.ValidationError(
                "Para cadastrar uma nova máquina, informe a descrição E a identificação "
                "(placa/patrimônio/série) — os dois campos são obrigatórios."
            )

        # Não deixa "colar" num equipamento novo um identificador que já
        # pertence a outra máquina cadastrada — isso é sinal de que a máquina
        # já existe e deveria ter sido encontrada pela busca, não recriada.
        if not maquina and novo_identificador:
            existente = Maquina.objects.filter(identificador=novo_identificador).first()
            if existente:
                raise forms.ValidationError(
                    f"O identificador '{novo_identificador}' já pertence à máquina "
                    f"'{existente}' — busque por ele no campo de busca em vez de "
                    f"cadastrar um novo equipamento."
                )
        return cleaned

    def save(self, commit=True):
        if not self.cleaned_data.get("maquina"):
            maquina = Maquina.objects.create(
                descricao=self.cleaned_data["nova_maquina_descricao"].strip(),
                identificador=self.cleaned_data["nova_maquina_identificador"].strip(),
            )
            self.instance.maquina = maquina
        return super().save(commit=commit)


class ItemChecklistForm(forms.ModelForm):
    class Meta:
        model = ItemChecklist
        fields = ["pergunta", "resultado", "observacao"]


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultiFileField(forms.FileField):
    """Permite selecionar e enviar várias fotos de uma vez no mesmo campo."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultiFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(item, initial) for item in data]
        return single_file_clean(data, initial)


class FotoUploadForm(forms.Form):
    imagens = MultiFileField(required=False, label="Fotos")
    item = forms.ModelChoiceField(
        queryset=ItemChecklist.objects.none(),
        required=False,
        label="Vincular a um item do checklist (opcional)",
    )
    legenda = forms.CharField(required=False, max_length=255, label="Legenda (opcional, vale para todas as fotos enviadas agora)")

    def __init__(self, *args, checklist=None, **kwargs):
        super().__init__(*args, **kwargs)
        if checklist is not None:
            self.fields["item"].queryset = checklist.itens.all()
            if not checklist.usa_itens_estruturados:
                self.fields.pop("item")