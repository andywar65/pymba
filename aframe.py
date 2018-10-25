from math import radians, sin, cos, asin, degrees, pi, sqrt, pow, fabs, atan2

def parse_dxf(dxf_f, material_gallery):

    output = {}
    layer_color = {}
    flag = False
    x = 0
    value = 'dummy'

    while value !='ENTITIES':
        key = dxf_f.readline().strip()
        value = dxf_f.readline().strip()
        if value == 'AcDbLayerTableRecord':#dict of layer names and colors
            key = dxf_f.readline().strip()
            layer_name = dxf_f.readline().strip()
            key = dxf_f.readline().strip()
            value = dxf_f.readline().strip()
            key = dxf_f.readline().strip()
            layer_color[layer_name] = cad2hex(dxf_f.readline().strip())

        elif value=='EOF' or key=='':#security to avoid loops if file is corrupted
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
            invisible = False#by default layer is visible

            if flag == 'face':#close 3D face
                data['2'] = '3dface'
                #is material set in model?
                try:
                    material = material_gallery.get(layer = data['8'])
                    data['color'] = material.color
                    invisible = material.invisible#layer visibility
                except:
                    data['color'] = layer_color[data['8']]
                    data['8'] = 'default'
                if invisible:
                    flag = False
                else:
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
                    invisible = material.invisible#layer visibility
                    if material.pattern:# == True
                        data['repeat']=True
                except:
                    data['color'] = layer_color[data['8']]
                    data['8'] = 'default'
                if invisible:
                    flag = False
                else:
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

def make_html(page_obj, collection, partitions, finishings, csv_f):

    output = {}
    for x, data in collection.items():

        if data['2'] == '3dface':
            output[x] = make_triangle(page_obj, x, data)

        if data['2'] == '6planes':#left for legacy
            output[x] = make_box(x, data)

        elif data['2'] == 'box' or data['2'] == 'a-box':
            output[x] = make_box(x, data)

        elif data['2'] == 'cylinder' or data['2'] == 'a-cylinder':
            output[x] = make_cylinder(x, data)

        elif data['2'] == 'a-curvedimage':
            output[x] = make_curvedimage(x, data)

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
            output[x] = make_light(page_obj, x, data)

        elif data['2'] == 'a-text':
            output[x] = make_text(x, data)

        elif data['2'] == 'a-link':
            output[x] = make_link(page_obj, x, data)

        elif data['2'] == 'a-door':
            door = AOpening(data, partitions, finishings, csv_f)
            if door.type_obj:
                door.has_type()
            else:
                door.no_type()
            if door.d['alert'] == 'None':
                output[x] = door.write_html()
            else:#by now useless, if is always true
                pass #output[x] = door.write_html_alert()

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
                zmaxd = zde * ( - backwards)
                zmind = zd * ( - backwards)
            else:
                zmaxd = zd * ( - backwards)
                zmind = zde * ( - backwards)
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

def make_curvedimage(x, data):
    outstr = f'<a-entity id="curvedimage-{x}-ent" \n'
    outstr += f'position="{data["10"]} {data["30"]} {data["20"]}" \n'
    outstr += f'rotation="{data["210"]} {data["50"]} {data["220"]}">\n'
    outstr += f'<a-curvedimage id="curvedimage-{x}" \n'
    outstr += f'position="0 {data["43"]/2} 0" \n'
    if float(data['43']) < 0:
        outstr += 'rotation="180 0 0">\n'
    outstr += f'scale="{fabs(data["41"])} {fabs(data["43"])} {fabs(data["42"])}" \n'
    try:
        if data['theta-length']!='270':
            outstr += f'theta-length="{data["theta-length"]}" '
        if data['theta-start']!='0':
            outstr += f'theta-start="{data["theta-start"]}" '
    except KeyError:
        pass
    outstr += f'src="#image-{data["8"]}">\n'
    outstr += '</a-curvedimage>\n</a-entity>\n'
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

def make_link(page_obj, x, data):
    outstr = f'<a-link id="link-{x}" \n'
    outstr += f'position="{data["10"]} {data["30"]} {data["20"]}" \n'
    outstr += f'rotation="{data["210"]} {data["50"]} {data["220"]}"\n'
    outstr += f'scale="{data["41"]} {data["43"]} {data["42"]}"\n'
    if data['tree'] == 'parent':
        target = page_obj.get_parent()
    elif data['tree'] == 'child':
        target = page_obj.get_first_child()
    elif data['tree'] == 'previous' or data['tree'] == 'prev':
        target = page_obj.get_prev_sibling()
    else:#we default to next sibling
        target = page_obj.get_next_sibling()
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

def make_triangle(page_obj, x, data):
    outstr = f'<a-triangle id="triangle-{x}" \n'
    outstr += f'geometry="vertexA:{data["10"]} {data["30"]} {data["20"]}; \n'
    outstr += f'vertexB:{data["11"]} {data["31"]} {data["21"]}; \n'
    outstr += f'vertexC:{data["12"]} {data["32"]} {data["22"]}" \n'
    outstr += f'material="src: #image-{data["8"]}; color: {data["color"]}; '
    if page_obj.double_face:
        outstr += 'side: double; '
    outstr += '">\n</a-triangle> \n'
    return outstr

def make_light(page_obj, x, data):
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
            if page_obj.shadows:
                outstr += 'castShadow: true; '
            outstr += '"> \n</a-entity>\n'#close light entity
        elif data['type'] == 'spot':
            outstr += f'light="type: spot; color: {data["color"]}; intensity: {data["intensity"]}; '
            outstr += f'decay: {data["decay"]}; distance: {data["distance"]}; '
            outstr += f'angle: {data["angle"]}; penumbra: {data["penumbra"]}; '
            if page_obj.shadows:
                outstr += 'castShadow: true; '
            outstr += f'target: #light-{x}-target;"> \n'
            outstr += f'<a-entity id="light-{x}-target" position="0 -1 0"> </a-entity> \n</a-entity> \n'#close light entity
        else:#defaults to directional
            outstr += f'light="type: directional; color: {data["color"]}; intensity: {data["intensity"]}; '
            if page_obj.shadows:
                outstr += 'castShadow: true; '
            outstr += f'target: #light-{x}-target;"> \n'
            outstr += f'<a-entity id="light-{x}-target" position="0 -1 0"> </a-entity> \n</a-entity> \n'#close light entity
    except KeyError:#default if no light type is set
        outstr += 'light="type: point; intensity: 0.75; distance: 50; decay: 2; '
        if page_obj.shadows:
            outstr += 'castShadow: true;'
        outstr += '">\n</a-entity>\n'#close light entity
    return outstr

class APartition(object):
    def __init__(self, data, types, finishings, csv_f):
        self.d = data#is it possible to use the self.__dict__=data construct? it would be much cleaner
        self.d['alert'] = 'None'
        self.type_obj = False
        if self.d['type']:
            try:
                self.type_obj = types.get(title = self.d['type'])
            except:
                pass
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
        self.csv_f.write(f'{self.d["num"]},{self.d["layer"]},{self.d["2"]},-,-,{self.type_obj.title},{self.d["10"]},{-self.d["20"]},{self.d["30"]},')
        self.csv_f.write(f'{self.d["210"]},{-self.d["220"]},{self.d["50"]},{self.d["41"]},{self.d["42"]},{self.d["43"]},{part_weight},{self.d["alert"]} \n')
        return

    def no_weight(self):
        #writing to csv file
        self.csv_f.write(f'{self.d["num"]},{self.d["layer"]},{self.d["2"]},-,-,None,{self.d["10"]},{-self.d["20"]},{self.d["30"]},')
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
            if self.d['42'] < 0:
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
            outstr += f'position="{self.d["41"]/2} {-y} {-self.d["42"]}" \n'
            if self.d['42'] > 0:
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
        outstr += f'position="0 {-y} {-self.d["42"]/2}" \n'
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
        outstr += f'position="{self.d["41"]} {-y} {-self.d["42"]/2}" \n'
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
            if self.d['42'] < 0:
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
            if self.d['42'] < 0:
                outstr += 'rotation="0 180 0"> \n'
            else:
                outstr += '> \n'
            outstr += self.part_striped_finishing()
            outstr += '</a-entity> \n'
            #inside top surface
            self.d['side'] = 'in'
            self.d['sub_side'] = 'in-top'
            self.d['width'] = fabs(self.d['41'])
            self.d['height'] = fabs(self.d['43'])

            outstr += f'<a-entity id="{self.d["2"]}-{self.d["num"]}-{self.d["sub_side"]}-ent" \n'
            outstr += f'position="{self.d["width"]/2} {self.d["door_height"]} 0" \n'
            if self.d['42'] < 0:
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
            outstr += f'position="{self.d["door_off_1"]/2} 0 {-self.d["42"]}" \n'
            if self.d['42'] > 0:
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
            outstr += f'position="{self.d["width"]/2+self.d["door_off_2"]} 0 {-self.d["42"]}" \n'
            if self.d['42'] > 0:
                outstr += 'rotation="0 180 0"> \n'
            else:
                outstr += '> \n'
            outstr += self.part_striped_finishing()
            outstr += '</a-entity> \n'
            #outside top surface
            self.d['side'] = 'out'
            self.d['sub_side'] = 'out-top'
            self.d['width'] = fabs(self.d['41'])
            self.d['height'] = fabs(self.d['43'])

            outstr += f'<a-entity id="{self.d["2"]}-{self.d["num"]}-{self.d["sub_side"]}-ent" \n'
            outstr += f'position="{self.d["width"]/2} {self.d["door_height"]} {-self.d["42"]}" \n'
            if self.d['42'] > 0:
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
            finishing = self.finishings.get(title = self.d[self.d['side']])
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

            self.csv_f.write(f'{self.d["num"]},{self.d["layer"]},{self.d["2"]},{self.d["sub_side"]},-,{part_image},-,-,-,-,-,-,-,{self.d["width"]},{self.d["height"]},-,-,- \n')
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
        if self.d['sub_side']=='in-top' or self.d['sub_side']=='out-top':
            door_height = fabs(self.d['door_height'])*self.d['43']/fabs(self.d['43'])
        else:
            door_height = 0

        try:
            finishing = self.finishings.get(title = self.d[self.d['side']])
            wall_height = fabs(self.d['height'])

            tiling_height = fabs(float(finishing.tiling_height))/100*self.d['43']/fabs(self.d['43'])
            skirting_height = fabs(float(finishing.skirting_height))/100*self.d['43']/fabs(self.d['43'])

            if door_height > wall_height:
                door_height = wall_height
                tiling_height = wall_height
                skirting_height = wall_height
            else:
                if skirting_height < door_height:
                    skirting_height = door_height
                if skirting_height > wall_height:
                    skirting_height = wall_height
                if tiling_height < skirting_height:
                    tiling_height = skirting_height
                if tiling_height > wall_height:
                    tiling_height = wall_height

            wall_height = wall_height - tiling_height
            tiling_height = tiling_height - skirting_height
            skirting_height = skirting_height - door_height

            if finishing.image:
                wall_image = 'finishing-' + finishing.title
                wall_repeat = finishing.pattern
            else:
                wall_image = self.d['8']
                wall_repeat = self.d['repeat']
            if finishing.color:
                wall_color = finishing.color
            else:
                wall_color = self.d['color']

            outstr = ''

            if wall_height:
                outstr += f'<a-plane id="{self.d["2"]}-{self.d["num"]}-{self.d["sub_side"]}" \n'
                outstr += f'position="0 {wall_height/2+tiling_height+skirting_height} 0" \n'
                outstr += f'width="{self.d["width"]}" height="{wall_height}" \n'
                outstr += f'material="src: #image-{wall_image}; color: {wall_color}'
                outstr += is_repeat(wall_repeat, self.d['width'], wall_height)
                outstr += '">\n</a-plane> \n'
                self.csv_f.write(f'{self.d["num"]},{self.d["layer"]},{self.d["2"]},{self.d["sub_side"]},Wall,{finishing.title},-,-,-,-,-,-,{self.d["width"]},{wall_height},-,-,- \n')

            if tiling_height:
                outstr += f'<a-plane id="{self.d["2"]}-{self.d["num"]}-{self.d["sub_side"]}-tiling" \n'
                outstr += f'position="0 {tiling_height/2+skirting_height} 0" \n'
                outstr += f'width="{self.d["width"]}" height="{tiling_height}" \n'
                outstr += f'material="src: #image-tiling-{finishing.title}; color: {finishing.tiling_color}'
                outstr += is_repeat(finishing.tiling_pattern, self.d['width'], tiling_height)
                outstr += '">\n</a-plane> \n'
                self.csv_f.write(f'{self.d["num"]},{self.d["layer"]},{self.d["2"]},{self.d["sub_side"]},Tiling,{finishing.title},-,-,-,-,-,-,{self.d["width"]},{tiling_height},-,-,- \n')

            if skirting_height:
                outstr += f'<a-plane id="{self.d["2"]}-{self.d["num"]}-{self.d["sub_side"]}-skirting" \n'
                outstr += f'position="0 {skirting_height/2} 0" \n'
                outstr += f'width="{self.d["width"]}" height="{skirting_height}" \n'
                outstr += f'material="src: #image-skirting-{finishing.title}; color: {finishing.skirting_color}'
                outstr += is_repeat(finishing.skirting_pattern, self.d['width'], skirting_height)
                outstr += '">\n</a-plane> \n'
                self.csv_f.write(f'{self.d["num"]},{self.d["layer"]},{self.d["2"]},{self.d["sub_side"]},Skirting,{finishing.title},-,-,-,-,-,-,{self.d["width"]},{skirting_height},-,-,- \n')

        except:
            outstr = f'<a-plane id="except-{self.d["2"]}-{self.d["num"]}-{self.d["sub_side"]}" \n'
            outstr += f'position="0 {(self.d["height"]-door_height)/2} 0" \n'
            outstr += f'width="{self.d["width"]}" height="{self.d["height"]-door_height}" \n'
            outstr += f'material="src: #image-{self.d["8"]}; color: {self.d["color"]}'
            outstr += is_repeat(self.d["repeat"], self.d["width"], self.d["height"]-door_height)
            outstr += f'">\n</a-plane> \n'
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

class AOpening(object):#face it, this could be a APartition subclass
    def __init__(self, data, types, finishings, csv_f):
        self.d = data#is it possible to use the self.__dict__=data construct? it would be much cleaner
        self.d['alert'] = 'None'
        self.type_obj = False
        if self.d['type']:
            try:
                self.type_obj = types.get(title = self.d['type'])
            except:
                pass
        self.finishings = finishings
        self.csv_f = csv_f

    def has_type(self):
        #we don't calculate door weight, but we change appearance accordingly to partition type
        if self.type_obj.image:
            self.d['8'] = 'partition-' + self.type_obj.title
            self.d['repeat'] = self.type_obj.pattern
        if self.type_obj.color:
            self.d['color'] = self.type_obj.color
        #writing to csv file
        opening_weight = 0#by now useless
        self.csv_f.write(f'{self.d["num"]},{self.d["layer"]},{self.d["2"]},-,-,{self.type_obj.title},{self.d["10"]},{-self.d["20"]},{self.d["30"]},')
        self.csv_f.write(f'{self.d["210"]},{-self.d["220"]},{self.d["50"]},{self.d["41"]},{self.d["42"]},{self.d["43"]},{opening_weight},{self.d["alert"]} \n')
        return

    def no_type(self):
        #writing to csv file
        self.csv_f.write(f'{self.d["num"]},{self.d["layer"]},{self.d["2"]},-,-,None,{self.d["10"]},{-self.d["20"]},{self.d["30"]},')
        self.csv_f.write(f'{self.d["210"]},{-self.d["220"]},{self.d["50"]},{self.d["41"]},{self.d["42"]},{self.d["43"]},0,{self.d["alert"]} \n')
        return

    def write_html(self):
        #start entity
        outstr = f'<a-entity id="{self.d["2"]}-{self.d["num"]}" \n'
        outstr += f'position="{self.d["10"]} {self.d["30"]} {self.d["20"]}" \n'
        outstr += f'rotation="{self.d["210"]} {self.d["50"]} {self.d["220"]}">\n'
        #left frame
        outstr += f'<a-box id="{self.d["2"]}-{self.d["num"]}-left-frame" \n'
        outstr += f'position="{-0.049*self.unit(self.d["41"])} {(self.d["43"]+0.099*self.unit(self.d["43"]))/2} {-self.d["42"]/2}" \n'
        outstr += f'scale="0.1 {fabs(self.d["43"])+0.099} {fabs(self.d["42"])+0.02}" \n'
        outstr += f'material="color: {self.d["color"]}">'
        outstr += '</a-box>\n'
        #right frame
        outstr += f'<a-box id="{self.d["2"]}-{self.d["num"]}-right-frame" \n'
        outstr += f'position="{self.d["41"]+0.049*self.unit(self.d["41"])} {(self.d["43"]+0.099*self.unit(self.d["43"]))/2} {-self.d["42"]/2}" \n'
        outstr += f'scale="0.1 {fabs(self.d["43"])+0.099} {fabs(self.d["42"])+0.02}" \n'
        outstr += f'material="color: {self.d["color"]}">'
        outstr += '</a-box>\n'
        #top frame
        outstr += f'<a-box id="{self.d["2"]}-{self.d["num"]}-top-frame" \n'
        outstr += f'position="{self.d["41"]/2} {self.d["43"]+0.049*self.unit(self.d["43"])} {-self.d["42"]/2}" \n'
        outstr += f'scale="{fabs(self.d["41"])-0.002} 0.1 {fabs(self.d["42"])+0.02}" \n'
        outstr += f'material="color: {self.d["color"]}">'
        outstr += '</a-box>\n'

        if self.d["type"] == 'ghost':
            outstr += '</a-entity>\n'
            return outstr
        else:
            if eval(self.d["sliding"]):
                if eval(self.d["double"]):
                    #animated slide 1
                    outstr += f'<a-entity id="{self.d["2"]}-{self.d["num"]}-slide-1"> \n'
                    outstr += f'<a-animation attribute="position" from="0 0 0" to="{-(self.d["41"])/2} 0 0" begin="click" repeat="1" direction="alternate"></a-animation>'
                    #moving part 1
                    outstr += f'<a-box id="{self.d["2"]}-{self.d["num"]}-moving-part-1" \n'
                    outstr += f'position="{self.d["41"]/4} {(self.d["43"]-0.001*self.unit(self.d["43"]))/2} {-self.d["42"]/2}" \n'
                    outstr += f'scale="{(fabs(self.d["41"]))/2-0.002} {self.d["43"]-0.001*self.unit(self.d["43"])} 0.05" \n'
                    outstr += f'material="src: #image-{self.d["8"]}; color: {self.d["color"]}'
                    outstr += is_repeat(self.d["repeat"], (fabs(self.d["41"]))/2-0.002, self.d["43"]-0.001*self.unit(self.d["43"]))
                    outstr += '"></a-box>\n'
                    outstr += '</a-entity>\n'
                    #animated slide 2
                    outstr += f'<a-entity id="{self.d["2"]}-{self.d["num"]}-slide-2" \n'
                    outstr += f'position="{self.d["41"]} 0 0"> \n'
                    outstr += f'<a-animation attribute="position" from="{self.d["41"]} 0 0" to="{(self.d["41"])*3/2} 0 0" begin="click" repeat="1" direction="alternate"></a-animation>'
                    #moving part 2
                    outstr += f'<a-box id="{self.d["2"]}-{self.d["num"]}-moving-part-2" \n'
                    outstr += f'position="{-self.d["41"]/4} {(self.d["43"]-0.001*self.unit(self.d["43"]))/2} {-self.d["42"]/2}" \n'
                    outstr += f'scale="{(fabs(self.d["41"]))/2-0.002} {self.d["43"]-0.001*self.unit(self.d["43"])} 0.05" \n'
                    outstr += f'material="src: #image-{self.d["8"]}; color: {self.d["color"]}'
                    outstr += is_repeat(self.d["repeat"], (fabs(self.d["41"]))/2-0.002, self.d["43"]-0.001*self.unit(self.d["43"]))
                    outstr += '"></a-box>\n'
                    outstr += '</a-entity>\n'
                    #end entity
                    outstr += '</a-entity>\n'
                    return outstr
                else:#single
                    #animated slide
                    outstr += f'<a-entity id="{self.d["2"]}-{self.d["num"]}-slide"> \n'
                    outstr += f'<a-animation attribute="position" from="0 0 0" to="{-self.d["41"]} 0 0" begin="click" repeat="1" direction="alternate"></a-animation>'
                    #moving part
                    outstr += f'<a-box id="{self.d["2"]}-{self.d["num"]}-moving-part" \n'
                    outstr += f'position="{self.d["41"]/2} {(self.d["43"]-0.001*self.unit(self.d["43"]))/2} {-self.d["42"]/2}" \n'
                    outstr += f'scale="{fabs(self.d["41"])-0.002} {self.d["43"]-0.001*self.unit(self.d["43"])} 0.05" \n'
                    outstr += f'material="src: #image-{self.d["8"]}; color: {self.d["color"]}'
                    outstr += is_repeat(self.d["repeat"], fabs(self.d["41"])-0.002, self.d["43"]-0.001*self.unit(self.d["43"]))
                    outstr += '"></a-box>\n'
                    outstr += '</a-entity>\n'
                    #end entity
                    outstr += '</a-entity>\n'
                    return outstr
            else:#hinged
                if eval(self.d["double"]):
                    #animated hinge 1
                    outstr += f'<a-entity id="{self.d["2"]}-{self.d["num"]}-hinge-1"> \n'
                    outstr += f'<a-animation attribute="rotation" from="0 0 0" to="0 {-90*self.unit(self.d["41"])*self.unit(self.d["42"])} 0" begin="click" repeat="1" direction="alternate"></a-animation>'
                    #moving part 1
                    outstr += f'<a-box id="{self.d["2"]}-{self.d["num"]}-moving-part-1" \n'
                    outstr += f'position="{self.d["41"]/4} {(self.d["43"]-0.001*self.unit(self.d["43"]))/2} {-0.025*self.unit(self.d["42"])}" \n'
                    outstr += f'scale="{(fabs(self.d["41"]))/2-0.002} {self.d["43"]-0.001*self.unit(self.d["43"])} 0.05" \n'
                    outstr += f'material="src: #image-{self.d["8"]}; color: {self.d["color"]}'
                    outstr += is_repeat(self.d["repeat"], (fabs(self.d["41"]))/2-0.002, self.d["43"]-0.001*self.unit(self.d["43"]))
                    outstr += '"></a-box>\n'
                    outstr += '</a-entity>\n'
                    #animated hinge 2
                    outstr += f'<a-entity id="{self.d["2"]}-{self.d["num"]}-hinge-2" '
                    outstr += f'position="{self.d["41"]} 0 0"> \n'
                    outstr += f'<a-animation attribute="rotation" from="0 0 0" to="0 {90*self.unit(self.d["41"])*self.unit(self.d["42"])} 0" begin="click" repeat="1" direction="alternate"></a-animation>'
                    #moving part 2
                    outstr += f'<a-box id="{self.d["2"]}-{self.d["num"]}-moving-part-2" \n'
                    outstr += f'position="{-self.d["41"]/4} {(self.d["43"]-0.001*self.unit(self.d["43"]))/2} {-0.025*self.unit(self.d["42"])}" \n'
                    outstr += f'scale="{(fabs(self.d["41"]))/2-0.002} {self.d["43"]-0.001*self.unit(self.d["43"])} 0.05" \n'
                    outstr += f'material="src: #image-{self.d["8"]}; color: {self.d["color"]}'
                    outstr += is_repeat(self.d["repeat"], (fabs(self.d["41"]))/2-0.002, self.d["43"]-0.001*self.unit(self.d["43"]))
                    outstr += '"></a-box>\n'
                    outstr += '</a-entity>\n'
                    #end entity
                    outstr += '</a-entity>\n'
                    return outstr
                else:#single
                    #animated hinge
                    outstr += f'<a-entity id="{self.d["2"]}-{self.d["num"]}-hinge"> \n'
                    outstr += f'<a-animation attribute="rotation" from="0 0 0" to="0 {-90*self.unit(self.d["41"])*self.unit(self.d["42"])} 0" begin="click" repeat="1" direction="alternate"></a-animation>'
                    #moving part
                    outstr += f'<a-box id="{self.d["2"]}-{self.d["num"]}-moving-part" \n'
                    outstr += f'position="{self.d["41"]/2} {(self.d["43"]-0.001*self.unit(self.d["43"]))/2} {-0.025*self.unit(self.d["42"])}" \n'
                    outstr += f'scale="{fabs(self.d["41"])-0.002} {self.d["43"]-0.001*self.unit(self.d["43"])} 0.05" \n'
                    outstr += f'material="src: #image-{self.d["8"]}; color: {self.d["color"]}'
                    outstr += is_repeat(self.d["repeat"], fabs(self.d["41"])-0.002, self.d["43"]-0.001*self.unit(self.d["43"]))
                    outstr += '"></a-box>\n'
                    outstr += '</a-entity>\n'
                    #end entity
                    outstr += '</a-entity>\n'
                    return outstr

    def unit(self, nounit):
        unit = fabs(nounit)/nounit
        return unit

    def is_repeat(self, repeat, rx, rz):#this repetition (!) makes me think that this should be a subclass of APartition
        if repeat:
            output = f'; repeat:{rx} {ry}'
            return output
        else:
            return ';'

def cad2hex(cad_color):
    cad_color = abs(int(cad_color))
    if cad_color<0 or cad_color>255:
        return 'white'
    else:
        RGB_list = (
        		 (0, 0, 0),
        		 (255, 0, 0),
        		 (255, 255, 0),
        		 (0, 255, 0),
        		 (0, 255, 255),
        		 (0, 0, 255),
        		 (255, 0, 255),
        		 (255, 255, 255),
        		 (128, 128, 128),
        		 (192, 192, 192),
        		 (255, 0, 0),
        		 (255, 127, 127),
        		 (165, 0, 0),
        		 (165, 82, 82),
        		 (127, 0, 0),
        		 (127, 63, 63),
        		 (76, 0, 0),
        		 (76, 38, 38),
        		 (38, 0, 0),
        		 (38, 19, 19),
        		 (255, 63, 0),
        		 (255, 159, 127),
        		 (165, 41, 0),
        		 (165, 103, 82),
        		 (127, 31, 0),
        		 (127, 79, 63),
        		 (76, 19, 0),
        		 (76, 47, 38),
        		 (38, 9, 0),
        		 (38, 23, 19),
        		 (255, 127, 0),
        		 (255, 191, 127),
        		 (165, 82, 0),
        		 (165, 124, 82),
        		 (127, 63, 0),
        		 (127, 95, 63),
        		 (76, 38, 0),
        		 (76, 57, 38),
        		 (38, 19, 0),
        		 (38, 28, 19),
        		 (255, 191, 0),
        		 (255, 223, 127),
        		 (165, 124, 0),
        		 (165, 145, 82),
        		 (127, 95, 0),
        		 (127, 111, 63),
        		 (76, 57, 0),
        		 (76, 66, 38),
        		 (38, 28, 0),
        		 (38, 33, 19),
        		 (255, 255, 0),
        		 (255, 255, 127),
        		 (165, 165, 0),
        		 (165, 165, 82),
        		 (127, 127, 0),
        		 (127, 127, 63),
        		 (76, 76, 0),
        		 (76, 76, 38),
        		 (38, 38, 0),
        		 (38, 38, 19),
        		 (191, 255, 0),
        		 (223, 255, 127),
        		 (124, 165, 0),
        		 (145, 165, 82),
        		 (95, 127, 0),
        		 (111, 127, 63),
        		 (57, 76, 0),
        		 (66, 76, 38),
        		 (28, 38, 0),
        		 (33, 38, 19),
        		 (127, 255, 0),
        		 (191, 255, 127),
        		 (82, 165, 0),
        		 (124, 165, 82),
        		 (63, 127, 0),
        		 (95, 127, 63),
        		 (38, 76, 0),
        		 (57, 76, 38),
        		 (19, 38, 0),
        		 (28, 38, 19),
        		 (63, 255, 0),
        		 (159, 255, 127),
        		 (41, 165, 0),
        		 (103, 165, 82),
        		 (31, 127, 0),
        		 (79, 127, 63),
        		 (19, 76, 0),
        		 (47, 76, 38),
        		 (9, 38, 0),
        		 (23, 38, 19),
        		 (0, 255, 0),
        		 (127, 255, 127),
        		 (0, 165, 0),
        		 (82, 165, 82),
        		 (0, 127, 0),
        		 (63, 127, 63),
        		 (0, 76, 0),
        		 (38, 76, 38),
        		 (0, 38, 0),
        		 (19, 38, 19),
        		 (0, 255, 63),
        		 (127, 255, 159),
        		 (0, 165, 41),
        		 (82, 165, 103),
        		 (0, 127, 31),
        		 (63, 127, 79),
        		 (0, 76, 19),
        		 (38, 76, 47),
        		 (0, 38, 9),
        		 (19, 38, 23),
        		 (0, 255, 127),
        		 (127, 255, 191),
        		 (0, 165, 82),
        		 (82, 165, 124),
        		 (0, 127, 63),
        		 (63, 127, 95),
        		 (0, 76, 38),
        		 (38, 76, 57),
        		 (0, 38, 19),
        		 (19, 38, 28),
        		 (0, 255, 191),
        		 (127, 255, 223),
        		 (0, 165, 124),
        		 (82, 165, 145),
        		 (0, 127, 95),
        		 (63, 127, 111),
        		 (0, 76, 57),
        		 (38, 76, 66),
        		 (0, 38, 28),
        		 (19, 38, 33),
        		 (0, 255, 255),
        		 (127, 255, 255),
        		 (0, 165, 165),
        		 (82, 165, 165),
        		 (0, 127, 127),
        		 (63, 127, 127),
        		 (0, 76, 76),
        		 (38, 76, 76),
        		 (0, 38, 38),
        		 (19, 38, 38),
        		 (0, 191, 255),
        		 (127, 223, 255),
        		 (0, 124, 165),
        		 (82, 145, 165),
        		 (0, 95, 127),
        		 (63, 111, 127),
        		 (0, 57, 76),
        		 (38, 66, 76),
        		 (0, 28, 38),
        		 (19, 33, 38),
        		 (0, 127, 255),
        		 (127, 191, 255),
        		 (0, 82, 165),
        		 (82, 124, 165),
        		 (0, 63, 127),
        		 (63, 95, 127),
        		 (0, 38, 76),
        		 (38, 57, 76),
        		 (0, 19, 38),
        		 (19, 28, 38),
        		 (0, 63, 255),
        		 (127, 159, 255),
        		 (0, 41, 165),
        		 (82, 103, 165),
        		 (0, 31, 127),
        		 (63, 79, 127),
        		 (0, 19, 76),
        		 (38, 47, 76),
        		 (0, 9, 38),
        		 (19, 23, 38),
        		 (0, 0, 255),
        		 (127, 127, 255),
        		 (0, 0, 165),
        		 (82, 82, 165),
        		 (0, 0, 127),
        		 (63, 63, 127),
        		 (0, 0, 76),
        		 (38, 38, 76),
        		 (0, 0, 38),
        		 (19, 19, 38),
        		 (63, 0, 255),
        		 (159, 127, 255),
        		 (41, 0, 165),
        		 (103, 82, 165),
        		 (31, 0, 127),
        		 (79, 63, 127),
        		 (19, 0, 76),
        		 (47, 38, 76),
        		 (9, 0, 38),
        		 (23, 19, 38),
        		 (127, 0, 255),
        		 (191, 127, 255),
        		 (82, 0, 165),
        		 (124, 82, 165),
        		 (63, 0, 127),
        		 (95, 63, 127),
        		 (38, 0, 76),
        		 (57, 38, 76),
        		 (19, 0, 38),
        		 (28, 19, 38),
        		 (191, 0, 255),
        		 (223, 127, 255),
        		 (124, 0, 165),
        		 (145, 82, 165),
        		 (95, 0, 127),
        		 (111, 63, 127),
        		 (57, 0, 76),
        		 (66, 38, 76),
        		 (28, 0, 38),
        		 (33, 19, 38),
        		 (255, 0, 255),
        		 (255, 127, 255),
        		 (165, 0, 165),
        		 (165, 82, 165),
        		 (127, 0, 127),
        		 (127, 63, 127),
        		 (76, 0, 76),
        		 (76, 38, 76),
        		 (38, 0, 38),
        		 (38, 19, 38),
        		 (255, 0, 191),
        		 (255, 127, 223),
        		 (165, 0, 124),
        		 (165, 82, 145),
        		 (127, 0, 95),
        		 (127, 63, 111),
        		 (76, 0, 57),
        		 (76, 38, 66),
        		 (38, 0, 28),
        		 (38, 19, 33),
        		 (255, 0, 127),
        		 (255, 127, 191),
        		 (165, 0, 82),
        		 (165, 82, 124),
        		 (127, 0, 63),
        		 (127, 63, 95),
        		 (76, 0, 38),
        		 (76, 38, 57),
        		 (38, 0, 19),
        		 (38, 19, 28),
        		 (255, 0, 63),
        		 (255, 127, 159),
        		 (165, 0, 41),
        		 (165, 82, 103),
        		 (127, 0, 31),
        		 (127, 63, 79),
        		 (76, 0, 19),
        		 (76, 38, 47),
        		 (38, 0, 9),
        		 (38, 19, 23),
        		 (0, 0, 0),
        		 (51, 51, 51),
        		 (102, 102, 102),
        		 (153, 153, 153),
        		 (204, 204, 204),
        		 (255, 255, 255),
        		)
        r = RGB_list[cad_color][0]
        g = RGB_list[cad_color][1]
        b = RGB_list[cad_color][2]
        hex = "#{:02x}{:02x}{:02x}".format(r,g,b)
        return hex
