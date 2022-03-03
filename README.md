# TkFire
TkInter manager using dictionaries
Ben Canty - November 5, 2021
To facilitate in the creation of tkinter GUIs

Using the tkinter, ttkinter, and scrolledtext modules and allowing for user-defined widgets, a TkFire object is a class which automates the tedium of creating, naming, packing, and linking objects.

The general definition is:

'name_of_frame_1': {\n
    LAYOUT: \[packing method (i.e. 'pack' or 'grid'), {kwargs for pack or grid}],\n
    TYPE: \[name of widget_class, {kwargs for the the widget.\_\_init\_\_() method}],\n
    CHILDREN: {\n
        'name_of_widget_1': {\n
            TYPE: \['name of widget_clas', {kwargs for the the widget.\_\_init\_\_() method}],\n
            LAYOUT: \[packing method (i.e. 'pack' or 'grid'), {kwargs for pack or grid}],\n
        },\n
        'name_of_widget_2': {\n
            TYPE: \['Button', {'text': "Button 2", 'command': name_of_user_defined_command}],\n
            LAYOUT: \['grid', {'row': 1, 'column': 0}],\n
        },\n
    },\n
}

And elements can be addressed 'name_of_frame_1!name_of_widget_1'
