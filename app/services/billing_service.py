import stripe
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.content_generation_usage import ContentGenerationUsage
from app.models.organization import Organization, SubscriptionTier
from app.core.config import settings
from datetime import datetime, timezone
from typing import Optional

if settings.stripe_api_key:
    stripe.api_key = settings.stripe_api_key

class BillingService:
    def __init__(self, db: Session):
        self.db = db

    def create_checkout_session(self, org: Organization, price_id: str, success_url: str, cancel_url: str):
        """Create a Stripe Checkout session for an organization."""
        if not stripe.api_key:
            raise ValueError("Stripe API key is not configured.")

        # Create or retrieve Stripe customer
        if not org.stripe_customer_id:
            customer = stripe.Customer.create(
                email=org.created_by.email if org.created_by else None,
                name=org.name,
                metadata={"org_id": org.id}
            )
            org.stripe_customer_id = customer.id
            self.db.commit()

        session = stripe.checkout.Session.create(
            customer=org.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"org_id": str(org.id)}
        )
        return session.url

    def create_portal_session(self, org: Organization, return_url: str):
        """Create a Stripe Customer Portal session for an organization."""
        if not stripe.api_key:
            raise ValueError("Stripe API key is not configured.")
        if not org.stripe_customer_id:
            raise ValueError("No Stripe customer found for this organization.")
            
        session = stripe.billing_portal.Session.create(
            customer=org.stripe_customer_id,
            return_url=return_url
        )
        return session.url

    def handle_webhook(self, payload: bytes, sig_header: str):
        """Handle Stripe webhooks to update subscription status."""
        if not settings.stripe_webhook_secret:
            raise ValueError("Stripe Webhook Secret is not configured.")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.stripe_webhook_secret
            )
        except Exception as e:
            raise ValueError(f"Invalid webhook payload/signature: {e}")

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            self._handle_subscription_success(session)
        elif event['type'] in ['customer.subscription.updated', 'customer.subscription.deleted']:
            subscription = event['data']['object']
            self._handle_subscription_change(subscription)

    def _handle_subscription_success(self, session):
        org_id = session.get('metadata', {}).get('org_id')
        if not org_id:
            return
        
        org = self.db.query(Organization).filter(Organization.id == int(org_id)).first()
        if org:
            org.subscription_status = "active"
            
            # Determine tier from the price_id used in checkout
            try:
                line_items = stripe.checkout.Session.list_line_items(session['id'], limit=1)
                if line_items and line_items.data:
                    price_id = line_items.data[0].price.id
                    if price_id == settings.stripe_agency_price_id:
                        org.subscription_tier = SubscriptionTier.AGENCY
                    elif price_id == settings.stripe_pro_price_id:
                        org.subscription_tier = SubscriptionTier.PRO
                    else:
                        org.subscription_tier = SubscriptionTier.FREE
            except Exception:
                pass  # If we can't determine tier, status is still updated

            self.db.commit()

    def _handle_subscription_change(self, subscription):
        customer_id = subscription.get('customer')
        org = self.db.query(Organization).filter(Organization.stripe_customer_id == customer_id).first()
        if org:
            status = subscription.get('status')
            org.subscription_status = status
            
            if status == 'active':
                # Try to map to tier based on price_id in subscription.items
                try:
                    price_id = subscription.get('items', {}).get('data', [{}])[0].get('price', {}).get('id')
                    if price_id == settings.stripe_agency_price_id:
                        org.subscription_tier = SubscriptionTier.AGENCY
                    elif price_id == settings.stripe_pro_price_id:
                        org.subscription_tier = SubscriptionTier.PRO
                except Exception:
                    pass
            elif status in ['canceled', 'unpaid', 'incomplete_expired']:
                org.subscription_tier = SubscriptionTier.FREE
            
            # Update end date
            end_timestamp = subscription.get('current_period_end')
            if end_timestamp:
                org.subscription_ends_at = datetime.fromtimestamp(end_timestamp)
                
            self.db.commit()

    def get_generation_usage(self, org: Organization, limit: int = 20):
        """Return organization-scoped AI token and estimated cost usage."""
        base = self.db.query(ContentGenerationUsage).filter(
            ContentGenerationUsage.organization_id == org.id
        )
        totals = self.db.query(
            func.count(ContentGenerationUsage.id),
            func.coalesce(func.sum(ContentGenerationUsage.prompt_token_count), 0),
            func.coalesce(func.sum(ContentGenerationUsage.candidates_token_count), 0),
            func.coalesce(func.sum(ContentGenerationUsage.thoughts_token_count), 0),
            func.coalesce(func.sum(ContentGenerationUsage.total_token_count), 0),
            func.coalesce(func.sum(ContentGenerationUsage.cost_usd), 0),
        ).filter(ContentGenerationUsage.organization_id == org.id).one()
        by_model = self.db.query(
            ContentGenerationUsage.provider,
            ContentGenerationUsage.model,
            func.count(ContentGenerationUsage.id),
            func.coalesce(func.sum(ContentGenerationUsage.total_token_count), 0),
            func.coalesce(func.sum(ContentGenerationUsage.cost_usd), 0),
        ).filter(ContentGenerationUsage.organization_id == org.id).group_by(
            ContentGenerationUsage.provider, ContentGenerationUsage.model
        ).all()
        month_start = datetime.now(timezone.utc).replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        monthly_totals = self.db.query(
            func.count(ContentGenerationUsage.id),
            func.coalesce(func.sum(ContentGenerationUsage.total_token_count), 0),
        ).filter(
            ContentGenerationUsage.organization_id == org.id,
            ContentGenerationUsage.created_at >= month_start,
        ).one()
        from app.services.settings_service import SettingsService
        tier = getattr(org.subscription_tier, "value", org.subscription_tier)
        ai_quota = SettingsService(self.db).get_ai_quota_limits(tier)
        recent = base.order_by(ContentGenerationUsage.created_at.desc()).limit(limit).all()
        return {
            "organization_id": org.id,
            "requests": int(totals[0] or 0),
            "prompt_tokens": int(totals[1] or 0),
            "candidates_tokens": int(totals[2] or 0),
            "thoughts_tokens": int(totals[3] or 0),
            "total_tokens": int(totals[4] or 0),
            "estimated_cost_usd": float(totals[5] or 0),
            "monthly_requests": int(monthly_totals[0] or 0),
            "monthly_total_tokens": int(monthly_totals[1] or 0),
            "ai_quota": ai_quota,
            "ai_quota_remaining": {
                "requests": max(0, ai_quota["max_ai_requests_per_month"] - int(monthly_totals[0] or 0)),
                "tokens": max(0, ai_quota["max_ai_tokens_per_month"] - int(monthly_totals[1] or 0)),
            },
            "by_model": [
                {
                    "provider": row[0],
                    "model": row[1],
                    "requests": int(row[2] or 0),
                    "total_tokens": int(row[3] or 0),
                    "estimated_cost_usd": float(row[4] or 0),
                }
                for row in by_model
            ],
            "recent": [
                {
                    "id": usage.id,
                    "generation_job_id": usage.generation_job_id,
                    "provider": usage.provider,
                    "model": usage.model,
                    "total_tokens": usage.total_token_count,
                    "estimated_cost_usd": float(usage.cost_usd or 0),
                    "created_at": usage.created_at,
                }
                for usage in recent
            ],
        }

    def get_org_limits(self, org: Organization):
        """Returns feature limits based on organization tier, with dynamic overrides."""
        from app.services.settings_service import SettingsService
        settings_service = SettingsService(self.db)
        
        limits = settings_service.get_quota_limits(org.subscription_tier.value)
        
        # Add non-quota features (like AI optimization)
        # These could also be migrated to SystemSettings later if needed
        is_pro_plus = org.subscription_tier in [SubscriptionTier.PRO, SubscriptionTier.AGENCY]
        limits["ai_optimized"] = is_pro_plus
        
        return limits
