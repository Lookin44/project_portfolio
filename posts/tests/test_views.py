from django import forms
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.test import Client, TestCase, modify_settings
from django.urls import reverse
from posts.models import Group, Post, User, Follow, Comment
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile


class DataBaseTests(TestCase):
    """Подготавливаем БД."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='test-group',
            slug='test_group',
            description='test-description'
        )
        cls.group_no_post = Group.objects.create(
            title='test-group-2',
            slug='test_group_2',
            description='test-description for second group'
        )
        cls.author = User.objects.create_user(
            username='test-author',
        )
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)
        cls.follower = User.objects.create_user(
            username='test-follower')
        cls.authorized_follower = Client()
        cls.authorized_follower.force_login(cls.follower)
        cls.not_follower = User.objects.create_user(
            username='test-not-follower')
        cls.authorized_not_follower = Client()
        cls.authorized_not_follower.force_login(cls.not_follower)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group,
            image=image
        )
        cls.site_one = Site(pk=1, domain='example.com', name='example.com')
        cls.site_one.save()
        cls.about_author = FlatPage.objects.create(
            url='/about-author/', title='Об авторе', content='Начинающий'
        )
        cls.about_spec = FlatPage.objects.create(
            url='/about-spec/', title='Технологии',
            content='О технологиях'
        )
        cls.about_author.sites.add(cls.site_one)
        cls.about_spec.sites.add(cls.site_one)


@modify_settings(MIDDLEWARE={'append': 'django.contrib.flatpages.middleware'
                                       '.FlatpageFallbackMiddleware'})
class PostPagesTests(DataBaseTests, TestCase):
    """Проверяем работу view-функций"""
    def setUp(self):
        cache.clear()

    def test_post_not_in_group(self):
        """Тестовый пост не появился на странице group_2"""
        response = self.authorized_author.get(
            reverse('group', kwargs={'slug': self.group_no_post.slug})
        )
        self.assertEqual(len(response.context['page']), 0)

    def test_author_flatpage_show_correct_context(self):
        response = self.authorized_author.get(reverse('about_author'))
        title = response.context.get('flatpage').title
        content = response.context.get('flatpage').content
        self.assertEqual(title, 'Об авторе')
        self.assertEqual(content, 'Начинающий')

    def test_spec_flatpage_show_correct_context(self):
        response = self.authorized_author.get(reverse('about_spec'))
        title = response.context.get('flatpage').title
        content = response.context.get('flatpage').content
        self.assertEqual(title, 'Технологии')
        self.assertEqual(content, 'О технологиях')

    def test_paginator(self):
        """В index передаеться не более 10 постов"""
        # Создаем несколько постов циклом
        for i in range(20):
            Post.objects.create(
                text='Тестовый текст',
                author=self.author,
                group=self.group_no_post,
            )
        response = self.authorized_author.get(reverse('index'))
        test_posts = response.context['page']
        self.assertEqual(len(test_posts), 10)

    def test_post_new_page_show_correct_context(self):
        """Шаблон post_new сформирован с правильным контекстом."""
        response = self.authorized_author.get(reverse('new_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_author.get(
            reverse('post_edit', args=(self.author.username, self.post.id))
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_author.get(reverse('index'))
        self.assertEqual(len(response.context['page']), 1)
        self.assertContains(response, '<img ')
        self.assertEqual(
            response.context['page'][0], self.post,
            'Шаблон index сформирован с неправильным контекстом'
        )

    def test_group_page_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_author.get(
            reverse('group', kwargs={'slug': self.group.slug}))
        self.assertEqual(len(response.context['page']), 1)
        self.assertContains(response, '<img ')
        self.assertEqual(
            response.context['page'][0], self.post,
            'Шаблон group сформирован с неправильным контекстом'
        )

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_author.get(
            reverse('profile', kwargs={'username': self.author})
        )
        self.assertContains(response, '<img ')
        self.assertEqual(response.context['page'][0], self.post)
        self.assertEqual(response.context['author'], self.post.author)

    def test_post_page_show_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        response = self.authorized_author.get(
            reverse('post', args=(self.author, self.post.id))
        )
        self.assertContains(response, '<img ')
        self.assertEqual(response.context['author'], self.post.author)
        self.assertEqual(response.context['post'], self.post)

    def test_index_page_show_correct_context_with_cache(self):
        """Шаблон index работает с кэшированием."""
        client = self.authorized_author
        response = client.get(reverse('index'))
        content = response.content
        Post.objects.all().delete()
        response = client.get(reverse('index'))
        self.assertEqual(content, response.content, 'Кеширование не работает')
        cache.clear()
        response = client.get(reverse('index'))
        self.assertNotEqual(content, response.content,
                            'Кеширование неисправно')


class FollowCaseTests(DataBaseTests, TestCase):
    def test_follow(self):
        """Авторизованный пользователь может подписываться на других
         пользователей"""
        self.authorized_follower.get(reverse('profile_follow',
                                             kwargs={'username': self.author}))
        follow = Follow.objects.first()
        follow_counts = Follow.objects.count()
        self.assertEqual(follow_counts, 1)
        self.assertEqual(follow.user, self.follower)
        self.assertEqual(follow.author, self.author)

    def test_unfollow(self):
        """Авторизованный пользователь может отписываться от других
         пользователей"""
        Follow.objects.create(user=self.follower, author=self.author)
        self.authorized_follower.get(reverse('profile_unfollow',
                                             kwargs={'username': self.author}))
        unfollows = Follow.objects.count()
        self.assertEqual(unfollows, 0)

    def test_unfollower_follow_index(self):
        """Новая запись пользователя не появляется в ленте тех, кто на него
         не подписан"""
        response = self.authorized_not_follower.get(reverse('follow_index'))
        self.assertFalse(response.context['page'])

    def test_follow_index_page_show_correct_context(self):
        """Шаблон follow_index сформирован с правильным контекстом."""
        self.authorized_follower.get(reverse('profile_follow',
                                             kwargs={'username': self.author}))
        response = self.authorized_follower.get(reverse('follow_index'))
        self.assertContains(response, '<img ')
        self.assertEqual(
            response.context['page'][0], self.post,
            'Шаблон follow_index сформирован с неправильным контекстом'
        )
