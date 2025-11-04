from django.contrib import admin
from django.urls import path, include
from django.conf import settings # Para servir arquivos de media em dev
from django.conf.urls.static import static # Para servir arquivos de media em dev

urlpatterns = [
    path('admin/', admin.site.urls),
    # Incluímos as URLs do nosso app 'vendas'
    path('', include('vendas.urls')), 
]

# Configuração para servir arquivos de Mídia (uploads) durante o desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
