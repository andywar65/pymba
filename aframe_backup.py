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
                data['num'] = x
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
                    data2['num'] = x
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
                data['num'] = x
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

        #elif data['2'] == 'a-wall':
            #output[x] = make_wall(x, data, partitions, finishings, csv_f)

        #elif data['2'] == 'a-openwall':
            #output[x] = make_openwall(x, data, partitions, finishings, csv_f)

        #elif data['2'] == 'a-slab':
            #output[x] = make_slab(x, data, partitions, finishings, csv_f)

        elif data['2'] == 'a-wall' or data['2'] == 'a-slab' or data['2'] == 'a-openwall':
            part = APartition(data, partitions, finishings, csv_f)
            if part.type_obj:
                part.calc_weight()
            else:
                part.no_weight()
            if part.d['alert'] == 'None':
                output[x] = part.write_html()
            else:
                output[x] = part.write_html_alert()

    return output

def reference_openings(collection):
    collection2 = collection.copy()
    for x, data in collection.items():
        if data['2'] == 'a-door':
            collection[x] = data
            for x2, data2 in collection2.items():
                if data2['2'] == 'a-wall':
                    if data['210']==0 and data['220']==0 and data2['210']==0 and data2['220']==0:
                        data2 = door_straight_case(x, data, data2)
                    else:
                        data2 = door_tilted_case(x, data, data2)
                    collection[x2] = data2

    return collection

def door_straight_case(x, data, data2):
    if data['30']==data2['30'] and data['43']>0 and data2['43']>0:
        rotd = round(data['50'], 0)
        rotw = round(data2['50'], 0)
        if rotd==rotw-180 or rotd-180==rotw:
            backwards = -1
        else:
            backwards = 1
        if rotd == rotw or backwards == -1:
            #translation
            xt = data['10']-data2['10']
            zt = data['20']-data2['20']
            #rotation
            alfa = radians(data2['50'])
            xd = round(xt*cos(alfa)-zt*sin(alfa), 4)
            zd = round(xt*sin(alfa)+zt*cos(alfa), 4)
            xde = xd + round(data['41'], 4)*backwards
            zde = zd + round(data['42'], 4)
            #wall bounding box
            if data2['41'] > 0:
                xmaxw = round(data2['41'], 4)
                xminw = 0
            else:
                xmaxw = 0
                xminw = round(data2['41'], 4)
            if data2['42'] > 0:
                zmaxw = 0
                zminw = -round(data2['42'], 4)
            else:
                zmaxw = -round(data2['42'], 4)
                zminw = 0
            #door bounding box
            if xde > xd:
                xmaxd = xde
                xmind = xd
            else:
                xmaxd = xd
                xmind = xde
            if zde > zd:
                zmaxd = zde
                zmind = zd
            else:
                zmaxd = zd
                zmind = zde
            #door inclusion
            if xmaxw >= xmaxd and xminw <= xmind and zmaxw >= zmaxd and zminw <= zmind:
                data2['door'] = x
                data2['2'] = 'a-openwall'
                if data['43']>data2['43']:
                    data2['door_height'] = data2['43']
                else:
                    data2['door_height'] = data['43']
                if data2['41']>0:
                    data2['door_off_1'] = xmind
                    data2['door_off_2'] = xmaxd
                else:
                    data2['door_off_1'] = xmaxd - xmaxw
                    data2['door_off_2'] = xmind - xmaxw

    return data2

#TODO
def door_tilted_case(x, data, data2):
    #d210 = round(data['210']*fabs(data['41'])/data['41'], 4)
    #d220 = round(data['220']*fabs(data['42'])/data['42'], 4)
    #d50 = round(data['50']*fabs(data['43'])/data['43'], 4)
    #w210 = round(data2['210']*fabs(data2['41'])/data2['41'], 4)
    #w220 = round(data2['220']*fabs(data2['42'])/data2['42'], 4)
    #w50 = round(data2['50']*fabs(data2['43'])/data2['43'], 4)
    return data2

def is_repeat(repeat, rx, ry):
    if repeat:
        output = f'; repeat:{fabs(rx)} {fabs(ry)}'
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
                    data['repeat'] = wall_type.pattern
                if wall_type.color:
                    data['color'] = wall_type.color

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
    if data['2']=='a-openwall' and (side=='in-top' or side=='out-top'):
        door_height = fabs(data['door_height'])*data['43']/fabs(data['43'])
    else:
        door_height = 0

    try:
        if side=='in-left' or side=='in-right' or side=='in-top':
            data_side = data['in']
        elif side=='out-left' or side=='out-right' or side=='out-top':
            data_side = data['out']
        else:
            data_side = data[side]
        finishing = finishings.get(title = data_side)

        tiling_height = fabs(float(finishing.tiling_height))/100*data['43']/fabs(data['43'])
        skirting_height = fabs(float(finishing.skirting_height))/100*data['43']/fabs(data['43'])
        if fabs(door_height) > fabs(data['43']):
            door_height = data['43']
        if fabs(skirting_height) < fabs(door_height):
            skirting_height = door_height
        if fabs(tiling_height) < fabs(skirting_height):
            tiling_height = skirting_height
        if fabs(tiling_height) < fabs(door_height):
            tiling_height = door_height
        wall_height = data['43'] - tiling_height
        tiling_height = tiling_height - skirting_height
        skirting_height = skirting_height - door_height

        if finishing.image:
            wall_image = 'finishing-' + finishing.title
            wall_repeat = finishing.pattern
        else:
            wall_image = data['8']
            wall_repeat = data['repeat']
        if finishing.color:
            wall_color = finishing.color
        else:
            wall_color = data['color']

        outstr = f'<a-plane id="wall-{x}-{side}" \n'
        outstr += f'position="0 {wall_height/2+tiling_height+skirting_height} 0" \n'
        outstr += f'width="{fabs(width)}" height="{fabs(wall_height)}" \n'
        outstr += f'material="src: #image-{wall_image}; color: {wall_color}'
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
        outstr += f'position="0 {(data["43"]-door_height)/2} 0" \n'
        outstr += f'width="{fabs(width)}" height="{fabs(data["43"]-door_height)}" \n'
        outstr += f'material="src: #image-{data["8"]}; color: {data["color"]}'
        outstr += is_repeat(data["repeat"], width, data["43"]-door_height)
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
                    data['repeat']= slab_type.pattern
                if slab_type.color:
                    data['color'] = slab_type.color

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
        if finishing.color:
            slab_color = finishing.color
        else:
            slab_color = data['color']

        outstr += f'material="src: #image-{slab_image}; color: {slab_color}'
        outstr += is_repeat(slab_repeat, data["41"], data["42"])
        csv_f.write(f'{x},{data["layer"]},a-slab/{side},{slab_image},-,-,-,-,-,-,-,{data["41"]},{data["42"]},-,-,- \n')
    except:
        outstr += f'material="src: #image-{data["8"]}; color: {data["color"]}'
        outstr += is_repeat(data["repeat"], data["41"], data["42"])
    outstr += '">\n</a-plane> \n'
    return outstr

def make_openwall(x, data, partitions, finishings, csv_f):
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
            if data['2'] == 'a-openwall':
                wall_weight = wall_weight - (unit_weight * fabs(data['door_off_2']-data['door_off_1']) * fabs(data['door_height']))#remove door
            if wall_thickness and fixed_thickness and fabs(data['42']) != wall_thickness/100:
                data['alert'] = 'Different than Wall Type'
            elif fabs(data['42']) < wall_thickness/100:
                data['alert'] = 'Wall too thin'
            else:
                if wall_type.image:
                    data['8'] = 'partition-' + wall_type.title
                    data['repeat'] = wall_type.pattern
                if wall_type.color:
                    data['color'] = wall_type.color

        except:
            pass
    #writing to csv file
    csv_f.write(f'{x},{data["layer"]},{data["2"]},{data["type"]},-,{data["10"]},{-data["20"]},{data["30"]},')
    csv_f.write(f'{data["210"]},{-data["220"]},{data["50"]},{data["41"]},{data["42"]},{data["43"]},{wall_weight},{data["alert"]} \n')
    #start openwall entity
    outstr = f'<a-entity id="openwall-{x}-ent" \n'
    outstr += f'position="{data["10"]} {data["30"]} {data["20"]}" \n'
    outstr += f'rotation="{data["210"]} {data["50"]} {data["220"]}">\n'
    if data['alert'] == 'None':#we have 6 planes, not a box
        #openwall top
        outstr += f'<a-plane id="openwall-{x}-top" \n'
        outstr += f'position="{data["41"]/2} {data["43"]} {-data["42"]/2}" \n'
        if data['43'] < 0:
            outstr += f'rotation="90 0 0" \n'
        else:
            outstr += f'rotation="-90 0 0" \n'
        outstr += f'width="{fabs(data["41"])}" height="{fabs(data["42"])}" \n'
        outstr += f'material="src: #image-{data["8"]}; color: {data["color"]}'
        outstr += is_repeat(data["repeat"], data["41"], data["42"])
        outstr += '">\n</a-plane> \n'
        #openwall bottom left
        outstr += f'<a-plane id="openwall-{x}-bottom-left" \n'
        outstr += f'position="{data["door_off_1"]/2} 0 {-data["42"]/2}" \n'
        if data['43'] < 0:
            outstr += f'rotation="-90 0 0" \n'
        else:
            outstr += f'rotation="90 0 0" \n'
        outstr += f'width="{fabs(data["door_off_1"])}" height="{fabs(data["42"])}" \n'
        outstr += f'material="src: #image-{data["8"]}; color: {data["color"]}'
        outstr += is_repeat(data["repeat"], data["door_off_1"], data["42"])
        outstr += '">\n</a-plane> \n'
        #openwall bottom right
        outstr += f'<a-plane id="openwall-{x}-bottom-right" \n'
        width = data["41"]-data["door_off_2"]
        outstr += f'position="{width/2+data["door_off_2"]} 0 {-data["42"]/2}" \n'
        if data['43'] < 0:
            outstr += f'rotation="-90 0 0" \n'
        else:
            outstr += f'rotation="90 0 0" \n'
        outstr += f'width="{fabs(width)}" height="{fabs(data["42"])}" \n'
        outstr += f'material="src: #image-{data["8"]}; color: {data["color"]}'
        outstr += is_repeat(data["repeat"], width, data["42"])
        outstr += '">\n</a-plane> \n'

        #openwall inside left
        outstr += f'<a-entity id="openwall-{x}-in-left-ent" \n'
        outstr += f'position="{data["door_off_1"]/2} 0 0" \n'
        if data['42'] < 0:
            outstr += 'rotation="0 180 0"> \n'
        else:
            outstr += '> \n'
        side = 'in-left'
        width = data['door_off_1']
        outstr += make_wall_finishing(x, data, finishings, width, side, csv_f)
        outstr += '</a-entity> \n'

        #openwall inside right
        outstr += f'<a-entity id="openwall-{x}-in-right-ent" \n'
        outstr += f'position="{(data["41"]-data["door_off_2"])/2+data["door_off_2"]} 0 0" \n'
        if data['42'] < 0:
            outstr += 'rotation="0 180 0"> \n'
        else:
            outstr += '> \n'
        side = 'in-right'
        width = data["41"]-data["door_off_2"]
        outstr += make_wall_finishing(x, data, finishings, width, side, csv_f)
        outstr += '</a-entity> \n'

        #openwall inside top
        outstr += f'<a-entity id="openwall-{x}-in-top-ent" \n'
        outstr += f'position="{(data["door_off_2"]-data["door_off_1"])/2+data["door_off_1"]} {data["door_height"]} 0" \n'
        if data['42'] < 0:
            outstr += 'rotation="0 180 0"> \n'
        else:
            outstr += '> \n'
        side = 'in-top'
        width = data["door_off_2"]-data["door_off_1"]
        outstr += make_wall_finishing(x, data, finishings, width, side, csv_f)
        outstr += '</a-entity> \n'

        #openwall outside left
        outstr += f'<a-entity id="openwall-{x}-out-left-ent" \n'
        outstr += f'position="{data["door_off_1"]/2} 0 {-data["42"]}" \n'
        if data['42'] > 0:
            outstr += 'rotation="0 180 0"> \n'
        else:
            outstr += '> \n'
        side = 'out-left'
        width = data['door_off_1']
        outstr += make_wall_finishing(x, data, finishings, width, side, csv_f)
        outstr += '</a-entity> \n'

        #openwall outside right
        outstr += f'<a-entity id="openwall-{x}-out-right-ent" \n'
        outstr += f'position="{(data["41"]-data["door_off_2"])/2+data["door_off_2"]} 0 {-data["42"]}" \n'
        if data['42'] > 0:
            outstr += 'rotation="0 180 0"> \n'
        else:
            outstr += '> \n'
        side = 'out-right'
        width = data["41"]-data["door_off_2"]
        outstr += make_wall_finishing(x, data, finishings, width, side, csv_f)
        outstr += '</a-entity> \n'

        #openwall outside top
        outstr += f'<a-entity id="openwall-{x}-out-top-ent" \n'
        outstr += f'position="{(data["door_off_2"]-data["door_off_1"])/2+data["door_off_1"]} {data["door_height"]} {-data["42"]}" \n'
        if data['42'] > 0:
            outstr += 'rotation="0 180 0"> \n'
        else:
            outstr += '> \n'
        side = 'out-top'
        width = data["door_off_2"]-data["door_off_1"]
        outstr += make_wall_finishing(x, data, finishings, width, side, csv_f)
        outstr += '</a-entity> \n'

        #openwall left
        outstr += f'<a-entity id="openwall-{x}-left-ent" \n'
        outstr += f'position="0 0 {-data["42"]/2}" \n'
        if data['41'] > 0:
            outstr += 'rotation="0 -90 0"> \n'
        else:
            outstr += 'rotation="0 90 0"> \n'
        side = 'left'
        width = data['42']
        outstr += make_wall_finishing(x, data, finishings, width, side, csv_f)
        outstr += '</a-entity> \n'

        #openwall right
        outstr += f'<a-entity id="openwall-{x}-right-ent" \n'
        outstr += f'position="{data["41"]} 0 {-data["42"]/2}" \n'
        if data['41'] > 0:
            outstr += 'rotation="0 90 0"> \n'
        else:
            outstr += 'rotation="0 -90 0"> \n'
        side = 'right'
        outstr += make_wall_finishing(x, data, finishings, width, side, csv_f)
        outstr += '</a-entity> \n'
        outstr += '</a-entity>\n'

    else:#there is an alert, the wall gets painted red, TODO hole for door
        outstr += f'<a-box id="openwall-{x}-alert" \n'
        outstr += f'position="{data["41"]/2} {data["43"]/2} {-data["42"]/2}" \n'
        outstr += f'scale="{fabs(data["41"])} {fabs(data["43"])} {fabs(data["42"])}" \n'
        outstr += 'material="color: red;'
        outstr += '">\n</a-box>\n </a-entity>\n'

    return outstr

class APartition(object):
    def __init__(self, data, types, finishings, csv_f):
        self.d = data#is it possible to use the self.__dict__=data construct? it would be much cleaner
        self.d['alert'] = 'None'
        if self.d['type']:
            try:
                self.type_obj = types.get(title = self.d['type'])
            except:
                self.type_obj = False
        self.finishings = finishings
        self.csv_f = csv_f

    def calc_weight(self):

        part_weight = 0
        unit_weight = 0
        zero_weight = 0
        part_thickness = 0
        fixed_thickness = True

        for part_layer in self.type_obj.part_layers.all():
            part_layer_thickness = fabs(float(part_layer.thickness))
            part_layer_weight = fabs(float(part_layer.weight))
            if part_layer_thickness == 0:
                fixed_thickness = False
                zero_weight = part_layer_weight
            part_thickness += part_layer_thickness
            unit_weight += part_layer_thickness/100 * part_layer_weight
        unit_weight += (fabs(self.d['42']) - part_thickness/100) * zero_weight#add eventual zero thickness layer
        part_weight = unit_weight * fabs(self.d['41']) * fabs(self.d['43'])#actual part size
        if self.d['2'] == 'a-openwall':
            part_weight = part_weight - (unit_weight * fabs(self.d['door_off_2']-self.d['door_off_1']) * fabs(self.d['door_height']))#remove door
        if part_thickness and fixed_thickness and fabs(self.d['42']) != part_thickness/100:
            self.d['alert'] = 'Different than Partition Type'
        elif fabs(self.d['42']) < part_thickness/100:
            self.d['alert'] = 'Partition too thin'
        else:
            if self.type_obj.image:
                self.d['8'] = 'partition-' + self.type_obj.title
                self.d['repeat'] = self.type_obj.pattern
            if self.type_obj.color:
                self.d['color'] = self.type_obj.color

        #writing to csv file
        self.csv_f.write(f'{self.d["num"]},{self.d["layer"]},{self.d["2"]},{self.type_obj.title},-,{self.d["10"]},{-self.d["20"]},{self.d["30"]},')
        self.csv_f.write(f'{self.d["210"]},{-self.d["220"]},{self.d["50"]},{self.d["41"]},{self.d["42"]},{self.d["43"]},{part_weight},{self.d["alert"]} \n')
        return

    def no_weight(self):
        #writing to csv file
        self.csv_f.write(f'{self.d["num"]},{self.d["layer"]},{self.d["2"]},None,-,{self.d["10"]},{-self.d["20"]},{self.d["30"]},')
        self.csv_f.write(f'{self.d["210"]},{-self.d["220"]},{self.d["50"]},{self.d["41"]},{self.d["42"]},{self.d["43"]},0,{self.d["alert"]} \n')
        return

    def write_html(self):
        #start entity
        outstr = f'<a-entity id="{self.d["2"]}-{self.d["num"]}" \n'
        outstr += f'position="{self.d["10"]} {self.d["30"]} {self.d["20"]}" \n'
        outstr += f'rotation="{self.d["210"]} {self.d["50"]} {self.d["220"]}">\n'
        #slab handle is on top
        if self.d['2'] == 'a-slab':
            y = self.d['43']
        else:
            y = 0

        #top surface
        if self.d['2'] == 'a-slab':
            self.d['side'] = 'floor'
        else:
            self.d['side'] = 'top'
        self.d['sub_side'] = self.d['side']
        self.d['width'] = fabs(self.d['41'])
        self.d['height'] = fabs(self.d['42'])

        outstr += f'<a-entity id="{self.d["2"]}-{self.d["num"]}-{self.d["side"]}-ent" \n'
        outstr += f'position="{self.d["41"]/2} {self.d["43"]-y} 0" \n'
        if self.d['43'] > 0:
            outstr += 'rotation="-90 0 0"> \n'
        else:
            outstr += 'rotation="-90 180 0"> \n'
        outstr += self.part_simple_finishing()
        outstr += '</a-entity> \n'

        #bottom surface, a-openwall has left and right bottoms
        if self.d['2'] == 'a-wall' or self.d['2'] == 'a-slab':
            if self.d['2'] == 'a-slab':
                self.d['side'] = 'ceiling'
            else:
                self.d['side'] = 'bottom'
            self.d['sub_side'] = self.d['side']
            self.d['width'] = fabs(self.d['41'])
            self.d['height'] = fabs(self.d['42'])

            outstr += f'<a-entity id="{self.d["2"]}-{self.d["num"]}-{self.d["side"]}-ent" \n'
            outstr += f'position="{self.d["41"]/2} {-y} 0" \n'
            if self.d['43'] > 0:
                outstr += 'rotation="90 180 0"> \n'
            else:
                outstr += 'rotation="90 0 0"> \n'
            outstr += self.part_simple_finishing()
            outstr += '</a-entity> \n'

        #inside surface, a-openwall has left, right and top insides
        if self.d['2'] == 'a-wall' or self.d['2'] == 'a-slab':
            if self.d['2'] == 'a-slab':
                self.d['side'] = 'front'
            else:
                self.d['side'] = 'in'
            self.d['sub_side'] = self.d['side']
            self.d['width'] = fabs(self.d['41'])
            self.d['height'] = fabs(self.d['43'])

            outstr += f'<a-entity id="{self.d["2"]}-{self.d["num"]}-{self.d["side"]}-ent" \n'
            outstr += f'position="{self.d["41"]/2} {-y} 0" \n'
            if self.d['42'] > 0:
                outstr += 'rotation="0 180 0"> \n'
            else:
                outstr += '> \n'
            if self.d['2'] == 'a-slab':
                outstr += self.part_simple_finishing()
            else:
                outstr += self.part_striped_finishing()
            outstr += '</a-entity> \n'

        #outside surface, a-openwall has left, right and top outsides
        if self.d['2'] == 'a-wall' or self.d['2'] == 'a-slab':
            if self.d['2'] == 'a-slab':
                self.d['side'] = 'back'
            else:
                self.d['side'] = 'out'
            self.d['sub_side'] = self.d['side']
            self.d['width'] = fabs(self.d['41'])
            self.d['height'] = fabs(self.d['43'])

            outstr += f'<a-entity id="{self.d["2"]}-{self.d["num"]}-{self.d["side"]}-ent" \n'
            outstr += f'position="{self.d["41"]/2} {-y} {self.d["42"]}" \n'
            if self.d['42'] < 0:
                outstr += 'rotation="0 180 0"> \n'
            else:
                outstr += '> \n'
            if self.d['2'] == 'a-slab':
                outstr += self.part_simple_finishing()
            else:
                outstr += self.part_striped_finishing()
            outstr += '</a-entity> \n'

        #left surface
        self.d['side'] = 'left'
        self.d['sub_side'] = 'left'
        self.d['width'] = fabs(self.d['42'])
        self.d['height'] = fabs(self.d['43'])

        outstr += f'<a-entity id="{self.d["2"]}-{self.d["num"]}-{self.d["side"]}-ent" \n'
        outstr += f'position="0 {-y} {self.d["42"]/2}" \n'
        if self.d['41'] > 0:
            outstr += 'rotation="0 -90 0"> \n'
        else:
            outstr += 'rotation="0 90 0"> \n'
        if self.d['2'] == 'a-slab':
            outstr += self.part_simple_finishing()
        else:
            outstr += self.part_striped_finishing()
        outstr += '</a-entity> \n'

        #right surface
        self.d['side'] = 'right'
        self.d['sub_side'] = 'right'
        self.d['width'] = fabs(self.d['42'])
        self.d['height'] = fabs(self.d['43'])

        outstr += f'<a-entity id="{self.d["2"]}-{self.d["num"]}-{self.d["side"]}-ent" \n'
        outstr += f'position="{self.d["41"]} {-y} {self.d["42"]/2}" \n'
        if self.d['41'] < 0:
            outstr += 'rotation="0 -90 0"> \n'
        else:
            outstr += 'rotation="0 90 0"> \n'
        if self.d['2'] == 'a-slab':
            outstr += self.part_simple_finishing()
        else:
            outstr += self.part_striped_finishing()
        outstr += '</a-entity> \n'

        if self.d['2'] == 'a-openwall':
            #bottom left surface
            self.d['side'] = 'bottom'
            self.d['sub_side'] = 'bottom-left'
            self.d['width'] = fabs(self.d['door_off_1'])
            self.d['height'] = fabs(self.d['42'])

            outstr += f'<a-entity id="{self.d["2"]}-{self.d["num"]}-{self.d["sub_side"]}-ent" \n'
            outstr += f'position="{self.d["door_off_1"]/2} 0 0" \n'
            if self.d['43'] > 0:
                outstr += 'rotation="90 180 0"> \n'
            else:
                outstr += 'rotation="90 0 0"> \n'
            outstr += self.part_simple_finishing()
            outstr += '</a-entity> \n'
            #bottom right surface
            self.d['side'] = 'bottom'
            self.d['sub_side'] = 'bottom-right'
            self.d['width'] = fabs(self.d['41']-self.d['door_off_2'])
            self.d['height'] = fabs(self.d['42'])

            outstr += f'<a-entity id="{self.d["2"]}-{self.d["num"]}-{self.d["sub_side"]}-ent" \n'
            outstr += f'position="{self.d["width"]/2+self.d["door_off_2"]} 0 0" \n'
            if self.d['43'] > 0:
                outstr += 'rotation="90 180 0"> \n'
            else:
                outstr += 'rotation="90 0 0"> \n'
            outstr += self.part_simple_finishing()
            outstr += '</a-entity> \n'
            #inside left surface
            self.d['side'] = 'in'
            self.d['sub_side'] = 'in-left'
            self.d['width'] = fabs(self.d['door_off_1'])
            self.d['height'] = fabs(self.d['door_height'])

            outstr += f'<a-entity id="{self.d["2"]}-{self.d["num"]}-{self.d["sub_side"]}-ent" \n'
            outstr += f'position="{self.d["door_off_1"]/2} 0 0" \n'
            if self.d['42'] > 0:
                outstr += 'rotation="0 180 0"> \n'
            else:
                outstr += '> \n'
            outstr += self.part_striped_finishing()
            outstr += '</a-entity> \n'
            #inside right surface
            self.d['side'] = 'in'
            self.d['sub_side'] = 'in-right'
            self.d['width'] = fabs(self.d['41']-self.d['door_off_2'])
            self.d['height'] = fabs(self.d['door_height'])

            outstr += f'<a-entity id="{self.d["2"]}-{self.d["num"]}-{self.d["sub_side"]}-ent" \n'
            outstr += f'position="{self.d["width"]/2+self.d["door_off_2"]} 0 0" \n'
            if self.d['42'] > 0:
                outstr += 'rotation="0 180 0"> \n'
            else:
                outstr += '> \n'
            outstr += self.part_striped_finishing()
            outstr += '</a-entity> \n'
            #inside top surface
            self.d['side'] = 'in'
            self.d['sub_side'] = 'in-top'
            self.d['width'] = fabs(self.d['41'])
            self.d['height'] = fabs(self.d['43']-self.d['door_height'])

            outstr += f'<a-entity id="{self.d["2"]}-{self.d["num"]}-{self.d["sub_side"]}-ent" \n'
            outstr += f'position="{self.d["width"]/2} {self.d["door_height"]} 0" \n'
            if self.d['42'] > 0:
                outstr += 'rotation="0 180 0"> \n'
            else:
                outstr += '> \n'
            outstr += self.part_striped_finishing()
            outstr += '</a-entity> \n'
            #outside left surface
            self.d['side'] = 'out'
            self.d['sub_side'] = 'out-left'
            self.d['width'] = fabs(self.d['door_off_1'])
            self.d['height'] = fabs(self.d['door_height'])

            outstr += f'<a-entity id="{self.d["2"]}-{self.d["num"]}-{self.d["sub_side"]}-ent" \n'
            outstr += f'position="{self.d["door_off_1"]/2} 0 {self.d["42"]}" \n'
            if self.d['42'] < 0:
                outstr += 'rotation="0 180 0"> \n'
            else:
                outstr += '> \n'
            outstr += self.part_striped_finishing()
            outstr += '</a-entity> \n'
            #outside right surface
            self.d['side'] = 'out'
            self.d['sub_side'] = 'out-right'
            self.d['width'] = fabs(self.d['41']-self.d['door_off_2'])
            self.d['height'] = fabs(self.d['door_height'])

            outstr += f'<a-entity id="{self.d["2"]}-{self.d["num"]}-{self.d["sub_side"]}-ent" \n'
            outstr += f'position="{self.d["width"]/2+self.d["door_off_2"]} 0 {self.d["42"]}" \n'
            if self.d['42'] < 0:
                outstr += 'rotation="0 180 0"> \n'
            else:
                outstr += '> \n'
            outstr += self.part_striped_finishing()
            outstr += '</a-entity> \n'
            #outside top surface
            self.d['side'] = 'out'
            self.d['sub_side'] = 'out-top'
            self.d['width'] = fabs(self.d['41'])
            self.d['height'] = fabs(self.d['43']-self.d['door_height'])

            outstr += f'<a-entity id="{self.d["2"]}-{self.d["num"]}-{self.d["sub_side"]}-ent" \n'
            outstr += f'position="{self.d["width"]/2} {self.d["door_height"]} {self.d["42"]}" \n'
            if self.d['42'] < 0:
                outstr += 'rotation="0 180 0"> \n'
            else:
                outstr += '> \n'
            outstr += self.part_striped_finishing()
            outstr += '</a-entity> \n'

        #end entity
        outstr += '</a-entity>\n'
        return outstr

    def part_simple_finishing(self):
        try:
            finishing = self.finishings.get(title = self.d['side'])
            if finishing.image:
                part_image = 'finishing-' + finishing.title
                part_repeat = finishing.pattern
            else:
                part_image = self.d['8']
                part_repeat = self.d['repeat']
            if finishing.color:
                part_color = finishing.color
            else:
                part_color = self.d['color']

            self.csv_f.write(f'{self.d["num"]},{self.d["layer"]},{self.d["2"]}/{self.d["sub_side"]},{part_image},-,-,-,-,-,-,-,{self.d["width"]},{self.d["height"]},-,-,- \n')
        except:
            part_image = self.d['8']
            part_repeat = self.d['repeat']
            part_color = self.d['color']

        outstr = f'<a-plane id="{self.d["2"]}-{self.d["num"]}-{self.d["sub_side"]}" \n'
        outstr += f'position="0 {self.d["height"]/2} 0" \n'
        outstr += f'width="{self.d["width"]}" height="{self.d["height"]}"\n'
        outstr += f'material="src: #image-{part_image}; color: {part_color}'
        outstr += is_repeat(part_repeat, self.d['width'], self.d['height'])
        outstr += '">\n</a-plane>\n'
        return outstr

    def part_striped_finishing(self):
        try:
            finishing = self.finishings.get(title = self.d['side'])
            if finishing.image:
                part_image = 'finishing-' + finishing.title
                part_repeat = finishing.pattern
            else:
                part_image = self.d['8']
                part_repeat = self.d['repeat']
            if finishing.color:
                part_color = finishing.color
            else:
                part_color = self.d['color']

            self.csv_f.write(f'{self.d["num"]},{self.d["layer"]},{self.d["2"]}/{self.d["sub_side"]},{part_image},-,-,-,-,-,-,-,{self.d["width"]},{self.d["height"]},-,-,- \n')
        except:
            part_image = self.d['8']
            part_repeat = self.d['repeat']
            part_color = self.d['color']

        outstr = f'<a-plane id="{self.d["2"]}-{self.d["num"]}-{self.d["sub_side"]}" \n'
        outstr += f'position="0 {self.d["height"]/2} 0" \n'
        outstr += f'width="{self.d["width"]}" height="{self.d["height"]}"\n'
        outstr += f'material="src: #image-{part_image}; color: {part_color}'
        outstr += is_repeat(part_repeat, self.d['width'], self.d['height'])
        outstr += '">\n</a-plane>\n'
        return outstr

    def is_repeat(self, repeat, rx, rz):
        if repeat:
            output = f'; repeat:{rx} {ry}'
            return output
        else:
            return ';'

    def write_html_alert(self):
        outstr = f'<a-entity id="{self.d["2"]}-{self.d["num"]}-alert: {self.d["alert"]}" \n'
        outstr += f'position="{self.d["10"]} {self.d["30"]} {self.d["20"]}" \n'
        outstr += f'rotation="{self.d["210"]} {self.d["50"]} {self.d["220"]}">\n'
        if self.d["2"] == 'a-openwall':
            outstr += f'<a-box id="{self.d["2"]}-{self.d["num"]}-alert-left" \n'
            outstr += f'position="{self.d["door_off_1"]/2} {self.d["door_height"]/2} {-self.d["42"]/2}" \n'
            outstr += f'scale="{fabs(self.d["door_off_1"])} {fabs(self.d["door_height"])} {fabs(self.d["42"])}" \n'
            outstr += 'material="color: red;">\n'
            outstr += '</a-box>\n'
            outstr += f'<a-box id="{self.d["2"]}-{self.d["num"]}-alert-right" \n'
            outstr += f'position="{(self.d["41"]-self.d["door_off_2"])/2+self.d["door_off_2"]} {self.d["door_height"]/2} {-self.d["42"]/2}" \n'
            outstr += f'scale="{fabs(self.d["41"]-self.d["door_off_2"])} {fabs(self.d["door_height"])} {fabs(self.d["42"])}" \n'
            outstr += 'material="color: red;">\n'
            outstr += '</a-box>\n'
            outstr += f'<a-box id="{self.d["2"]}-{self.d["num"]}-alert-top" \n'
            outstr += f'position="{self.d["41"]/2} {(self.d["43"] - self.d["door_height"])/2+self.d["door_height"]} {-self.d["42"]/2}" \n'
            outstr += f'scale="{fabs(self.d["41"])} {fabs(self.d["43"] - self.d["door_height"])} {fabs(self.d["42"])}" \n'
            outstr += 'material="color: red;">\n'
            outstr += '</a-box>\n'
        else:
            outstr += f'<a-box id="{self.d["2"]}-{self.d["num"]}-alert" \n'
            outstr += f'position="{self.d["41"]/2} {self.d["43"]/2} {-self.d["42"]/2}" \n'
            outstr += f'scale="{fabs(self.d["41"])} {fabs(self.d["43"])} {fabs(self.d["42"])}" \n'
            outstr += 'material="color: red;">\n'
            outstr += '</a-box>\n'
        outstr += '</a-entity>\n'
        return outstr