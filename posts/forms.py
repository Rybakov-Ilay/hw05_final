from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        labels = {
            'group': 'группа',
            'text': 'пост',
            'image': 'изображение',
        }
        help_texts = {
            'group': 'выбор группы',
            'text': 'описание поста',
            'image': 'картинка к посту'
        }

        fields = ['group', 'text', 'image',]


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
