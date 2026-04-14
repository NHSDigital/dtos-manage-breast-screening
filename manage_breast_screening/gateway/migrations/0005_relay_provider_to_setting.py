import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinics", "0001_squashed_0021_alter_clinicstatus_options"),
        ("gateway", "0004_add_image_failed_status"),
    ]

    operations = [
        # Add the new FK as nullable so existing rows don't need a default
        migrations.AddField(
            model_name="relay",
            name="setting",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="clinics.setting",
            ),
        ),
        # Remove the old FK
        migrations.RemoveField(
            model_name="relay",
            name="provider",
        ),
        # Make setting non-nullable now that provider is gone
        migrations.AlterField(
            model_name="relay",
            name="setting",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="clinics.setting",
            ),
        ),
    ]
