"""Tests for auth endpoints."""

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class RegisterViewTest(APITestCase):
    """Tests for POST /api/auth/register/."""

    url = reverse("register")

    def test_register_success(self) -> None:
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "securepass123",
            "password_confirm": "securepass123",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)
        self.assertIn("tokens", response.data)
        self.assertEqual(response.data["user"]["username"], "newuser")
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_register_duplicate_email(self) -> None:
        User.objects.create_user(username="existing", email="dup@example.com", password="pass1234")
        data = {
            "username": "another",
            "email": "DUP@example.com",
            "password": "securepass123",
            "password_confirm": "securepass123",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_mismatch(self) -> None:
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "password1",
            "password_confirm": "password2",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginViewTest(APITestCase):
    """Tests for POST /api/auth/login/."""

    url = reverse("login")

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            username="loginuser", email="login@example.com", password="testpass123"
        )

    def test_login_valid(self) -> None:
        response = self.client.post(
            self.url, {"username": "loginuser", "password": "testpass123"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_invalid(self) -> None:
        response = self.client.post(
            self.url, {"username": "loginuser", "password": "wrong"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TokenRefreshTest(APITestCase):
    """Tests for POST /api/auth/refresh/."""

    def test_token_refresh(self) -> None:
        User.objects.create_user(username="refreshuser", password="testpass123")
        login_response = self.client.post(
            reverse("login"),
            {"username": "refreshuser", "password": "testpass123"},
            format="json",
        )
        refresh_token = login_response.data["refresh"]

        response = self.client.post(
            reverse("token_refresh"), {"refresh": refresh_token}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
