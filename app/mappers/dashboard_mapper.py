from app.read_models import dashboard as read_model
from app.schemas import dashboard as schema


def to_dashboard_stats_schema(
    stats: read_model.DashboardStatsReadModel,
) -> schema.DashboardStats:
    return schema.DashboardStats(
        summary=schema.DashboardSummary(
            totalSubmissions=stats.summary.total_submissions,
            pendingCount=stats.summary.pending_count,
            approvedCount=stats.summary.approved_count,
            rejectedCount=stats.summary.rejected_count,
            flaggedCount=stats.summary.flagged_count,
        ),
        byType=[
            schema.DashboardByType(
                type=item.type,
                count=item.count,
                approvalRate=item.approval_rate,
            )
            for item in stats.by_type
        ],
        recentActivity=[
            schema.RecentActivity(
                submissionId=item.submission_id,
                title=item.title,
                action=item.action,
                actorName=item.actor_name,
                occurredAt=item.occurred_at,
            )
            for item in stats.recent_activity
        ],
        topSubmitters=[
            schema.TopSubmitter(
                submitterId=item.submitter_id,
                name=item.name,
                tier=item.tier,
                submissionCount=item.submission_count,
                approvalRate=item.approval_rate,
            )
            for item in stats.top_submitters
        ],
    )
