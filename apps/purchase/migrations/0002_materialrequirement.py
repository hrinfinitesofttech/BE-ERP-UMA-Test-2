# Generated for MaterialRequirement model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purchase', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MaterialRequirement',
            fields=[
                ('id', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('project_id', models.CharField(blank=True, default='', max_length=64)),
                ('job_id', models.CharField(blank=True, default='', max_length=64)),
                ('job_number', models.CharField(blank=True, default='', max_length=64)),
                ('customer_name', models.CharField(blank=True, default='', max_length=200)),
                ('design_job_id', models.CharField(blank=True, default='', max_length=64)),
                ('bom_id', models.CharField(blank=True, default='', max_length=64)),
                ('bom_number', models.CharField(blank=True, default='', max_length=64)),
                ('bom_revision', models.CharField(default='REV-01', max_length=30)),
                ('part_number', models.CharField(blank=True, default='', max_length=100)),
                ('item_code', models.CharField(blank=True, default='', max_length=100)),
                ('item_name', models.CharField(max_length=200)),
                ('material_name', models.CharField(blank=True, default='', max_length=200)),
                ('specification', models.TextField(blank=True, default='')),
                ('category', models.CharField(default='Raw Material', max_length=100)),
                ('required_quantity', models.FloatField(default=0)),
                ('unit_of_measure', models.CharField(default='NOS', max_length=30)),
                ('available_stock', models.FloatField(default=0)),
                ('reserved_stock', models.FloatField(default=0)),
                ('on_order_quantity', models.FloatField(default=0)),
                ('shortage_quantity', models.FloatField(default=0)),
                ('required_by_date', models.CharField(blank=True, default='', max_length=50)),
                ('procurement_type', models.CharField(default='Purchase', max_length=50)),
                ('procurement_status', models.CharField(default='Pending', max_length=50)),
                ('drawing_number', models.CharField(blank=True, default='', max_length=100)),
                ('status', models.CharField(default='shortage', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
