import pytest
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """REST API client fixture."""
    return APIClient()

@pytest.mark.django_db
def test_api_root_accessibility(api_client):
    """Проверяем, что корневой API-эндпоинт доступен."""
    response = api_client.get('/api/')
    assert response.status_code == status.HTTP_200_OK
