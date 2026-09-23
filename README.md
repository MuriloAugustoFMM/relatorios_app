# Sistema de Relatórios Fotográficos e Checklist de Máquinas

Stack: Django + PostgreSQL + MinIO (storage S3-compatível) + WeasyPrint (PDF), tudo rodando em containers Docker na sua máquina.

## Estrutura

- `core/` — cadastros mestres: **Cliente** e **Máquina**
- `checklist/` — **Checklist** (remessa, devolução ou checklist de máquina), **ItemChecklist** (perguntas, só para checklist de máquina), **Foto** (soltas ou vinculadas a um item)
- `config/` — settings do Django, já configurado para Postgres + MinIO

## Subindo pela primeira vez

1. Copie o arquivo de variáveis de ambiente:
   ```bash
   cp .env.example .env
   ```
   (pode deixar os valores padrão pra rodar local; troque as senhas se quiser mais segurança)

2. Suba tudo:
   ```bash
   docker compose up --build
   ```
   Na primeira subida isso vai: criar o banco Postgres, subir o MinIO, criar o bucket automaticamente (`createbuckets`), rodar as migrations do Django e subir o servidor.

3. Crie um usuário admin (em outro terminal, com os containers já rodando):
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

4. Acesse:
   - **Admin do Django** (cadastrar clientes, máquinas, checklists, fotos): http://localhost:8000/admin/
   - **Console do MinIO** (ver os arquivos armazenados): http://localhost:9001/ — login com `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` do `.env`

## Gerando um PDF

Depois de cadastrar um Checklist (com máquina, fotos etc.) pelo admin, acesse:
```
http://localhost:8000/checklist/<ID_DO_CHECKLIST>/pdf/
```
Isso gera o PDF, salva uma cópia no MinIO (campo `pdf_gerado`) e devolve o arquivo pro navegador.

Para conferir antes o layout em HTML puro (sem gerar o PDF):
```
http://localhost:8000/checklist/<ID_DO_CHECKLIST>/preview/
```

## Próximos passos sugeridos

- [ ] Criar formulários próprios (fora do admin) para preenchimento por quem opera no campo, incluindo captura de foto pelo celular
- [ ] Transformar em PWA (manifest.json + service worker) para uso mobile
- [ ] Endpoint de listagem/dashboard dos checklists gerados
- [ ] DNS local (mDNS/Avahi ou dnsmasq) para acessar via nome amigável na rede da empresa, em vez de IP
