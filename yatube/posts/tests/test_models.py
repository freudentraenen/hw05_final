from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_group_model_have_correct_object_name(self):
        group = PostModelTest.group
        self.assertEqual(
            group.__str__(),
            group.title,
            'метод __str__ модели Group работает неправильно'
        )

    def test_post_model_have_correct_object_name(self):
        post = PostModelTest.post
        self.assertEqual(
            post.__str__(),
            post.text[:15],
            'метод __str__ модели Post работает неправильно')

    def test_verbose_name(self):
        field_verboses = {
            'text': 'текст записи',
            'created': 'дата создания',
            'group': 'группа',
            'author': 'автор',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Post._meta.get_field(field).verbose_name, expected_value)

    def test_help_text(self):
        field_help_texts = {
            'text': 'Введите текст записи',
            'group': 'Группа, к которой будет относиться запись',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Post._meta.get_field(field).help_text, expected_value)
