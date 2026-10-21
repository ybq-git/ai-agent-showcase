from datetime import timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from tickets.forms import AssignForm, AttachmentForm, CommentForm, RoleForm, StatusForm, TicketForm
from tickets.models import (
    Attachment,
    Comment,
    Priority,
    Role,
    StatusLog,
    Ticket,
    TicketStatus,
    UserProfile,
)
from tickets.permissions import (
    can_assign,
    can_change_status,
    can_edit_ticket,
    can_view_ticket,
    get_role,
    is_admin,
    is_agent,
    valid_transition,
)
from tickets.tasks import notify_assignment, notify_status_change

User = get_user_model()


class TicketLoginView(LoginView):
    template_name = "tickets/login.html"
    redirect_authenticated_user = True


def logout_view(request):
    logout(request)
    return redirect("login")


def agent_required(view):
    @login_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not is_agent(request.user):
            raise PermissionDenied("只有处理人或管理员可以执行该操作")
        return view(request, *args, **kwargs)

    return wrapper


def admin_required(view):
    @login_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not is_admin(request.user):
            raise PermissionDenied("只有管理员可以执行该操作")
        return view(request, *args, **kwargs)

    return wrapper


def health(request):
    return JsonResponse({"status": "ok"})


@login_required
def ticket_list(request):
    query = Ticket.objects.select_related("category", "created_by", "assigned_to")
    if not is_agent(request.user):
        query = query.filter(created_by=request.user)

    status = request.GET.get("status", "")
    priority = request.GET.get("priority", "")
    keyword = request.GET.get("q", "").strip()
    if status:
        query = query.filter(status=status)
    if priority:
        query = query.filter(priority=priority)
    if keyword:
        query = query.filter(Q(title__icontains=keyword) | Q(description__icontains=keyword))

    paginator = Paginator(query, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "tickets/ticket_list.html",
        {
            "page_obj": page_obj,
            "statuses": TicketStatus.choices,
            "priorities": Priority.choices,
            "filters": {"status": status, "priority": priority, "q": keyword},
        },
    )


@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(
        Ticket.objects.select_related("category", "created_by", "assigned_to").prefetch_related(
            "comments__author",
            "attachments__uploaded_by",
            "status_logs__operator",
        ),
        pk=pk,
    )
    if not can_view_ticket(request.user, ticket):
        raise PermissionDenied("无权查看该工单")

    return render(
        request,
        "tickets/ticket_detail.html",
        {
            "ticket": ticket,
            "comment_form": CommentForm(),
            "attachment_form": AttachmentForm(),
            "assign_form": AssignForm(),
            "status_form": StatusForm(),
            "can_assign": can_assign(request.user),
            "can_change_status": can_change_status(request.user),
            "can_edit": can_edit_ticket(request.user, ticket),
        },
    )


@login_required
def ticket_create(request):
    if request.method == "POST":
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.save()
            StatusLog.objects.create(
                ticket=ticket,
                from_status="",
                to_status=TicketStatus.OPEN,
                operator=request.user,
                note="创建工单",
            )
            cache.delete("dashboard_stats")
            messages.success(request, f"工单 #{ticket.pk} 已创建")
            return redirect("ticket_detail", pk=ticket.pk)
    else:
        form = TicketForm()
    return render(request, "tickets/ticket_form.html", {"form": form, "title": "新建工单"})


@login_required
def ticket_edit(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if not can_edit_ticket(request.user, ticket):
        raise PermissionDenied("当前状态或角色不能编辑该工单")

    if request.method == "POST":
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, "工单已更新")
            return redirect("ticket_detail", pk=ticket.pk)
    else:
        form = TicketForm(instance=ticket)
    return render(request, "tickets/ticket_form.html", {"form": form, "title": "编辑工单"})


@agent_required
@require_POST
def ticket_assign(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    form = AssignForm(request.POST)
    if not form.is_valid():
        messages.error(request, "请选择有效的处理人")
        return redirect("ticket_detail", pk=pk)

    agent = form.cleaned_data["agent"]
    old_status = ticket.status
    ticket.assigned_to = agent
    if ticket.status == TicketStatus.OPEN:
        ticket.status = TicketStatus.IN_PROGRESS
    ticket.save()
    StatusLog.objects.create(
        ticket=ticket,
        from_status=old_status,
        to_status=ticket.status,
        operator=request.user,
        note=f"指派给 {agent.username}",
    )
    notify_assignment.delay(ticket.pk, agent.pk)
    cache.delete("dashboard_stats")
    messages.success(request, f"已指派给 {agent.username}")
    return redirect("ticket_detail", pk=pk)


@agent_required
@require_POST
def ticket_update_status(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    form = StatusForm(request.POST)
    if not form.is_valid():
        messages.error(request, "状态参数不合法")
        return redirect("ticket_detail", pk=pk)

    target = form.cleaned_data["status"]
    if not valid_transition(ticket.status, target):
        messages.error(
            request,
            f"不能从「{ticket.get_status_display()}」流转到「{dict(TicketStatus.choices)[target]}」",
        )
        return redirect("ticket_detail", pk=pk)

    old_status = ticket.status
    ticket.status = target
    if target == TicketStatus.RESOLVED:
        ticket.resolved_at = timezone.now()
    elif old_status == TicketStatus.RESOLVED:
        ticket.resolved_at = None
    ticket.save()
    StatusLog.objects.create(
        ticket=ticket,
        from_status=old_status,
        to_status=target,
        operator=request.user,
        note=form.cleaned_data.get("note", ""),
    )
    notify_status_change.delay(ticket.pk, old_status, target, request.user.pk)
    cache.delete("dashboard_stats")
    messages.success(request, f"状态已更新为 {ticket.get_status_display()}")
    return redirect("ticket_detail", pk=pk)


@login_required
@require_POST
def add_comment(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if not can_view_ticket(request.user, ticket):
        raise PermissionDenied("无权评论该工单")
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.ticket = ticket
        comment.author = request.user
        comment.save()
        messages.success(request, "评论已添加")
    else:
        messages.error(request, "评论内容不能为空")
    return redirect("ticket_detail", pk=pk)


@login_required
@require_POST
def add_attachment(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if not can_view_ticket(request.user, ticket):
        raise PermissionDenied("无权上传附件")
    form = AttachmentForm(request.POST, request.FILES)
    if form.is_valid():
        attachment = form.save(commit=False)
        attachment.ticket = ticket
        attachment.uploaded_by = request.user
        attachment.save()
        messages.success(request, "附件已上传")
    else:
        messages.error(request, "附件上传失败")
    return redirect("ticket_detail", pk=pk)


@agent_required
def dashboard(request):
    stats = cache.get("dashboard_stats")
    if stats is None:
        counts = {
            row["status"]: row["count"]
            for row in Ticket.objects.values("status").annotate(count=Count("id"))
        }
        resolved = Ticket.objects.filter(resolved_at__isnull=False).only(
            "created_at", "resolved_at"
        )[:1000]
        durations = [
            (ticket.resolved_at - ticket.created_at).total_seconds()
            for ticket in resolved
            if ticket.resolved_at and ticket.created_at
        ]
        avg_hours = round(sum(durations) / len(durations) / 3600, 1) if durations else 0

        start = timezone.localdate() - timedelta(days=6)
        daily_rows = (
            Ticket.objects.filter(created_at__date__gte=start)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        daily = {row["day"].strftime("%m-%d"): row["count"] for row in daily_rows}
        labels = [
            (start + timedelta(days=offset)).strftime("%m-%d") for offset in range(7)
        ]

        stats = {
            "open": counts.get(TicketStatus.OPEN, 0),
            "in_progress": counts.get(TicketStatus.IN_PROGRESS, 0),
            "resolved": counts.get(TicketStatus.RESOLVED, 0),
            "closed": counts.get(TicketStatus.CLOSED, 0),
            "avg_hours": avg_hours,
            "chart_labels": labels,
            "chart_data": [daily.get(label, 0) for label in labels],
        }
        cache.set("dashboard_stats", stats, 30)

    return render(request, "tickets/dashboard.html", {"stats": stats})


@admin_required
def user_management(request):
    users = User.objects.select_related("profile").order_by("id")
    return render(request, "tickets/user_management.html", {"users": users})


@admin_required
@require_POST
def change_role(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    form = RoleForm(request.POST)
    if form.is_valid():
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = form.cleaned_data["role"]
        profile.save()
        messages.success(request, f"{user.username} 的角色已更新")
    else:
        messages.error(request, "角色参数不合法")
    return redirect("user_management")


@admin_required
@require_POST
def toggle_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user == request.user:
        messages.error(request, "不能禁用自己的账号")
        return redirect("user_management")
    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])
    messages.success(request, f"{user.username} 已{'启用' if user.is_active else '禁用'}")
    return redirect("user_management")
