# apps/directory/management/commands/seed.py
import random, string
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone

from faker import Faker

from apps.directory.models import Business
from apps.reviews.models import Review
from apps.wallets.models import UserWallet
from apps.onchain.models import OnChainRecord
try:
    from apps.promotions.models import Promotion
    HAS_PROMO = True
except Exception:
    HAS_PROMO = False

fake = Faker()
User = get_user_model()
CHAINS = ["eth", "polygon", "bsc"]

def short_hex(n):
    return "0x" + "".join(random.choice("0123456789abcdef") for _ in range(n))

def field_names(model):
    return {f.name for f in model._meta.get_fields() if hasattr(f, "attname")}

def filtered_kwargs(model, **kwargs):
    allowed = field_names(model)
    return {k: v for k, v in kwargs.items() if k in allowed}

def unique_slug(base):
    base = base.strip().lower().replace(" ", "-")
    base = "".join(ch for ch in base if ch.isalnum() or ch == "-")[:200]
    slug = base or "biz"
    i = 1
    while Business.objects.filter(slug=slug).exists():
        slug = f"{base}-{i}"
        i += 1
    return slug

def pick_field(existing: set, *candidates):
    """Return the first candidate name that exists in the model's fields."""
    for c in candidates:
        if c in existing:
            return c
    return None

def set_if_present(d: dict, key: str, value):
    if key:
        d[key] = value

def slugify_base(text: str, max_len=220):
    base = text.strip().lower().replace(" ", "-")
    base = "".join(ch for ch in base if ch.isalnum() or ch == "-")[:max_len]
    return base or "promo"

def unique_model_slug(model, field_name: str, base_text: str, extra: str = "", max_len=220):
    base = slugify_base(base_text, max_len=max_len)
    if extra:
        base = slugify_base(f"{base}-{extra}", max_len=max_len)
    slug = base
    i = 1
    exists = model.objects.filter(**{field_name: slug}).exists()
    while exists:
        slug = slugify_base(f"{base}-{i}", max_len=max_len)
        exists = model.objects.filter(**{field_name: slug}).exists()
        i += 1
    return slug


class Command(BaseCommand):
    help = "Seed demo data across users, wallets, businesses, reviews, promotions, onchain."

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=8)
        parser.add_argument("--businesses", type=int, default=18)
        parser.add_argument("--reviews", type=int, default=120)
        parser.add_argument("--promos", type=int, default=10)
        parser.add_argument("--fresh", action="store_true")
        parser.add_argument("--seed", type=int, default=42)

    @transaction.atomic
    def handle(self, *args, **opts):
        random.seed(opts["seed"]); fake.seed_instance(opts["seed"])

        # wipe demo data if asked
        if opts["fresh"]:
            self.stdout.write(self.style.WARNING("Clearing existing demo rows…"))
            OnChainRecord.objects.all().delete()
            if HAS_PROMO:
                Promotion.objects.all().delete()
            Review.objects.all().delete()
            Business.objects.all().delete()
            demo_users = User.objects.filter(email__endswith="@example.com")
            UserWallet.objects.filter(user__in=demo_users).delete()
            demo_users.delete()

        # USERS
        users = []
        for i in range(opts["users"]):
            email = f"user{i+1}@example.com"
            u, created = User.objects.get_or_create(
                username=f"demo{i+1}",
                defaults={"email": email}
            )
            if created:
                u.set_password("demo1234")
                u.save()
            users.append(u)

        # some wallets
        for u in users:
            if random.random() < 0.6 and not u.wallets.exists():
                UserWallet.objects.get_or_create(
                    user=u,
                    address=short_hex(40),
                    defaults={"chain": random.choice(CHAINS), "scheme": "eip191"},
                )
        self.stdout.write(self.style.SUCCESS(f"Users: {len(users)}  (wallet-linked: {UserWallet.objects.count()})"))

        # BUSINESSES
        categories = ["Cafe", "Gym", "Bookstore", "Pet Care", "Mechanic", "Grocery", "Bakery", "Salon", "Electronics", "Clothing"]
        biz_list = []
        for _ in range(opts["businesses"]):
            owner = random.choice(users)
            name = f"{fake.company()} {random.choice(['Ltd','Co','Inc',''])}".strip()
            slug = unique_slug(name)
            owner_wallet_val = None
            if "owner_wallet" in field_names(Business):
                w = owner.wallets.first()
                owner_wallet_val = w.address if w else None

            kwargs = filtered_kwargs(
                Business,
                name=name[:200],
                category=random.choice(categories),
                description=fake.paragraph(nb_sentences=3),
                address=fake.address().replace("\n", ", ")[:255],
                phone=fake.phone_number()[:50],
                website=f"https://{fake.domain_name()}",
                slug=slug[:220],
                owner=owner,
                owner_wallet=owner_wallet_val,  # silently dropped if field doesn't exist
            )
            try:
                b = Business.objects.create(**kwargs)
            except IntegrityError:
                # fallback: tweak slug and retry once
                kwargs["slug"] = unique_slug(name + "-" + ''.join(random.choice(string.ascii_lowercase) for _ in range(4)))
                b = Business.objects.create(**kwargs)
            biz_list.append(b)

        self.stdout.write(self.style.SUCCESS(f"Businesses: {len(biz_list)}"))

        # REVIEWS
        review_objs = []
        has_hidden = "is_hidden" in field_names(Review)
        has_created_at = "created_at" in field_names(Review)
        for _ in range(opts["reviews"]):
            biz = random.choice(biz_list)
            reviewer = random.choice(users)
            base_kwargs = dict(
                business=biz, user=reviewer,
                rating=random.randint(1, 5),
                text=fake.sentence(nb_words=16),
            )
            if has_hidden:
                base_kwargs["is_hidden"] = (random.random() < 0.05)
            if has_created_at:
                base_kwargs["created_at"] = timezone.now() - timedelta(days=random.randint(0, 60), hours=random.randint(0, 23))
            r = Review.objects.create(**filtered_kwargs(Review, **base_kwargs))
            review_objs.append(r)
        hidden_count = sum(1 for r in review_objs if getattr(r, "is_hidden", False))
        self.stdout.write(self.style.SUCCESS(f"Reviews: {len(review_objs)} (hidden: {hidden_count})"))


        # PROMOTIONS (only if model exists)
        if HAS_PROMO:
            promo_fields = field_names(Promotion)

            # Resolve field names dynamically
            f_title = pick_field(promo_fields, "title", "name")
            f_desc  = pick_field(promo_fields, "description", "details", "content")
            f_start = pick_field(promo_fields, "start_date", "starts_at", "start_at", "start")
            f_end   = pick_field(promo_fields, "end_date", "ends_at", "end_at", "end")
            f_active = pick_field(promo_fields, "is_active", "active", "enabled", "status")
            f_slug  = pick_field(promo_fields, "slug")  # <-- NEW

            must_have_dates = bool(f_start) or bool(f_end)

            promo_objs = []
            for _ in range(opts["promos"]):
                biz = random.choice(biz_list)
                title_val = random.choice([
                    "Summer Sale","Buy 1 Get 1","Weekend Deal","Festive Offer","New Customer 15%"
                ])
                start_val = timezone.now() - timedelta(days=random.randint(0, 10))
                end_val   = start_val + timedelta(days=random.randint(5, 30))

                kw = {}
                set_if_present(kw, f_title, title_val)
                set_if_present(kw, f_desc, fake.sentence(nb_words=20))
                set_if_present(kw, f_start, start_val)
                set_if_present(kw, f_end, end_val)
                set_if_present(kw, f_active, True)

                # FK to Business
                if "business" in promo_fields:
                    kw["business"] = biz
                elif "business_id" in promo_fields:
                    kw["business_id"] = biz.id

                # Ensure unique slug if the model has one
                if f_slug:
                    # tie to business to reduce collisions, then uniquify
                    base_text = f"{title_val}-{getattr(biz, 'slug', biz.id)}"
                    kw[f_slug] = unique_model_slug(Promotion, f_slug, base_text)

                # Fallback safety for required dates
                if must_have_dates:
                    for k in ("start_date","starts_at","start_at","start"):
                        if k in promo_fields and k not in kw:
                            kw[k] = start_val
                    for k in ("end_date","ends_at","end_at","end"):
                        if k in promo_fields and k not in kw:
                            kw[k] = end_val

                p = Promotion.objects.create(**filtered_kwargs(Promotion, **kw))
                promo_objs.append(p)

            self.stdout.write(self.style.SUCCESS(f"Promotions: {len(promo_objs)}"))



        # ONCHAIN activity (light)
        vis_reviews = [r for r in review_objs if not getattr(r, "is_hidden", False)]
        for r in vis_reviews:
            if random.random() < 0.3:
                OnChainRecord.objects.get_or_create(
                    kind="SIGNED_REVIEW",
                    review=r,
                    defaults={"business": r.business, "created_at": getattr(r, "created_at", timezone.now()) + timedelta(minutes=5)},
                )

        for b in biz_list:
            owner_wallet_val = getattr(b, "owner_wallet", None)
            if owner_wallet_val and random.random() < 0.4:
                OnChainRecord.objects.create(
                    kind="TX_LINKED",
                    business=b,
                    chain=random.choice(CHAINS),
                    tx_hash=short_hex(64),
                    note=random.choice([
                        "Proof of business ownership",
                        "Posted verification note",
                        "Campaign announcement tx",
                        "Address attestation",
                    ]),
                    created_at=timezone.now() - timedelta(days=random.randint(0, 20)),
                )

        self.stdout.write(self.style.SUCCESS(f"OnChain rows: {OnChainRecord.objects.count()}"))
        self.stdout.write(self.style.SUCCESS("✅ Seeding complete."))
