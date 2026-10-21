from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def notify_assignment(ticket_id: int, agent_id: int) -> str:
    from tickets.models import Ticket

    ticket = Ticket.objects.select_related("assigned_to", "created_by").get(pk=ticket_id)
    agent = ticket.assigned_to
    if not agent or not agent.email:
        return "skip: agent has no email"
    send_mail(
        subject=f"[工单 #{ticket.pk}] 你被指派了一个新工单",
        message=f"工单：{ticket.title}\n提交人：{ticket.created_by.username}\n优先级：{ticket.get_priority_display()}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[agent.email],
        fail_silently=True,
    )
    return f"notified {agent.email}"


@shared_task
def notify_status_change(ticket_id: int, from_status: str, to_status: str, operator_id: int) -> str:
    from tickets.models import Ticket

    ticket = Ticket.objects.select_related("created_by").get(pk=ticket_id)
    if not ticket.created_by.email:
        return "skip: creator has no email"
    send_mail(
        subject=f"[工单 #{ticket.pk}] 状态更新：{from_status} -> {to_status}",
        message=f"工单：{ticket.title}\n当前状态：{ticket.get_status_display()}\n处理人：{ticket.assigned_to or '未指派'}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[ticket.created_by.email],
        fail_silently=True,
    )
    return f"notified {ticket.created_by.email}"
