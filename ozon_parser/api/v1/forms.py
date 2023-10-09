from django import forms


class QueryForm(forms.Form):
    """Форма для валидации параметров запроса."""

    products_count = forms.IntegerField(max_value=50, min_value=0)
