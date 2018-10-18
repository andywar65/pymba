import os
from pymba import aframe

from django import forms
from django.db import models
from django.conf import settings

from modelcluster.fields import ParentalKey

from wagtail.core.models import Page, Orderable
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index
from wagtail.documents.models import Document
from wagtail.documents.edit_handlers import DocumentChooserPanel

class PymbaFinishingPage(Page):
    intro = models.CharField(max_length=250, null=True, blank=True, help_text="Finishing description",)
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete = models.SET_NULL,
        related_name = '+',
        help_text="Sets the finishing general appearance",
        )
    pattern = models.BooleanField(default=False, help_text="Is it a 1x1 meter pattern?",)
    color = models.CharField(max_length=250, null=True, blank=True, help_text="Accepts hex (#ffffff) or HTML color",)
    tiling_height = models.CharField(max_length=250, default="0", help_text="Tiling height from floor in cm",)
    tiling_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete = models.SET_NULL,
        related_name = '+',
        help_text="Sets the tiling general appearance",
        )
    tiling_pattern = models.BooleanField(default=False,  help_text="Is it a 1x1 meter pattern?",)
    tiling_color = models.CharField(max_length=250, default="white", help_text="Accepts hex (#ffffff) or HTML color",)
    skirting_height = models.CharField(max_length=250, default="0", help_text="Skirting height from floor in cm",)
    skirting_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete = models.SET_NULL,
        related_name = '+',
        help_text="Sets the skirting general appearance",
        )
    skirting_pattern = models.BooleanField(default=False,  help_text="Is it a 1x1 meter pattern?",)
    skirting_color = models.CharField(max_length=250, default="white", help_text="Accepts hex (#ffffff) or HTML color",)

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
    intro = models.CharField(max_length=250, null=True, blank=True, help_text="Partition description",)
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete = models.SET_NULL,
        related_name = '+',
        help_text="Sets the partition general appearance",
        )
    pattern = models.BooleanField(default=False,  help_text="Is it a 1x1 meter pattern?",)
    color = models.CharField(max_length=250, null=True, blank=True, help_text="Accepts hex (#ffffff) or HTML color",)

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
    material = models.CharField(max_length=250, default="brick", help_text="Material description",)
    thickness = models.CharField(max_length=250, default="0", help_text="In centimeters",)
    weight = models.CharField(max_length=250, default="0", help_text="In kilos per cubic meter",)

    panels = [
        FieldPanel('material'),
        FieldPanel('thickness'),
        FieldPanel('weight'),
    ]

class PymbaPage(Page):
    intro = models.CharField(max_length=250, null=True, blank=True, help_text="Project description",)
    equirectangular_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete = models.SET_NULL,
        related_name = '+',
        help_text="Landscape surrounding your project",
        )
    dxf_file = models.ForeignKey(
        'wagtaildocs.Document',
        null=True,
        on_delete = models.SET_NULL,
        related_name = '+',
        help_text="CAD file of your project",
        )
    shadows = models.BooleanField(default=False, help_text="Want to cast shadows?",)
    fly_camera = models.BooleanField(default=False, help_text="Vertical movement of camera?",)
    double_face = models.BooleanField(default=False, help_text="Planes are visible on both sides?",)

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

        collection = aframe.reference_openings(collection)

        path_to_csv = os.path.join(settings.MEDIA_ROOT, 'documents', self.slug + '.csv')
        csv_f = open(path_to_csv, 'w', encoding = 'utf-8',)
        csv_f.write('Elem,Layer,Block,Surf,Strip,Type,X,Y,Z,Rx,Ry,Rz,Width,Depth,Height,Weight, Alert \n')

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
        help_text="Sets general appearance of material",
    )
    layer = models.CharField(max_length=250, default="0", help_text="Layer name in CAD file",)
    color = models.CharField(max_length=250, default="white", help_text="Accepts hex (#ffffff) or HTML color",)
    pattern = models.BooleanField(default=False, help_text="Is it a 1x1 meter pattern?",)
    invisible = models.BooleanField(default=False, help_text="Hide layer?",)

    panels = [
        FieldPanel('layer'),
        FieldPanel('invisible'),
        ImageChooserPanel('image'),
        FieldPanel('pattern'),
        FieldPanel('color'),
    ]

class PymbaIndexPage(Page):
    introduction = models.TextField(
        help_text='Text to describe the page',
        blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('introduction', classname="full"),
    ]

    # Speficies that only PymbaPage objects can live under this index page
    subpage_types = ['PymbaPage']

    # Defines a method to access the children of the page (e.g. PymbaPage
    # objects).
    def children(self):
        return self.get_children().specific().live()

    # Overrides the context to list all child items, that are live, by the
    # date that they were published
    # http://docs.wagtail.io/en/latest/getting_started/tutorial.html#overriding-context
    def get_context(self, request):
        context = super(PymbaIndexPage, self).get_context(request)
        context['posts'] = PymbaPage.objects.descendant_of(
            self).live().order_by(
            '-first_published_at')
        return context
