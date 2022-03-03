# TkFire
TkInter manager using dictionaries

Ben Canty - November 5, 2021

To facilitate in the creation of tkinter GUIs

Using the tkinter, ttkinter, and scrolledtext modules and allowing for user-defined widgets, a TkFire object is a class which automates the tedium of creating, naming, packing, and linking objects.

The general definition is:

- name_of_frame_1:
  - LAYOUT: \[packing method (i.e. 'pack' or 'grid'), {kwargs for pack or grid}]
  - TYPE: \[name of widget_class, {kwargs for the the widget.\_\_init\_\_() method}]
  - CHILDREN:
    - name_of_widget_1:
      - TYPE: \['name of widget_class', {kwargs for the the widget.\_\_init\_\_() method}]
      - LAYOUT: \[packing method (i.e. 'pack' or 'grid'), {kwargs for pack or grid}]
    - name_of_widget_2:
      - TYPE: \['Button', {'text': "Button 2", 'command': name_of_user_defined_command}]
      - LAYOUT: \['grid', {'row': 1, 'column': 0}]

And elements can be addressed 'name_of_frame_1!name_of_widget_1'
