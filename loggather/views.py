from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from ohapi.api import get_all_results

from openhumans.models import OpenHumansMember

from .tasks import get_logs
from .forms import RetrieveLogsForm

OLDEST_LOGS_DATE = (datetime.now() - timedelta(days=settings.LOG_RETENTION_DAYS)).date()
TODAY = datetime.now().date()


class IndexView(TemplateView):
    template_name = "main/index.html"

    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to provide redirect to dashboard if user is logged in.
        """
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """
        Add auth url to context
        """
        context = super().get_context_data(*args, **kwargs)
        auth_url = OpenHumansMember.get_auth_url()
        context.update({"auth_url": auth_url})
        return context


class DashboardView(LoginRequiredMixin, FormView):
    form_class = RetrieveLogsForm
    success_url = reverse_lazy("dashboard")
    template_name = "main/dashboard.html"

    def get_context_data(self, *args, **kwargs):
        """
        Get available files
        """
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "data_files": self.request.user.openhumansmember.list_files(),
                "log_retention_days": settings.LOG_RETENTION_DAYS,
                "oldest_date": OLDEST_LOGS_DATE,
                "newest_date": TODAY,
            }
        )
        return context

    def form_valid(self, form):
        """
        On clicking the 'retrieve logs' button, grabs the logs from the selected date range.
        """
        start_date = self.request.POST.get("start_date")
        end_date = self.request.POST.get("end_date")
        get_logs.delay(
            self.request.user.openhumansmember.pk,
            start_date=start_date,
            end_date=end_date,
        )

        messages.success(self.request, "Log retrieval initiated")

        return HttpResponseRedirect(self.get_success_url())


class LogoutUserView(LoginRequiredMixin, TemplateView):
    template_name = "main/index.html"

    def post(self, request, **kwargs):
        """
        Logout user.
        """
        logout(request)
        redirect_url = settings.LOGOUT_REDIRECT_URL
        return redirect(redirect_url)


class AboutView(TemplateView):
    template_name = "main/about.html"
