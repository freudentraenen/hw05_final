from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from http import HTTPStatus

from ..models import Post, Group, User


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(URLTests.user)
        cls.group = Group.objects.create(
            title='test group',
            slug='test-slug',
            description='test description'
        )
        cls.post = Post.objects.create(
            id=12,
            text='test text',
            group=cls.group,
            author=cls.user
        )

    def test_login_unrequired_pages(self):
        cache.clear()
        response_index = reverse('posts:index')
        response_group = reverse(
            'posts:group_list',
            kwargs={'slug': 'test-slug'}
        )
        response_profile = reverse(
            'posts:profile',
            kwargs={'username': 'TestUser'}
        )
        response_post_detail = reverse(
            'posts:post_detail',
            kwargs={'post_id': 12}
        )
        urls_response_codes = {
            response_index: HTTPStatus.OK,
            response_group: HTTPStatus.OK,
            response_profile: HTTPStatus.OK,
            response_post_detail: HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND
        }
        urls_templates = {
            response_index: 'posts/index.html',
            response_group: 'posts/group_list.html',
            response_profile: 'posts/profile.html',
            response_post_detail: 'posts/post_detail.html',
        }
        for url, response_code in urls_response_codes.items():
            with self.subTest():
                response = URLTests.guest_client.get(url)
                self.assertEqual(response.status_code, response_code)
        for url, template in urls_templates.items():
            with self.subTest():
                response = URLTests.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_login_required_pages(self):
        response_post_edit = reverse(
            'posts:post_edit',
            kwargs={'post_id': 12}
        )
        response_post_create = reverse('posts:post_create')
        url_response_codes = {
            response_post_edit: HTTPStatus.OK,
            response_post_create: HTTPStatus.OK
        }
        url_templates = {
            response_post_edit: 'posts/post_create.html',
            response_post_create: 'posts/post_create.html',
        }
        for url, response_code in url_response_codes.items():
            with self.subTest():
                response = URLTests.authorized_client.get(url)
                self.assertEqual(response.status_code, response_code)
        for url, template in url_templates.items():
            with self.subTest():
                response = URLTests.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_post_edit_redirect(self):
        response = URLTests.guest_client.get(
            reverse('posts:post_edit', kwargs={'post_id': 12}),
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', kwargs={'post_id': 12})
        )

    def test_add_comment_login_required(self):
        response_authorized = self.authorized_client.post(reverse(
            'posts:add_comment',
            kwargs={'post_id': 12}
        ))
        response_unauthorized = self.guest_client.post(reverse(
            'posts:add_comment',
            kwargs={'post_id': 12},
        ), follow=True)
        redirect_authorized = reverse(
            'posts:post_detail',
            kwargs={'post_id': 12},
        )
        redirect_unauthorized = '/auth/login/?next=/posts/12/comment/'
        self.assertRedirects(response_authorized, redirect_authorized)
        self.assertRedirects(response_unauthorized, redirect_unauthorized)