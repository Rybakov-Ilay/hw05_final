from django import template

register = template.Library()


@register.filter
def uglify(text):
    new_text = ''
    for i in range(len(text)):
        if i % 2 == 0:
            new_text += text[i].lower()
        else:
            new_text += text[i].upper()
    return new_text
