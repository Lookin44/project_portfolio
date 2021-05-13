from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.expressions import Exists, OuterRef


User = get_user_model()


class PostQuerySet(models.Manager):
    def annotate_liked(self, user):
        return self.annotate(
            liked=Exists(
                Like.objects.filter(user=user.id, post_id=OuterRef("id")).only(
                    "id",
                ),
            ),
        )


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='Название',
        help_text='Напишите название группы'
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Ссылка',
        help_text='Напишите латиницей ссылку'
    )
    description = models.TextField(
        max_length=200,
        verbose_name='Описание',
        help_text='Напишите описание группы'
    )

    def __str__(self):
        return self.title


class Post(models.Model):

    text = models.TextField(
        verbose_name='Текст',
        help_text='Опишите свои мысли'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        help_text='Добавьте дату публикации',
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        help_text='Кто автор',
        on_delete=models.CASCADE,
        related_name="posts"
    )
    group = models.ForeignKey(
        Group,
        verbose_name='Группа',
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
        help_text='Выберите группу'
    )
    image = models.ImageField(
        upload_to='posts/',
        blank=True,
        null=True,
        verbose_name='Изображение',
        help_text='Выберите изображение'
    )
    objects = PostQuerySet()

    class Meta:
        ordering = ('-pub_date', )

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):

    post = models.ForeignKey(
        Post,
        related_name='comments',
        verbose_name='Пост',
        help_text='Комментарии к какому посту',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор комментария',
        help_text='Кто автор комментария',
        related_name='comments',
        on_delete=models.CASCADE
    )
    text = models.TextField(
        verbose_name='Комментарий',
        help_text='Напишите свой комментарий'
    )
    created = models.DateTimeField(
        verbose_name='Дата публикации комментария',
        help_text='Добавьте дату публикации комментария',
        auto_now_add=True
    )

    class Meta:
        ordering = ('-created', )

    def __str__(self):
        return self.text


class Follow(models.Model):

    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        help_text='Кто подписывается',
        related_name='follower',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        verbose_name='Подписка на автора',
        help_text='На кого подписываться',
        related_name='following',
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follows'
            )
        ]


class Like(models.Model):

    user = models.ForeignKey(
        User,
        related_name='liker',
        on_delete=models.CASCADE
    )
    post = models.ForeignKey(
        Post,
        related_name='likes',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Лайк',
        verbose_name_plural = 'Лайки',
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'post'],
                name='unique_likes'
            )
        ]
