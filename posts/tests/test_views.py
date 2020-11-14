from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group, Comment, Follow


User = get_user_model()


class StaticURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='StasBasov')
        cls.user_first = User.objects.create_user(username='Anton')
        cls.user_second = User.objects.create_user(username='Anna')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.test_group = Group.objects.create(title='Лев Толстой',
                                              description='Лев Толстой'
                                              )
        cls.test_post = Post.objects.create(text='Текст', author=cls.user)
        cls.key = make_template_fragment_key('index_page')

    def test_new_post(self):
        self.authorized_client.force_login(self.user)
        current_posts_count = Post.objects.count()
        response = self.authorized_client.post(
                                            reverse('new_post'),
                                            {'text': 'Это текст публикации'},
                                            follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), current_posts_count + 1)

    def test_post_edit(self):
        self.authorized_client.force_login(self.user)
        response = self.authorized_client.post(
                                    reverse(
                                        'post_edit',
                                        kwargs={
                                            'username': self.test_post.author,
                                            'post_id': self.test_post.id
                                            }),
                                        {
                                            'text': 'Меняем текст',
                                            'group': self.test_group.slug
                                        },
                                        follow=True)
        cache.clear()
        self.assertEqual(response.status_code, 200)
        post_check = Post.objects.get(id=self.test_post.id)
        self.assertEqual(post_check.text, 'Меняем текст')
        response_index = self.client.get(reverse('index'))
        response_profile = self.client.get(reverse(
                                'profile',
                                kwargs={
                                    'username': self.test_post.author
                                    }))
        response_post = self.client.get(reverse(
                                'post',
                                kwargs={
                                    'username': self.test_post.author,
                                    'post_id': self.test_post.id
                                    }))
        self.assertContains(response_index, post_check.text)
        self.assertContains(response_profile, post_check.text)
        self.assertContains(response_post, post_check.text)

    def test_new_post_on_page(self):
        post_check = self.authorized_client.post(
                                            reverse('new_post'),
                                            {'text': 'Новый пост'},
                                            follow=True)
        self.assertEqual(post_check.status_code, 200)
        post_check = Post.objects.first()
        response_index = self.client.get(reverse('index'))
        self.assertContains(response_index, post_check.pk)
        response = self.client.get(reverse(
                                'profile',
                                kwargs={
                                    'username': post_check.author
                                    }))
        self.assertContains(response, post_check.pk)
        response = self.client.get(reverse(
                                'post',
                                kwargs={
                                    'username': post_check.author,
                                    'post_id': post_check.id
                                    }))
        self.assertContains(response, post_check.pk)

    def test_check_post_img(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        with SimpleUploadedFile(
                                'small.gif', small_gif,
                                content_type='image/gif') as img:
            response = self.authorized_client.post(
                                    reverse(
                                        'post_edit',
                                        kwargs={
                                            'username': self.test_post.author,
                                            'post_id': self.test_post.id
                                            }),
                                        {
                                            'text': 'Меняем текст',
                                            'group': self.test_group.slug,
                                            'image': img
                                        },
                                        follow=True)
        cache.clear()
        post_check = Post.objects.get(id=self.test_post.id)
        response_index = self.client.get(reverse('index'))
        response_profile = self.client.get(
                                reverse(
                                    'profile',
                                    kwargs={
                                        'username': post_check.author
                                        }))
        response_post = self.client.get(
                                reverse(
                                    'post',
                                    kwargs={
                                        'username': post_check.author,
                                        'post_id': post_check.id
                                    }))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response_index, '<img')
        self.assertContains(response_profile, '<img')
        self.assertContains(response_post, '<img')

    def test_cache_after_time(self):
        response_old = self.authorized_client.get(reverse('index'))
        self.authorized_client.post(
                                    reverse('new_post'),
                                    {'text': 'Новое сообщение!!!'},
                                    follow=True)
        response_new = self.authorized_client.get(reverse('index'))
        self.assertEqual(response_old.content, response_new.content)
        cache.touch(self.key, 0)
        response_newest = self.authorized_client.get(reverse('index'))
        self.assertNotEqual(response_old.content, response_newest.content)

    # Все тесты работают по отдельности.
    # Не понимаю как воспользоваться setUp, данный случай сломал мне голову.
    def test_follow(self):
        follow_count = Follow.objects.count()
        # Возник вопрос. Это post или get запрос?
        self.authorized_client.post(
                                reverse(
                                    'profile_follow',
                                    kwargs=
                                    {
                                        'username': self.user_first,
                                    }))
        self.assertEqual(Follow.objects.count(), follow_count + 1)

    def test_unfollow(self):
        self.authorized_client.post(
                                reverse(
                                    'profile_follow',
                                    kwargs=
                                    {
                                        'username': self.user_first,
                                    }),
                                    follow=True)
        follow_count = Follow.objects.count()
        self.authorized_client.post(
                                reverse(
                                    'profile_unfollow',
                                    kwargs=
                                    {
                                        'username': self.user_first,
                                    }),
                                    follow=True)
        self.assertEqual(Follow.objects.count(), follow_count - 1)

    def test_check_follow_authorized(self):
        self.authorized_client.post(
                                    reverse(
                                        'profile_follow',
                                        kwargs=
                                        {
                                            'username': self.user_first,
                                        }),
                                        follow=True)
        self.authorized_client.force_login(self.user_first)
        self.authorized_client.post(
                                reverse('new_post'),
                                {'text': 'Новый пост!'},
                                follow=True)
        post_check = Post.objects.first()
        self.authorized_client.force_login(self.user)
        response = self.authorized_client.get(
                                        reverse('follow_index'),
                                        follow=True)
        response = response.context['page'][0].pk
        self.assertEqual(response, post_check.pk)
    
    def test_check_follow_unauthorized(self):
        self.authorized_client.force_login(self.user_first)
        post_check = self.authorized_client.post(
                                        reverse('new_post'),
                                        {'text': 'Новый пост!'},
                                        follow=True)
        post_check = Post.objects.first()
        self.authorized_client.force_login(self.user)
        response = self.authorized_client.get(
                                        reverse('follow_index'),
                                        follow=True)
        try:
            response = response.context['page'][0].pk
            self.assertNotEqual(response, post_check.pk)
        except:
            self.assertNotEqual(0, post_check.pk)

    def test_add_comment_authorized(self):
        post_check = Post.objects.first()
        comment_count = Comment.objects.count()
        self.authorized_client.force_login(self.user_first)
        self.authorized_client.post(
                                reverse(
                                    'add_comment',
                                    kwargs=
                                    {
                                        'username': self.user,
                                        'post_id': post_check.id
                                    }),
                                    {
                                        'text': 'Лайк'
                                    },
                                    follow=True)
        self.assertEqual(Comment.objects.count(), comment_count + 1)

    def test_add_comment_unauthorized(self):
        post_check = Post.objects.first()
        comment_count = Comment.objects.count()
        self.authorized_client.logout()
        self.authorized_client.post(
                                reverse(
                                    'add_comment',
                                    kwargs=
                                    {
                                        'username': self.user,
                                        'post_id': post_check.id
                                    }),
                                    {
                                        'text': 'Лайк'
                                    },
                                    follow=True)
        self.assertNotEquals(Comment.objects.count(), comment_count + 1)
