from django import forms
from django.contrib.auth import get_user_model

from tickets.models import Attachment, Comment, Ticket, TicketStatus, UserProfile


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["title", "description", "category", "priority"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "priority": forms.Select(attrs={"class": "form-select"}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "补充说明…"}
            )
        }


class AttachmentForm(forms.ModelForm):
    class Meta:
        model = Attachment
        fields = ["file"]
        widgets = {"file": forms.ClearableFileInput(attrs={"class": "form-control"})}


class AssignForm(forms.Form):
    agent = forms.ModelChoiceField(
        queryset=get_user_model().objects.none(),
        label="指派给",
        empty_label=None,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["agent"].queryset = (
            get_user_model()
            .objects.filter(is_active=True, profile__role__in=["agent", "admin"])
            .order_by("username")
        )


class StatusForm(forms.Form):
    status = forms.ChoiceField(
        choices=TicketStatus.choices,
        label="新状态",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    note = forms.CharField(
        required=False,
        max_length=255,
        label="备注",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "可选"}),
    )


class RoleForm(forms.Form):
    role = forms.ChoiceField(
        choices=UserProfile._meta.get_field("role").choices,
        label="角色",
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
