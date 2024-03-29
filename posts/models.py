from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name="описание")
    pub_date = models.DateTimeField("date published", auto_now_add=True,
                                    db_index=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="posts",
        verbose_name="автор"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="posts",
        verbose_name="группа",
    )
    image = models.ImageField(upload_to="posts/", blank=True, null=True)

    def __str__(self):
        return f"{self.author}: {self.text[:10]}"

    class Meta:
        ordering = ("-pub_date",)


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Комментарий",
        related_name="comments",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Автор комментария",
    )
    text = models.TextField()
    created = models.DateTimeField("date published", auto_now_add=True)

    def __str__(self):
        return self.text


class Follow(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="following")
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="follower")

    class Meta:
        unique_together = ('author', 'user',)

    def __str__(self):
        return self.user.username
