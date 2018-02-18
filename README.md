# PYMba

A basic BIM as a [Django](https://www.djangoproject.com/) / [Wagtail](https://wagtail.io/) app that imports [CAD](https://en.wikipedia.org/wiki/AutoCAD_DXF) files and renders Virtual Reality using [A-Frame](https://aframe.io) library.

### What does PYMba mean?

Main project was named BIMba or [BIM-ba](http://bim-ba.net), which stands for "basic Building Information Modeling". Now the app is written in Python, so BI becomes PY.

### How to get DXF files

DXF files are drawing exchange files, and they are human readable (if in ASCII format). Obviously you will need a CAD if you want to generate your own files. For free I recommend [NanoCAD](http://nanocad.com/) even if you won't be able to work with solids. It doesn't matter, you won't need them. Unfortunately open source CAD projects never match the industry.

Lots of programs deal with DXF, but the goal here is to have blocks with attributes (data!), not just surfaces. Refer to the DXF constraints paragraph to understand what your files have to look like.

### Install Wagtail app

The app can be cloned or downloaded from [Github](https://github.com/andywar65/pymba). Using a shell get into the project folder and type  `git clone https://github.com/andywar65/pymba`. Add `pymba` to the INSTALLED_APPS in your settings file. Migrate. The app's templates look for a `base.html` file, so be sure to have one.

### DXF constraints

Generate a DXF in ascii mode and don't try to modify it. DXF is a sequence of key / value pairs, and deleting just one line can break up everything. By now only 3Dfaces and standard blocks (see further) can be translated, other entities will just be ignored. Create as many layers as you need, and place your entities on the desired one. Layers relate to the appearance of the entity, how it's explained in the backend paragraph.

To include meshes, explode them to 3Dfaces (I know it's bad, but this is how it works by now). If you have an Acis solid, use `3DCONVERT` to obtain a mesh, then explode it.

### Standard blocks

Standard blocks may be found in `static/samples/standard-blocks.dxf` bundled within the app: box, cylinder, cone, sphere, circle, plane, look-at, text, links and lights. These mimic entities of the A-Frame library, with unit dimensions. Insert the block and scale it to the desired width, length and height. You can rotate it along all axis (previous limitations solved thanks to [Marilena Vendittelli](http://www.dis.uniroma1.it/~venditt/)). You can explode the standard blocks without affecting geometry: they will degrade to a series of 3D faces.

Standard blocks come with attributes that affect their geometry. In CAD, attributes are prompted when inserting a block, and can be modified in the Property window. To understand how attributes affect geometry, refer to [A-Frame Documentation](https://aframe.io/docs/0.7.0/primitives/a-box.html) .

Light standard block has a `type` attribute which can be set to ambient, directional, point and spot. Refer to [A-Frame Light Component Documentation](https://aframe.io/docs/0.7.0/components/light.html) for further details.

Look-at standard block is a plane that always faces the camera.

Text standard block is a text centered in a bounding plane. The attributes control alignment, content and wrap count, which is the number of letters that fill the width of the bounding plane.

Link standard block allows you to link different pages on a click. The `Tree` attribute lets you select among parent, previous, next and first child page. If target has an equirectangular image (see backend paragraph) it will appear in the link.

### Wagtail backend

Create a page of the `Pymba Page` kind. You will have to enter a Title and an Intro for the page, and an Equirectangular Image for the background (if none, a default one will be picked). Equirectangular images are like those planispheres where Greenland is bigger than Africa. In the Visual Settings panel you will have to check if you want your shadows on, if you want your camera to be able to fly and if 3D faces must be double sided.

Then load the most important stuff: the DXF file. It will be stored in the `media/documents` folder. After that, you may create as many Material Gallery items as the layers used in the DXF file. Each material needs a Name that must match the layer name (default is `0`), an Image that will be applied to the entity and a Color. If the image is a 1x1 meter pattern, check the appropriate box. Default color is `white`, but you can use hexadecimal notation (like `#ffffff`) or standard HTML colors. Color affects appearance of the image. If you don't add materials, elements will be just white.

Okay, now publish and go to the frontend to see how your model behaves.

### Interaction

The model window is embedded within your website, but you can go fullscreen by pressing `F` or the visor icon in the right bottom corner of the window. On some mobiles the image will be split in two, with stereoscopic effect. You will need one of those cardboard headgears to appreciate the effect. Press `ESC` to exit fullscreen mode. On laptops, if you want to look around, you have to press and drag the mouse. To move around press the `W-A-S-D` keys. On some mobiles you literally walk to explore the model, but I've never experienced that. Last but not least, press the `Ctrl+Alt+I` to 
enter the Inspector mode, that makes you inspect and modify the entities of the model. Modifications can be saved to HTML files.

### BIM standard blocks

BIM standard blocks are recognized as real life building elements. By now we have only the `Wall` BIM element. It behaves pretty much as a box, but attributes are different: wall `type` and inside, outside, right and left `finishing`.

Wall types are defined in the backend as `PYMba Wall Pages`, and must be children of the `Pymba Page` they are related to. Creating a new wall type requires Title, Intro, Image (is it a pattern?) and Color. You can then add as many wall Layers to the Wall Type as you want. Layers require a Material, a Thickness (in centimeters) and a Weight in kilograms per cubic meter.
The app controls if wall dimensions in CAD are consistent with Wall Type features, i.e. wall thickness. If inconsistency arises, wall is rendered in flat red. 

Wall data is stored in a CSV file downloadable from the frontend. Data includes wall weight.

### Next improvements

Wall surfaces.