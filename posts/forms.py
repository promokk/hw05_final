from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta():
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'text': 'Введите текст', 'group': 'Выберите группу', 'image': 'Загрузите картинку'}
        help_texts = {'group': 'Из уже существующих'}


class CommentForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea)

    class Meta():
        model = Comment
        fields = ('text',)
        labels = {'text': 'Введите текст комментария'}
