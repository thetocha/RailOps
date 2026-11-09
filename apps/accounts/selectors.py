"""Read queries for accounts. Keep trivial one-off filters in views."""

from __future__ import annotations

from django.db.models import Q, QuerySet

from apps.accounts.models import User


def user_directory(*, search: str = "") -> QuerySet[User]:
    queryset = User.objects.prefetch_related("groups").order_by("username")
    term = search.strip()
    if term:
        queryset = queryset.filter(
            Q(username__icontains=term)
            | Q(email__icontains=term)
            | Q(first_name__icontains=term)
            | Q(last_name__icontains=term)
        )
    return queryset
