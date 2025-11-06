from django.urls import path

from mailing.views import WebinarListView

from . import views
from .views import get_attempt_details

app_name = "mailing"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    # Client URLs
    path("clients/", views.ClientListView.as_view(), name="client_list"),
    path("clients/create/", views.ClientCreateView.as_view(), name="client_create"),
    path(
        "clients/<int:pk>/update/",
        views.ClientUpdateView.as_view(),
        name="client_update",
    ),
    path(
        "clients/<int:pk>/delete/",
        views.ClientDeleteView.as_view(),
        name="client_delete",
    ),
    # Message URLs
    path("messages/", views.MessageListView.as_view(), name="message_list"),
    path("messages/create/", views.MessageCreateView.as_view(), name="message_create"),
    path(
        "messages/<int:pk>/update/",
        views.MessageUpdateView.as_view(),
        name="message_update",
    ),
    path(
        "messages/<int:pk>/delete/",
        views.MessageDeleteView.as_view(),
        name="message_delete",
    ),
    # Mailing URLs
    path("mailings/<int:pk>/send/", views.send_mailing_now, name="mailing_send"),
    path("mailings/", views.MailingListView.as_view(), name="mailing_list"),
    path("mailings/create/", views.MailingCreateView.as_view(), name="mailing_create"),
    path(
        "mailings/create/from-message/<int:message_id>/",
        views.MailingCreateView.as_view(),
        name="mailing_create_with_message",
    ),
    path(
        "mailings/<int:pk>/update/",
        views.MailingUpdateView.as_view(),
        name="mailing_update",
    ),
    path(
        "mailings/<int:pk>/delete/",
        views.MailingDeleteView.as_view(),
        name="mailing_delete",
    ),
    # Attempt URLs
    path("attempts/", views.MailingAttemptListView.as_view(), name="attempt_list"),
    path("attempts/<int:pk>/details/", get_attempt_details, name="attempt_details"),
    path(
        "webinars/",
        WebinarListView.as_view(template_name="webinar/webinar_list.html"),
        name="webinar_list",
    ),
]
