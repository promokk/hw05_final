from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group


User = get_user_model()


class StaticURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='StasBasov')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.unauthorized_client = Client()
        cls.test_group = Group.objects.create(title='Лев Толстой',
                                              slug='tolstoy',
                                              description='Лев Толстой'
                                              )
        cls.test_post = Post.objects.create(text='Текст', author=cls.user)

    def test_homepage(self):
        client = Client()
        response = client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_force_login(self):
        self.authorized_client.force_login(self.user)
        response = self.authorized_client.get('/new/')
        self.assertEqual(response.status_code, 200)

    def test_unauthorized_user_newpage(self):
        response = self.unauthorized_client.get('/new/')
        self.assertRedirects(
                            response,
                            '/auth/login/?next=/new/',
                            status_code=302, target_status_code=200)

    def test_profile(self):
        self.authorized_client.force_login(self.user)
        response = self.authorized_client.get('/StasBasov/')
        self.assertEqual(response.status_code, 200)


    def test_error_page(self):
        response = self.authorized_client.get('/error12345/')
        self.assertEqual(response.status_code, 404)
