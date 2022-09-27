from django.test import TestCase, Client
from django.urls import reverse
from django import forms
from django.core.cache import cache

from ..models import Post, Group, User, Comment, Follow


class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser1')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(ViewsTests.user)
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

    def setUp(self):
        self.user = User.objects.create_user(username='TestUser2')
        self.user2 = User.objects.create_user(username='TestUser3')
        self.user3 = User.objects.create_user(username='TestUser4')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user3)
        self.post = Post.objects.create(
            pk=13,
            text='pages contain this post',
            author=self.user,
            group=Group.objects.create(
                title='this group',
                description='this group contains this post',
                slug='this-slug'
            )
        )
        self.comment = Comment.objects.create(
            text='test comment',
            author=self.user,
            post=self.post,
        )

    def test_pages_use_correct_templates_guest(self):
        cache.clear()
        pages_templates = {
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}): 'posts/group_list.html',
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:profile',
                kwargs={'username': 'TestUser2'}): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': 12}): 'posts/post_detail.html',
        }
        for page, template in pages_templates.items():
            with self.subTest():
                response = self.guest_client.get(page)
                self.assertTemplateUsed(response, template)

    def test_pages_use_correct_templates_authorized(self):
        pages_templates = {
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': 13}
            ): 'posts/post_create.html',
        }
        for page, template in pages_templates.items():
            with self.subTest():
                response = self.authorized_client.get(page)
                self.assertTemplateUsed(response, template)

    def test_correct_context(self):
        response_group_list = self.guest_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'test-slug'}
        ))
        response_profile = self.guest_client.get(reverse(
            'posts:profile', kwargs={'username': 'TestUser1'}
        ))
        response_post_detail = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': 12}
        ))
        post = response_post_detail.context['post']
        current_user = response_post_detail.context['current_user']
        group = response_group_list.context['group']
        author = response_profile.context['author']
        values_expected_values_names = {
            group: ViewsTests.group,
            author: ViewsTests.user,
            post: ViewsTests.post,
            current_user: self.user,
        }
        for value, expected in values_expected_values_names.items():
            with self.subTest():
                self.assertEqual(value, expected)

    def test_forms_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_pages_contain_new_post(self):
        cache.clear()
        response_index = self.guest_client.get(reverse('posts:index'))
        response_group = self.guest_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.post.group.slug}
        ))
        response_profile = self.guest_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.user.username}
        ))
        responses = [
            response_index,
            response_group,
            response_profile,
        ]
        for response in responses:
            with self.subTest():
                self.assertIn(self.post, response.context['page_obj'])

    def another_group_doesnt_contain_new_post(self):
        response = self.guest_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': 'test=slug'}
        ))
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_post_detail_contains_new_comment(self):
        response = self.guest_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': 13},
        ))
        self.assertIn(self.comment, response.context['comments'])

    def test_cache_index_page(self):
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        content = response.content
        self.post.delete()
        response = self.guest_client.get(reverse('posts:index'))
        content2 = response.content
        self.assertEqual(content, content2)

    def test_auth_user_can_follow(self):
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username':self.user2.username}
        ))
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.user2
            ).exists()
        )
    
    def test_auth_user_can_unfollow(self):
        Follow.objects.create(
            user=self.user,
            author=self.user2
        )
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username':self.user2.username}
        ))
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.user2
            ).exists()
        )

    def test_followers_have_new_post(self):
        Follow.objects.create(
            user=self.user,
            author=self.user2
        )
        post = Post.objects.create(
            text='very cool',
            author=self.user2
        )
        response = self.authorized_client.get(reverse('posts:followed'))
        self.assertIn(post, response.context['post_list'])

    def test_not_followers_dont_have_new_post(self):
        Follow.objects.create(
            user=self.user,
            author=self.user2
        )
        post = Post.objects.create(
            text='very cool',
            author=self.user2
        )
        response = self.authorized_client2.get(reverse('posts:followed'))
        self.assertNotIn(post, response.context['post_list'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='test group',
            slug='test-slug',
            description='test description'
        )
        for i in range(1, 14):
            Post.objects.create(
                id=i,
                text=f'test text {i}',
                group=cls.group,
                author=cls.user
            )

    def test_paginator(self):
        cache.clear()
        response_index = PaginatorViewsTest.guest_client.get(reverse(
            'posts:index'
        ))
        response_group = PaginatorViewsTest.guest_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': 'test-slug'}
        ))
        response_profile = PaginatorViewsTest.guest_client.get(reverse(
            'posts:profile',
            kwargs={'username': 'TestUser'}
        ))
        response_index_2 = PaginatorViewsTest.guest_client.get(reverse(
            'posts:index'
        ) + '?page=2')
        response_group_2 = PaginatorViewsTest.guest_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': 'test-slug'}
        ) + '?page=2')
        response_profile_2 = PaginatorViewsTest.guest_client.get(reverse(
            'posts:profile',
            kwargs={'username': 'TestUser'}
        ) + '?page=2')
        responses_first_page = [
            response_index,
            response_group,
            response_profile
        ]
        responses_second_page = [
            response_index_2,
            response_group_2,
            response_profile_2
        ]
        for response in responses_first_page:
            with self.subTest():
                self.assertEqual(len(response.context['page_obj']), 10)
        for response in responses_second_page:
            with self.subTest():
                self.assertEqual(len(response.context['page_obj']), 3)
