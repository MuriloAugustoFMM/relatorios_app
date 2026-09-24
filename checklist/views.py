from pathlib import Path
import base64

from django.conf import settings
from django.contrib import messages
from django.core.files.base import ContentFile
from django.db.models import Q
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from weasyprint import HTML, default_url_fetcher

from core.models import Maquina
from .forms import ChecklistForm, FotoUploadForm, ItemChecklistForm
from .models import Checklist, Foto

_LOGO_PATH = Path(settings.BASE_DIR) / "assets" / "logo.webp"


def _logo_base64():
    """Lê a logo da empresa (assets/logo.webp) e devolve como base64, pra embutir direto no PDF/preview."""
    try:
        return base64.b64encode(_LOGO_PATH.read_bytes()).decode("ascii")
    except FileNotFoundError:
        return ""


def _fetcher_interno(url, *args, **kwargs):
    """
    O WeasyPrint roda DENTRO do container 'web' e precisa buscar as imagens
    das fotos para montar o PDF.

    Com storage local: em vez de fazer uma requisição HTTP da aplicação pra
    ela mesma (o que trava numa VPS pequena — ocupa 2 workers do Gunicorn ao
    mesmo tempo bem na hora que o WeasyPrint já está pesando na RAM), lemos o
    arquivo DIRETO DO DISCO. Mais rápido e não disputa memória/worker com a
    própria geração do PDF.

    Com MinIO (S3): as URLs salvas no banco apontam para o endpoint PÚBLICO
    do MinIO (ex: localhost:9000/bucket), que só existe do ponto de vista do
    navegador do usuário — de dentro do container, o MinIO só é alcançável
    pelo nome do serviço docker ("minio:9000"). Por isso, trocamos só o HOST
    público pelo host interno, preservando o resto do caminho.
    """
    if settings.MEDIA_BACKEND == "local":
        marcador = settings.MEDIA_URL  # "/media/"
        posicao = url.find(marcador)
        if posicao != -1:
            caminho_relativo = url[posicao + len(marcador):]
            caminho_arquivo = Path(settings.MEDIA_ROOT) / caminho_relativo
            return default_url_fetcher(caminho_arquivo.resolve().as_uri())
        return default_url_fetcher(url, *args, **kwargs)

    if settings.MEDIA_BACKEND == "s3":
        publico_host = settings.AWS_S3_CUSTOM_DOMAIN.split("/")[0]  # ex: "localhost:9000"
        interno_host = settings.AWS_S3_ENDPOINT_URL.replace("http://", "").replace("https://", "")  # ex: "minio:9000"
        if publico_host and publico_host in url:
            url = url.replace(publico_host, interno_host).replace("https://", "http://")
    return default_url_fetcher(url, *args, **kwargs)


def gerar_pdf_checklist(request, pk):
    """
    Gera (ou regenera) o PDF de um checklist a partir do template HTML,
    salva o resultado no storage configurado (campo pdf_gerado) e devolve o arquivo.
    """
    checklist = get_object_or_404(Checklist, pk=pk)

    html_string = render_to_string(
        "checklist/relatorio_pdf.html", {"checklist": checklist, "logo_base64": _logo_base64()}
    )
    # base_url é o que permite ao WeasyPrint resolver URLs relativas de mídia
    # (ex: "/media/fotos/x.jpg", usado quando MEDIA_BACKEND=local) em endereços
    # que ele consegue buscar. Usamos 127.0.0.1 (loopback) em vez do host público
    # (request.build_absolute_uri) de propósito: muitos provedores de nuvem não
    # suportam o servidor se conectar no próprio IP público de dentro pra fora
    # ("NAT hairpinning"), o que travava a geração do PDF esperando uma resposta
    # que nunca chegava. Loopback sempre funciona, porque nunca sai do container.
    # Com MinIO (S3) as URLs já vêm absolutas, então isso não muda nada nesse caso.
    pdf_bytes = HTML(
        string=html_string, base_url="http://127.0.0.1:8000/", url_fetcher=_fetcher_interno
    ).write_pdf()

    # Salva/atualiza o PDF no storage para consulta futura sem reprocessar
    nome_arquivo = f"{checklist.titulo}.pdf"
    checklist.pdf_gerado.save(nome_arquivo, ContentFile(pdf_bytes), save=True)


    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{nome_arquivo}"'
    return response


def visualizar_checklist(request, pk):
    """Preview em HTML do relatório (útil pra conferir antes de gerar o PDF)."""
    checklist = get_object_or_404(Checklist, pk=pk)
    return render(
        request, "checklist/relatorio_pdf.html", {"checklist": checklist, "logo_base64": _logo_base64()}
    )


def novo_checklist(request):
    """
    Formulário enxuto pro usuário comum: só tipo, máquina (já cadastrada),
    responsável, data e observações. Cliente e título são preenchidos
    sozinhos pelo model.
    """
    if request.method == "POST":
        form = ChecklistForm(request.POST)
        if form.is_valid():
            checklist = form.save()
            messages.success(request, "Checklist criado. Agora adicione as fotos (e itens, se for o caso).")
            return redirect("checklist:detalhe", pk=checklist.pk)
    else:
        form = ChecklistForm()
    return render(request, "checklist/novo.html", {"form": form})


def detalhe_checklist(request, pk):
    """
    Página onde o usuário comum completa o checklist: adiciona itens
    (só para CHECKLIST_MAQUINA) e sobe fotos. A partir daqui ele também
    consegue gerar o PDF quando terminar.
    """
    checklist = get_object_or_404(Checklist, pk=pk)
    item_form = ItemChecklistForm()
    foto_form = FotoUploadForm(checklist=checklist)

    if request.method == "POST":
        if "adicionar_item" in request.POST and checklist.usa_itens_estruturados:
            item_form = ItemChecklistForm(request.POST)
            if item_form.is_valid():
                item = item_form.save(commit=False)
                item.checklist = checklist
                item.ordem = checklist.itens.count()
                item.save()
                messages.success(request, "Item adicionado.")
                return redirect("checklist:detalhe", pk=pk)

        elif "adicionar_fotos" in request.POST:
            foto_form = FotoUploadForm(request.POST, request.FILES, checklist=checklist)
            if foto_form.is_valid():
                item = foto_form.cleaned_data.get("item") if checklist.usa_itens_estruturados else None
                legenda = foto_form.cleaned_data.get("legenda")
                imagens = foto_form.cleaned_data.get("imagens") or []
                proxima_ordem = checklist.fotos.count()
                for i, imagem in enumerate(imagens):
                    Foto.objects.create(
                        checklist=checklist, item=item, imagem=imagem, legenda=legenda, ordem=proxima_ordem + i
                    )
                if imagens:
                    messages.success(request, f"{len(imagens)} foto(s) adicionada(s).")
                return redirect("checklist:detalhe", pk=pk)

        elif "salvar_ordem" in request.POST:
            ids_str = request.POST.get("ordem_ids", "")
            ids = [int(i) for i in ids_str.split(",") if i.strip().isdigit()]
            for indice, foto_id in enumerate(ids):
                Foto.objects.filter(pk=foto_id, checklist=checklist).update(ordem=indice)
            messages.success(request, "Ordem das fotos atualizada.")
            return redirect("checklist:detalhe", pk=pk)

    return render(
        request,
        "checklist/detalhe.html",
        {"checklist": checklist, "item_form": item_form, "foto_form": foto_form},
    )


def buscar_checklists(request):
    """
    Busca de checklists já cadastrados — por título, identificador da
    máquina ou nome do cliente. É aqui que o usuário 'pesquisa e encontra'
    o que já foi registrado, em vez de digitar tudo de novo.
    """
    query = request.GET.get("q", "").strip()
    resultados = Checklist.objects.select_related("maquina", "cliente").order_by("-data", "-criado_em")
    if query:
        resultados = resultados.filter(
            Q(titulo__icontains=query)
            | Q(maquina__identificador__icontains=query)
            | Q(maquina__descricao__icontains=query)
            | Q(cliente__nome__icontains=query)
        )
    return render(request, "checklist/buscar.html", {"resultados": resultados[:50], "query": query})


def buscar_maquinas(request):
    """
    Endpoint JSON usado pelo campo de busca (digitado) de máquina no
    formulário de novo checklist — procura por identificador OU descrição.
    """
    query = request.GET.get("q", "").strip()
    maquinas = Maquina.objects.filter(ativo=True)
    if query:
        maquinas = maquinas.filter(Q(identificador__icontains=query) | Q(descricao__icontains=query))
    resultados = [{"id": m.pk, "texto": str(m)} for m in maquinas.order_by("descricao")[:15]]
    return JsonResponse({"resultados": resultados})