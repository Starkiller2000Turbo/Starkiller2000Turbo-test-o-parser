from django.contrib import admin
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view

schema_view = get_schema_view(
    openapi.Info(
        title='Ozon parser API',
        default_version='v1',
        description='Ozon API Documentation',
        contact=openapi.Contact(email='maksim_ermoshin@mail.com'),
    ),
    public=True,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('api.urls')),
    re_path(
        r'^swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=0),
        name='schema-json',
    ),
    re_path(
        r'^swagger/$',
        schema_view.with_ui('swagger', cache_timeout=0),
        name='schema-swagger-ui',
    ),
    re_path(
        r'^redoc/$',
        schema_view.with_ui('redoc', cache_timeout=0),
        name='schema-redoc',
    ),
]
