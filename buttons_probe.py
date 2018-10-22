from tkinter import *

class ButtonCanvas(Canvas):
    """docstring for ButtonCanvas"""
    def __init__(self, *args, w=40, h=40, oncolor='blue', offcolor='white', placekw={}, callback=None, **kw):
        assert callback is not None
        super().__init__(*args, **kw)
        self.place(w=w, h=h, **placekw)

        self.colors = [offcolor, oncolor]
        self.external_callback = callback

        self.create_rectangle([0, 0], [w, h/2], fill=self.colors[0], tag='up')
        self.create_rectangle([0, h/2], [w, h], fill=self.colors[0], tag='down')

        self.create_line([w/2-6, h/4+3], [w/2, h/4-3], [w/2+6, h/4+3], fill=self.colors[1], tag='up_arrow')
        self.create_line([w/2-6, h*3/4-3], [w/2, h*3/4+3], [w/2+6, h*3/4-3], fill=self.colors[1], tag='down_arrow')

        def get_callback(kind, direction):
            return lambda event: self.callback(kind, direction)
        for kind in ('up', 'down'):
            for direction in ('Press', 'Release'):
                def _fun(event):
                    self.callback(kind, direction)
                self.tag_bind(kind, '<Button{}-1>'.format(direction), get_callback(kind, direction))
                self.tag_bind(kind+'_arrow', '<Button{}-1>'.format(direction), get_callback(kind, direction))
    def callback(self, kind, direction):
        directions = ('Press', 'Release')
        kinds = ('up', 'down')
        assert kind in kinds
        assert direction in directions

        di = directions.index(direction)
        self.itemconfig(kind, fill=self.colors[1-di])
        self.itemconfig(kind + '_arrow', fill=self.colors[di])
        if 1:
            self.external_callback(kind, direction)
if __name__ == '__main__':
    root = Tk()
    root.geometry('{w}x{h}+{x}+{y}'.format(w=640, h=480, x=10, y=10))
    root.resizable(True, True)
    root.title('Tk')

    bc = ButtonCanvas(root, callback=print)
    bc.place(x=50, y=50, width=40, height=40)
    root.mainloop()
