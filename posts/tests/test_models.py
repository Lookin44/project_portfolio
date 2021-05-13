import datetime as dt

from django.contrib.auth import get_user_model
from django.test import TestCase
from posts.models import Group, Post, Comment, Follow


class ModelsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаем объект тестувую БД"""
        super().setUpClass()
        user = get_user_model()
        cls.user = user.objects.create(
            username='test-author',
            password='123456'
        )
        cls.user_follower = user.objects.create(
            username='test-follower',
            password='123456'
        )
        cls.group = Group.objects.create(
            title='A' * 200,
            slug='test_group',
            description='Б' * 200
        )
        cls.post = Post.objects.create(
            text='A' * 100,
            pub_date=dt.datetime.now(),
            author=cls.user,
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            post=cls.post,
            author=cls.user,
            created=dt.datetime.now()
        )
        cls.follow = Follow.objects.create(
            user=cls.user_follower,
            author=cls.user
        )

    def test_verbose_name_group(self):
        """verbose_name модели group в полях совпадает с ожидаемым."""
        group = ModelsTest.group
        field_verbose = {
            'title': 'Название',
            'slug': 'Ссылка',
            'description': 'Описание'
        }
        for value, expected in field_verbose.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).verbose_name, expected)

    def test_verbose_name_post(self):
        """verbose_name модели post в полях совпадает с ожидаемым."""
        post = ModelsTest.post
        field_verbose = {
            'text': 'Текст',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
            'image': 'Изображение'
        }
        for value, expected in field_verbose.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_verbose_name_comment(self):
        """verbose_name модели comment в полях совпадает с ожидаемым."""
        comment = ModelsTest.comment
        field_verbose = {
            'text': 'Комментарий',
            'created': 'Дата публикации комментария',
            'author': 'Автор комментария',
            'post': 'Пост'
        }
        for value, expected in field_verbose.items():
            with self.subTest(value=value):
                self.assertEqual(
                    comment._meta.get_field(value).verbose_name, expected)

    def test_verbose_name_follow(self):
        """verbose_name модели follow в полях совпадает с ожидаемым."""
        follow = ModelsTest.follow
        field_verbose = {
            'user': 'Подписчик',
            'author': 'Подписка на автора'
        }
        for value, expected in field_verbose.items():
            with self.subTest(value=value):
                self.assertEqual(
                    follow._meta.get_field(value).verbose_name, expected)

    def test_help_text_group(self):
        """help_text модели group в полях совпадает с ожидаемым."""
        group = ModelsTest.group
        field_help_texts = {
            'title': 'Напишите название группы',
            'slug': 'Напишите латиницей ссылку',
            'description': 'Напишите описание группы'
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).help_text, expected)

    def test_help_text_post(self):
        """help_text модели post в полях совпадает с ожидаемым."""
        post = ModelsTest.post
        field_help_texts = {
            'text': 'Опишите свои мысли',
            'pub_date': 'Добавьте дату публикации',
            'author': 'Кто автор',
            'group': 'Выберите группу',
            'image': 'Выберите изображение'
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

    def test_help_text_comment(self):
        """help_text модели post в полях совпадает с ожидаемым."""
        comment = ModelsTest.comment
        field_help_texts = {
            'text': 'Напишите свой комментарий',
            'created': 'Добавьте дату публикации комментария',
            'author': 'Кто автор комментария',
            'post': 'Комментарии к какому посту'
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    comment._meta.get_field(value).help_text, expected)

    def test_help_text_follow(self):
        """help_text модели follow в полях совпадает с ожидаемым."""
        follow = ModelsTest.follow
        field_help_texts = {
            'user': 'Кто подписывается',
            'author': 'На кого подписываться'
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    follow._meta.get_field(value).help_text, expected)

    def test_object_name_is_title_field_group(self):
        """В поле __str__ объекта group записано значение поля group.title."""
        group = ModelsTest.group
        expected_object_name = group.title
        self.assertEquals(expected_object_name, str(group))

    def test_object_name_is_title_field_post(self):
        """В поле __str__ объекта post записано значение поля post.title не
         превышающее 15 символов."""
        post = ModelsTest.post
        expected_object_name = post.text[:15]
        self.assertEquals(expected_object_name, str(post))

    def test_object_name_is_title_field_comment(self):
        """В поле __str__ объекта comment записано значение поля
        comment.text."""
        comment = ModelsTest.comment
        expected_object_name = comment.text
        self.assertEquals(expected_object_name, str(comment))
