#!/usr/bin/env python
import os
import sys
import random
import string
import argparse
from datetime import datetime

# --- Point to your settings module ---
# Adjust this if your settings module path differs
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "patriot.settings")

import django
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.text import slugify

# Your model (app path based on your project)
# If your app path is different, adjust:
from apps.directory.models import Business  # <- change if your app label is different

# Try to use Faker if available; fall back to simple generators
try:
    from faker import Faker
    fake = Faker()
    HAS_FAKER = True
except Exception:
    fake = None
    HAS_FAKER = False

CATEGORIES = [
    "Restaurant", "Cafe", "Bakery", "Grocery", "Bookstore", "Salon", "Gym",
    "Pharmacy", "Mechanic", "Electronics", "Pet Care", "Clothing",
    "Consulting", "Accounting", "Software", "Legal", "Real Estate"
]

def rand_word(n=6):
    return "".join(random.choices(string.ascii_lowercase, k=n))

def gen_name():
    if HAS_FAKER:
        return f"{fake.company()} {random.choice(['LLC','Inc','Co','Group',''])}".strip()
    return f"{random.choice(['Alpha','Nova','Prime','Apex','Atlas','Vertex'])} {random.choice(['Tech','Foods','Works','Solutions','Outlet','Studio'])}"

def gen_desc():
    if HAS_FAKER:
        return fake.paragraph(nb_sentences=3)
    return "We provide great service and quality products for our local community."

def gen_address():
    if HAS_FAKER:
        return fake.address().replace("\n", ", ")
    return f"{random.randint(10, 999)} Main St, Springfield"

def gen_phone():
    if HAS_FAKER:
        return fake.phone_number()
    return f"+1-{random.randint(200,999)}-{random.randint(200,999)}-{random.randint(1000,9999)}"

def gen_website(name):
    base = slugify(name).replace("-", "")
    tld = random.choice(["com", "net", "org", "io"])
    return f"https://www.{base[:15] or 'biz'}.{tld}"

def unique_slug(base):
    """
    Ensure slug uniqueness against Business.slug unique constraint.
    """
    s = slugify(base)[:210]  # keep room for suffix
    if not s:
        s = rand_word(8)
    candidate = s
    i = 2
    while Business.objects.filter(slug=candidate).exists():
        suffix = f"-{i}"
        candidate = f"{s[:(220 - len(suffix))]}{suffix}"
        i += 1
    return candidate

def get_or_create_owner(username="demo_owner", email="demo@example.com", password="demo1234"):
    User = get_user_model()
    user, created = User.objects.get_or_create(
        username=username,
        defaults={"email": email}
    )
    # If newly created or missing password, set one
    if created or not user.has_usable_password():
        user.set_password(password)
        user.save()
    return user

@transaction.atomic
def seed_businesses(count=50, with_owner=True, owner_username="demo_owner"):
    """
    Create `count` Business rows. If with_owner=True, attach to demo user.
    """
    owner = get_or_create_owner(owner_username) if with_owner else None

    created = 0
    for _ in range(count):
        name = gen_name()
        category = random.choice(CATEGORIES)
        description = gen_desc()
        address = gen_address()
        phone = gen_phone()
        website = gen_website(name)
        slug = unique_slug(name)

        Business.objects.create(
            name=name,
            category=category,
            description=description,
            address=address,
            phone=phone,
            website=website,
            slug=slug,
            owner=owner
        )
        created += 1

    return created

def main():
    parser = argparse.ArgumentParser(description="Seed dummy Business data.")
    parser.add_argument("--count", type=int, default=50, help="How many businesses to create (default: 50)")
    parser.add_argument("--no-owner", action="store_true", help="Do not set an owner on created businesses")
    parser.add_argument("--owner", type=str, default="demo_owner", help="Username for the owner (default: demo_owner)")
    parser.add_argument("--reset", action="store_true", help="Delete all Business rows before seeding")
    args = parser.parse_args()

    if args.reset:
        n = Business.objects.count()
        Business.objects.all().delete()
        print(f"Deleted {n} existing Business rows.")

    created = seed_businesses(
        count=args.count,
        with_owner=(not args.no_owner),
        owner_username=args.owner
    )
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Created {created} businesses.")

if __name__ == "__main__":
    random.seed(42)
    main()
