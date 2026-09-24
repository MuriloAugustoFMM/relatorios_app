import json

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Garante que o bucket do MinIO exista e tenha política de leitura pública "
        "(substitui o antigo serviço 'createbuckets' baseado na imagem mc, que ficou instável)."
    )

    def handle(self, *args, **options):
        if settings.MEDIA_BACKEND == "local":
            self.stdout.write("MEDIA_BACKEND=local — sem MinIO pra configurar, pulando.")
            return

        client = boto3.client(
            "s3",
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        bucket = settings.AWS_STORAGE_BUCKET_NAME

        try:
            client.head_bucket(Bucket=bucket)
            self.stdout.write(self.style.SUCCESS(f"Bucket '{bucket}' já existe."))
        except ClientError:
            client.create_bucket(Bucket=bucket)
            self.stdout.write(self.style.SUCCESS(f"Bucket '{bucket}' criado."))

        # Equivalente ao antigo "mc anonymous set download" — permite leitura
        # pública dos objetos (necessário pras fotos abrirem no navegador/PDF).
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket}/*"],
                }
            ],
        }
        client.put_bucket_policy(Bucket=bucket, Policy=json.dumps(policy))
        self.stdout.write(self.style.SUCCESS("Política de leitura pública aplicada ao bucket."))