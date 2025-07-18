# Generated by Django 5.2.3 on 2025-06-20 15:18

import uuid

import django.db.models.deletion
from django.db import migrations, models


def extract_status(apps, schema_editor):
    Appointment = apps.get_model("participants", "Appointment")
    for appointment in Appointment.objects.all():
        appointment.statuses.create(state=appointment.status)


def revert_extract_status(apps, schema_editor):
    Appointment = apps.get_model("participants", "Appointment")
    for appointment in Appointment.objects.all():
        appointment.status = appointment.statuses.first().state
        appointment.save()


class Migration(migrations.Migration):

    dependencies = [
        ("participants", "0012_alter_appointment_clinic_slot_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="appointment",
            name="status",
            field=models.CharField(
                choices=[
                    ("CONFIRMED", "Confirmed"),
                    ("CANCELLED", "Cancelled"),
                    ("DID_NOT_ATTEND", "Did not attend"),
                    ("CHECKED_IN", "Checked in"),
                    ("SCREENED", "Screened"),
                    ("PARTIALLY_SCREENED", "Partially screened"),
                    ("ATTENDED_NOT_SCREENED", "Attended not screened"),
                ],
                max_length=50,
                null=True,
            ),
        ),
        migrations.CreateModel(
            name="AppointmentStatus",
            fields=[
                (
                    "state",
                    models.CharField(
                        choices=[
                            ("CONFIRMED", "Confirmed"),
                            ("CANCELLED", "Cancelled"),
                            ("DID_NOT_ATTEND", "Did not attend"),
                            ("CHECKED_IN", "Checked in"),
                            ("SCREENED", "Screened"),
                            ("PARTIALLY_SCREENED", "Partially screened"),
                            ("ATTENDED_NOT_SCREENED", "Attended not screened"),
                        ],
                        default="CONFIRMED",
                        max_length=50,
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "appointment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="statuses",
                        to="participants.appointment",
                    ),
                ),
            ],
        ),
        migrations.RunPython(extract_status, revert_extract_status),
        migrations.RemoveField(
            model_name="appointment",
            name="status",
        ),
    ]
