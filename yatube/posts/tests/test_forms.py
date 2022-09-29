import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from ..forms import PostForm
from ..models import Post, Group, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='test group',
            slug='test-slug',
            description='test desciption'
        )
        cls.post = Post.objects.create(
            text='test text',
            group=cls.group,
            author=cls.user,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'test text',
            'group': PostCreateFormTests.group.id,
            'image': uploaded,
        }
        response = PostCreateFormTests.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': 'TestUser'}
        ))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='test text',
                group=PostCreateFormTests.group,
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post(self):
        posts_count = Post.objects.count()
        edited_post = PostCreateFormTests.post
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small2.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'edited text',
            'group': PostCreateFormTests.group.pk,
            'image': uploaded,
        }
        response = PostCreateFormTests.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': str(edited_post.pk)}
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': str(edited_post.pk)}
        ))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                pk=edited_post.pk,
                text='edited text',
                group=PostCreateFormTests.group,
                image='posts/small2.gif'
            ).exists()
        )

    def test_add_comment(self):
        post = PostCreateFormTests.post
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'test comment text',
            'post': post,
            'author': PostCreateFormTests.user,
        }
        response = PostCreateFormTests.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': str(post.pk)}
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': str(post.pk)}
        ))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='test comment text',
                post=post,
                author=PostCreateFormTests.user
            ).exists()
        )
