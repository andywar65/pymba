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
    color = models.CharField(max_length=250, default="white",)
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
    color = models.CharField(max_length=250, default="white",)

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

    def get_wall_children(self):
        wall_children = self.get_children().type(PymbaPartitionPage).all()
        return wall_children

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

    def extract_dxf2(self):
        path_to_dxf = os.path.join(settings.MEDIA_ROOT, 'documents', self.dxf_file.filename)
        dxf_f = open(path_to_dxf, encoding = 'utf-8')
        material_gallery=self.material_images.all()
        collection = aframe.parse_dxf(dxf_f, material_gallery)

        path_to_csv = os.path.join(settings.MEDIA_ROOT, 'documents', self.slug + '.csv')
        csv_f = open(path_to_csv, 'w', encoding = 'utf-8',)
        csv_f.write('Num,Layer,Block/Side,Type,Finishing,X,Y,Z,Rx,Ry,Rz,Width,Depth,Height,Weight, Alert \n')

        wall_types = PymbaPartitionPage.objects#how can I restrict to children?TO DO
        wall_finishings = PymbaFinishingPage.objects#how can I restrict to children?TO DO
        output = aframe.make_html(self, collection, csv_f)

        output = {}
        flag = False
        x = 0
        value = 'dummy'
        while value !='ENTITIES':
            key = dxf_f.readline().strip()
            value = dxf_f.readline().strip()
        while value !='ENDSEC':
            key = dxf_f.readline().strip()
            value = dxf_f.readline().strip()
            if flag == 'face':#stores values for 3D faces
                if key == '8':#layer name
                    temp[key] = value
                elif key == '10' or key == '11' or key == '12' or key == '13':#X position
                    temp[key] = float(value)
                elif key == '20' or key == '21' or key == '22' or key == '23':#mirror Y position
                    temp[key] = -float(value)
                elif key == '30' or key == '31' or key == '32' or key == '33':#Z position
                    temp[key] = float(value)
            elif flag == 'block':#stores values for blocks
                if key == '2':#block name
                    temp[key] = value
                if key == '8':#layer name
                    temp[key] = value
                    temp['layer'] = value#sometimes key 8 is replaced, so I need the original layer value
                elif key == '10' or key == '30':#X Z position
                    temp[key] = float(value)
                elif key == '20':#Y position, mirrored
                    temp[key] = -float(value)
                elif key == '50':#Z rotation
                    temp[key] = float(value)
                elif key == '41' or key == '42' or key == '43':#scale values
                    temp[key] = float(value)
                elif key == '210':#X of OCS unitary vector
                    Az_1 = float(value)
                    P_x = temp['10']
                elif key == '220':#Y of OCS unitary vector
                    Az_2 = float(value)
                    P_y = -temp['20']#reset original value
                elif key == '230':#Z of OCS unitary vector
                    Az_3 = float(value)
                    P_z = temp['30']
                    #arbitrary axis algorithm
                    #see if OCS z vector is close to world Z axis
                    if fabs(Az_1) < (1/64) and fabs(Az_2) < (1/64):
                        W = ('Y', 0, 1, 0)
                    else:
                        W = ('Z', 0, 0, 1)
                    #cross product for OCS x arbitrary vector, normalized
                    Ax_1 = W[2]*Az_3-W[3]*Az_2
                    Ax_2 = W[3]*Az_1-W[1]*Az_3
                    Ax_3 = W[1]*Az_2-W[2]*Az_1
                    Norm = sqrt(pow(Ax_1, 2)+pow(Ax_2, 2)+pow(Ax_3, 2))
                    Ax_1 = Ax_1/Norm
                    Ax_2 = Ax_2/Norm
                    Ax_3 = Ax_3/Norm
                    #cross product for OCS y arbitrary vector, normalized
                    Ay_1 = Az_2*Ax_3-Az_3*Ax_2
                    Ay_2 = Az_3*Ax_1-Az_1*Ax_3
                    Ay_3 = Az_1*Ax_2-Az_2*Ax_1
                    Norm = sqrt(pow(Ay_1, 2)+pow(Ay_2, 2)+pow(Ay_3, 2))
                    Ay_1 = Ay_1/Norm
                    Ay_2 = Ay_2/Norm
                    Ay_3 = Ay_3/Norm
                    #insertion world coordinates from OCS
                    temp['10'] = P_x*Ax_1+P_y*Ay_1+P_z*Az_1
                    temp['20'] = P_x*Ax_2+P_y*Ay_2+P_z*Az_2
                    temp['30'] = P_x*Ax_3+P_y*Ay_3+P_z*Az_3
                    #OCS X vector translated into WCS
                    Ax_1 = ((P_x+cos(radians(temp['50'])))*Ax_1+(P_y+sin(radians(temp['50'])))*Ay_1+P_z*Az_1)-temp['10']
                    Ax_2 = ((P_x+cos(radians(temp['50'])))*Ax_2+(P_y+sin(radians(temp['50'])))*Ay_2+P_z*Az_2)-temp['20']
                    Ax_3 = ((P_x+cos(radians(temp['50'])))*Ax_3+(P_y+sin(radians(temp['50'])))*Ay_3+P_z*Az_3)-temp['30']
                    #cross product for OCS y vector, normalized
                    Ay_1 = Az_2*Ax_3-Az_3*Ax_2
                    Ay_2 = Az_3*Ax_1-Az_1*Ax_3
                    Ay_3 = Az_1*Ax_2-Az_2*Ax_1
                    Norm = sqrt(pow(Ay_1, 2)+pow(Ay_2, 2)+pow(Ay_3, 2))
                    Ay_1 = Ay_1/Norm
                    Ay_2 = Ay_2/Norm
                    Ay_3 = Ay_3/Norm

                    #A-Frame rotation order is Yaw(Z), Pitch(X) and Roll(Y)
                    #thanks for help Marilena Vendittelli and https://www.geometrictools.com/
                    if Ay_3<1:
                        if Ay_3>-1:
                            pitch = asin(Ay_3)
                            yaw = atan2(-Ay_1, Ay_2)
                            roll = atan2(-Ax_3, Az_3)
                        else:
                            pitch = -pi/2
                            yaw = -atan2(Az_1, Ax_1)
                            roll = 0
                    else:
                        pitch = pi/2
                        yaw = atan2(Az_1, Ax_1)
                        roll = 0

                    #Y position, mirrored
                    temp['20'] = -temp['20']
                    #rotations from radians to degrees
                    temp['210'] = degrees(pitch)
                    temp['50'] = degrees(yaw)
                    temp['220'] = -degrees(roll)

            elif flag == 'attrib':#stores values for attributes within block
                if key == '1':#attribute value
                    attr_value = value
                elif key == '2':#attribute key
                    temp[value] = attr_value
                    flag = 'block'#restore block modality

            if key == '0':

                if flag == 'face':#close 3D face
                    #is material set in model?
                    try:
                        material = material_gallery.get(layer = temp['8'])
                        temp['color'] = material.color
                    except:
                        temp['8'] = 'default'
                        temp['color'] = 'white'

                    output[x] = self.make_triangle_1(x, temp)
                    if temp['12']!=temp['13'] or temp['22']!=temp['23'] or temp['32']!=temp['33']:
                        x += 1
                        output[x] = self.make_triangle_2(x, temp)
                    flag = False

                elif value == 'ATTRIB':#start attribute within block
                    attr_value = ''
                    flag = 'attrib'

                elif flag == 'block':#close block
                    #material images are patterns? is material set in model?
                    try:
                        material = material_gallery.get(layer = temp['8'])
                        temp['color'] = material.color
                        if material.pattern:# == True
                            temp['repeat']=True
                    except:
                        temp['8'] = 'default'
                        temp['color'] = 'white'

                    if temp['2'] == '6planes':#left for legacy
                        output[x] = self.make_box(x, temp)

                    elif temp['2'] == 'box' or temp['2'] == 'a-box':
                        output[x] = self.make_box(x, temp)

                    elif temp['2'] == 'cylinder' or temp['2'] == 'a-cylinder':
                        output[x] = self.make_cylinder(x, temp)

                    elif temp['2'] == 'cone' or temp['2'] == 'a-cone':
                        output[x] = self.make_cone(x, temp)

                    elif temp['2'] == 'sphere' or temp['2'] == 'a-sphere':
                        output[x] = self.make_sphere(x, temp)

                    elif temp['2'] == 'circle' or temp['2'] == 'a-circle':
                        output[x] = self.make_circle(x, temp)

                    elif temp['2'] == 'plane' or temp['2'] == 'a-plane' or temp['2'] == 'look-at':
                        output[x] = self.make_plane(x, temp)

                    elif temp['2'] == 'floor':#left for legacy
                        temp['210'] = temp['210'] - 90
                        output[x] = self.make_plane(x, temp)

                    elif temp['2'] == 'ceiling':#left for legacy
                        temp['210'] = temp['210'] + 90
                        output[x] = self.make_plane(x, temp)

                    elif temp['2'] == 'light' or temp['2'] == 'a-light':
                        output[x] = self.make_light(x, temp)

                    elif temp['2'] == 'a-text':
                        output[x] = self.make_text(x, temp)

                    elif temp['2'] == 'a-link':
                        output[x] = self.make_link(x, temp)

                    elif temp['2'] == 'a-wall':
                        output[x] = self.make_wall(x, temp, wall_types, wall_finishings, csv_f)

                    elif temp['2'] == 'a-slab':
                        output[x] = self.make_slab(x, temp, wall_types, wall_finishings, csv_f)

                    flag = False

                if value == '3DFACE':#start 3D face
                    temp = {}#default values
                    flag = 'face'
                    x += 1
                elif value == 'INSERT':#start block
                    temp = {'41': 1, '42': 1, '43': 1, '50': 0, '210': 0, '220': 0, '230': 1,'repeat': False, 'type': '',}#default values
                    flag = 'block'
                    x += 1

        dxf_f.close()
        csv_f.close()

        return output

    def is_repeat(self, repeat, rx, ry):
        if repeat:
            output = f'; repeat:{fabs(float(rx))} {fabs(float(ry))}'
            return output
        else:
            return ';'

    def get_csv_path(self):
        path_to_csv = os.path.join(settings.MEDIA_URL, 'documents', self.slug + '.csv')
        return path_to_csv

    def make_box(self, x, temp):
        outstr = f'<a-entity id="box-{x}-ent" \n'
        outstr += f'position="{temp["10"]} {temp["30"]} {temp["20"]}" \n'
        outstr += f'rotation="{temp["210"]} {temp["50"]} {temp["220"]}">\n'
        outstr += f'<a-box id="box-{x}" \n'
        outstr += f'position="{temp["41"]/2} {temp["43"]/2} {-temp["42"]/2}" \n'
        outstr += f'scale="{fabs(temp["41"])} {fabs(temp["43"])} {fabs(temp["42"])}" \n'
        outstr += 'geometry="'
        try:
            if temp['segments-depth']!='1':
                outstr += f'segments-depth: {temp["segments-depth"]};'
            if temp['segments-height']!='1':
                outstr += f'segments-height: {temp["segments-height"]};'
            if temp['segments-width']!='1':
                outstr += f'segments-width: {temp["segments-width"]};'
            outstr += '" \n'
        except KeyError:
            outstr += '" \n'
        outstr += f'material="src: #image-{temp["8"]}; color: {temp["color"]}'
        outstr += self.is_repeat(temp["repeat"], temp["41"], temp["43"])
        outstr += '">\n</a-box>\n</a-entity>\n'
        return outstr

    def make_cone(self, x, temp):
        outstr = f'<a-entity id="cone-{x}-ent" \n'
        outstr += f'position="{temp["10"]} {temp["30"]} {temp["20"]}" \n'
        outstr += f'rotation="{temp["210"]} {temp["50"]} {temp["220"]}">\n'
        outstr += f'<a-cone id="cone-{x}" \n'
        outstr += f'position="0 {temp["43"]/2} 0" \n'
        if float(temp['43']) < 0:
            outstr += 'rotation="180 0 0">\n'
        outstr += f'scale="{fabs(temp["41"])} {fabs(temp["43"])} {fabs(temp["42"])}" \n'
        outstr += 'geometry="'
        try:
            if temp['open-ended']!='false':
                outstr += 'open-ended: true;'
            if temp['radius-top']!='0':
                outstr += f'radius-top: {temp["radius-top"]};'
            if temp['segments-height']!='18':
                outstr += f'segments-height: {temp["segments-height"]};'
            if temp['segments-radial']!='36':
                outstr += f'segments-radial: {temp["segments-radial"]};'
            if temp['theta-length']!='360':
                outstr += f'theta-length: {temp["theta-length"]};'
            if temp['theta-start']!='0':
                outstr += f'theta-start: {temp["theta-start"]};'
            outstr += '" \n'
        except KeyError:
            outstr += '" \n'
        outstr += f'material="src: #image-{temp["8"]}; color: {temp["color"]}'
        outstr += self.is_repeat(temp["repeat"], temp["41"], temp["43"])
        outstr += '">\n</a-cone>\n</a-entity>\n'
        return outstr

    def make_circle(self, x, temp):
        outstr = f'<a-entity id="circle-{x}-ent" \n'
        outstr += f'position="{temp["10"]} {temp["30"]} {temp["20"]}" \n'
        outstr += f'rotation="{temp["210"]} {temp["50"]} {temp["220"]}">\n'
        outstr += f'<a-circle id="circle-{x}" \n'
        if temp['2'] == 'circle':
            outstr += f'rotation="-90 0 0"\n'
        outstr += f'radius="{fabs(temp["41"])}" \n'
        outstr += 'geometry="'
        try:
            if temp['segments']!='32':
                outstr += f'segments: {temp["segments"]};'
            if temp['theta-length']!='360':
                outstr += f'theta-length: {temp["theta-length"]};'
            if temp['theta-start']!='0':
                outstr += f'theta-start: {temp["theta-start"]};'
            outstr += '" \n'
        except KeyError:
            outstr += '" \n'
        outstr += f'material="src: #image-{temp["8"]}; color: {temp["color"]}'
        outstr += self.is_repeat(temp["repeat"], temp["41"], temp["43"])
        outstr += '">\n</a-circle>\n</a-entity>\n'
        return outstr

    def make_cylinder(self, x, temp):
        outstr = f'<a-entity id="cylinder-{x}-ent" \n'
        outstr += f'position="{temp["10"]} {temp["30"]} {temp["20"]}" \n'
        outstr += f'rotation="{temp["210"]} {temp["50"]} {temp["220"]}">\n'
        outstr += f'<a-cylinder id="cylinder-{x}" \n'
        outstr += f'position="0 {temp["43"]/2} 0" \n'
        if float(temp['43']) < 0:
            outstr += 'rotation="180 0 0">\n'
        outstr += f'scale="{fabs(temp["41"])} {fabs(temp["43"])} {fabs(temp["42"])}" \n'
        outstr += 'geometry="'
        try:
            if temp['open-ended']!='false':
                outstr += 'open-ended: true;'
            if temp['radius-top']!='0':
                outstr += f'radius-top: {temp["radius-top"]};'
            if temp['segments-height']!='18':
                outstr += f'segments-height: {temp["segments-height"]};'
            if temp['segments-radial']!='36':
                outstr += f'segments-radial: {temp["segments-radial"]};'
            if temp['theta-length']!='360':
                outstr += f'theta-length: {temp["theta-length"]};'
            if temp['theta-start']!='0':
                outstr += f'theta-start: {temp["theta-start"]};'
            outstr += '" \n'
        except KeyError:
            outstr += '" \n'
        outstr += f'material="src: #image-{temp["8"]}; color: {temp["color"]}'
        outstr += self.is_repeat(temp["repeat"], temp["41"], temp["43"])
        outstr += '">\n</a-cylinder>\n</a-entity>\n'
        return outstr

    def make_sphere(self, x, temp):
        outstr = f'<a-entity id="sphere-{x}-ent" \n'
        outstr += f'position="{temp["10"]} {temp["30"]} {temp["20"]}" \n'
        outstr += f'rotation="{temp["210"]} {temp["50"]} {temp["220"]}">\n'
        outstr += f'<a-sphere id="sphere-{x}" \n'
        outstr += f'position="0 {temp["43"]} 0" \n'
        if float(temp['43']) < 0:
            outstr += 'rotation="180 0 0">\n'
        outstr += f'scale="{fabs(temp["41"])} {fabs(temp["43"])} {fabs(temp["42"])}" \n'
        outstr += 'geometry="'
        try:
            if temp['phi-length']!='360':
                outstr += f'phi-length: {temp["phi-length"]};'
            if temp['phi-start']!='0':
                outstr += f'phi-start: {temp["phi-start"]};'
            if temp['segments-height']!='18':
                outstr += f'segments-height: {temp["segments-height"]};'
            if temp['segments-width']!='36':
                outstr += f'segments-width: {temp["segments-width"]};'
            if temp['theta-length']!='180':
                outstr += f'theta-length: {temp["theta-length"]};'
            if temp['theta-start']!='0':
                outstr += f'theta-start: {temp["theta-start"]};'
            outstr += '" \n'
        except KeyError:
            outstr += '" \n'
        outstr += f'material="src: #image-{temp["8"]}; color: {temp["color"]}'
        outstr += self.is_repeat(temp["repeat"], temp["41"], temp["43"])
        outstr += '">\n</a-sphere>\n</a-entity>\n'
        return outstr

    def make_plane(self, x, temp):
        outstr = f'<a-entity id="plane-{x}-ent" \n'
        outstr += f'position="{temp["10"]} {temp["30"]} {temp["20"]}" \n'
        outstr += f'rotation="{temp["210"]} {temp["50"]} {temp["220"]}">\n'
        outstr += f'<a-plane id="plane-{x}" \n'
        if temp['2'] == 'look-at':#if it's a look at, it is centered and looks at the camera foot
            outstr += f'position="0 {temp["43"]/2} 0" \n'
            outstr += 'look-at="#camera-foot" \n'
        elif temp['2'] == 'ceiling':#if it's a ceiling, correct position
            outstr += f'position="{temp["41"]/2} {-temp["43"]/2} 0" \n'
        else:#insertion is at corner
            outstr += f'position="{temp["41"]/2} {temp["43"]/2} 0" \n'
        outstr += f'width="{fabs(temp["41"])}" height="{fabs(temp["43"])}" \n'
        outstr += 'geometry="'
        try:
            if temp['segments-height']!='1':
                outstr += f'segments-height: {temp["segments-height"]};'
            if temp['segments-width']!='1':
                outstr += f'segments-width: {temp["segments-width"]};'
            outstr += '" \n'
        except KeyError:
            outstr += '" \n'
        outstr += f'material="src: #image-{temp["8"]}; color: {temp["color"]}'
        outstr += self.is_repeat(temp["repeat"], temp["41"], temp["43"])
        outstr += '">\n</a-plane>\n</a-entity>\n'
        return outstr

    def make_text(self, x, temp):
        outstr = f'<a-entity id="text-{x}" \n'
        outstr += f'position="{temp["10"]} {temp["30"]} {temp["20"]}" \n'
        outstr += f'rotation="{temp["210"]} {temp["50"]} {temp["220"]}"\n'
        outstr += f'text="width: {temp["41"]}; align: {temp["align"]}; color: {temp["color"]}; '
        outstr += f'value: {temp["text"]}; wrap-count: {temp["wrap-count"]}; '
        outstr += '">\n</a-entity>\n'
        return outstr

    def make_link(self, x, temp):
        outstr = f'<a-link id="link-{x}" \n'
        outstr += f'position="{temp["10"]} {temp["30"]} {temp["20"]}" \n'
        outstr += f'rotation="{temp["210"]} {temp["50"]} {temp["220"]}"\n'
        outstr += f'scale="{temp["41"]} {temp["43"]} {temp["42"]}"\n'
        if temp['tree'] == 'parent':
            target = self.get_parent()
        elif temp['tree'] == 'child':
            target = self.get_first_child()
        elif temp['tree'] == 'previous' or temp['tree'] == 'prev':
            target = self.get_prev_sibling()
        else:#we default to next sibling
            target = self.get_next_sibling()
        if target:
            outstr += f'href="{target.url}"\n'
            outstr += f'title="{temp["title"]}" color="{temp["color"]}" on="click"\n'
            eq_image = target.specific.equirectangular_image
            if eq_image:
                outstr += f'image="{eq_image.file.url}"'
            else:
                outstr += 'image="#default-sky"'
            outstr += '>\n</a-link>\n'
            return outstr
        else:
            return ''

    def make_triangle_1(self, x, temp):
        outstr = f'<a-triangle id="triangle-{x}" \n'
        outstr += f'geometry="vertexA:{temp["10"]} {temp["30"]} {temp["20"]}; \n'
        outstr += f'vertexB:{temp["11"]} {temp["31"]} {temp["21"]}; \n'
        outstr += f'vertexC:{temp["12"]} {temp["32"]} {temp["22"]}" \n'
        outstr += f'material="src: #image-{temp["8"]}; color: {temp["color"]}; '
        if self.double_face:
            outstr += 'side: double; '
        outstr += '">\n</a-triangle> \n'
        return outstr

    def make_triangle_2(self, x, temp):
        outstr = f'<a-triangle id="triangle-{x}" \n'
        outstr += f'geometry="vertexA:{temp["10"]} {temp["30"]} {temp["20"]}; \n'
        outstr += f'vertexB:{temp["12"]} {temp["32"]} {temp["22"]}; \n'
        outstr += f'vertexC:{temp["13"]} {temp["33"]} {temp["23"]}" \n'
        outstr += f'material="src: #image-{temp["8"]}; color: {temp["color"]}; '
        if self.double_face:
            outstr += 'side: double; '
        outstr += '">\n</a-triangle> \n'
        return outstr

    def make_light(self, x, temp):
        outstr = f'<a-entity id="light-{x}" \n'
        outstr += f'position="{temp["10"]} {temp["30"]} {temp["20"]}" \n'
        outstr += f'rotation="{temp["210"]} {temp["50"]} {temp["220"]}"\n'
        try:
            if temp['type'] == 'ambient':
                outstr += f'light="type: ambient; color: {temp["color"]}; intensity: {temp["intensity"]}; '
                outstr += '">\n</a-entity>\n'#close light entity
            elif temp['type'] == 'point':
                outstr += f'light="type: point; color: {temp["color"]}; intensity: {temp["intensity"]}; '
                outstr += f'decay: {temp["decay"]}; distance: {temp["distance"]}; '
                if self.shadows:
                    outstr += 'castShadow: true; '
                outstr += '"> \n</a-entity>\n'#close light entity
            elif temp['type'] == 'spot':
                outstr += f'light="type: spot; color: {temp["color"]}; intensity: {temp["intensity"]}; '
                outstr += f'decay: {temp["decay"]}; distance: {temp["distance"]}; '
                outstr += f'angle: {temp["angle"]}; penumbra: {temp["penumbra"]}; '
                if self.shadows:
                    outstr += 'castShadow: true; '
                outstr += f'target: #light-{x}-target;"> \n'
                outstr += f'<a-entity id="light-{x}-target" position="0 -1 0"> </a-entity> \n</a-entity> \n'#close light entity
            else:#defaults to directional
                outstr += f'light="type: directional; color: {temp["color"]}; intensity: {temp["intensity"]}; '
                if self.shadows:
                    outstr += 'castShadow: true; '
                outstr += f'target: #light-{x}-target;"> \n'
                outstr += f'<a-entity id="light-{x}-target" position="0 -1 0"> </a-entity> \n</a-entity> \n'#close light entity
        except KeyError:#default if no light type is set
            outstr += 'light="type: point; intensity: 0.75; distance: 50; decay: 2; '
            if self.shadows:
                outstr += 'castShadow: true;'
            outstr += '">\n</a-entity>\n'#close light entity
        return outstr

    def make_wall(self, x, temp, wall_types, wall_finishings, csv_f):
        temp['alert'] = 'None'#outside the try or they could crash file write
        wall_weight = 0
        if temp['type']:
            try:
                wall_type = wall_types.get(title = temp['type'])
                wall_thickness = 0
                fixed_thickness = True
                unit_weight = 0
                zero_weight = 0
                for wall_layer in wall_type.part_layers.all():
                    wall_layer_thickness = fabs(float(wall_layer.thickness))
                    wall_layer_weight = fabs(float(wall_layer.weight))
                    if wall_layer_thickness == 0:
                        fixed_thickness = False
                        zero_weight = wall_layer_weight
                    wall_thickness += wall_layer_thickness
                    unit_weight += wall_layer_thickness/100 * wall_layer_weight
                unit_weight += (fabs(temp['42']) - wall_thickness/100) * zero_weight#add eventual zero thickness layer
                wall_weight = unit_weight * fabs(temp['41']) * fabs(temp['43'])#actual wall size
                if wall_thickness and fixed_thickness and fabs(temp['42']) != wall_thickness/100:
                    temp['alert'] = 'Different than Wall Type'
                elif fabs(temp['42']) < wall_thickness/100:
                    temp['alert'] = 'Wall too thin'
                else:
                    if wall_type.image:
                        temp['8'] = 'wall-' + wall_type.title
                    temp['color'] = wall_type.color
                    temp['repeat']=False
                    if wall_type.pattern:# == True
                        temp['repeat']=True
            except:
                pass
        #writing to csv file
        csv_f.write(f'{x},{temp["layer"]},{temp["2"]},{temp["type"]},-,{temp["10"]},{-temp["20"]},{temp["30"]},')
        csv_f.write(f'{temp["210"]},{-temp["220"]},{temp["50"]},{temp["41"]},{temp["42"]},{temp["43"]},{wall_weight},{temp["alert"]} \n')
        #start wall entity
        outstr = f'<a-entity id="wall-{x}-ent" \n'
        outstr += f'position="{temp["10"]} {temp["30"]} {temp["20"]}" \n'
        outstr += f'rotation="{temp["210"]} {temp["50"]} {temp["220"]}">\n'
        if temp['alert'] == 'None':#we have 6 planes, not a box
            #wall top
            outstr += f'<a-plane id="wall-{x}-top" \n'
            outstr += f'position="{temp["41"]/2} {temp["43"]} {-temp["42"]/2}" \n'
            if temp['43'] < 0:
                outstr += f'rotation="90 0 0" \n'
            else:
                outstr += f'rotation="-90 0 0" \n'
            outstr += f'width="{fabs(temp["41"])}" height="{fabs(temp["42"])}" \n'
            outstr += f'material="src: #image-{temp["8"]}; color: {temp["color"]}'
            outstr += self.is_repeat(temp["repeat"], temp["41"], temp["42"])
            outstr += '">\n</a-plane> \n'
            #wall bottom
            outstr += f'<a-plane id="wall-{x}-bottom" \n'
            outstr += f'position="{temp["41"]/2} 0 {-temp["42"]/2}" \n'
            if temp['43'] < 0:
                outstr += f'rotation="-90 0 0" \n'
            else:
                outstr += f'rotation="90 0 0" \n'
            outstr += f'width="{fabs(temp["41"])}" height="{fabs(temp["42"])}" \n'
            outstr += f'material="src: #image-{temp["8"]}; color: {temp["color"]}'
            outstr += self.is_repeat(temp["repeat"], temp["41"], temp["42"])
            outstr += '">\n</a-plane> \n'

            #wall inside
            outstr += f'<a-entity id="wall-{x}-in-ent" \n'
            outstr += f'position="{temp["41"]/2} 0 0" \n'
            if temp['42'] < 0:
                outstr += 'rotation="0 180 0"> \n'
            else:
                outstr += '> \n'
            side = 'in'
            width = temp['41']
            outstr += self.make_wall_finishing(x, temp, wall_finishings, width, side, csv_f)
            outstr += '</a-entity> \n'

            #wall outside
            outstr += f'<a-entity id="wall-{x}-out-ent" \n'
            outstr += f'position="{temp["41"]/2} 0 {-temp["42"]}" \n'
            if temp['42'] > 0:
                outstr += 'rotation="0 180 0"> \n'
            else:
                outstr += '> \n'
            side = 'out'
            outstr += self.make_wall_finishing(x, temp, wall_finishings, width, side, csv_f)
            outstr += '</a-entity> \n'

            #wall left
            outstr += f'<a-entity id="wall-{x}-left-ent" \n'
            outstr += f'position="0 0 {-temp["42"]/2}" \n'
            if temp['41'] > 0:
                outstr += 'rotation="0 -90 0"> \n'
            else:
                outstr += 'rotation="0 90 0"> \n'
            side = 'left'
            width = temp['42']
            outstr += self.make_wall_finishing(x, temp, wall_finishings, width, side, csv_f)
            outstr += '</a-entity> \n'

            #wall right
            outstr += f'<a-entity id="wall-{x}-right-ent" \n'
            outstr += f'position="{temp["41"]} 0 {-temp["42"]/2}" \n'
            if temp['41'] > 0:
                outstr += 'rotation="0 90 0"> \n'
            else:
                outstr += 'rotation="0 -90 0"> \n'
            side = 'right'
            outstr += self.make_wall_finishing(x, temp, wall_finishings, width, side, csv_f)
            outstr += '</a-entity> \n'
            outstr += '</a-entity>\n'

        else:#there is an alert, the wall gets painted red
            outstr += f'<a-box id="wall-{x}-alert" \n'
            outstr += f'position="{temp["41"]/2} {temp["43"]/2} {-temp["42"]/2}" \n'
            outstr += f'scale="{fabs(temp["41"])} {fabs(temp["43"])} {fabs(temp["42"])}" \n'
            outstr += 'material="color: red;'
            outstr += '">\n</a-box>\n </a-entity>\n'

        return outstr

    def make_wall_finishing(self, x, temp, wall_finishings, width, side, csv_f):
        try:
            wall_finishing = wall_finishings.get(title = temp[side])
            tiling_height = fabs(float(wall_finishing.tiling_height))/100*temp['43']/fabs(temp['43'])
            skirting_height = fabs(float(wall_finishing.skirting_height))/100*temp['43']/fabs(temp['43'])
            if tiling_height:
                if fabs(tiling_height) > fabs(temp['43']):
                    tiling_height = temp['43']
                if fabs(skirting_height) > fabs(tiling_height):
                    skirting_height = tiling_height
                tiling_height = tiling_height - skirting_height
            elif skirting_height:
                if fabs(skirting_height) > fabs(temp['43']):
                    skirting_height = temp['43']
            wall_height = temp['43'] - tiling_height - skirting_height
            outstr = f'<a-plane id="wall-{x}-{side}" \n'
            outstr += f'position="0 {wall_height/2+tiling_height+skirting_height} 0" \n'
            outstr += f'width="{fabs(width)}" height="{fabs(wall_height)}" \n'
            outstr += f'material="src: #image-finishing-{wall_finishing.title}; color: {wall_finishing.color}'
            outstr += self.is_repeat(wall_finishing.pattern, width, wall_height)
            outstr += '">\n</a-plane> \n'
            csv_f.write(f'{x},{temp["layer"]},a-wall/{side},{wall_finishing.title},Wall,-,-,-,-,-,-,{width},-,{wall_height},-,- \n')
            outstr += f'<a-plane id="wall-{x}-{side}-tiling" \n'
            outstr += f'position="0 {tiling_height/2+skirting_height} 0" \n'
            outstr += f'width="{fabs(width)}" height="{fabs(tiling_height)}" \n'
            outstr += f'material="src: #image-tiling-{wall_finishing.title}; color: {wall_finishing.tiling_color}'
            outstr += self.is_repeat(wall_finishing.tiling_pattern, width, tiling_height)
            outstr += '">\n</a-plane> \n'
            csv_f.write(f'{x},{temp["layer"]},a-wall/{side},{wall_finishing.title},Tiling,-,-,-,-,-,-,{width},-,{tiling_height},-,- \n')
            outstr += f'<a-plane id="wall-{x}-{side}-skirting" \n'
            outstr += f'position="0 {skirting_height/2} 0" \n'
            outstr += f'width="{fabs(width)}" height="{fabs(skirting_height)}" \n'
            outstr += f'material="src: #image-skirting-{wall_finishing.title}; color: {wall_finishing.skirting_color}'
            outstr += self.is_repeat(wall_finishing.skirting_pattern, width, skirting_height)
            outstr += '">\n</a-plane> \n'
            csv_f.write(f'{x},{temp["layer"]},a-wall/{side},{wall_finishing.title},Skirting,-,-,-,-,-,-,{width},-,{skirting_height},-,- \n')
        except:
            outstr = f'<a-plane id="wall-{x}-{side}" \n'
            outstr += f'position="0 {temp["43"]/2} 0" \n'
            outstr += f'width="{fabs(width)}" height="{fabs(temp["43"])}" \n'
            outstr += f'material="src: #image-{temp["8"]}; color: {temp["color"]}'
            outstr += self.is_repeat(temp["repeat"], width, temp["43"])
            outstr += '">\n</a-plane> \n'
        return outstr

    def make_slab(self, x, temp, slab_types, slab_finishings, csv_f):
        temp['alert'] = 'None'#outside the try or they could crash file write
        slab_weight = 0
        if temp['type']:
            try:
                slab_type = slab_types.get(title = temp['type'])
                slab_thickness = 0
                fixed_thickness = True
                unit_weight = 0
                zero_weight = 0
                for slab_layer in slab_type.part_layers.all():
                    slab_layer_thickness = fabs(float(slab_layer.thickness))
                    slab_layer_weight = fabs(float(slab_layer.weight))
                    if slab_layer_thickness == 0:
                        fixed_thickness = False
                        zero_weight = slab_layer_weight
                    slab_thickness += slab_layer_thickness
                    unit_weight += slab_layer_thickness/100 * slab_layer_weight
                unit_weight += (fabs(temp['43']) - slab_thickness/100) * zero_weight#add eventual zero thickness layer
                slab_weight = unit_weight * fabs(temp['41']) * fabs(temp['42'])#actual slab size
                if slab_thickness and fixed_thickness and fabs(temp['43']) != slab_thickness/100:
                    temp['alert'] = 'Different than Wall/Slab Type'
                elif fabs(temp['43']) < slab_thickness/100:
                    temp['alert'] = 'Slab too thin'
                else:
                    if slab_type.image:
                        temp['8'] = 'wall-' + slab_type.title
                    temp['color'] = slab_type.color
                    temp['repeat']=False
                    if slab_type.pattern:# == True
                        temp['repeat']=True
            except:
                pass
        #writing to csv file
        csv_f.write(f'{x},{temp["layer"]},{temp["2"]},{temp["type"]},-,{temp["10"]},{-temp["20"]},{temp["30"]},')
        csv_f.write(f'{temp["210"]},{-temp["220"]},{temp["50"]},{temp["41"]},{temp["42"]},{temp["43"]},{slab_weight},{temp["alert"]} \n')
        #start slab entity
        outstr = f'<a-entity id="slab-{x}-ent" \n'
        outstr += f'position="{temp["10"]} {temp["30"]} {temp["20"]}" \n'
        outstr += f'rotation="{temp["210"]} {temp["50"]} {temp["220"]}">\n'
        if temp['alert'] == 'None':#we have 6 planes, not a box
            #slab top (floor)
            outstr += f'<a-entity id="slab-{x}-floor-ent" \n'
            outstr += f'position="{temp["41"]/2} 0 {-temp["42"]/2}" \n'
            if temp['43'] < 0:
                outstr += f'rotation="90 0 0"> \n'
            else:
                outstr += f'rotation="-90 0 0"> \n'
            side = 'floor'
            outstr += self.make_slab_finishing(x, temp, slab_finishings, side, csv_f)
            outstr += '</a-entity> \n'

            #slab bottom (ceiling)
            outstr += f'<a-entity id="slab-{x}-ceiling-ent" \n'
            outstr += f'position="{temp["41"]/2} {-temp["43"]} {-temp["42"]/2}" \n'
            if temp['43'] < 0:
                outstr += f'rotation="-90 0 0"> \n'
            else:
                outstr += f'rotation="90 0 0"> \n'
            side = 'ceiling'
            outstr += self.make_slab_finishing(x, temp, slab_finishings, side, csv_f)
            outstr += '</a-entity> \n'

            #slab front
            outstr += f'<a-plane id="slab-{x}-front" \n'
            outstr += f'position="{temp["41"]/2} {-temp["43"]/2} 0" \n'
            if temp['42'] < 0:
                outstr += 'rotation="0 180 0" \n'
            outstr += f'width="{fabs(temp["41"])}" height="{fabs(temp["43"])}" \n'
            outstr += f'material="src: #image-{temp["8"]}; color: {temp["color"]}'
            outstr += self.is_repeat(temp["repeat"], temp["41"], temp["43"])
            outstr += '">\n</a-plane> \n'

            #slab back
            outstr += f'<a-plane id="slab-{x}-back" \n'
            outstr += f'position="{temp["41"]/2} {-temp["43"]/2} {-temp["42"]}" \n'
            if temp['42'] > 0:
                outstr += 'rotation="0 180 0" \n'
            outstr += f'width="{fabs(temp["41"])}" height="{fabs(temp["43"])}" \n'
            outstr += f'material="src: #image-{temp["8"]}; color: {temp["color"]}'
            outstr += self.is_repeat(temp["repeat"], temp["41"], temp["43"])
            outstr += '">\n</a-plane> \n'

            #slab left
            outstr += f'<a-plane id="slab-{x}-left" \n'
            outstr += f'position="0 {-temp["43"]/2} {-temp["42"]/2}" \n'
            if temp['41'] > 0:
                outstr += 'rotation="0 -90 0" \n'
            else:
                outstr += 'rotation="0 90 0" \n'
            outstr += f'width="{fabs(temp["42"])}" height="{fabs(temp["43"])}" \n'
            outstr += f'material="src: #image-{temp["8"]}; color: {temp["color"]}'
            outstr += self.is_repeat(temp["repeat"], temp["42"], temp["43"])
            outstr += '">\n</a-plane> \n'

            #slab right
            outstr += f'<a-plane id="slab-{x}-right" \n'
            outstr += f'position="{temp["41"]} {-temp["43"]/2} {-temp["42"]/2}" \n'
            if temp['41'] > 0:
                outstr += 'rotation="0 90 0" \n'
            else:
                outstr += 'rotation="0 -90 0" \n'
            outstr += f'width="{fabs(temp["42"])}" height="{fabs(temp["43"])}" \n'
            outstr += f'material="src: #image-{temp["8"]}; color: {temp["color"]}'
            outstr += self.is_repeat(temp["repeat"], temp["42"], temp["43"])
            outstr += '">\n</a-plane> \n </a-entity>\n'

        else:#there is an alert, the slab gets painted red
            outstr += f'<a-box id="slab-{x}-alert" \n'
            outstr += f'position="{temp["41"]/2} {-temp["43"]/2} {-temp["42"]/2}" \n'
            outstr += f'scale="{fabs(temp["41"])} {fabs(temp["43"])} {fabs(temp["42"])}" \n'
            outstr += 'material="color: red;'
            outstr += '">\n</a-box>\n </a-entity>\n'

        return outstr

    def make_slab_finishing(self, x, temp, slab_finishings, side, csv_f):
        outstr = f'<a-plane id="slab-{x}-{side}" \n'
        outstr += f'width="{fabs(temp["41"])}" height="{fabs(temp["42"])}" \n'
        try:
            slab_finishing = slab_finishings.get(title = temp[side])
            outstr += f'material="src: #image-finishing-{slab_finishing.title}; color: {slab_finishing.color}'
            outstr += self.is_repeat(slab_finishing.pattern, temp["41"], temp["42"])
            csv_f.write(f'{x},{temp["layer"]},a-slab/{side},{slab_finishing.title},-,-,-,-,-,-,-,{temp["41"]},{temp["42"]},-,-,- \n')
        except:
            outstr += f'material="src: #image-{temp["8"]}; color: {temp["color"]}'
            outstr += self.is_repeat(temp["repeat"], temp["41"], temp["42"])
        outstr += '">\n</a-plane> \n'
        return outstr

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