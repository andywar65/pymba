import os
from pymba import aframe

from django import forms
from django.db import models
from django.conf import settings

from modelcluster.fields import ParentalKey

from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtailadmin.edit_handlers import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailsearch import index
from wagtail.wagtaildocs.models import Document
from wagtail.wagtaildocs.edit_handlers import DocumentChooserPanel

class PymbaFinishingPage(Page):
    intro = models.CharField(max_length=250, null=True, blank=True,)
    image = models.ForeignKey(
        'wagtailimages.Image', 
        null=True,
        blank=True,
        on_delete = models.SET_NULL, 
        related_name = '+',
        )
    pattern = models.BooleanField(default=False)
    color = models.CharField(max_length=250, null=True, blank=True,)
    tiling_height = models.CharField(max_length=250, default="0",)
    tiling_image = models.ForeignKey(
        'wagtailimages.Image', 
        null=True,
        blank=True,
        on_delete = models.SET_NULL, 
        related_name = '+',
        )
    tiling_pattern = models.BooleanField(default=False)
    tiling_color = models.CharField(max_length=250, default="white",)
    skirting_height = models.CharField(max_length=250, default="0",)
    skirting_image = models.ForeignKey(
        'wagtailimages.Image', 
        null=True,
        blank=True,
        on_delete = models.SET_NULL, 
        related_name = '+',
        )
    skirting_pattern = models.BooleanField(default=False)
    skirting_color = models.CharField(max_length=250, default="white",)

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        MultiFieldPanel([
            ImageChooserPanel('image'),
            FieldPanel('pattern'),
            FieldPanel('color'),
        ], heading="Appearance"),
        MultiFieldPanel([
            FieldPanel('tiling_height'),
            ImageChooserPanel('tiling_image'),
            FieldPanel('tiling_pattern'),
            FieldPanel('tiling_color'),
        ], heading="Tiling"),
        MultiFieldPanel([
            FieldPanel('skirting_height'),
            ImageChooserPanel('skirting_image'),
            FieldPanel('skirting_pattern'),
            FieldPanel('skirting_color'),
        ], heading="Skirting"),
    ]

class PymbaPartitionPage(Page):
    intro = models.CharField(max_length=250, null=True, blank=True,)
    image = models.ForeignKey(
        'wagtailimages.Image', 
        null=True,
        blank=True,
        on_delete = models.SET_NULL, 
        related_name = '+',
        )
    pattern = models.BooleanField(default=False)
    color = models.CharField(max_length=250, null=True, blank=True,)

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        MultiFieldPanel([
            ImageChooserPanel('image'),
            FieldPanel('pattern'),
            FieldPanel('color'),
        ], heading="Appearance"),
        InlinePanel('part_layers', label="Partition layers",),
    ]

class PymbaPartitionPageLayers(Orderable):
    page = ParentalKey(PymbaPartitionPage, related_name='part_layers')
    material = models.CharField(max_length=250, default="brick",)
    thickness = models.CharField(max_length=250, default="0",)
    weight = models.CharField(max_length=250, default="0",)

    panels = [
        FieldPanel('material'),
        FieldPanel('thickness'),
        FieldPanel('weight'),
    ]

class PymbaPage(Page):
    intro = models.CharField(max_length=250, null=True, blank=True,)
    equirectangular_image = models.ForeignKey(
        'wagtailimages.Image', 
        null=True,
        blank=True,
        on_delete = models.SET_NULL, 
        related_name = '+',
        )
    dxf_file = models.ForeignKey(
        'wagtaildocs.Document', 
        null=True, 
        on_delete = models.SET_NULL,
        related_name = '+',
        )
    shadows = models.BooleanField(default=False)
    fly_camera = models.BooleanField(default=False)
    double_face = models.BooleanField(default=False)

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        DocumentChooserPanel('dxf_file'),
        ImageChooserPanel('equirectangular_image'),
        MultiFieldPanel([
            FieldPanel('shadows'),
            FieldPanel('fly_camera'),
            FieldPanel('double_face'),
        ], heading="Visual settings"),
        InlinePanel('material_images', label="Material Image Gallery",),
    ]

    def get_partition_children(self):
        partition_children = self.get_children().type(PymbaPartitionPage).all()
        return partition_children

    def get_finishing_children(self):
        finishing_children = self.get_children().type(PymbaFinishingPage).all()
        return finishing_children

    def extract_dxf(self):

        path_to_dxf = os.path.join(settings.MEDIA_ROOT, 'documents', self.dxf_file.filename)
        dxf_f = open(path_to_dxf, encoding = 'utf-8')
        material_gallery=self.material_images.all()
        collection = aframe.parse_dxf(dxf_f, material_gallery)
        dxf_f.close()

        path_to_csv = os.path.join(settings.MEDIA_ROOT, 'documents', self.slug + '.csv')
        csv_f = open(path_to_csv, 'w', encoding = 'utf-8',)
        csv_f.write('Num,Layer,Block/Side,Type,Finishing,X,Y,Z,Rx,Ry,Rz,Width,Depth,Height,Weight, Alert \n')

        partitions = PymbaPartitionPage.objects#how can I restrict to children?TO DO
        finishings = PymbaFinishingPage.objects#how can I restrict to children?TO DO
        output = aframe.make_html(self, collection, partitions, finishings, csv_f)
        csv_f.close()

        return output

    def get_csv_path(self):
        path_to_csv = os.path.join(settings.MEDIA_URL, 'documents', self.slug + '.csv')
        return path_to_csv

class PymbaPageMaterialImage(Orderable):
    page = ParentalKey(PymbaPage, related_name='material_images')
    image = models.ForeignKey(
        'wagtailimages.Image', 
        null=True,
        blank=True,
        on_delete = models.SET_NULL, 
        related_name = '+',
    )
    layer = models.CharField(max_length=250, default="0",)
    color = models.CharField(max_length=250, default="white",)
    pattern = models.BooleanField(default=False)

    panels = [
        FieldPanel('layer'),
        ImageChooserPanel('image'),
        FieldPanel('pattern'),
        FieldPanel('color'),
    ]