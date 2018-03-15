from math import radians, sin, cos, asin, degrees, pi, sqrt, pow, fabs, atan2

def parse_dxf(dxf_f, material_gallery):

    output = {}
    flag = False
    x = 0
    value = 'dummy'

    while value !='ENTITIES':
        key = dxf_f.readline().strip()
        value = dxf_f.readline().strip()
        if value=='EOF' or key=='':#security to avoid loops if file is corrupted
            return output

    while value !='ENDSEC':
        key = dxf_f.readline().strip()
        value = dxf_f.readline().strip()
        if value=='EOF' or key=='':#security to avoid loops if file is corrupted
            return output

        if flag == 'face':#stores values for 3D faces
            if key == '8':#layer name
                data[key] = value
            elif key == '10' or key == '11' or key == '12' or key == '13':#X position
                data[key] = float(value)
            elif key == '20' or key == '21' or key == '22' or key == '23':#mirror Y position
                data[key] = -float(value)
            elif key == '30' or key == '31' or key == '32' or key == '33':#Z position
                data[key] = float(value)

        elif flag == 'block':#stores values for blocks
            if key == '2':#block name
                data[key] = value
            if key == '8':#layer name
                data[key] = value
                data['layer'] = value#sometimes key 8 is replaced, so I need the original layer value
            elif key == '10' or key == '30':#X Z position
                data[key] = float(value)
            elif key == '20':#Y position, mirrored
                data[key] = -float(value)
            elif key == '50':#Z rotation
                data[key] = float(value)
            elif key == '41' or key == '42' or key == '43':#scale values
                data[key] = float(value)
            elif key == '210':#X of OCS unitary vector
                Az_1 = float(value)
                P_x = data['10']
            elif key == '220':#Y of OCS unitary vector
                Az_2 = float(value)
                P_y = -data['20']#reset original value
            elif key == '230':#Z of OCS unitary vector
                Az_3 = float(value)
                P_z = data['30']
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
                data['10'] = P_x*Ax_1+P_y*Ay_1+P_z*Az_1
                data['20'] = P_x*Ax_2+P_y*Ay_2+P_z*Az_2
                data['30'] = P_x*Ax_3+P_y*Ay_3+P_z*Az_3
                #OCS X vector translated into WCS
                Ax_1 = ((P_x+cos(radians(data['50'])))*Ax_1+(P_y+sin(radians(data['50'])))*Ay_1+P_z*Az_1)-data['10']
                Ax_2 = ((P_x+cos(radians(data['50'])))*Ax_2+(P_y+sin(radians(data['50'])))*Ay_2+P_z*Az_2)-data['20']
                Ax_3 = ((P_x+cos(radians(data['50'])))*Ax_3+(P_y+sin(radians(data['50'])))*Ay_3+P_z*Az_3)-data['30']
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
                data['20'] = -data['20']
                #rotations from radians to degrees
                data['210'] = degrees(pitch)
                data['50'] = degrees(yaw)
                data['220'] = -degrees(roll)

        elif flag == 'attrib':#stores values for attributes within block
            if key == '1':#attribute value
                attr_value = value
            elif key == '2':#attribute key
                data[value] = attr_value
                flag = 'block'#restore block modality

        if key == '0':

            if flag == 'face':#close 3D face
                data['2'] = '3dface'
                #is material set in model?
                try:
                    material = material_gallery.get(layer = data['8'])
                    data['color'] = material.color
                except:
                    data['8'] = 'default'
                    data['color'] = 'white'

                output[x] = data

                if data['12']!=data['13'] or data['22']!=data['23'] or data['32']!=data['33']:
                    data2 = data.copy()
                    data2['11'] = data['12']
                    data2['21'] = data['22']
                    data2['31'] = data['32']
                    data2['12'] = data['13']
                    data2['22'] = data['23']
                    data2['32'] = data['33']
                    x += 1
                    output[x] = data2

                flag = False

            elif value == 'ATTRIB':#start attribute within block
                attr_value = ''
                flag = 'attrib'

            elif flag == 'block':#close block
                #material images are patterns? is material set in model?
                try:
                    material = material_gallery.get(layer = data['8'])
                    data['color'] = material.color
                    if material.pattern:# == True
                        data['repeat']=True
                except:
                    data['8'] = 'default'
                    data['color'] = 'white'
                output[x] = data

                flag = False

            if value == '3DFACE':#start 3D face
                data = {}#default values
                flag = 'face'
                x += 1

            elif value == 'INSERT':#start block
                data = {'41': 1, '42': 1, '43': 1, '50': 0, '210': 0, '220': 0, '230': 1,'repeat': False, 'type': '',}#default values
                flag = 'block'
                x += 1

    return output

def make_html(self_page, collection, partitions, finishings, csv_f):

    output = {}
    for x, data in collection.items():

        if data['2'] == '3dface':#left for legacy
            output[x] = make_triangle(x, data)

        if data['2'] == '6planes':#left for legacy
            output[x] = make_box(x, data)

        elif data['2'] == 'box' or data['2'] == 'a-box':
            output[x] = make_box(x, data)

        elif data['2'] == 'cylinder' or data['2'] == 'a-cylinder':
            output[x] = make_cylinder(x, data)

        elif data['2'] == 'cone' or data['2'] == 'a-cone':
            output[x] = make_cone(x, data)

        elif data['2'] == 'sphere' or data['2'] == 'a-sphere':
            output[x] = make_sphere(x, data)

        elif data['2'] == 'circle' or data['2'] == 'a-circle':
            output[x] = make_circle(x, data)

        elif data['2'] == 'plane' or data['2'] == 'a-plane' or data['2'] == 'look-at':
            output[x] = make_plane(x, data)

        elif data['2'] == 'floor':#left for legacy
            data['210'] = data['210'] - 90
            output[x] = make_plane(x, data)

        elif data['2'] == 'ceiling':#left for legacy
            data['210'] = data['210'] + 90
            output[x] = make_plane(x, data)

        elif data['2'] == 'light' or data['2'] == 'a-light':
            output[x] = make_light(x, data)

        elif data['2'] == 'a-text':
            output[x] = make_text(x, data)

        elif data['2'] == 'a-link':
            output[x] = make_link(self_page, x, data)

        elif data['2'] == 'a-wall':
            output[x] = make_wall(x, data, partitions, finishings, csv_f)

        elif data['2'] == 'a-slab':
            output[x] = make_slab(x, data, partitions, finishings, csv_f)

    return output

def is_repeat(repeat, rx, ry):
    if repeat:
        output = f'; repeat:{fabs(float(rx))} {fabs(float(ry))}'
        return output
    else:
        return ';'

def make_box(x, data):
    outstr = f'<a-entity id="box-{x}-ent" \n'
    outstr += f'position="{data["10"]} {data["30"]} {data["20"]}" \n'
    outstr += f'rotation="{data["210"]} {data["50"]} {data["220"]}">\n'
    outstr += f'<a-box id="box-{x}" \n'
    outstr += f'position="{data["41"]/2} {data["43"]/2} {-data["42"]/2}" \n'
    outstr += f'scale="{fabs(data["41"])} {fabs(data["43"])} {fabs(data["42"])}" \n'
    outstr += 'geometry="'
    try:
        if data['segments-depth']!='1':
            outstr += f'segments-depth: {data["segments-depth"]};'
        if data['segments-height']!='1':
            outstr += f'segments-height: {data["segments-height"]};'
        if data['segments-width']!='1':
            outstr += f'segments-width: {data["segments-width"]};'
        outstr += '" \n'
    except KeyError:
        outstr += '" \n'
    outstr += f'material="src: #image-{data["8"]}; color: {data["color"]}'
    outstr += is_repeat(data["repeat"], data["41"], data["43"])
    outstr += '">\n</a-box>\n</a-entity>\n'
    return outstr

def make_cone(x, data):
    outstr = f'<a-entity id="cone-{x}-ent" \n'
    outstr += f'position="{data["10"]} {data["30"]} {data["20"]}" \n'
    outstr += f'rotation="{data["210"]} {data["50"]} {data["220"]}">\n'
    outstr += f'<a-cone id="cone-{x}" \n'
    outstr += f'position="0 {data["43"]/2} 0" \n'
    if float(data['43']) < 0:
        outstr += 'rotation="180 0 0">\n'
    outstr += f'scale="{fabs(data["41"])} {fabs(data["43"])} {fabs(data["42"])}" \n'
    outstr += 'geometry="'
    try:
        if data['open-ended']!='false':
            outstr += 'open-ended: true;'
        if data['radius-top']!='0':
            outstr += f'radius-top: {data["radius-top"]};'
        if data['segments-height']!='18':
            outstr += f'segments-height: {data["segments-height"]};'
        if data['segments-radial']!='36':
            outstr += f'segments-radial: {data["segments-radial"]};'
        if data['theta-length']!='360':
            outstr += f'theta-length: {data["theta-length"]};'
        if data['theta-start']!='0':
            outstr += f'theta-start: {data["theta-start"]};'
        outstr += '" \n'
    except KeyError:
        outstr += '" \n'
    outstr += f'material="src: #image-{data["8"]}; color: {data["color"]}'
    outstr += is_repeat(data["repeat"], data["41"], data["43"])
    outstr += '">\n</a-cone>\n</a-entity>\n'
    return outstr

def make_circle(x, data):
    outstr = f'<a-entity id="circle-{x}-ent" \n'
    outstr += f'position="{data["10"]} {data["30"]} {data["20"]}" \n'
    outstr += f'rotation="{data["210"]} {data["50"]} {data["220"]}">\n'
    outstr += f'<a-circle id="circle-{x}" \n'
    if data['2'] == 'circle':
        outstr += f'rotation="-90 0 0"\n'
    outstr += f'radius="{fabs(data["41"])}" \n'
    outstr += 'geometry="'
    try:
        if data['segments']!='32':
            outstr += f'segments: {data["segments"]};'
        if data['theta-length']!='360':
            outstr += f'theta-length: {data["theta-length"]};'
        if data['theta-start']!='0':
            outstr += f'theta-start: {data["theta-start"]};'
        outstr += '" \n'
    except KeyError:
        outstr += '" \n'
    outstr += f'material="src: #image-{data["8"]}; color: {data["color"]}'
    outstr += is_repeat(data["repeat"], data["41"], data["43"])
    outstr += '">\n</a-circle>\n</a-entity>\n'
    return outstr

def make_cylinder(x, data):
    outstr = f'<a-entity id="cylinder-{x}-ent" \n'
    outstr += f'position="{data["10"]} {data["30"]} {data["20"]}" \n'
    outstr += f'rotation="{data["210"]} {data["50"]} {data["220"]}">\n'
    outstr += f'<a-cylinder id="cylinder-{x}" \n'
    outstr += f'position="0 {data["43"]/2} 0" \n'
    if float(data['43']) < 0:
        outstr += 'rotation="180 0 0">\n'
    outstr += f'scale="{fabs(data["41"])} {fabs(data["43"])} {fabs(data["42"])}" \n'
    outstr += 'geometry="'
    try:
        if data['open-ended']!='false':
            outstr += 'open-ended: true;'
        if data['radius-top']!='0':
            outstr += f'radius-top: {data["radius-top"]};'
        if data['segments-height']!='18':
            outstr += f'segments-height: {data["segments-height"]};'
        if data['segments-radial']!='36':
            outstr += f'segments-radial: {data["segments-radial"]};'
        if data['theta-length']!='360':
            outstr += f'theta-length: {data["theta-length"]};'
        if data['theta-start']!='0':
            outstr += f'theta-start: {data["theta-start"]};'
        outstr += '" \n'
    except KeyError:
        outstr += '" \n'
    outstr += f'material="src: #image-{data["8"]}; color: {data["color"]}'
    outstr += is_repeat(data["repeat"], data["41"], data["43"])
    outstr += '">\n</a-cylinder>\n</a-entity>\n'
    return outstr

def make_sphere(x, data):
    outstr = f'<a-entity id="sphere-{x}-ent" \n'
    outstr += f'position="{data["10"]} {data["30"]} {data["20"]}" \n'
    outstr += f'rotation="{data["210"]} {data["50"]} {data["220"]}">\n'
    outstr += f'<a-sphere id="sphere-{x}" \n'
    outstr += f'position="0 {data["43"]} 0" \n'
    if float(data['43']) < 0:
        outstr += 'rotation="180 0 0">\n'
    outstr += f'scale="{fabs(data["41"])} {fabs(data["43"])} {fabs(data["42"])}" \n'
    outstr += 'geometry="'
    try:
        if data['phi-length']!='360':
            outstr += f'phi-length: {data["phi-length"]};'
        if data['phi-start']!='0':
            outstr += f'phi-start: {data["phi-start"]};'
        if data['segments-height']!='18':
            outstr += f'segments-height: {data["segments-height"]};'
        if data['segments-width']!='36':
            outstr += f'segments-width: {data["segments-width"]};'
        if data['theta-length']!='180':
            outstr += f'theta-length: {data["theta-length"]};'
        if data['theta-start']!='0':
            outstr += f'theta-start: {data["theta-start"]};'
        outstr += '" \n'
    except KeyError:
        outstr += '" \n'
    outstr += f'material="src: #image-{data["8"]}; color: {data["color"]}'
    outstr += is_repeat(data["repeat"], data["41"], data["43"])
    outstr += '">\n</a-sphere>\n</a-entity>\n'
    return outstr

def make_plane(x, data):
    outstr = f'<a-entity id="plane-{x}-ent" \n'
    outstr += f'position="{data["10"]} {data["30"]} {data["20"]}" \n'
    outstr += f'rotation="{data["210"]} {data["50"]} {data["220"]}">\n'
    outstr += f'<a-plane id="plane-{x}" \n'
    if data['2'] == 'look-at':#if it's a look at, it is centered and looks at the camera foot
        outstr += f'position="0 {data["43"]/2} 0" \n'
        outstr += 'look-at="#camera-foot" \n'
    elif data['2'] == 'ceiling':#if it's a ceiling, correct position
        outstr += f'position="{data["41"]/2} {-data["43"]/2} 0" \n'
    else:#insertion is at corner
        outstr += f'position="{data["41"]/2} {data["43"]/2} 0" \n'
    outstr += f'width="{fabs(data["41"])}" height="{fabs(data["43"])}" \n'
    outstr += 'geometry="'
    try:
        if data['segments-height']!='1':
            outstr += f'segments-height: {data["segments-height"]};'
        if data['segments-width']!='1':
            outstr += f'segments-width: {data["segments-width"]};'
        outstr += '" \n'
    except KeyError:
        outstr += '" \n'
    outstr += f'material="src: #image-{data["8"]}; color: {data["color"]}'
    outstr += is_repeat(data["repeat"], data["41"], data["43"])
    outstr += '">\n</a-plane>\n</a-entity>\n'
    return outstr

def make_text(x, data):
    outstr = f'<a-entity id="text-{x}" \n'
    outstr += f'position="{data["10"]} {data["30"]} {data["20"]}" \n'
    outstr += f'rotation="{data["210"]} {data["50"]} {data["220"]}"\n'
    outstr += f'text="width: {data["41"]}; align: {data["align"]}; color: {data["color"]}; '
    outstr += f'value: {data["text"]}; wrap-count: {data["wrap-count"]}; '
    outstr += '">\n</a-entity>\n'
    return outstr

def make_link(self_page, x, data):
    outstr = f'<a-link id="link-{x}" \n'
    outstr += f'position="{data["10"]} {data["30"]} {data["20"]}" \n'
    outstr += f'rotation="{data["210"]} {data["50"]} {data["220"]}"\n'
    outstr += f'scale="{data["41"]} {data["43"]} {data["42"]}"\n'
    if data['tree'] == 'parent':
        target = self_page.get_parent()
    elif data['tree'] == 'child':
        target = self_page.get_first_child()
    elif data['tree'] == 'previous' or data['tree'] == 'prev':
        target = self_page.get_prev_sibling()
    else:#we default to next sibling
        target = self_page.get_next_sibling()
    if target:
        outstr += f'href="{target.url}"\n'
        outstr += f'title="{data["title"]}" color="{data["color"]}" on="click"\n'
        eq_image = target.specific.equirectangular_image
        if eq_image:
            outstr += f'image="{eq_image.file.url}"'
        else:
            outstr += 'image="#default-sky"'
        outstr += '>\n</a-link>\n'
        return outstr
    else:
        return ''

def make_triangle(x, data):
    outstr = f'<a-triangle id="triangle-{x}" \n'
    outstr += f'geometry="vertexA:{data["10"]} {data["30"]} {data["20"]}; \n'
    outstr += f'vertexB:{data["11"]} {data["31"]} {data["21"]}; \n'
    outstr += f'vertexC:{data["12"]} {data["32"]} {data["22"]}" \n'
    outstr += f'material="src: #image-{data["8"]}; color: {data["color"]}; '
    if self.double_face:
        outstr += 'side: double; '
    outstr += '">\n</a-triangle> \n'
    return outstr

def make_light(x, data):
    outstr = f'<a-entity id="light-{x}" \n'
    outstr += f'position="{data["10"]} {data["30"]} {data["20"]}" \n'
    outstr += f'rotation="{data["210"]} {data["50"]} {data["220"]}"\n'
    try:
        if data['type'] == 'ambient':
            outstr += f'light="type: ambient; color: {data["color"]}; intensity: {data["intensity"]}; '
            outstr += '">\n</a-entity>\n'#close light entity
        elif data['type'] == 'point':
            outstr += f'light="type: point; color: {data["color"]}; intensity: {data["intensity"]}; '
            outstr += f'decay: {data["decay"]}; distance: {data["distance"]}; '
            if self.shadows:
                outstr += 'castShadow: true; '
            outstr += '"> \n</a-entity>\n'#close light entity
        elif data['type'] == 'spot':
            outstr += f'light="type: spot; color: {data["color"]}; intensity: {data["intensity"]}; '
            outstr += f'decay: {data["decay"]}; distance: {data["distance"]}; '
            outstr += f'angle: {data["angle"]}; penumbra: {data["penumbra"]}; '
            if self.shadows:
                outstr += 'castShadow: true; '
            outstr += f'target: #light-{x}-target;"> \n'
            outstr += f'<a-entity id="light-{x}-target" position="0 -1 0"> </a-entity> \n</a-entity> \n'#close light entity
        else:#defaults to directional
            outstr += f'light="type: directional; color: {data["color"]}; intensity: {data["intensity"]}; '
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

def make_wall(x, data, partitions, finishings, csv_f):
    data['alert'] = 'None'#outside the try or they could crash file write
    wall_weight = 0
    if data['type']:
        try:
            wall_type = partitions.get(title = data['type'])
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
            unit_weight += (fabs(data['42']) - wall_thickness/100) * zero_weight#add eventual zero thickness layer
            wall_weight = unit_weight * fabs(data['41']) * fabs(data['43'])#actual wall size
            if wall_thickness and fixed_thickness and fabs(data['42']) != wall_thickness/100:
                data['alert'] = 'Different than Wall Type'
            elif fabs(data['42']) < wall_thickness/100:
                data['alert'] = 'Wall too thin'
            else:
                if wall_type.image:
                    data['8'] = 'partition-' + wall_type.title
                data['color'] = wall_type.color
                data['repeat']=False
                if wall_type.pattern:# == True
                    data['repeat']=True
        except:
            pass
    #writing to csv file
    csv_f.write(f'{x},{data["layer"]},{data["2"]},{data["type"]},-,{data["10"]},{-data["20"]},{data["30"]},')
    csv_f.write(f'{data["210"]},{-data["220"]},{data["50"]},{data["41"]},{data["42"]},{data["43"]},{wall_weight},{data["alert"]} \n')
    #start wall entity
    outstr = f'<a-entity id="wall-{x}-ent" \n'
    outstr += f'position="{data["10"]} {data["30"]} {data["20"]}" \n'
    outstr += f'rotation="{data["210"]} {data["50"]} {data["220"]}">\n'
    if data['alert'] == 'None':#we have 6 planes, not a box
        #wall top
        outstr += f'<a-plane id="wall-{x}-top" \n'
        outstr += f'position="{data["41"]/2} {data["43"]} {-data["42"]/2}" \n'
        if data['43'] < 0:
            outstr += f'rotation="90 0 0" \n'
        else:
            outstr += f'rotation="-90 0 0" \n'
        outstr += f'width="{fabs(data["41"])}" height="{fabs(data["42"])}" \n'
        outstr += f'material="src: #image-{data["8"]}; color: {data["color"]}'
        outstr += is_repeat(data["repeat"], data["41"], data["42"])
        outstr += '">\n</a-plane> \n'
        #wall bottom
        outstr += f'<a-plane id="wall-{x}-bottom" \n'
        outstr += f'position="{data["41"]/2} 0 {-data["42"]/2}" \n'
        if data['43'] < 0:
            outstr += f'rotation="-90 0 0" \n'
        else:
            outstr += f'rotation="90 0 0" \n'
        outstr += f'width="{fabs(data["41"])}" height="{fabs(data["42"])}" \n'
        outstr += f'material="src: #image-{data["8"]}; color: {data["color"]}'
        outstr += is_repeat(data["repeat"], data["41"], data["42"])
        outstr += '">\n</a-plane> \n'

        #wall inside
        outstr += f'<a-entity id="wall-{x}-in-ent" \n'
        outstr += f'position="{data["41"]/2} 0 0" \n'
        if data['42'] < 0:
            outstr += 'rotation="0 180 0"> \n'
        else:
            outstr += '> \n'
        side = 'in'
        width = data['41']
        outstr += make_wall_finishing(x, data, finishings, width, side, csv_f)
        outstr += '</a-entity> \n'

        #wall outside
        outstr += f'<a-entity id="wall-{x}-out-ent" \n'
        outstr += f'position="{data["41"]/2} 0 {-data["42"]}" \n'
        if data['42'] > 0:
            outstr += 'rotation="0 180 0"> \n'
        else:
            outstr += '> \n'
        side = 'out'
        outstr += make_wall_finishing(x, data, finishings, width, side, csv_f)
        outstr += '</a-entity> \n'

        #wall left
        outstr += f'<a-entity id="wall-{x}-left-ent" \n'
        outstr += f'position="0 0 {-data["42"]/2}" \n'
        if data['41'] > 0:
            outstr += 'rotation="0 -90 0"> \n'
        else:
            outstr += 'rotation="0 90 0"> \n'
        side = 'left'
        width = data['42']
        outstr += make_wall_finishing(x, data, finishings, width, side, csv_f)
        outstr += '</a-entity> \n'

        #wall right
        outstr += f'<a-entity id="wall-{x}-right-ent" \n'
        outstr += f'position="{data["41"]} 0 {-data["42"]/2}" \n'
        if data['41'] > 0:
            outstr += 'rotation="0 90 0"> \n'
        else:
            outstr += 'rotation="0 -90 0"> \n'
        side = 'right'
        outstr += make_wall_finishing(x, data, finishings, width, side, csv_f)
        outstr += '</a-entity> \n'
        outstr += '</a-entity>\n'

    else:#there is an alert, the wall gets painted red
        outstr += f'<a-box id="wall-{x}-alert" \n'
        outstr += f'position="{data["41"]/2} {data["43"]/2} {-data["42"]/2}" \n'
        outstr += f'scale="{fabs(data["41"])} {fabs(data["43"])} {fabs(data["42"])}" \n'
        outstr += 'material="color: red;'
        outstr += '">\n</a-box>\n </a-entity>\n'

    return outstr

def make_wall_finishing(x, data, finishings, width, side, csv_f):
    try:
        finishing = finishings.get(title = data[side])
		
        tiling_height = fabs(float(finishing.tiling_height))/100*data['43']/fabs(data['43'])
        skirting_height = fabs(float(finishing.skirting_height))/100*data['43']/fabs(data['43'])
        if tiling_height:
            if fabs(tiling_height) > fabs(data['43']):
                tiling_height = data['43']
            if fabs(skirting_height) > fabs(tiling_height):
                skirting_height = tiling_height
            tiling_height = tiling_height - skirting_height
        elif skirting_height:
            if fabs(skirting_height) > fabs(data['43']):
                skirting_height = data['43']
        wall_height = data['43'] - tiling_height - skirting_height

        if finishing.image:
            wall_image = 'finishing-' + finishing.title
            wall_repeat = finishing.pattern
        else:
            wall_image = data['8']
            wall_repeat = data['repeat']

        outstr = f'<a-plane id="wall-{x}-{side}" \n'
        outstr += f'position="0 {wall_height/2+tiling_height+skirting_height} 0" \n'
        outstr += f'width="{fabs(width)}" height="{fabs(wall_height)}" \n'
        outstr += f'material="src: #image-{wall_image}; color: {finishing.color}'
        outstr += is_repeat(wall_repeat, width, wall_height)
        outstr += '">\n</a-plane> \n'
        csv_f.write(f'{x},{data["layer"]},a-wall/{side},{wall_image},Wall,-,-,-,-,-,-,{width},-,{wall_height},-,- \n')
        outstr += f'<a-plane id="wall-{x}-{side}-tiling" \n'
        outstr += f'position="0 {tiling_height/2+skirting_height} 0" \n'
        outstr += f'width="{fabs(width)}" height="{fabs(tiling_height)}" \n'
        outstr += f'material="src: #image-tiling-{finishing.title}; color: {finishing.tiling_color}'
        outstr += is_repeat(finishing.tiling_pattern, width, tiling_height)
        outstr += '">\n</a-plane> \n'
        csv_f.write(f'{x},{data["layer"]},a-wall/{side},{finishing.title},Tiling,-,-,-,-,-,-,{width},-,{tiling_height},-,- \n')
        outstr += f'<a-plane id="wall-{x}-{side}-skirting" \n'
        outstr += f'position="0 {skirting_height/2} 0" \n'
        outstr += f'width="{fabs(width)}" height="{fabs(skirting_height)}" \n'
        outstr += f'material="src: #image-skirting-{finishing.title}; color: {finishing.skirting_color}'
        outstr += is_repeat(finishing.skirting_pattern, width, skirting_height)
        outstr += '">\n</a-plane> \n'
        csv_f.write(f'{x},{data["layer"]},a-wall/{side},{finishing.title},Skirting,-,-,-,-,-,-,{width},-,{skirting_height},-,- \n')
    except:
        outstr = f'<a-plane id="wall-{x}-{side}" \n'
        outstr += f'position="0 {data["43"]/2} 0" \n'
        outstr += f'width="{fabs(width)}" height="{fabs(data["43"])}" \n'
        outstr += f'material="src: #image-{data["8"]}; color: {data["color"]}'
        outstr += is_repeat(data["repeat"], width, data["43"])
        outstr += '">\n</a-plane> \n'
    return outstr

def make_slab(x, data, partitions, finishings, csv_f):
    data['alert'] = 'None'#outside the try or they could crash file write
    slab_weight = 0
    if data['type']:
        try:
            slab_type = partitions.get(title = data['type'])
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
            unit_weight += (fabs(data['43']) - slab_thickness/100) * zero_weight#add eventual zero thickness layer
            slab_weight = unit_weight * fabs(data['41']) * fabs(data['42'])#actual slab size
            if slab_thickness and fixed_thickness and fabs(data['43']) != slab_thickness/100:
                data['alert'] = 'Different than Wall/Slab Type'
            elif fabs(data['43']) < slab_thickness/100:
                data['alert'] = 'Slab too thin'
            else:
                if slab_type.image:
                    data['8'] = 'partition-' + slab_type.title
                data['color'] = slab_type.color
                data['repeat']=False
                if slab_type.pattern:# == True
                    data['repeat']=True
        except:
            pass
    #writing to csv file
    csv_f.write(f'{x},{data["layer"]},{data["2"]},{data["type"]},-,{data["10"]},{-data["20"]},{data["30"]},')
    csv_f.write(f'{data["210"]},{-data["220"]},{data["50"]},{data["41"]},{data["42"]},{data["43"]},{slab_weight},{data["alert"]} \n')
    #start slab entity
    outstr = f'<a-entity id="slab-{x}-ent" \n'
    outstr += f'position="{data["10"]} {data["30"]} {data["20"]}" \n'
    outstr += f'rotation="{data["210"]} {data["50"]} {data["220"]}">\n'
    if data['alert'] == 'None':#we have 6 planes, not a box
        #slab top (floor)
        outstr += f'<a-entity id="slab-{x}-floor-ent" \n'
        outstr += f'position="{data["41"]/2} 0 {-data["42"]/2}" \n'
        if data['43'] < 0:
            outstr += f'rotation="90 0 0"> \n'
        else:
            outstr += f'rotation="-90 0 0"> \n'
        side = 'floor'
        outstr += make_slab_finishing(x, data, finishings, side, csv_f)
        outstr += '</a-entity> \n'

        #slab bottom (ceiling)
        outstr += f'<a-entity id="slab-{x}-ceiling-ent" \n'
        outstr += f'position="{data["41"]/2} {-data["43"]} {-data["42"]/2}" \n'
        if data['43'] < 0:
            outstr += f'rotation="-90 0 0"> \n'
        else:
            outstr += f'rotation="90 0 0"> \n'
        side = 'ceiling'
        outstr += make_slab_finishing(x, data, finishings, side, csv_f)
        outstr += '</a-entity> \n'

        #slab front
        outstr += f'<a-plane id="slab-{x}-front" \n'
        outstr += f'position="{data["41"]/2} {-data["43"]/2} 0" \n'
        if data['42'] < 0:
            outstr += 'rotation="0 180 0" \n'
        outstr += f'width="{fabs(data["41"])}" height="{fabs(data["43"])}" \n'
        outstr += f'material="src: #image-{data["8"]}; color: {data["color"]}'
        outstr += is_repeat(data["repeat"], data["41"], data["43"])
        outstr += '">\n</a-plane> \n'

        #slab back
        outstr += f'<a-plane id="slab-{x}-back" \n'
        outstr += f'position="{data["41"]/2} {-data["43"]/2} {-data["42"]}" \n'
        if data['42'] > 0:
            outstr += 'rotation="0 180 0" \n'
        outstr += f'width="{fabs(data["41"])}" height="{fabs(data["43"])}" \n'
        outstr += f'material="src: #image-{data["8"]}; color: {data["color"]}'
        outstr += is_repeat(data["repeat"], data["41"], data["43"])
        outstr += '">\n</a-plane> \n'

        #slab left
        outstr += f'<a-plane id="slab-{x}-left" \n'
        outstr += f'position="0 {-data["43"]/2} {-data["42"]/2}" \n'
        if data['41'] > 0:
            outstr += 'rotation="0 -90 0" \n'
        else:
            outstr += 'rotation="0 90 0" \n'
        outstr += f'width="{fabs(data["42"])}" height="{fabs(data["43"])}" \n'
        outstr += f'material="src: #image-{data["8"]}; color: {data["color"]}'
        outstr += is_repeat(data["repeat"], data["42"], data["43"])
        outstr += '">\n</a-plane> \n'

        #slab right
        outstr += f'<a-plane id="slab-{x}-right" \n'
        outstr += f'position="{data["41"]} {-data["43"]/2} {-data["42"]/2}" \n'
        if data['41'] > 0:
            outstr += 'rotation="0 90 0" \n'
        else:
            outstr += 'rotation="0 -90 0" \n'
        outstr += f'width="{fabs(data["42"])}" height="{fabs(data["43"])}" \n'
        outstr += f'material="src: #image-{data["8"]}; color: {data["color"]}'
        outstr += is_repeat(data["repeat"], data["42"], data["43"])
        outstr += '">\n</a-plane> \n </a-entity>\n'

    else:#there is an alert, the slab gets painted red
        outstr += f'<a-box id="slab-{x}-alert" \n'
        outstr += f'position="{data["41"]/2} {-data["43"]/2} {-data["42"]/2}" \n'
        outstr += f'scale="{fabs(data["41"])} {fabs(data["43"])} {fabs(data["42"])}" \n'
        outstr += 'material="color: red;'
        outstr += '">\n</a-box>\n </a-entity>\n'

    return outstr

def make_slab_finishing(x, data, finishings, side, csv_f):
    outstr = f'<a-plane id="slab-{x}-{side}" \n'
    outstr += f'width="{fabs(data["41"])}" height="{fabs(data["42"])}" \n'
    try:
        finishing = finishings.get(title = data[side])
        if finishing.image:
            slab_image = 'finishing-' + finishing.title
            slab_repeat = finishing.pattern
        else:
            slab_image = data['8']
            slab_repeat = data['repeat']
        outstr += f'material="src: #image-{slab_image}; color: {finishing.color}'
        outstr += is_repeat(slab_repeat, data["41"], data["42"])
        csv_f.write(f'{x},{data["layer"]},a-slab/{side},{slab_image},-,-,-,-,-,-,-,{data["41"]},{data["42"]},-,-,- \n')
    except:
        outstr += f'material="src: #image-{data["8"]}; color: {data["color"]}'
        outstr += is_repeat(data["repeat"], data["41"], data["42"])
    outstr += '">\n</a-plane> \n'
    return outstr