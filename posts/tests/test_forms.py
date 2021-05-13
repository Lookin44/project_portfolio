import shutil
import tempfile
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post, User, Comment
from django.core.files.uploadedfile import SimpleUploadedFile


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(dir=settings.BASE_DIR))
class FormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем тетсувую группу
        cls.group = Group.objects.create(
            title='test-group',
            slug='test_group',
        )
        # Создаем авторизированный аккаунт
        cls.user = User.objects.create_user(
            username='test-author',
            password='123456'
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_new_post(self):
        """Тестируем добовление поста."""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        img = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        test_text = 'Тестовое создание поста'
        form_data = {
            'text': test_text,
            'group': self.group.id,
            'image': img,
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        post = Post.objects.first()
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(post.text, test_text)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, self.group)
        self.assertIsNotNone(response.context['post'].image)

    def test_edit_post(self):
        """Тестируем изменение поста."""
        test_text = 'Тестовое создание поста'
        test_text_edit = 'Измененый текст для тестового поста'
        post = Post.objects.create(
            text=test_text,
            author=self.user,
            group=self.group,
        )
        group_havent_post = Group.objects.create(
            title='test-group-2',
            slug='test_group_2',
        )
        post_count = Post.objects.count()
        form_data = {
            'text': test_text_edit,
            'group': group_havent_post.id,
        }
        response = self.authorized_client.post(
            reverse('post_edit', args=(self.user.username, post.id)),
            data=form_data,
            follow=True
        )
        post_edit = Post.objects.first()
        self.assertRedirects(
            response,
            reverse('post', args=(self.user.username, post.id))
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(post_edit.text, test_text_edit)
        self.assertEqual(post_edit.author, self.user)
        self.assertEqual(post_edit.group, group_havent_post)

    def test_del_post(self):
        """Тестируем удаление поста."""
        post = Post.objects.create(
            text='Тестовое создание поста',
            author=self.user,
            group=self.group,
        )
        response = self.authorized_client.post(
            reverse('post_delete', args=(self.user.username, post.id)),
        )
        self.assertRedirects(
            response,
            reverse('profile', args=(self.user,))
        )
        self.assertEqual(Post.objects.count(), 0)

    def test_add_comment(self):
        """Авторизированный пользователь может комментировать посты."""
        post = Post.objects.create(
            text='Тестовое создание поста',
            author=self.user,
            group=self.group,
        )
        form_data = {
            'post': post,
            'author': self.user,
            'text': 'тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse('add_comment', args=(self.user, post.id)),
            data=form_data,
            follow=True
        )
        comment = Comment.objects.first()
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.user)
        self.assertRedirects(
            response,
            reverse('post', args=(self.user.username, post.id)))
        self.assertEqual(post.comments.count(), 1)
        self.assertEqual(comment.post, post)

    def test_comment_unuthorized(self):
        """Невторизированный пользователь неможет комментировать посты."""
        post = Post.objects.create(
            text='Тестовое создание поста',
            author=self.user,
            group=self.group,
        )
        guest_client = Client()
        guest_client.post(
            reverse('add_comment', args=(self.user, post.id)),
            {'text': 'Test comment guest'}
        )
        self.assertEqual(Comment.objects.count(), 0)

    def test_del_comment(self):
        post = Post.objects.create(
            text='Тестовое создание поста',
            author=self.user,
            group=self.group,
        )
        comment = Comment.objects.create(
            text='Тестовый комментарий',
            author=self.user
        )
        response = self.authorized_client.post(
            reverse('delete_comment', args=(self.user, post.id, comment.id)),
        )
        self.assertRedirects(
            response,
            reverse('post', args=(self.user.username, post.id)))
        self.assertEqual(Comment.objects.count(), 0)
