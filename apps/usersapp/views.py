"""
Views for the usersapp.

Provides list, detail, create and update views for user profiles.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, DeleteView

from .models import Profile


class ProfileListView(ListView):
    """Display a list of user profiles."""

    model = Profile
    template_name = "usersapp/profile_list.html"
    context_object_name = "profiles"


class ProfileDetailView(DetailView):
    """Display a single user profile."""

    model = Profile
    template_name = "usersapp/profile_detail.html"
    context_object_name = "profile"


class ProfileCreateView(LoginRequiredMixin, CreateView):
    model = Profile
    fields = ["bio", "website", "location"]

    def dispatch(self, request, *args, **kwargs):
        # If user already has a profile, don't let them create another
        if request.user.is_authenticated and hasattr(request.user, "profile"):
            return redirect(request.user.profile.get_absolute_url())
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Allow authenticated users to edit their profile."""

    model = Profile
    fields = ["bio", "website", "location"]
    template_name = "usersapp/profile_form.html"

    def get_success_url(self):
        return self.object.get_absolute_url()


class ProfileDeleteView(LoginRequiredMixin, DeleteView):
    """Allow authenticated users to delete their profile."""

    model = Profile
    template_name = "usersapp/profile_confirm_delete.html"
    success_url = reverse_lazy("usersapp:list")
