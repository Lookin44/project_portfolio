from django.contrib.auth import get_user_model
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.test import Client, TestCase, modify_settings
from django.urls import reverse
from posts.models import Group, Post, Comment, Follow
from django.core.cache import cache


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
        cls.guest_client = Client()
        user = get_user_model()
        cls.author = user.objects.create_user(
            username='test-author-1',
            password='123456'
        )
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)
        cls.not_author = user.objects.create_user(
            username='test-not-author',
            password='123456'
        )
        cls.authorized_not_author = Client()
        cls.authorized_not_author.force_login(cls.not_author)
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            post=cls.post,
            author=cls.author,
        )
        cls.follow = Follow.objects.create(
            user=cls.not_author,
            author=cls.author
        )
        cls.site = Site(pk=1, domain='example.com', name='example.com')
        cls.site.save()
        cls.about_author = FlatPage.objects.create(
            url='/about-author/', title='Об авторе', content='Начинающий'
        )
        cls.about_spec = FlatPage.objects.create(
            url='/about-spec/', title='Технологии',
            content="О технологиях"
        )
        cls.about_author.sites.add(cls.site)
        cls.about_spec.sites.add(cls.site)


@modify_settings(MIDDLEWARE={'append': 'django.contrib.flatpages.middleware'
                                       '.FlatpageFallbackMiddleware'})
class StaticURLTest(DataBaseTests, TestCase):
    """Тестируем статические URL."""

    def test_pages_unauthorized_client(self):
        """Проверяем работу страниц для неавторизированого пользователя."""
        reverse_name_status_code = {
            reverse('index'): 200,
            reverse('group', kwargs={'slug': self.group.slug}): 200,
            reverse('post', args=(self.author, self.post.id)): 200,
            reverse('new_post'): 302,
            reverse('post_edit', args=(self.author, self.post.id)): 302,
            reverse('post_delete', args=(self.author, self.post.id)): 302,
            reverse('profile', kwargs={'username': 'author_not_in'}): 404,
            reverse('profile', kwargs={'username': self.author}): 200,
            reverse('profile_follow', kwargs={'username': self.author}): 302,
            reverse('profile_unfollow', kwargs={'username': self.author}): 302,
            reverse('add_comment', args=(self.not_author, self.post.id)):
                302,
            reverse('delete_comment', args=(
                self.author, self.post.id, self.comment.id)): 302,
            reverse('about_author'): 200,
            reverse('about_spec'): 200,
        }
        for reverse_name, status_code in reverse_name_status_code.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.status_code, status_code)

    def test_pages_authorized_client(self):
        """Проверяем работу страниц для авторизированого пользователя."""
        reverse_name = [
            reverse('index'),
            reverse('group', kwargs={'slug': self.group.slug}),
            reverse('profile', kwargs={'username': self.author}),
            reverse('new_post'),
            reverse('post', args=(self.author, self.post.id)),
            reverse('post_edit', args=(self.author, self.post.id)),
            reverse('about_author'),
            reverse('about_spec'),
                    ]
        for reverse_name in reverse_name:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertEqual(response.status_code, 200)

    def test_pages_authorized_client_not_author(self):
        """Проверяем работу страниц для авторизированого пользователя,
        но не автора."""
        reverse_name_status_code = {
            reverse('post_edit', args=(self.author, self.post.id)): 302,
            reverse('add_comment', args=(self.not_author, self.post.id)):
                302,
        }
        for reverse_name, status_code in reverse_name_status_code.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_not_author.get(reverse_name)
                self.assertEqual(response.status_code, status_code)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_reverse_name = {
            reverse('index'): 'index.html',
            reverse('new_post'): 'post_new.html',
            reverse('group', kwargs={'slug': self.group.slug}): 'group.html',
            reverse('post_edit',
                    args=(self.author, self.post.id)): 'post_new.html',
        }
        for reverse_name, template in templates_reverse_name.items():
            with self.subTest(reverse_name=reverse_name):
                cache.clear()
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_new_post_unauthorized(self):
        """Проверка редиректа неавторизированного пользователя."""
        rev_name_rev_name_exp = {
            reverse('new_post'):
                reverse('login') + '?next=' + reverse('new_post'),
            reverse('post_edit',
                    args=(self.author, self.post.id)):
                reverse('login') + '?next=' +
                reverse('post_edit',
                        args=(self.author, self.post.id)),
            reverse('profile_follow', kwargs={'username': self.author}):
                reverse('login') + '?next=' + reverse(
                    'profile_follow', kwargs={'username': self.author}
                ),
            reverse('add_comment', args=(self.author, self.post.id)):
                reverse('login') + '?next=' + reverse(
                    'add_comment', args=(self.author, self.post.id)
                )
        }
        for reverse_name, url in rev_name_rev_name_exp.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(
                    reverse_name, follow=False
                )
                self.assertRedirects(response, url, 302)

    def test_new_post_authorized_not_author(self):
        """Проверка редиректа авторизированного пользователя, но не автора."""
        reverse_name_url = {
            reverse('post_edit', args=(self.author, self.post.id)):
                reverse('post', args=(self.author, self.post.id)),
        }
        for reverse_name, url in reverse_name_url.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_not_author.get(reverse_name,
                                                          follow=True)
                self.assertRedirects(response, url, 302)
