# TkFire
TkInter manager using dictionaries

Richard "Ben" Canty - November 5, 2021

To facilitate in the creation of tkinter GUIs

Using the tkinter modules and allowing for user-defined widgets, a TkFire object is a class which automates the tedium of creating, naming, packing, and linking objects.

The general definition is:

- name_of_frame_1:
  - LAYOUT: packing method (fire_pack(), fire_grid(), and fire_place() are provided for convenience)
  - TYPE: widget_class, args, and kwargs for the widget's \_\_init\_\_() method} (spec() provided for convenience)
  - CHILDREN:
    - name_of_widget_1:
      - TYPE: (same as above)
      - LAYOUT: (same as above)
      - POST: A list of commands to execute after the parent ('name_of_widget_1') is created and located in the GUI (post() provided for convenience)
    - name_of_widget_2:
      - TYPE: (same as above)
      - LAYOUT: (same as above)
      - CHILDREN: ...

And elements can be addressed 'name_of_frame_1!name_of_widget_1'

The children of a frame can be widgets or another frame, the syntax allows for nesting and multiple layers.

TYPE and LAYOUT are required, CHILDREN and POST are optional

The spec() and post() methods format entries for TYPE and POST to spare the need to specify a 
tuple\[type | str, tuple, dict\] for each of them.  The first argument of spec is a constructor (e.g. Frame, Button)
and the first argument of post is a string naming a callable attribute of the parent object.  Both will then take
args and kwargs like a python function.

The Memory object allows for the specification of constructable tkinter objects to be initialized and declared at
build time (e.g. IntVar, StringVar) as well as for variables to undergo dynamically determined unpacking (e.g.
a variable, X, may be passed into a constructor as X, *X, or **X as determined by the parameter 'unpack', which
may be 0, 1, or 2, respectively)
